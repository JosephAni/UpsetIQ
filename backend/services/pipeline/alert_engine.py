"""Alert engine - detects threshold crossings and delivers alerts."""
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

from services.supabase_client import (
    get_supabase_client,
    get_subscriptions_by_threshold,
    get_pending_alerts,
    queue_alert,
    mark_alert_sent,
    mark_alert_failed,
    pipeline_run_context,
    is_supabase_configured,
)

logger = logging.getLogger(__name__)

# Import WebSocket and webhook services
try:
    from services.websocket_server import broadcast_alert, emit_to_room
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False
    logger.warning("WebSocket server not available")

try:
    from services.webhook import send_push_notification, send_webhook
    WEBHOOK_AVAILABLE = True
except ImportError:
    WEBHOOK_AVAILABLE = False
    logger.warning("Webhook service not available")


def format_alert_message(
    game: Dict[str, Any],
    ups_score: float,
    signals: List[str],
) -> tuple:
    """
    Format alert title and message.
    
    Returns:
        Tuple of (title, message)
    """
    favorite = game.get("favorite", "Team A")
    underdog = game.get("underdog", "Team B")
    
    # Title based on UPS score
    if ups_score >= 75:
        title = f"🔥 HIGH ALERT: {underdog} upset potential!"
    elif ups_score >= 65:
        title = f"⚠️ ALERT: {underdog} upset watch"
    else:
        title = f"📊 {underdog} vs {favorite} update"
    
    # Build message
    message_parts = [
        f"{underdog} (+{int(ups_score)}% upset probability) vs {favorite}",
    ]
    
    if signals:
        message_parts.append("")
        message_parts.append("Key signals:")
        for signal in signals[:3]:
            message_parts.append(f"• {signal}")
    
    message = "\n".join(message_parts)
    
    return title, message


async def check_threshold_alerts() -> List[Dict[str, Any]]:
    """
    Check for games that have crossed user UPS thresholds.
    
    Returns:
        List of alerts to send
    """
    if not is_supabase_configured():
        return []
    
    alerts_to_send = []
    
    try:
        client = get_supabase_client()
        
        # Get games with high UPS scores
        result = (
            client.table("game_features")
            .select("*")
            .gte("ups_score", 55)  # Minimum threshold to check
            .order("ups_score", desc=True)
            .execute()
        )
        
        high_ups_games = result.data or []
        
        for game in high_ups_games:
            ups_score = game.get("ups_score", 0)
            game_id = game.get("game_id")
            
            # Get subscriptions for this UPS level
            subscriptions = get_subscriptions_by_threshold(ups_score, "NFL")
            
            for sub in subscriptions:
                user_id = sub.get("user_id")
                threshold = sub.get("ups_threshold", 65)
                
                # Check if we already sent an alert for this game/user
                existing = (
                    client.table("alert_queue")
                    .select("id")
                    .eq("game_id", game_id)
                    .eq("user_id", user_id)
                    .eq("alert_type", "ups_threshold")
                    .execute()
                )
                
                if existing.data:
                    continue  # Already alerted
                
                # Format and queue alert
                title, message = format_alert_message(
                    game,
                    ups_score,
                    [],  # Would parse signals from metadata
                )
                
                alert = {
                    "user_id": user_id,
                    "game_id": game_id,
                    "alert_type": "ups_threshold",
                    "title": title,
                    "message": message,
                    "ups_score": ups_score,
                    "threshold": threshold,
                    "push_token": sub.get("push_token"),
                    "push_provider": sub.get("push_provider"),
                    "websocket_enabled": sub.get("websocket_enabled", True),
                    "push_enabled": sub.get("push_enabled", True),
                }
                
                alerts_to_send.append(alert)
    
    except Exception as e:
        logger.error(f"Error checking threshold alerts: {e}")
    
    return alerts_to_send


async def deliver_alert(alert: Dict[str, Any]) -> bool:
    """
    Deliver a single alert via configured channels.
    
    Args:
        alert: Alert data dictionary
        
    Returns:
        True if delivered successfully
    """
    alert_id = alert.get("id")
    delivered = False
    
    try:
        # 1. WebSocket delivery
        if alert.get("websocket_enabled", True) and WEBSOCKET_AVAILABLE:
            try:
                await broadcast_alert({
                    "type": alert.get("alert_type"),
                    "title": alert.get("title"),
                    "message": alert.get("message"),
                    "game_id": alert.get("game_id"),
                    "ups_score": alert.get("ups_score"),
                })
                logger.info(f"Alert {alert_id} sent via WebSocket")
                delivered = True
            except Exception as e:
                logger.error(f"WebSocket delivery failed: {e}")
        
        # 2. Push notification delivery
        if alert.get("push_enabled", True) and WEBHOOK_AVAILABLE:
            push_token = alert.get("push_token")
            push_provider = alert.get("push_provider")
            
            if push_token:
                try:
                    success = await send_push_notification(
                        token=push_token,
                        provider=push_provider,
                        title=alert.get("title"),
                        body=alert.get("message"),
                        data={
                            "game_id": alert.get("game_id"),
                            "ups_score": alert.get("ups_score"),
                            "alert_type": alert.get("alert_type"),
                        },
                    )
                    if success:
                        logger.info(f"Alert {alert_id} sent via push")
                        delivered = True
                except Exception as e:
                    logger.error(f"Push delivery failed: {e}")
        
        # Mark as delivered
        if delivered and alert_id:
            mark_alert_sent(alert_id, "push" if alert.get("push_enabled") else "websocket")
        
        return delivered
    
    except Exception as e:
        logger.error(f"Alert delivery failed: {e}")
        if alert_id:
            mark_alert_failed(alert_id, str(e))
        return False


async def process_pending_alerts() -> Dict[str, int]:
    """
    Process all pending alerts in the queue.
    
    Returns:
        Dict with counts of processed, delivered, failed
    """
    stats = {
        "processed": 0,
        "delivered": 0,
        "failed": 0,
    }
    
    try:
        pending = get_pending_alerts(limit=100)
        
        for alert in pending:
            stats["processed"] += 1
            
            success = await deliver_alert(alert)
            
            if success:
                stats["delivered"] += 1
            else:
                stats["failed"] += 1
    
    except Exception as e:
        logger.error(f"Error processing pending alerts: {e}")
    
    return stats


async def run_alert_processing() -> Dict[str, Any]:
    """
    Run the alert processing pipeline.
    
    1. Check for threshold crossings
    2. Queue new alerts
    3. Deliver pending alerts
    
    Returns:
        Job result summary
    """
    logger.info("Starting alert processing job")
    
    if not is_supabase_configured():
        logger.warning("Supabase not configured - skipping alert processing")
        return {
            "status": "skipped",
            "reason": "Supabase not configured",
        }
    
    alerts_queued = 0
    delivery_stats = {"processed": 0, "delivered": 0, "failed": 0}
    errors = []
    
    try:
        with pipeline_run_context("alert_process", "alert") as run:
            # 1. Check for new threshold alerts
            logger.info("Checking for threshold crossings")
            new_alerts = await check_threshold_alerts()
            
            # 2. Queue new alerts
            for alert in new_alerts:
                try:
                    alert_id = queue_alert(
                        alert_type=alert["alert_type"],
                        title=alert["title"],
                        message=alert["message"],
                        game_id=alert.get("game_id"),
                        user_id=alert.get("user_id"),
                        ups_score=alert.get("ups_score"),
                        threshold=alert.get("threshold"),
                        priority=8 if alert.get("ups_score", 0) >= 70 else 5,
                        metadata={
                            "push_token": alert.get("push_token"),
                            "push_provider": alert.get("push_provider"),
                        },
                    )
                    
                    if alert_id:
                        alerts_queued += 1
                
                except Exception as e:
                    error_msg = f"Error queuing alert: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            logger.info(f"Queued {alerts_queued} new alerts")
            
            # 3. Process pending alerts
            logger.info("Processing pending alerts")
            delivery_stats = await process_pending_alerts()
            
            run["records_processed"] = delivery_stats["processed"]
            run["records_created"] = alerts_queued
            run["metadata"] = {
                "alerts_queued": alerts_queued,
                "alerts_delivered": delivery_stats["delivered"],
                "alerts_failed": delivery_stats["failed"],
                "errors": errors,
            }
    
    except Exception as e:
        logger.error(f"Alert processing job failed: {e}")
        raise
    
    result = {
        "status": "completed" if not errors else "completed_with_errors",
        "alerts_queued": alerts_queued,
        "alerts_processed": delivery_stats["processed"],
        "alerts_delivered": delivery_stats["delivered"],
        "alerts_failed": delivery_stats["failed"],
        "errors": errors,
    }
    
    logger.info(f"Alert processing job completed: {result}")
    return result

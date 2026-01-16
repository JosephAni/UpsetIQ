"""Supabase client for UpsetIQ pipeline data storage."""
import os
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Lazy initialization
_supabase_client = None


def get_supabase_client():
    """Get or create Supabase client instance."""
    global _supabase_client
    
    if _supabase_client is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_KEY environment variables required"
            )
        
        from supabase import create_client, Client
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Supabase client initialized")
    
    return _supabase_client


def is_supabase_configured() -> bool:
    """Check if Supabase is configured."""
    return bool(SUPABASE_URL and SUPABASE_KEY)


# =============================================================================
# ODDS SNAPSHOTS
# =============================================================================

def insert_odds_snapshot(snapshot: Dict[str, Any]) -> Optional[Dict]:
    """
    Insert a single odds snapshot.
    
    Args:
        snapshot: Dict with game_id, sport, odds data, etc.
        
    Returns:
        Inserted record or None on failure
    """
    try:
        client = get_supabase_client()
        result = client.table("odds_snapshots").insert(snapshot).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error inserting odds snapshot: {e}")
        return None


def insert_odds_snapshots_batch(snapshots: List[Dict[str, Any]]) -> int:
    """
    Batch insert odds snapshots.
    
    Args:
        snapshots: List of snapshot dicts
        
    Returns:
        Number of records inserted
    """
    if not snapshots:
        return 0
    
    try:
        client = get_supabase_client()
        result = client.table("odds_snapshots").insert(snapshots).execute()
        return len(result.data) if result.data else 0
    except Exception as e:
        logger.error(f"Error batch inserting odds snapshots: {e}")
        return 0


def get_latest_odds_snapshot(game_id: str) -> Optional[Dict]:
    """Get the most recent odds snapshot for a game."""
    try:
        client = get_supabase_client()
        result = (
            client.table("odds_snapshots")
            .select("*")
            .eq("game_id", game_id)
            .order("captured_at", desc=True)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error getting latest odds snapshot: {e}")
        return None


def get_odds_history(
    game_id: str, 
    limit: int = 100
) -> List[Dict]:
    """Get odds history for a game (for line movement analysis)."""
    try:
        client = get_supabase_client()
        result = (
            client.table("odds_snapshots")
            .select("*")
            .eq("game_id", game_id)
            .order("captured_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data if result.data else []
    except Exception as e:
        logger.error(f"Error getting odds history: {e}")
        return []


# =============================================================================
# SENTIMENT SCORES
# =============================================================================

def insert_sentiment_score(score: Dict[str, Any]) -> Optional[Dict]:
    """Insert a sentiment score record."""
    try:
        client = get_supabase_client()
        result = client.table("sentiment_scores").insert(score).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error inserting sentiment score: {e}")
        return None


def insert_sentiment_scores_batch(scores: List[Dict[str, Any]]) -> int:
    """Batch insert sentiment scores."""
    if not scores:
        return 0
    
    try:
        client = get_supabase_client()
        result = client.table("sentiment_scores").insert(scores).execute()
        return len(result.data) if result.data else 0
    except Exception as e:
        logger.error(f"Error batch inserting sentiment scores: {e}")
        return 0


def get_latest_sentiment(
    target_type: str,
    target_id: str,
    source: Optional[str] = None
) -> Optional[Dict]:
    """Get latest sentiment score for a team or game."""
    try:
        client = get_supabase_client()
        query = (
            client.table("sentiment_scores")
            .select("*")
            .eq("target_type", target_type)
            .eq("target_id", target_id)
        )
        
        if source:
            query = query.eq("source", source)
        
        result = query.order("window_end", desc=True).limit(1).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error getting latest sentiment: {e}")
        return None


def get_team_sentiment_history(
    team: str,
    hours: int = 24,
    source: Optional[str] = None
) -> List[Dict]:
    """Get sentiment history for a team over the past N hours."""
    try:
        client = get_supabase_client()
        cutoff = datetime.now(timezone.utc).isoformat()
        
        query = (
            client.table("sentiment_scores")
            .select("*")
            .eq("target_type", "team")
            .eq("target_id", team)
            .gte("window_end", f"now() - interval '{hours} hours'")
        )
        
        if source:
            query = query.eq("source", source)
        
        result = query.order("window_end", desc=True).execute()
        return result.data if result.data else []
    except Exception as e:
        logger.error(f"Error getting team sentiment history: {e}")
        return []


# =============================================================================
# PIPELINE RUNS
# =============================================================================

def start_pipeline_run(job_name: str, job_type: str) -> Optional[str]:
    """
    Record start of a pipeline run.
    
    Returns:
        Run ID or None on failure
    """
    try:
        client = get_supabase_client()
        result = client.table("pipeline_runs").insert({
            "job_name": job_name,
            "job_type": job_type,
            "status": "running",
            "started_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
        
        if result.data:
            return result.data[0]["id"]
        return None
    except Exception as e:
        logger.error(f"Error starting pipeline run: {e}")
        return None


def complete_pipeline_run(
    run_id: str,
    status: str = "completed",
    records_processed: int = 0,
    records_created: int = 0,
    records_updated: int = 0,
    error_message: Optional[str] = None,
    metadata: Optional[Dict] = None
) -> bool:
    """Update pipeline run with completion status."""
    try:
        client = get_supabase_client()
        
        now = datetime.now(timezone.utc)
        
        # Calculate duration
        run_result = client.table("pipeline_runs").select("started_at").eq("id", run_id).execute()
        duration = None
        if run_result.data:
            started = datetime.fromisoformat(run_result.data[0]["started_at"].replace("Z", "+00:00"))
            duration = (now - started).total_seconds()
        
        update_data = {
            "status": status,
            "completed_at": now.isoformat(),
            "duration_seconds": duration,
            "records_processed": records_processed,
            "records_created": records_created,
            "records_updated": records_updated,
        }
        
        if error_message:
            update_data["error_message"] = error_message
        
        if metadata:
            update_data["metadata"] = metadata
        
        client.table("pipeline_runs").update(update_data).eq("id", run_id).execute()
        return True
    except Exception as e:
        logger.error(f"Error completing pipeline run: {e}")
        return False


def get_recent_pipeline_runs(
    job_name: Optional[str] = None,
    limit: int = 20
) -> List[Dict]:
    """Get recent pipeline runs for monitoring."""
    try:
        client = get_supabase_client()
        query = client.table("pipeline_runs").select("*")
        
        if job_name:
            query = query.eq("job_name", job_name)
        
        result = query.order("started_at", desc=True).limit(limit).execute()
        return result.data if result.data else []
    except Exception as e:
        logger.error(f"Error getting pipeline runs: {e}")
        return []


@contextmanager
def pipeline_run_context(job_name: str, job_type: str):
    """
    Context manager for pipeline runs with automatic tracking.
    
    Usage:
        with pipeline_run_context("odds_snapshot", "odds") as run:
            # Do work
            run["records_processed"] = 10
    """
    run_id = start_pipeline_run(job_name, job_type)
    run_data = {
        "id": run_id,
        "records_processed": 0,
        "records_created": 0,
        "records_updated": 0,
        "metadata": {},
    }
    
    try:
        yield run_data
        complete_pipeline_run(
            run_id,
            status="completed",
            records_processed=run_data["records_processed"],
            records_created=run_data["records_created"],
            records_updated=run_data["records_updated"],
            metadata=run_data.get("metadata"),
        )
    except Exception as e:
        complete_pipeline_run(
            run_id,
            status="failed",
            error_message=str(e),
            records_processed=run_data["records_processed"],
        )
        raise


# =============================================================================
# ALERT QUEUE
# =============================================================================

def queue_alert(
    alert_type: str,
    title: str,
    message: str,
    game_id: Optional[str] = None,
    user_id: Optional[str] = None,
    ups_score: Optional[float] = None,
    previous_ups: Optional[float] = None,
    threshold: Optional[float] = None,
    priority: int = 5,
    expires_at: Optional[datetime] = None,
    metadata: Optional[Dict] = None
) -> Optional[str]:
    """
    Add an alert to the queue.
    
    Returns:
        Alert ID or None on failure
    """
    try:
        client = get_supabase_client()
        
        alert_data = {
            "alert_type": alert_type,
            "title": title,
            "message": message,
            "priority": priority,
            "status": "pending",
        }
        
        if game_id:
            alert_data["game_id"] = game_id
        if user_id:
            alert_data["user_id"] = user_id
        if ups_score is not None:
            alert_data["ups_score"] = ups_score
        if previous_ups is not None:
            alert_data["previous_ups"] = previous_ups
        if threshold is not None:
            alert_data["threshold"] = threshold
        if expires_at:
            alert_data["expires_at"] = expires_at.isoformat()
        if metadata:
            alert_data["metadata"] = metadata
        
        result = client.table("alert_queue").insert(alert_data).execute()
        
        if result.data:
            return result.data[0]["id"]
        return None
    except Exception as e:
        logger.error(f"Error queuing alert: {e}")
        return None


def get_pending_alerts(limit: int = 50) -> List[Dict]:
    """Get pending alerts ordered by priority."""
    try:
        client = get_supabase_client()
        result = (
            client.table("alert_queue")
            .select("*")
            .eq("status", "pending")
            .order("priority", desc=True)
            .order("created_at")
            .limit(limit)
            .execute()
        )
        return result.data if result.data else []
    except Exception as e:
        logger.error(f"Error getting pending alerts: {e}")
        return []


def mark_alert_sent(
    alert_id: str,
    delivery_method: str,
    status: str = "sent"
) -> bool:
    """Mark an alert as sent."""
    try:
        client = get_supabase_client()
        client.table("alert_queue").update({
            "status": status,
            "delivery_method": delivery_method,
            "sent_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", alert_id).execute()
        return True
    except Exception as e:
        logger.error(f"Error marking alert sent: {e}")
        return False


def mark_alert_delivered(alert_id: str) -> bool:
    """Mark an alert as delivered."""
    try:
        client = get_supabase_client()
        client.table("alert_queue").update({
            "status": "delivered",
            "delivered_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", alert_id).execute()
        return True
    except Exception as e:
        logger.error(f"Error marking alert delivered: {e}")
        return False


def mark_alert_failed(alert_id: str, error: str) -> bool:
    """Mark an alert as failed and increment retry count."""
    try:
        client = get_supabase_client()
        
        # Get current retry count
        result = client.table("alert_queue").select("retry_count, max_retries").eq("id", alert_id).execute()
        
        if result.data:
            current = result.data[0]
            new_retry = current["retry_count"] + 1
            
            # If max retries exceeded, mark as failed permanently
            if new_retry >= current["max_retries"]:
                status = "failed"
            else:
                status = "pending"  # Will be retried
            
            client.table("alert_queue").update({
                "status": status,
                "retry_count": new_retry,
                "last_error": error,
            }).eq("id", alert_id).execute()
        
        return True
    except Exception as e:
        logger.error(f"Error marking alert failed: {e}")
        return False


# =============================================================================
# ALERT SUBSCRIPTIONS
# =============================================================================

def get_user_subscriptions(user_id: str) -> List[Dict]:
    """Get all active subscriptions for a user."""
    try:
        client = get_supabase_client()
        result = (
            client.table("alert_subscriptions")
            .select("*")
            .eq("user_id", user_id)
            .eq("active", True)
            .execute()
        )
        return result.data if result.data else []
    except Exception as e:
        logger.error(f"Error getting user subscriptions: {e}")
        return []


def get_subscriptions_for_game(game_id: str) -> List[Dict]:
    """Get all subscriptions that should receive alerts for a game."""
    try:
        client = get_supabase_client()
        
        # Get game-specific and all-upsets subscriptions
        result = (
            client.table("alert_subscriptions")
            .select("*")
            .eq("active", True)
            .or_(f"target_id.eq.{game_id},subscription_type.eq.all_upsets")
            .execute()
        )
        return result.data if result.data else []
    except Exception as e:
        logger.error(f"Error getting subscriptions for game: {e}")
        return []


def get_subscriptions_by_threshold(
    ups_score: float,
    sport: str = "NFL"
) -> List[Dict]:
    """Get subscriptions where UPS score exceeds user's threshold."""
    try:
        client = get_supabase_client()
        result = (
            client.table("alert_subscriptions")
            .select("*")
            .eq("active", True)
            .eq("subscription_type", "ups_threshold")
            .eq("sport", sport)
            .lte("ups_threshold", ups_score)
            .execute()
        )
        return result.data if result.data else []
    except Exception as e:
        logger.error(f"Error getting subscriptions by threshold: {e}")
        return []


def create_subscription(
    user_id: str,
    subscription_type: str,
    target_id: Optional[str] = None,
    ups_threshold: float = 65.0,
    push_token: Optional[str] = None,
    push_provider: Optional[str] = None
) -> Optional[Dict]:
    """Create a new alert subscription."""
    try:
        client = get_supabase_client()
        
        sub_data = {
            "user_id": user_id,
            "subscription_type": subscription_type,
            "ups_threshold": ups_threshold,
            "active": True,
        }
        
        if target_id:
            sub_data["target_id"] = target_id
        if push_token:
            sub_data["push_token"] = push_token
        if push_provider:
            sub_data["push_provider"] = push_provider
        
        result = client.table("alert_subscriptions").insert(sub_data).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error creating subscription: {e}")
        return None


# =============================================================================
# GAME FEATURES
# =============================================================================

def insert_game_features(features: Dict[str, Any]) -> Optional[Dict]:
    """Insert computed game features."""
    try:
        client = get_supabase_client()
        result = client.table("game_features").insert(features).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error inserting game features: {e}")
        return None


def insert_game_features_batch(features_list: List[Dict[str, Any]]) -> int:
    """Batch insert game features."""
    if not features_list:
        return 0
    
    try:
        client = get_supabase_client()
        result = client.table("game_features").insert(features_list).execute()
        return len(result.data) if result.data else 0
    except Exception as e:
        logger.error(f"Error batch inserting game features: {e}")
        return 0


def get_latest_game_features(game_id: str) -> Optional[Dict]:
    """Get most recent features for a game."""
    try:
        client = get_supabase_client()
        result = (
            client.table("game_features")
            .select("*")
            .eq("game_id", game_id)
            .order("computed_at", desc=True)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error getting latest game features: {e}")
        return None


def get_high_ups_games(
    min_ups: float = 60.0,
    sport: str = "NFL",
    limit: int = 20
) -> List[Dict]:
    """Get games with high UPS scores."""
    try:
        client = get_supabase_client()
        result = (
            client.table("game_features")
            .select("*")
            .eq("sport", sport)
            .gte("ups_score", min_ups)
            .order("ups_score", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data if result.data else []
    except Exception as e:
        logger.error(f"Error getting high UPS games: {e}")
        return []

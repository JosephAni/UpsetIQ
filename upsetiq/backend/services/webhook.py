"""Webhook and push notification service."""
import os
import logging
from typing import Dict, Any, Optional
import asyncio

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Firebase configuration
FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH")

# Expo configuration
EXPO_ACCESS_TOKEN = os.getenv("EXPO_ACCESS_TOKEN")

# Firebase app (initialized lazily)
_firebase_app = None


def _init_firebase():
    """Initialize Firebase Admin SDK."""
    global _firebase_app
    
    if _firebase_app is not None:
        return _firebase_app
    
    if not FIREBASE_CREDENTIALS_PATH:
        logger.warning("Firebase credentials not configured")
        return None
    
    try:
        import firebase_admin
        from firebase_admin import credentials
        
        cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
        _firebase_app = firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin SDK initialized")
        return _firebase_app
    
    except FileNotFoundError:
        logger.error(f"Firebase credentials file not found: {FIREBASE_CREDENTIALS_PATH}")
    except Exception as e:
        logger.error(f"Error initializing Firebase: {e}")
    
    return None


async def send_firebase_push(
    token: str,
    title: str,
    body: str,
    data: Optional[Dict[str, str]] = None,
) -> bool:
    """
    Send push notification via Firebase Cloud Messaging.
    
    Args:
        token: FCM device token
        title: Notification title
        body: Notification body
        data: Optional data payload
        
    Returns:
        True if sent successfully
    """
    if not _init_firebase():
        return False
    
    try:
        from firebase_admin import messaging
        
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data or {},
            token=token,
        )
        
        # Send in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            messaging.send,
            message,
        )
        
        logger.info(f"Firebase push sent: {response}")
        return True
    
    except Exception as e:
        logger.error(f"Firebase push failed: {e}")
        return False


async def send_expo_push(
    token: str,
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Send push notification via Expo Push Service.
    
    Args:
        token: Expo push token
        title: Notification title
        body: Notification body
        data: Optional data payload
        
    Returns:
        True if sent successfully
    """
    try:
        import httpx
        
        message = {
            "to": token,
            "title": title,
            "body": body,
            "sound": "default",
            "priority": "high",
        }
        
        if data:
            message["data"] = data
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        
        if EXPO_ACCESS_TOKEN:
            headers["Authorization"] = f"Bearer {EXPO_ACCESS_TOKEN}"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://exp.host/--/api/v2/push/send",
                json=message,
                headers=headers,
                timeout=10.0,
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("data", {}).get("status") == "ok":
                    logger.info(f"Expo push sent to {token[:20]}...")
                    return True
                else:
                    logger.warning(f"Expo push warning: {result}")
                    return True  # Still consider it sent
            else:
                logger.error(f"Expo push failed: {response.status_code}")
                return False
    
    except Exception as e:
        logger.error(f"Expo push error: {e}")
        return False


async def send_push_notification(
    token: str,
    provider: str,
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Send push notification via appropriate provider.
    
    Args:
        token: Push token
        provider: Provider name ("firebase", "expo", "apns")
        title: Notification title
        body: Notification body
        data: Optional data payload
        
    Returns:
        True if sent successfully
    """
    # Convert data values to strings for FCM
    string_data = None
    if data:
        string_data = {k: str(v) for k, v in data.items()}
    
    if provider == "firebase":
        return await send_firebase_push(token, title, body, string_data)
    elif provider == "expo":
        return await send_expo_push(token, title, body, data)
    else:
        # Default to Expo for unknown providers
        return await send_expo_push(token, title, body, data)


async def send_webhook(
    url: str,
    payload: Dict[str, Any],
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 10.0,
) -> bool:
    """
    Send webhook POST request.
    
    Args:
        url: Webhook URL
        payload: JSON payload
        headers: Optional headers
        timeout: Request timeout
        
    Returns:
        True if successful (2xx response)
    """
    try:
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                headers=headers or {},
                timeout=timeout,
            )
            
            if 200 <= response.status_code < 300:
                logger.info(f"Webhook sent to {url}: {response.status_code}")
                return True
            else:
                logger.warning(f"Webhook failed: {url} returned {response.status_code}")
                return False
    
    except Exception as e:
        logger.error(f"Webhook error for {url}: {e}")
        return False


async def send_batch_push(
    notifications: list,
) -> Dict[str, int]:
    """
    Send batch push notifications.
    
    Args:
        notifications: List of dicts with token, provider, title, body, data
        
    Returns:
        Dict with sent and failed counts
    """
    results = {"sent": 0, "failed": 0}
    
    tasks = []
    for notif in notifications:
        task = send_push_notification(
            token=notif.get("token"),
            provider=notif.get("provider", "expo"),
            title=notif.get("title", ""),
            body=notif.get("body", ""),
            data=notif.get("data"),
        )
        tasks.append(task)
    
    if tasks:
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        for response in responses:
            if isinstance(response, Exception):
                results["failed"] += 1
            elif response:
                results["sent"] += 1
            else:
                results["failed"] += 1
    
    return results


# Webhook URL registry for external integrations
_webhook_registry: Dict[str, str] = {}


def register_webhook(name: str, url: str) -> None:
    """Register a webhook URL."""
    _webhook_registry[name] = url
    logger.info(f"Registered webhook: {name}")


def unregister_webhook(name: str) -> None:
    """Unregister a webhook URL."""
    _webhook_registry.pop(name, None)
    logger.info(f"Unregistered webhook: {name}")


async def notify_webhooks(event: str, payload: Dict[str, Any]) -> Dict[str, bool]:
    """
    Send event to all registered webhooks.
    
    Args:
        event: Event name
        payload: Event payload
        
    Returns:
        Dict mapping webhook name to success status
    """
    results = {}
    
    for name, url in _webhook_registry.items():
        full_payload = {
            "event": event,
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "data": payload,
        }
        results[name] = await send_webhook(url, full_payload)
    
    return results

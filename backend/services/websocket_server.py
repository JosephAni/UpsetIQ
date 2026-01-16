"""WebSocket server for real-time alert delivery using Socket.IO."""
import os
import logging
from typing import Dict, Any, Optional, Set

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Socket.IO instance (initialized lazily)
_sio = None
_connected_clients: Set[str] = set()


def get_socketio():
    """Get or create Socket.IO server instance."""
    global _sio
    
    if _sio is None:
        try:
            import socketio
            
            # Create Socket.IO server
            _sio = socketio.AsyncServer(
                async_mode="asgi",
                cors_allowed_origins="*",  # Configure for production
                logger=True,
                engineio_logger=True,
            )
            
            # Register event handlers
            @_sio.event
            async def connect(sid, environ):
                """Handle client connection."""
                _connected_clients.add(sid)
                logger.info(f"Client connected: {sid}")
                await _sio.emit("connected", {"sid": sid}, to=sid)
            
            @_sio.event
            async def disconnect(sid):
                """Handle client disconnection."""
                _connected_clients.discard(sid)
                logger.info(f"Client disconnected: {sid}")
            
            @_sio.event
            async def join_room(sid, data):
                """Handle room join request."""
                room = data.get("room")
                if room:
                    _sio.enter_room(sid, room)
                    logger.info(f"Client {sid} joined room: {room}")
                    await _sio.emit("room_joined", {"room": room}, to=sid)
            
            @_sio.event
            async def leave_room(sid, data):
                """Handle room leave request."""
                room = data.get("room")
                if room:
                    _sio.leave_room(sid, room)
                    logger.info(f"Client {sid} left room: {room}")
            
            @_sio.event
            async def subscribe_game(sid, data):
                """Subscribe to alerts for a specific game."""
                game_id = data.get("game_id")
                if game_id:
                    room = f"game_{game_id}"
                    _sio.enter_room(sid, room)
                    logger.info(f"Client {sid} subscribed to game: {game_id}")
                    await _sio.emit("subscribed", {"game_id": game_id}, to=sid)
            
            @_sio.event
            async def subscribe_team(sid, data):
                """Subscribe to alerts for a specific team."""
                team = data.get("team")
                if team:
                    room = f"team_{team}"
                    _sio.enter_room(sid, room)
                    logger.info(f"Client {sid} subscribed to team: {team}")
                    await _sio.emit("subscribed", {"team": team}, to=sid)
            
            @_sio.event
            async def subscribe_sport(sid, data):
                """Subscribe to all alerts for a sport."""
                sport = data.get("sport", "NFL")
                room = f"sport_{sport}"
                _sio.enter_room(sid, room)
                logger.info(f"Client {sid} subscribed to sport: {sport}")
                await _sio.emit("subscribed", {"sport": sport}, to=sid)
            
            logger.info("Socket.IO server initialized")
        
        except ImportError:
            logger.error("python-socketio not installed")
            return None
    
    return _sio


def get_socket_app():
    """Get ASGI app for Socket.IO."""
    sio = get_socketio()
    if sio:
        import socketio
        return socketio.ASGIApp(sio)
    return None


async def broadcast_alert(alert: Dict[str, Any]) -> bool:
    """
    Broadcast an alert to all connected clients.
    
    Args:
        alert: Alert data to broadcast
        
    Returns:
        True if sent successfully
    """
    sio = get_socketio()
    if not sio:
        return False
    
    try:
        await sio.emit("alert", alert)
        logger.info(f"Broadcast alert to {len(_connected_clients)} clients")
        return True
    except Exception as e:
        logger.error(f"Error broadcasting alert: {e}")
        return False


async def emit_to_room(room: str, event: str, data: Dict[str, Any]) -> bool:
    """
    Emit an event to a specific room.
    
    Args:
        room: Room name (e.g., "game_abc123", "team_KC")
        event: Event name
        data: Event data
        
    Returns:
        True if sent successfully
    """
    sio = get_socketio()
    if not sio:
        return False
    
    try:
        await sio.emit(event, data, room=room)
        logger.info(f"Emitted {event} to room {room}")
        return True
    except Exception as e:
        logger.error(f"Error emitting to room {room}: {e}")
        return False


async def emit_game_update(game_id: str, update: Dict[str, Any]) -> bool:
    """
    Emit a game update to subscribers.
    
    Args:
        game_id: Game identifier
        update: Update data (UPS change, odds change, etc.)
        
    Returns:
        True if sent
    """
    return await emit_to_room(f"game_{game_id}", "game_update", update)


async def emit_ups_alert(
    game_id: str,
    ups_score: float,
    previous_ups: float,
    favorite: str,
    underdog: str,
    signals: list,
) -> bool:
    """
    Emit a UPS threshold alert.
    
    Args:
        game_id: Game identifier
        ups_score: Current UPS
        previous_ups: Previous UPS
        favorite: Favorite team
        underdog: Underdog team
        signals: List of signal descriptions
        
    Returns:
        True if sent
    """
    alert = {
        "type": "ups_alert",
        "game_id": game_id,
        "ups_score": ups_score,
        "previous_ups": previous_ups,
        "change": ups_score - previous_ups,
        "favorite": favorite,
        "underdog": underdog,
        "signals": signals,
        "timestamp": __import__("datetime").datetime.now().isoformat(),
    }
    
    # Emit to game room and NFL room
    await emit_to_room(f"game_{game_id}", "ups_alert", alert)
    await emit_to_room("sport_NFL", "ups_alert", alert)
    
    return True


async def emit_injury_update(team: str, injuries: list) -> bool:
    """
    Emit an injury update for a team.
    
    Args:
        team: Team abbreviation
        injuries: List of injury updates
        
    Returns:
        True if sent
    """
    update = {
        "type": "injury_update",
        "team": team,
        "injuries": injuries,
        "count": len(injuries),
        "timestamp": __import__("datetime").datetime.now().isoformat(),
    }
    
    return await emit_to_room(f"team_{team}", "injury_update", update)


def get_connected_count() -> int:
    """Get count of connected clients."""
    return len(_connected_clients)


def get_room_members(room: str) -> Set[str]:
    """Get members of a room."""
    sio = get_socketio()
    if sio:
        try:
            return sio.manager.get_participants("/", room)
        except:
            pass
    return set()

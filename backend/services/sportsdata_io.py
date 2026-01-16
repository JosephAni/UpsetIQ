"""SportsDataIO NFL API service - fetches comprehensive NFL data."""
import os
import time
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# API Configuration
SDIO_KEY = os.getenv("SPORTSDATAIO_KEY")
BASE_URL = "https://api.sportsdata.io/v3/nfl"

# Cache TTL settings (in seconds)
CACHE_TTL = {
    "schedules": 3600,      # 1 hour
    "injuries": 900,        # 15 minutes
    "standings": 3600,      # 1 hour
    "player_stats": 3600,   # 1 hour
    "team_stats": 3600,     # 1 hour
    "news": 300,            # 5 minutes
    "scores": 60,           # 1 minute (live data)
    "teams": 86400,         # 24 hours (rarely changes)
    "players": 3600,        # 1 hour
}

# In-memory cache structure
_cache: Dict[str, Dict[str, Any]] = {}


def _get_session() -> requests.Session:
    """
    Create a requests session with retry logic.
    
    Implements exponential backoff for transient failures.
    """
    session = requests.Session()
    
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    
    return session


# Global session for connection pooling
_session: Optional[requests.Session] = None


def get_session() -> requests.Session:
    """Get or create the global session."""
    global _session
    if _session is None:
        _session = _get_session()
    return _session


def _get_cache(cache_key: str, ttl_key: str) -> Optional[Any]:
    """
    Retrieve data from cache if valid.
    
    Args:
        cache_key: Unique cache identifier
        ttl_key: Key to lookup TTL in CACHE_TTL dict
        
    Returns:
        Cached data if valid, None otherwise
    """
    if cache_key not in _cache:
        return None
    
    cached = _cache[cache_key]
    ttl = CACHE_TTL.get(ttl_key, 300)
    
    if time.time() - cached.get("timestamp", 0) < ttl:
        logger.debug(f"Cache hit for {cache_key}")
        return cached.get("data")
    
    logger.debug(f"Cache expired for {cache_key}")
    return None


def _set_cache(cache_key: str, data: Any) -> None:
    """Store data in cache with current timestamp."""
    _cache[cache_key] = {
        "data": data,
        "timestamp": time.time(),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def sdio_get(endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
    """
    Make authenticated GET request to SportsDataIO API.
    
    Args:
        endpoint: API endpoint path (e.g., "scores/json/Schedules/2025")
        params: Additional query parameters
        
    Returns:
        JSON response from API
        
    Raises:
        ValueError: If API key not configured
        requests.exceptions.RequestException: For network/API errors
    """
    if not SDIO_KEY:
        raise ValueError("SPORTSDATAIO_KEY environment variable not set")
    
    url = f"{BASE_URL}/{endpoint}"
    
    # SportsDataIO uses header-based authentication
    headers = {
        "Ocp-Apim-Subscription-Key": SDIO_KEY,
    }
    
    request_params = params or {}
    
    session = get_session()
    
    try:
        response = session.get(
            url,
            headers=headers,
            params=request_params,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.Timeout:
        logger.error(f"Timeout fetching {endpoint}")
        raise
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error fetching {endpoint}: {e.response.status_code}")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error fetching {endpoint}: {str(e)}")
        raise


# =============================================================================
# SCHEDULES
# =============================================================================

def get_schedules(season: int = 2025) -> Tuple[List[Dict], str, bool]:
    """
    Fetch NFL schedule for a season.
    
    Args:
        season: NFL season year (e.g., 2025)
        
    Returns:
        Tuple of (schedule data, fetched_at timestamp, cached flag)
    """
    cache_key = f"schedules_{season}"
    
    cached_data = _get_cache(cache_key, "schedules")
    if cached_data is not None:
        return cached_data, _cache[cache_key]["fetched_at"], True
    
    try:
        data = sdio_get(f"scores/json/Schedules/{season}")
        _set_cache(cache_key, data)
        return data, _cache[cache_key]["fetched_at"], False
    except requests.exceptions.RequestException:
        # Return cached data if available, even if expired
        if cache_key in _cache:
            return _cache[cache_key]["data"], _cache[cache_key]["fetched_at"], True
        raise


def get_schedule_by_week(season: int, week: int) -> Tuple[List[Dict], str, bool]:
    """
    Fetch NFL schedule for a specific week.
    
    Args:
        season: NFL season year
        week: Week number (1-18 for regular season, 19-22 for playoffs)
        
    Returns:
        Tuple of (schedule data, fetched_at timestamp, cached flag)
    """
    cache_key = f"schedule_{season}_week_{week}"
    
    cached_data = _get_cache(cache_key, "schedules")
    if cached_data is not None:
        return cached_data, _cache[cache_key]["fetched_at"], True
    
    try:
        data = sdio_get(f"scores/json/ScoresByWeek/{season}/{week}")
        _set_cache(cache_key, data)
        return data, _cache[cache_key]["fetched_at"], False
    except requests.exceptions.RequestException:
        if cache_key in _cache:
            return _cache[cache_key]["data"], _cache[cache_key]["fetched_at"], True
        raise


# =============================================================================
# INJURIES
# =============================================================================

def get_injuries(season: int = 2025, week: Optional[int] = None) -> Tuple[List[Dict], str, bool]:
    """
    Fetch current NFL injury reports.
    
    Args:
        season: NFL season year
        week: Optional week number for week-specific injuries
        
    Returns:
        Tuple of (injury data, fetched_at timestamp, cached flag)
    """
    if week:
        cache_key = f"injuries_{season}_week_{week}"
        endpoint = f"scores/json/Injuries/{season}/{week}"
    else:
        cache_key = f"injuries_{season}"
        endpoint = f"scores/json/Injuries/{season}"
    
    cached_data = _get_cache(cache_key, "injuries")
    if cached_data is not None:
        return cached_data, _cache[cache_key]["fetched_at"], True
    
    try:
        data = sdio_get(endpoint)
        _set_cache(cache_key, data)
        return data, _cache[cache_key]["fetched_at"], False
    except requests.exceptions.RequestException:
        if cache_key in _cache:
            return _cache[cache_key]["data"], _cache[cache_key]["fetched_at"], True
        raise


def get_injuries_by_team(team: str, season: int = 2025) -> List[Dict]:
    """
    Get injuries filtered by team.
    
    Args:
        team: Team abbreviation (e.g., "KC", "PHI", "SF")
        season: NFL season year
        
    Returns:
        List of injuries for the specified team
    """
    injuries, _, _ = get_injuries(season)
    return [inj for inj in injuries if inj.get("Team") == team.upper()]


# =============================================================================
# STANDINGS
# =============================================================================

def get_standings(season: int = 2025) -> Tuple[List[Dict], str, bool]:
    """
    Fetch NFL standings for a season.
    
    Args:
        season: NFL season year
        
    Returns:
        Tuple of (standings data, fetched_at timestamp, cached flag)
    """
    cache_key = f"standings_{season}"
    
    cached_data = _get_cache(cache_key, "standings")
    if cached_data is not None:
        return cached_data, _cache[cache_key]["fetched_at"], True
    
    try:
        data = sdio_get(f"scores/json/Standings/{season}")
        _set_cache(cache_key, data)
        return data, _cache[cache_key]["fetched_at"], False
    except requests.exceptions.RequestException:
        if cache_key in _cache:
            return _cache[cache_key]["data"], _cache[cache_key]["fetched_at"], True
        raise


# =============================================================================
# PLAYER STATISTICS
# =============================================================================

def get_player_season_stats(season: int = 2025) -> Tuple[List[Dict], str, bool]:
    """
    Fetch player season statistics.
    
    Args:
        season: NFL season year
        
    Returns:
        Tuple of (player stats data, fetched_at timestamp, cached flag)
    """
    cache_key = f"player_stats_{season}"
    
    cached_data = _get_cache(cache_key, "player_stats")
    if cached_data is not None:
        return cached_data, _cache[cache_key]["fetched_at"], True
    
    try:
        data = sdio_get(f"stats/json/PlayerSeasonStats/{season}")
        _set_cache(cache_key, data)
        return data, _cache[cache_key]["fetched_at"], False
    except requests.exceptions.RequestException:
        if cache_key in _cache:
            return _cache[cache_key]["data"], _cache[cache_key]["fetched_at"], True
        raise


def get_player_stats_by_week(season: int, week: int) -> Tuple[List[Dict], str, bool]:
    """
    Fetch player statistics for a specific week.
    
    Args:
        season: NFL season year
        week: Week number
        
    Returns:
        Tuple of (player stats data, fetched_at timestamp, cached flag)
    """
    cache_key = f"player_stats_{season}_week_{week}"
    
    cached_data = _get_cache(cache_key, "player_stats")
    if cached_data is not None:
        return cached_data, _cache[cache_key]["fetched_at"], True
    
    try:
        data = sdio_get(f"stats/json/PlayerGameStatsByWeek/{season}/{week}")
        _set_cache(cache_key, data)
        return data, _cache[cache_key]["fetched_at"], False
    except requests.exceptions.RequestException:
        if cache_key in _cache:
            return _cache[cache_key]["data"], _cache[cache_key]["fetched_at"], True
        raise


# =============================================================================
# TEAM STATISTICS
# =============================================================================

def get_team_season_stats(season: int = 2025) -> Tuple[List[Dict], str, bool]:
    """
    Fetch team season statistics.
    
    Args:
        season: NFL season year
        
    Returns:
        Tuple of (team stats data, fetched_at timestamp, cached flag)
    """
    cache_key = f"team_stats_{season}"
    
    cached_data = _get_cache(cache_key, "team_stats")
    if cached_data is not None:
        return cached_data, _cache[cache_key]["fetched_at"], True
    
    try:
        data = sdio_get(f"stats/json/TeamSeasonStats/{season}")
        _set_cache(cache_key, data)
        return data, _cache[cache_key]["fetched_at"], False
    except requests.exceptions.RequestException:
        if cache_key in _cache:
            return _cache[cache_key]["data"], _cache[cache_key]["fetched_at"], True
        raise


# =============================================================================
# NEWS
# =============================================================================

def get_news() -> Tuple[List[Dict], str, bool]:
    """
    Fetch latest NFL news.
    
    Returns:
        Tuple of (news data, fetched_at timestamp, cached flag)
    """
    cache_key = "news"
    
    cached_data = _get_cache(cache_key, "news")
    if cached_data is not None:
        return cached_data, _cache[cache_key]["fetched_at"], True
    
    try:
        data = sdio_get("scores/json/News")
        _set_cache(cache_key, data)
        return data, _cache[cache_key]["fetched_at"], False
    except requests.exceptions.RequestException:
        if cache_key in _cache:
            return _cache[cache_key]["data"], _cache[cache_key]["fetched_at"], True
        raise


def get_news_by_team(team: str) -> Tuple[List[Dict], str, bool]:
    """
    Fetch news for a specific team.
    
    Args:
        team: Team abbreviation
        
    Returns:
        Tuple of (news data, fetched_at timestamp, cached flag)
    """
    cache_key = f"news_{team}"
    
    cached_data = _get_cache(cache_key, "news")
    if cached_data is not None:
        return cached_data, _cache[cache_key]["fetched_at"], True
    
    try:
        data = sdio_get(f"scores/json/NewsByTeam/{team.upper()}")
        _set_cache(cache_key, data)
        return data, _cache[cache_key]["fetched_at"], False
    except requests.exceptions.RequestException:
        if cache_key in _cache:
            return _cache[cache_key]["data"], _cache[cache_key]["fetched_at"], True
        raise


# =============================================================================
# LIVE SCORES
# =============================================================================

def get_live_scores(season: int = 2025, week: Optional[int] = None) -> Tuple[List[Dict], str, bool]:
    """
    Fetch live/recent game scores.
    
    Args:
        season: NFL season year
        week: Optional week number (defaults to current week)
        
    Returns:
        Tuple of (scores data, fetched_at timestamp, cached flag)
    """
    if week:
        cache_key = f"scores_{season}_week_{week}"
        endpoint = f"scores/json/ScoresBasic/{season}/{week}"
    else:
        cache_key = f"scores_{season}_current"
        endpoint = f"scores/json/ScoresBasic/{season}"
    
    cached_data = _get_cache(cache_key, "scores")
    if cached_data is not None:
        return cached_data, _cache[cache_key]["fetched_at"], True
    
    try:
        data = sdio_get(endpoint)
        _set_cache(cache_key, data)
        return data, _cache[cache_key]["fetched_at"], False
    except requests.exceptions.RequestException:
        if cache_key in _cache:
            return _cache[cache_key]["data"], _cache[cache_key]["fetched_at"], True
        raise


def get_scores_by_date(date: str) -> Tuple[List[Dict], str, bool]:
    """
    Fetch scores for a specific date.
    
    Args:
        date: Date string in format "YYYY-MM-DD"
        
    Returns:
        Tuple of (scores data, fetched_at timestamp, cached flag)
    """
    cache_key = f"scores_{date}"
    
    cached_data = _get_cache(cache_key, "scores")
    if cached_data is not None:
        return cached_data, _cache[cache_key]["fetched_at"], True
    
    try:
        # Format date for API: YYYY-MMM-DD (e.g., 2025-JAN-09)
        data = sdio_get(f"scores/json/ScoresByDate/{date}")
        _set_cache(cache_key, data)
        return data, _cache[cache_key]["fetched_at"], False
    except requests.exceptions.RequestException:
        if cache_key in _cache:
            return _cache[cache_key]["data"], _cache[cache_key]["fetched_at"], True
        raise


# =============================================================================
# TEAMS & PLAYERS (Reference Data)
# =============================================================================

def get_teams() -> Tuple[List[Dict], str, bool]:
    """
    Fetch all NFL teams.
    
    Returns:
        Tuple of (teams data, fetched_at timestamp, cached flag)
    """
    cache_key = "teams"
    
    cached_data = _get_cache(cache_key, "teams")
    if cached_data is not None:
        return cached_data, _cache[cache_key]["fetched_at"], True
    
    try:
        data = sdio_get("scores/json/Teams")
        _set_cache(cache_key, data)
        return data, _cache[cache_key]["fetched_at"], False
    except requests.exceptions.RequestException:
        if cache_key in _cache:
            return _cache[cache_key]["data"], _cache[cache_key]["fetched_at"], True
        raise


def get_players(team: Optional[str] = None) -> Tuple[List[Dict], str, bool]:
    """
    Fetch NFL players.
    
    Args:
        team: Optional team abbreviation to filter by
        
    Returns:
        Tuple of (players data, fetched_at timestamp, cached flag)
    """
    if team:
        cache_key = f"players_{team}"
        endpoint = f"scores/json/Players/{team.upper()}"
    else:
        cache_key = "players_all"
        endpoint = "scores/json/Players"
    
    cached_data = _get_cache(cache_key, "players")
    if cached_data is not None:
        return cached_data, _cache[cache_key]["fetched_at"], True
    
    try:
        data = sdio_get(endpoint)
        _set_cache(cache_key, data)
        return data, _cache[cache_key]["fetched_at"], False
    except requests.exceptions.RequestException:
        if cache_key in _cache:
            return _cache[cache_key]["data"], _cache[cache_key]["fetched_at"], True
        raise


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_current_season() -> int:
    """
    Determine the current NFL season year.
    
    NFL season spans two calendar years. Games played after Super Bowl
    (typically February) belong to the previous season.
    """
    now = datetime.now()
    # NFL season typically starts in September
    # If we're in Jan-Aug, we're likely in the previous season's playoffs/offseason
    if now.month < 9:
        return now.year - 1 if now.month < 3 else now.year
    return now.year


def get_current_week(season: Optional[int] = None) -> int:
    """
    Estimate the current NFL week.
    
    This is a rough approximation. For accurate week,
    use the schedule data to determine based on game dates.
    """
    if season is None:
        season = get_current_season()
    
    # Try to get from schedules
    try:
        schedules, _, _ = get_schedules(season)
        now = datetime.now(timezone.utc)
        
        for game in schedules:
            game_date_str = game.get("Date") or game.get("DateTime")
            if game_date_str:
                try:
                    game_date = datetime.fromisoformat(
                        game_date_str.replace("Z", "+00:00")
                    )
                    if game_date > now:
                        return game.get("Week", 1)
                except (ValueError, TypeError):
                    continue
        
        return 1
    except Exception:
        return 1


def clear_cache(cache_key: Optional[str] = None) -> None:
    """
    Clear cache entries.
    
    Args:
        cache_key: Specific key to clear, or None to clear all
    """
    global _cache
    
    if cache_key:
        _cache.pop(cache_key, None)
        logger.info(f"Cleared cache for {cache_key}")
    else:
        _cache = {}
        logger.info("Cleared all cache")


def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics for monitoring.
    
    Returns:
        Dict with cache keys and their timestamps
    """
    stats = {}
    for key, value in _cache.items():
        stats[key] = {
            "fetched_at": value.get("fetched_at"),
            "age_seconds": int(time.time() - value.get("timestamp", 0)),
        }
    return stats

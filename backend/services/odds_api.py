"""Odds API service - fetches live odds data from the-odds-api.com."""
import os
import time
import logging
from datetime import datetime, timezone
from typing import List, Tuple, Optional, Dict, Any

import requests
from dotenv import load_dotenv

from models import GameWithPrediction
from services.transformer import transform_odds_to_games

load_dotenv()

logger = logging.getLogger(__name__)

API_KEY = os.getenv("ODDS_API_KEY")
BASE_URL = "https://api.the-odds-api.com/v4"
CACHE_TTL = int(os.getenv("CACHE_TTL", 300))  # 5 minutes default

# Simple in-memory cache
_cache: Dict[str, Any] = {
    "data": None,
    "timestamp": 0,
    "fetched_at": None,
}


def _get_sport_key(sport: str) -> str:
    """Map sport name to Odds API sport key."""
    sport_keys = {
        "NFL": "americanfootball_nfl",
        "NBA": "basketball_nba",
        "MLB": "baseball_mlb",
        "NHL": "icehockey_nhl",
        "CFB": "americanfootball_ncaaf",
        "Soccer": "soccer_epl",  # Default to EPL for soccer
    }
    return sport_keys.get(sport, "americanfootball_nfl")


def fetch_odds_from_api(sport: str = "NFL") -> Tuple[str, List[Dict]]:
    """
    Fetch odds data from the-odds-api.com.
    
    Returns:
        Tuple of (pulled_at ISO string, list of event data)
    """
    if not API_KEY:
        raise ValueError("ODDS_API_KEY environment variable not set")
    
    sport_key = _get_sport_key(sport)
    
    params = {
        "apiKey": API_KEY,
        "regions": "us",
        "markets": "h2h,spreads,totals",
        "oddsFormat": "american",
        "dateFormat": "iso",
    }
    
    url = f"{BASE_URL}/sports/{sport_key}/odds"
    
    response = requests.get(url, params=params, timeout=30)
    
    # Handle authentication errors with better messages
    if response.status_code == 401:
        raise ValueError(
            f"ODDS_API_KEY is invalid or expired. "
            f"Please check your API key at https://the-odds-api.com/. "
            f"Status: {response.status_code}"
        )
    elif response.status_code == 403:
        raise ValueError(
            f"ODDS_API_KEY access denied. Check your API plan and usage limits. "
            f"Status: {response.status_code}"
        )
    elif response.status_code == 429:
        raise ValueError(
            f"API rate limit exceeded. Please wait before making more requests. "
            f"Status: {response.status_code}"
        )
    
    response.raise_for_status()
    
    pulled_at = datetime.now(timezone.utc).isoformat()
    
    return pulled_at, response.json()


def get_games_with_predictions(
    sport: str = "NFL"
) -> Tuple[List[GameWithPrediction], str, bool]:
    """
    Get games with predictions, using cache if available.
    
    Returns:
        Tuple of (list of games, fetched_at timestamp, cached flag)
    """
    global _cache
    
    current_time = time.time()
    cache_key = f"{sport}_games"
    
    # Check if cache is valid
    if (
        _cache.get("data") is not None
        and _cache.get("sport") == sport
        and current_time - _cache.get("timestamp", 0) < CACHE_TTL
    ):
        return _cache["data"], _cache["fetched_at"], True
    
    # Fetch fresh data
    try:
        fetched_at, raw_data = fetch_odds_from_api(sport)
        
        # Transform to our game format
        games = transform_odds_to_games(raw_data, sport)
        
        # Update cache
        _cache = {
            "data": games,
            "timestamp": current_time,
            "fetched_at": fetched_at,
            "sport": sport,
        }
        
        return games, fetched_at, False
        
    except ValueError as e:
        # Re-raise ValueError (auth/rate limit errors) - don't cache these
        raise
    except requests.exceptions.RequestException as e:
        # If API fails and we have cached data, return it
        if _cache.get("data") is not None and _cache.get("sport") == sport:
            logger.warning(f"API request failed, returning cached data: {str(e)}")
            return _cache["data"], _cache["fetched_at"], True
        # If no cache, raise with more context
        error_msg = str(e)
        if "401" in error_msg or "Unauthorized" in error_msg:
            raise ValueError(
                f"ODDS_API_KEY is invalid or expired. Please check your API key. "
                f"Original error: {error_msg}"
            )
        raise Exception(f"Failed to fetch odds data: {error_msg}")


def get_remaining_requests() -> Optional[int]:
    """
    Check remaining API requests (from response headers).
    The-odds-api includes this in response headers.
    """
    # This would be populated from the last API response
    # For now, return None as we don't track this yet
    return None

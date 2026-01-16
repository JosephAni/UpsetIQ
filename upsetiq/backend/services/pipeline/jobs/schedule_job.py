"""Schedule refresh job - updates game schedules from SportsDataIO."""
import logging
from datetime import datetime, timezone
from typing import Dict, Any

from services.sportsdata_io import (
    get_schedules,
    get_current_season,
    get_current_week,
)
from services.supabase_client import (
    pipeline_run_context,
    is_supabase_configured,
    get_supabase_client,
)

logger = logging.getLogger(__name__)


def transform_schedule_to_game(schedule: Dict[str, Any]) -> Dict[str, Any]:
    """Transform SportsDataIO schedule item to game record."""
    return {
        "id": schedule.get("GameKey") or str(schedule.get("ScoreID", "")),
        "sport": "NFL",
        "home_team": schedule.get("HomeTeam", ""),
        "away_team": schedule.get("AwayTeam", ""),
        "start_time": schedule.get("DateTime") or schedule.get("Date"),
        "status": _map_game_status(schedule.get("Status", "")),
        "season": schedule.get("Season"),
        "week": schedule.get("Week"),
        "season_type": schedule.get("SeasonType", 1),
        "stadium": schedule.get("Stadium"),
        "channel": schedule.get("Channel"),
        "point_spread": schedule.get("PointSpread"),
        "over_under": schedule.get("OverUnder"),
        "home_team_moneyline": schedule.get("HomeTeamMoneyLine"),
        "away_team_moneyline": schedule.get("AwayTeamMoneyLine"),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def _map_game_status(status: str) -> str:
    """Map SportsDataIO status to internal status."""
    status_lower = status.lower() if status else ""
    
    if "scheduled" in status_lower:
        return "upcoming"
    elif "inprogress" in status_lower or "in progress" in status_lower:
        return "live"
    elif "final" in status_lower:
        return "completed"
    elif "postponed" in status_lower or "canceled" in status_lower:
        return "cancelled"
    else:
        return "upcoming"


async def run_schedule_refresh() -> Dict[str, Any]:
    """
    Run the schedule refresh job.
    
    Fetches current season schedule from SportsDataIO and updates
    the games table in Supabase.
    
    Returns:
        Job result summary
    """
    logger.info("Starting schedule refresh job")
    
    season = get_current_season()
    current_week = get_current_week(season)
    
    games_processed = 0
    games_updated = 0
    games_created = 0
    errors = []
    
    use_supabase = is_supabase_configured()
    
    try:
        logger.info(f"Fetching schedule for {season} season")
        schedules, fetched_at, cached = get_schedules(season)
        
        if not schedules:
            logger.warning("No schedule data returned")
            return {
                "status": "completed",
                "games_processed": 0,
                "message": "No schedule data available",
            }
        
        logger.info(f"Fetched {len(schedules)} games (cached: {cached})")
        games_processed = len(schedules)
        
        if use_supabase:
            with pipeline_run_context("schedule_refresh", "schedule") as run:
                client = get_supabase_client()
                
                # Transform and upsert games
                for schedule in schedules:
                    try:
                        game_data = transform_schedule_to_game(schedule)
                        game_id = game_data["id"]
                        
                        # Upsert: update if exists, insert if not
                        result = (
                            client.table("games")
                            .upsert(game_data, on_conflict="id")
                            .execute()
                        )
                        
                        if result.data:
                            games_updated += 1
                    
                    except Exception as e:
                        error_msg = f"Error processing game {schedule.get('GameKey')}: {e}"
                        logger.error(error_msg)
                        errors.append(error_msg)
                
                run["records_processed"] = games_processed
                run["records_updated"] = games_updated
                run["metadata"] = {
                    "season": season,
                    "current_week": current_week,
                    "cached": cached,
                    "errors": errors,
                }
        
        else:
            logger.warning("Supabase not configured - schedule refresh in dry-run mode")
    
    except Exception as e:
        logger.error(f"Schedule refresh job failed: {e}")
        raise
    
    result = {
        "status": "completed" if not errors else "completed_with_errors",
        "games_processed": games_processed,
        "games_updated": games_updated,
        "season": season,
        "current_week": current_week,
        "errors": errors,
    }
    
    logger.info(f"Schedule refresh job completed: {result}")
    return result

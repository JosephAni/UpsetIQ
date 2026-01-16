"""Injury update job - fetches current injury reports from SportsDataIO."""
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List

from services.sportsdata_io import get_injuries, get_current_season
from services.supabase_client import (
    pipeline_run_context,
    is_supabase_configured,
    get_supabase_client,
)

logger = logging.getLogger(__name__)


def transform_injury_record(injury: Dict[str, Any]) -> Dict[str, Any]:
    """Transform SportsDataIO injury to database record."""
    return {
        "player_id": injury.get("PlayerID"),
        "player_name": injury.get("Name", "Unknown"),
        "team": injury.get("Team", ""),
        "position": injury.get("Position", ""),
        "status": _normalize_injury_status(injury.get("Status", "")),
        "body_part": injury.get("BodyPart", "Undisclosed"),
        "practice_status": injury.get("PracticeStatus"),
        "practice_description": injury.get("PracticeDescription"),
        "declared_inactive": injury.get("DeclaredInactive", False),
        "injury_start_date": injury.get("InjuryStartDate"),
        "updated_at": injury.get("Updated") or datetime.now(timezone.utc).isoformat(),
        "source": "sportsdata_io",
    }


def _normalize_injury_status(status: str) -> str:
    """Normalize injury status to standard values."""
    status_lower = status.lower() if status else ""
    
    if "out" in status_lower:
        return "Out"
    elif "doubtful" in status_lower:
        return "Doubtful"
    elif "questionable" in status_lower:
        return "Questionable"
    elif "probable" in status_lower:
        return "Probable"
    elif "ir" in status_lower or "injured reserve" in status_lower:
        return "IR"
    elif "pup" in status_lower:
        return "PUP"
    elif "suspended" in status_lower:
        return "Suspended"
    else:
        return status or "Unknown"


def calculate_team_injury_impact(injuries: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculate injury impact score by team.
    
    Returns dict mapping team abbreviation to impact score (0-100).
    """
    team_impacts = {}
    
    # Position weights for impact calculation
    position_weights = {
        "QB": 15.0,
        "RB": 4.0,
        "WR": 3.0,
        "TE": 2.5,
        "LT": 4.0,
        "RT": 2.5,
        "LG": 2.0,
        "RG": 2.0,
        "C": 2.5,
        "DE": 3.0,
        "DT": 2.5,
        "OLB": 2.5,
        "ILB": 2.5,
        "MLB": 2.5,
        "LB": 2.5,
        "CB": 3.0,
        "SS": 2.5,
        "FS": 2.5,
        "S": 2.5,
        "K": 1.5,
        "P": 1.0,
    }
    
    # Status weights
    status_weights = {
        "Out": 1.0,
        "IR": 1.0,
        "Suspended": 1.0,
        "Doubtful": 0.8,
        "PUP": 0.7,
        "Questionable": 0.4,
        "Probable": 0.1,
    }
    
    for injury in injuries:
        team = injury.get("team", "")
        if not team:
            continue
        
        position = injury.get("position", "")
        status = injury.get("status", "")
        
        pos_weight = position_weights.get(position, 1.0)
        status_weight = status_weights.get(status, 0.5)
        
        impact = pos_weight * status_weight
        
        if team not in team_impacts:
            team_impacts[team] = 0.0
        team_impacts[team] += impact
    
    # Cap at 100
    for team in team_impacts:
        team_impacts[team] = min(100.0, team_impacts[team])
    
    return team_impacts


async def run_injury_update() -> Dict[str, Any]:
    """
    Run the injury update job.
    
    Fetches current injury reports from SportsDataIO and updates
    the injuries table in Supabase. Also calculates team injury impact scores.
    
    Returns:
        Job result summary
    """
    logger.info("Starting injury update job")
    
    season = get_current_season()
    injuries_processed = 0
    injuries_updated = 0
    errors = []
    team_impacts = {}
    
    use_supabase = is_supabase_configured()
    
    try:
        logger.info(f"Fetching injuries for {season} season")
        raw_injuries, fetched_at, cached = get_injuries(season)
        
        if not raw_injuries:
            logger.warning("No injury data returned")
            return {
                "status": "completed",
                "injuries_processed": 0,
                "message": "No injury data available",
            }
        
        logger.info(f"Fetched {len(raw_injuries)} injury records (cached: {cached})")
        injuries_processed = len(raw_injuries)
        
        # Transform injuries
        transformed_injuries = [
            transform_injury_record(inj) for inj in raw_injuries
        ]
        
        # Calculate team impacts
        team_impacts = calculate_team_injury_impact(transformed_injuries)
        logger.info(f"Calculated injury impacts for {len(team_impacts)} teams")
        
        if use_supabase:
            with pipeline_run_context("injury_update", "injury") as run:
                client = get_supabase_client()
                
                # Clear existing injuries and insert fresh data
                # This ensures we don't have stale injury records
                try:
                    # Delete injuries older than 7 days that are still "Out"
                    # Keep historical data for analysis
                    
                    # Batch insert current injuries
                    for injury in transformed_injuries:
                        try:
                            # Upsert by player_id
                            result = (
                                client.table("injuries")
                                .upsert(injury, on_conflict="player_id")
                                .execute()
                            )
                            injuries_updated += 1
                        except Exception as e:
                            error_msg = f"Error upserting injury for {injury.get('player_name')}: {e}"
                            logger.error(error_msg)
                            errors.append(error_msg)
                
                except Exception as e:
                    logger.error(f"Error updating injuries: {e}")
                    errors.append(str(e))
                
                run["records_processed"] = injuries_processed
                run["records_updated"] = injuries_updated
                run["metadata"] = {
                    "season": season,
                    "cached": cached,
                    "team_impacts": team_impacts,
                    "errors": errors,
                }
        
        else:
            logger.warning("Supabase not configured - injury update in dry-run mode")
    
    except Exception as e:
        logger.error(f"Injury update job failed: {e}")
        raise
    
    result = {
        "status": "completed" if not errors else "completed_with_errors",
        "injuries_processed": injuries_processed,
        "injuries_updated": injuries_updated,
        "season": season,
        "team_impacts": team_impacts,
        "top_impacted_teams": sorted(
            team_impacts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10],
        "errors": errors,
    }
    
    logger.info(f"Injury update job completed: {result}")
    return result

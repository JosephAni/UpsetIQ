"""Odds snapshot job - captures live odds from The Odds API."""
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any

from services.odds_api import fetch_odds_from_api, _get_sport_key
from services.supabase_client import (
    insert_odds_snapshots_batch,
    pipeline_run_context,
    is_supabase_configured,
)

logger = logging.getLogger(__name__)

# Sports to capture odds for
SPORTS_TO_TRACK = ["NFL", "NBA", "MLB", "NHL"]


def transform_odds_event_to_snapshot(
    event: Dict[str, Any],
    sport: str,
    captured_at: str
) -> List[Dict[str, Any]]:
    """
    Transform a single odds event to snapshot records.
    
    Creates one record per bookmaker for complete odds history.
    """
    snapshots = []
    
    game_id = event.get("id", "")
    home_team = event.get("home_team", "")
    away_team = event.get("away_team", "")
    commence_time = event.get("commence_time", "")
    
    for bookmaker in event.get("bookmakers", []):
        bookmaker_key = bookmaker.get("key", "")
        
        snapshot = {
            "game_id": game_id,
            "sport": sport,
            "home_team": home_team,
            "away_team": away_team,
            "bookmaker": bookmaker_key,
            "source": "odds_api",
            "captured_at": captured_at,
            "game_start_time": commence_time,
        }
        
        # Extract odds from markets
        for market in bookmaker.get("markets", []):
            market_key = market.get("key")
            outcomes = market.get("outcomes", [])
            
            if market_key == "h2h":
                # Moneyline odds
                for outcome in outcomes:
                    if outcome.get("name") == home_team:
                        snapshot["home_moneyline"] = outcome.get("price")
                    elif outcome.get("name") == away_team:
                        snapshot["away_moneyline"] = outcome.get("price")
                
                # Determine favorite/underdog
                home_ml = snapshot.get("home_moneyline", 0)
                away_ml = snapshot.get("away_moneyline", 0)
                
                if home_ml and away_ml:
                    if home_ml < away_ml:
                        snapshot["favorite"] = home_team
                        snapshot["underdog"] = away_team
                        snapshot["favorite_odds"] = home_ml
                        snapshot["underdog_odds"] = away_ml
                    else:
                        snapshot["favorite"] = away_team
                        snapshot["underdog"] = home_team
                        snapshot["favorite_odds"] = away_ml
                        snapshot["underdog_odds"] = home_ml
            
            elif market_key == "spreads":
                # Point spread
                for outcome in outcomes:
                    point = outcome.get("point")
                    price = outcome.get("price")
                    
                    if outcome.get("name") == home_team:
                        snapshot["spread"] = point
                        snapshot["spread_odds_home"] = price
                    elif outcome.get("name") == away_team:
                        snapshot["spread_odds_away"] = price
            
            elif market_key == "totals":
                # Over/under
                for outcome in outcomes:
                    if outcome.get("name") == "Over":
                        snapshot["total"] = outcome.get("point")
                        snapshot["over_odds"] = outcome.get("price")
                    elif outcome.get("name") == "Under":
                        snapshot["under_odds"] = outcome.get("price")
        
        snapshots.append(snapshot)
    
    return snapshots


async def run_odds_snapshot() -> Dict[str, Any]:
    """
    Run the odds snapshot job.
    
    Fetches current odds from The Odds API and stores snapshots
    in Supabase for historical tracking and line movement analysis.
    
    Returns:
        Job result summary
    """
    logger.info("Starting odds snapshot job")
    
    captured_at = datetime.now(timezone.utc).isoformat()
    total_snapshots = 0
    total_events = 0
    errors = []
    
    # Check if Supabase is configured
    use_supabase = is_supabase_configured()
    
    if use_supabase:
        try:
            with pipeline_run_context("odds_snapshot", "odds") as run:
                for sport in SPORTS_TO_TRACK:
                    try:
                        logger.info(f"Fetching odds for {sport}")
                        _, events = fetch_odds_from_api(sport)
                        
                        if not events:
                            logger.info(f"No events found for {sport}")
                            continue
                        
                        # Transform to snapshots
                        all_snapshots = []
                        for event in events:
                            snapshots = transform_odds_event_to_snapshot(
                                event, sport, captured_at
                            )
                            all_snapshots.extend(snapshots)
                        
                        # Batch insert
                        if all_snapshots:
                            inserted = insert_odds_snapshots_batch(all_snapshots)
                            total_snapshots += inserted
                            total_events += len(events)
                            logger.info(
                                f"Inserted {inserted} snapshots for {sport} "
                                f"({len(events)} events)"
                            )
                    
                    except Exception as e:
                        error_msg = f"Error fetching {sport} odds: {e}"
                        logger.error(error_msg)
                        errors.append(error_msg)
                
                run["records_processed"] = total_events
                run["records_created"] = total_snapshots
                run["metadata"] = {
                    "sports": SPORTS_TO_TRACK,
                    "errors": errors,
                }
        
        except Exception as e:
            logger.error(f"Odds snapshot job failed: {e}")
            raise
    
    else:
        # Supabase not configured - just fetch and log
        logger.warning("Supabase not configured - running in dry-run mode")
        
        for sport in SPORTS_TO_TRACK:
            try:
                _, events = fetch_odds_from_api(sport)
                total_events += len(events) if events else 0
                logger.info(f"Fetched {len(events) if events else 0} events for {sport}")
            except Exception as e:
                logger.error(f"Error fetching {sport}: {e}")
    
    result = {
        "status": "completed" if not errors else "completed_with_errors",
        "events_processed": total_events,
        "snapshots_created": total_snapshots,
        "sports": SPORTS_TO_TRACK,
        "errors": errors,
        "captured_at": captured_at,
    }
    
    logger.info(f"Odds snapshot job completed: {result}")
    return result

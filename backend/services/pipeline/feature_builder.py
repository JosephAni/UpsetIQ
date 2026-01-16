"""Feature builder - combines data sources into ML-ready features."""
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

from services.supabase_client import (
    get_supabase_client,
    get_latest_odds_snapshot,
    get_odds_history,
    get_latest_sentiment,
    insert_game_features_batch,
    pipeline_run_context,
    is_supabase_configured,
)

logger = logging.getLogger(__name__)


def calculate_line_movement(odds_history: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculate line movement from odds history.
    
    Returns:
        Dict with spread_movement, moneyline_movement, etc.
    """
    if not odds_history or len(odds_history) < 2:
        return {
            "spread_movement": 0.0,
            "moneyline_movement": 0,
            "movement_direction": "stable",
        }
    
    # Sort by capture time (oldest first)
    sorted_history = sorted(odds_history, key=lambda x: x.get("captured_at", ""))
    
    first = sorted_history[0]
    latest = sorted_history[-1]
    
    # Calculate movements
    first_spread = first.get("spread") or 0
    latest_spread = latest.get("spread") or 0
    spread_movement = latest_spread - first_spread
    
    first_ml = first.get("underdog_odds") or 0
    latest_ml = latest.get("underdog_odds") or 0
    ml_movement = latest_ml - first_ml
    
    # Determine direction
    if spread_movement < -0.5:
        direction = "favorite"  # Line moved toward favorite
    elif spread_movement > 0.5:
        direction = "underdog"  # Line moved toward underdog
    else:
        direction = "stable"
    
    return {
        "spread_movement": spread_movement,
        "moneyline_movement": ml_movement,
        "opening_spread": first_spread,
        "current_spread": latest_spread,
        "opening_moneyline": first_ml,
        "current_moneyline": latest_ml,
        "movement_direction": direction,
        "snapshots_analyzed": len(sorted_history),
    }


def calculate_implied_probability(odds: int) -> float:
    """
    Convert American odds to implied probability.
    
    Args:
        odds: American odds (e.g., +150 or -200)
        
    Returns:
        Implied probability (0 to 1)
    """
    if odds > 0:
        return 100 / (odds + 100)
    elif odds < 0:
        return abs(odds) / (abs(odds) + 100)
    else:
        return 0.5


def build_game_features(
    game: Dict[str, Any],
    odds_snapshot: Optional[Dict[str, Any]],
    favorite_sentiment: Optional[Dict[str, Any]],
    underdog_sentiment: Optional[Dict[str, Any]],
    favorite_injuries: Optional[List[Dict[str, Any]]],
    underdog_injuries: Optional[List[Dict[str, Any]]],
    favorite_record: Optional[Dict[str, Any]],
    underdog_record: Optional[Dict[str, Any]],
    line_movement: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Build comprehensive feature set for a game.
    
    Args:
        game: Game data
        odds_snapshot: Latest odds
        favorite_sentiment: Sentiment for favorite team
        underdog_sentiment: Sentiment for underdog team
        favorite_injuries: Injuries on favorite team
        underdog_injuries: Injuries on underdog team
        favorite_record: Standings record for favorite
        underdog_record: Standings record for underdog
        line_movement: Calculated line movement
        
    Returns:
        Feature dictionary ready for model scoring
    """
    features = {
        "game_id": game.get("id"),
        "sport": game.get("sport", "NFL"),
        "favorite": game.get("favorite") or game.get("home_team", ""),
        "underdog": game.get("underdog") or game.get("away_team", ""),
        "game_start_time": game.get("start_time") or game.get("DateTime"),
        "computed_at": datetime.now(timezone.utc).isoformat(),
    }
    
    # Odds features
    if odds_snapshot:
        features.update({
            "current_spread": odds_snapshot.get("spread"),
            "current_moneyline": odds_snapshot.get("underdog_odds"),
            "implied_probability": calculate_implied_probability(
                odds_snapshot.get("underdog_odds") or 0
            ),
            "over_under": odds_snapshot.get("total"),
        })
    
    # Line movement features
    if line_movement:
        features.update({
            "opening_spread": line_movement.get("opening_spread"),
            "spread_movement": line_movement.get("spread_movement"),
            "opening_moneyline": line_movement.get("opening_moneyline"),
            "moneyline_movement": line_movement.get("moneyline_movement"),
        })
    
    # Sentiment features
    if favorite_sentiment:
        features.update({
            "favorite_sentiment": favorite_sentiment.get("sentiment_score", 0),
            "reddit_volume_favorite": favorite_sentiment.get("total_posts", 0),
        })
    
    if underdog_sentiment:
        features.update({
            "underdog_sentiment": underdog_sentiment.get("sentiment_score", 0),
            "reddit_volume_underdog": underdog_sentiment.get("total_posts", 0),
        })
    
    if favorite_sentiment and underdog_sentiment:
        features["sentiment_differential"] = (
            (underdog_sentiment.get("sentiment_score", 0) or 0) -
            (favorite_sentiment.get("sentiment_score", 0) or 0)
        )
    
    # Injury features
    features["favorite_injury_score"] = calculate_injury_score(favorite_injuries)
    features["underdog_injury_score"] = calculate_injury_score(underdog_injuries)
    features["qb_injury_favorite"] = has_qb_injury(favorite_injuries)
    features["qb_injury_underdog"] = has_qb_injury(underdog_injuries)
    features["key_players_out_favorite"] = count_key_injuries(favorite_injuries)
    features["key_players_out_underdog"] = count_key_injuries(underdog_injuries)
    
    # Record/standings features
    if favorite_record:
        features.update({
            "favorite_win_pct": favorite_record.get("win_percentage", 0),
            "favorite_streak": favorite_record.get("streak", 0),
        })
    
    if underdog_record:
        features.update({
            "underdog_win_pct": underdog_record.get("win_percentage", 0),
            "underdog_streak": underdog_record.get("streak", 0),
        })
    
    # Situational features
    features["is_prime_time"] = is_prime_time_game(game)
    
    return features


def calculate_injury_score(injuries: Optional[List[Dict[str, Any]]]) -> float:
    """Calculate total injury impact score for a team."""
    if not injuries:
        return 0.0
    
    position_weights = {
        "QB": 15.0, "RB": 4.0, "WR": 3.0, "TE": 2.5,
        "LT": 4.0, "RT": 2.5, "C": 2.5, "LG": 2.0, "RG": 2.0,
        "DE": 3.0, "DT": 2.5, "LB": 2.5, "CB": 3.0, "S": 2.5,
    }
    
    status_weights = {
        "Out": 1.0, "IR": 1.0, "Doubtful": 0.8,
        "Questionable": 0.4, "Probable": 0.1,
    }
    
    total = 0.0
    for injury in injuries:
        pos = injury.get("position", "")
        status = injury.get("status", "")
        
        pos_weight = position_weights.get(pos, 1.0)
        status_weight = status_weights.get(status, 0.5)
        
        total += pos_weight * status_weight
    
    return min(100.0, total)


def has_qb_injury(injuries: Optional[List[Dict[str, Any]]]) -> bool:
    """Check if there's a significant QB injury."""
    if not injuries:
        return False
    
    for injury in injuries:
        if injury.get("position") == "QB":
            status = injury.get("status", "")
            if status in ["Out", "IR", "Doubtful"]:
                return True
    
    return False


def count_key_injuries(injuries: Optional[List[Dict[str, Any]]]) -> int:
    """Count significant injuries to key players."""
    if not injuries:
        return 0
    
    key_positions = {"QB", "RB", "WR", "LT", "DE", "CB"}
    significant_statuses = {"Out", "IR", "Doubtful"}
    
    count = 0
    for injury in injuries:
        if (
            injury.get("position") in key_positions and
            injury.get("status") in significant_statuses
        ):
            count += 1
    
    return count


def is_prime_time_game(game: Dict[str, Any]) -> bool:
    """Check if game is a prime time game."""
    start_time = game.get("start_time") or game.get("DateTime", "")
    
    if not start_time:
        return False
    
    try:
        dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        hour = dt.hour
        weekday = dt.weekday()
        
        # Thursday (3), Sunday night (6), Monday (0) evening
        if weekday == 3 and hour >= 20:  # Thursday Night
            return True
        if weekday == 6 and hour >= 20:  # Sunday Night
            return True
        if weekday == 0 and hour >= 20:  # Monday Night
            return True
        
        return False
    except:
        return False


async def run_feature_build() -> Dict[str, Any]:
    """
    Run the feature building pipeline.
    
    Combines odds, sentiment, injury, and standings data into
    ML-ready features for each upcoming game.
    
    Returns:
        Job result summary
    """
    logger.info("Starting feature build job")
    
    if not is_supabase_configured():
        logger.warning("Supabase not configured - skipping feature build")
        return {
            "status": "skipped",
            "reason": "Supabase not configured",
        }
    
    features_built = 0
    errors = []
    
    try:
        with pipeline_run_context("feature_build", "feature") as run:
            client = get_supabase_client()
            
            # Get upcoming games
            result = (
                client.table("games")
                .select("*")
                .eq("status", "upcoming")
                .execute()
            )
            
            games = result.data if result.data else []
            logger.info(f"Building features for {len(games)} upcoming games")
            
            all_features = []
            
            for game in games:
                try:
                    game_id = game.get("id")
                    favorite = game.get("favorite") or game.get("home_team", "")
                    underdog = game.get("underdog") or game.get("away_team", "")
                    
                    # Get latest odds
                    odds = get_latest_odds_snapshot(game_id)
                    
                    # Get odds history for line movement
                    odds_history = get_odds_history(game_id, limit=50)
                    line_movement = calculate_line_movement(odds_history)
                    
                    # Get sentiment
                    fav_sentiment = get_latest_sentiment("team", favorite, "reddit")
                    und_sentiment = get_latest_sentiment("team", underdog, "reddit")
                    
                    # Get injuries (from injuries table)
                    fav_injuries = (
                        client.table("injuries")
                        .select("*")
                        .eq("team", favorite)
                        .execute()
                    ).data or []
                    
                    und_injuries = (
                        client.table("injuries")
                        .select("*")
                        .eq("team", underdog)
                        .execute()
                    ).data or []
                    
                    # Get standings
                    fav_record = (
                        client.table("standings")
                        .select("*")
                        .eq("team", favorite)
                        .limit(1)
                        .execute()
                    ).data
                    fav_record = fav_record[0] if fav_record else None
                    
                    und_record = (
                        client.table("standings")
                        .select("*")
                        .eq("team", underdog)
                        .limit(1)
                        .execute()
                    ).data
                    und_record = und_record[0] if und_record else None
                    
                    # Build features
                    features = build_game_features(
                        game=game,
                        odds_snapshot=odds,
                        favorite_sentiment=fav_sentiment,
                        underdog_sentiment=und_sentiment,
                        favorite_injuries=fav_injuries,
                        underdog_injuries=und_injuries,
                        favorite_record=fav_record,
                        underdog_record=und_record,
                        line_movement=line_movement,
                    )
                    
                    all_features.append(features)
                    features_built += 1
                
                except Exception as e:
                    error_msg = f"Error building features for game {game.get('id')}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            # Store features
            if all_features:
                inserted = insert_game_features_batch(all_features)
                logger.info(f"Inserted {inserted} feature records")
            
            run["records_processed"] = len(games)
            run["records_created"] = features_built
            run["metadata"] = {"errors": errors}
    
    except Exception as e:
        logger.error(f"Feature build job failed: {e}")
        raise
    
    result = {
        "status": "completed" if not errors else "completed_with_errors",
        "games_processed": len(games) if 'games' in locals() else 0,
        "features_built": features_built,
        "errors": errors,
    }
    
    logger.info(f"Feature build job completed: {result}")
    return result

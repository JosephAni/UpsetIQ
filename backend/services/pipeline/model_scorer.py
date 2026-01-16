"""Model scorer - calculates Upset Probability Score (UPS) from features."""
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

from services.supabase_client import (
    get_supabase_client,
    get_latest_game_features,
    pipeline_run_context,
    is_supabase_configured,
)

logger = logging.getLogger(__name__)

# Model version
MODEL_VERSION = "v2.1-pipeline"


def calculate_base_ups(
    implied_prob: float,
    spread: Optional[float],
) -> float:
    """
    Calculate base UPS from implied probability and spread.
    
    Args:
        implied_prob: Implied win probability for underdog (0-1)
        spread: Point spread (negative for favorite)
        
    Returns:
        Base UPS score (0-100)
    """
    # Base UPS from implied probability
    base_ups = implied_prob * 100
    
    # Spread adjustment
    if spread is not None:
        abs_spread = abs(spread)
        if abs_spread <= 3:
            base_ups += 12
        elif abs_spread <= 6:
            base_ups += 8
        elif abs_spread <= 10:
            base_ups += 4
        # Large spreads slightly reduce UPS
        elif abs_spread > 14:
            base_ups -= 5
    
    return base_ups


def calculate_injury_adjustment(
    favorite_injury_score: float,
    underdog_injury_score: float,
    qb_injury_favorite: bool,
    qb_injury_underdog: bool,
) -> Tuple[float, List[str]]:
    """
    Calculate UPS adjustment from injury data.
    
    Args:
        favorite_injury_score: Total injury impact on favorite
        underdog_injury_score: Total injury impact on underdog
        qb_injury_favorite: Whether favorite has QB injury
        qb_injury_underdog: Whether underdog has QB injury
        
    Returns:
        Tuple of (adjustment, list of signal descriptions)
    """
    adjustment = 0.0
    signals = []
    
    # QB injury is massive
    if qb_injury_favorite:
        adjustment += 15.0
        signals.append("Favorite QB injured/out")
    
    if qb_injury_underdog:
        adjustment -= 10.0
        signals.append("Underdog QB injured/out")
    
    # General injury differential
    injury_diff = favorite_injury_score - underdog_injury_score
    
    if injury_diff > 20:
        adjustment += 8.0
        signals.append("Favorite heavily impacted by injuries")
    elif injury_diff > 10:
        adjustment += 4.0
        signals.append("Favorite has more injuries")
    elif injury_diff < -20:
        adjustment -= 5.0
        signals.append("Underdog heavily impacted by injuries")
    
    return adjustment, signals


def calculate_sentiment_adjustment(
    favorite_sentiment: Optional[float],
    underdog_sentiment: Optional[float],
    sentiment_differential: Optional[float],
) -> Tuple[float, List[str]]:
    """
    Calculate UPS adjustment from sentiment data.
    
    Contrarian indicator: extreme public sentiment may indicate value
    in betting against the crowd.
    
    Returns:
        Tuple of (adjustment, list of signals)
    """
    adjustment = 0.0
    signals = []
    
    if sentiment_differential is not None:
        # Positive differential = underdog more popular sentiment
        # This could be contrarian signal
        if sentiment_differential > 0.3:
            adjustment -= 3.0  # Public on underdog, less upset value
        elif sentiment_differential < -0.3:
            adjustment += 5.0  # Public against underdog, more upset value
            signals.append("Public sentiment favoring favorite heavily")
    
    if favorite_sentiment is not None and favorite_sentiment > 0.4:
        adjustment += 3.0
        signals.append("Extremely positive buzz around favorite")
    
    return adjustment, signals


def calculate_line_movement_adjustment(
    spread_movement: Optional[float],
    moneyline_movement: Optional[int],
) -> Tuple[float, List[str]]:
    """
    Calculate UPS adjustment from line movement.
    
    Sharp money often moves lines. Movement toward underdog
    may indicate smart money on the upset.
    
    Returns:
        Tuple of (adjustment, list of signals)
    """
    adjustment = 0.0
    signals = []
    
    if spread_movement is not None:
        # Positive spread_movement = line moved toward underdog
        if spread_movement >= 1.5:
            adjustment += 8.0
            signals.append(f"Line moved {spread_movement:.1f} pts toward underdog")
        elif spread_movement >= 0.5:
            adjustment += 4.0
            signals.append("Sharp money potentially on underdog")
        elif spread_movement <= -1.5:
            adjustment -= 5.0
            signals.append("Line moved heavily toward favorite")
    
    return adjustment, signals


def calculate_record_adjustment(
    favorite_win_pct: Optional[float],
    underdog_win_pct: Optional[float],
    favorite_streak: Optional[int],
    underdog_streak: Optional[int],
) -> Tuple[float, List[str]]:
    """
    Calculate UPS adjustment from team records and streaks.
    
    Returns:
        Tuple of (adjustment, list of signals)
    """
    adjustment = 0.0
    signals = []
    
    # Win percentage comparison
    if favorite_win_pct is not None and underdog_win_pct is not None:
        diff = underdog_win_pct - favorite_win_pct
        
        if diff >= 0:
            # Underdog has equal or better record!
            adjustment += 10.0
            signals.append("Underdog has equal or better record")
        elif diff >= -0.15:
            adjustment += 4.0
            signals.append("Teams have similar records")
    
    # Streak analysis
    if underdog_streak is not None and underdog_streak >= 3:
        adjustment += 5.0
        signals.append(f"Underdog on {underdog_streak}-game win streak")
    
    if favorite_streak is not None and favorite_streak <= -3:
        adjustment += 5.0
        signals.append(f"Favorite on {abs(favorite_streak)}-game losing streak")
    
    return adjustment, signals


def calculate_situational_adjustment(
    is_prime_time: bool,
) -> Tuple[float, List[str]]:
    """
    Calculate UPS adjustment from situational factors.
    
    Returns:
        Tuple of (adjustment, list of signals)
    """
    adjustment = 0.0
    signals = []
    
    # Prime time games historically have more upsets
    if is_prime_time:
        adjustment += 3.0
        signals.append("Prime time game - historically more upsets")
    
    return adjustment, signals


def score_game(features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate final UPS score from features.
    
    Args:
        features: Feature dictionary from feature builder
        
    Returns:
        Scoring result with UPS, confidence, and signals
    """
    all_signals = []
    
    # 1. Base UPS from odds
    implied_prob = features.get("implied_probability", 0.35)
    spread = features.get("current_spread")
    
    ups = calculate_base_ups(implied_prob, spread)
    
    # 2. Injury adjustment
    injury_adj, injury_signals = calculate_injury_adjustment(
        features.get("favorite_injury_score", 0),
        features.get("underdog_injury_score", 0),
        features.get("qb_injury_favorite", False),
        features.get("qb_injury_underdog", False),
    )
    ups += injury_adj
    all_signals.extend(injury_signals)
    
    # 3. Sentiment adjustment
    sentiment_adj, sentiment_signals = calculate_sentiment_adjustment(
        features.get("favorite_sentiment"),
        features.get("underdog_sentiment"),
        features.get("sentiment_differential"),
    )
    ups += sentiment_adj
    all_signals.extend(sentiment_signals)
    
    # 4. Line movement adjustment
    line_adj, line_signals = calculate_line_movement_adjustment(
        features.get("spread_movement"),
        features.get("moneyline_movement"),
    )
    ups += line_adj
    all_signals.extend(line_signals)
    
    # 5. Record adjustment
    record_adj, record_signals = calculate_record_adjustment(
        features.get("favorite_win_pct"),
        features.get("underdog_win_pct"),
        features.get("favorite_streak"),
        features.get("underdog_streak"),
    )
    ups += record_adj
    all_signals.extend(record_signals)
    
    # 6. Situational adjustment
    situational_adj, situational_signals = calculate_situational_adjustment(
        features.get("is_prime_time", False),
    )
    ups += situational_adj
    all_signals.extend(situational_signals)
    
    # Clamp UPS to 0-100
    ups = max(0, min(100, ups))
    
    # Calculate confidence based on data completeness
    data_points = sum(1 for k, v in features.items() if v is not None)
    total_expected = 20  # Expected feature count
    confidence = min(1.0, data_points / total_expected)
    
    return {
        "game_id": features.get("game_id"),
        "ups_score": round(ups, 1),
        "ups_confidence": round(confidence, 3),
        "model_version": MODEL_VERSION,
        "signals": all_signals[:6],  # Top 6 signals
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "adjustments": {
            "base": round(calculate_base_ups(implied_prob, spread), 1),
            "injury": round(injury_adj, 1),
            "sentiment": round(sentiment_adj, 1),
            "line_movement": round(line_adj, 1),
            "record": round(record_adj, 1),
            "situational": round(situational_adj, 1),
        },
    }


async def run_model_scoring() -> Dict[str, Any]:
    """
    Run the model scoring pipeline.
    
    Reads features for upcoming games and calculates UPS scores.
    Updates game_features table with scores.
    
    Returns:
        Job result summary
    """
    logger.info("Starting model scoring job")
    
    if not is_supabase_configured():
        logger.warning("Supabase not configured - skipping model scoring")
        return {
            "status": "skipped",
            "reason": "Supabase not configured",
        }
    
    games_scored = 0
    high_ups_games = []
    errors = []
    
    try:
        with pipeline_run_context("model_score", "score") as run:
            client = get_supabase_client()
            
            # Get latest features for each game
            result = (
                client.table("game_features")
                .select("*")
                .order("computed_at", desc=True)
                .execute()
            )
            
            # Group by game_id, take latest
            features_by_game = {}
            for f in (result.data or []):
                game_id = f.get("game_id")
                if game_id not in features_by_game:
                    features_by_game[game_id] = f
            
            logger.info(f"Scoring {len(features_by_game)} games")
            
            for game_id, features in features_by_game.items():
                try:
                    # Score the game
                    score_result = score_game(features)
                    
                    # Update features with score
                    client.table("game_features").update({
                        "ups_score": score_result["ups_score"],
                        "ups_confidence": score_result["ups_confidence"],
                        "model_version": score_result["model_version"],
                    }).eq("game_id", game_id).execute()
                    
                    games_scored += 1
                    
                    # Track high UPS games for alerts
                    if score_result["ups_score"] >= 60:
                        high_ups_games.append({
                            "game_id": game_id,
                            "favorite": features.get("favorite"),
                            "underdog": features.get("underdog"),
                            "ups_score": score_result["ups_score"],
                            "signals": score_result["signals"],
                        })
                
                except Exception as e:
                    error_msg = f"Error scoring game {game_id}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            run["records_processed"] = len(features_by_game)
            run["records_updated"] = games_scored
            run["metadata"] = {
                "high_ups_games": len(high_ups_games),
                "errors": errors,
            }
    
    except Exception as e:
        logger.error(f"Model scoring job failed: {e}")
        raise
    
    result = {
        "status": "completed" if not errors else "completed_with_errors",
        "games_scored": games_scored,
        "high_ups_games": high_ups_games,
        "model_version": MODEL_VERSION,
        "errors": errors,
    }
    
    logger.info(f"Model scoring job completed: {result}")
    return result

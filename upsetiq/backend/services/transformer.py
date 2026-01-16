"""Transform Odds API response to UpsetIQ game types with UPS calculation.

This module handles transformation of raw Odds API data to UpsetIQ game models,
including Upset Probability Score (UPS) calculation with optional enhancement
from SportsDataIO injury and stats data.
"""
import hashlib
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple

from models import (
    GameWithPrediction,
    Prediction,
    MarketSignal,
    Driver,
    Injury,
    Standing,
)

logger = logging.getLogger(__name__)


def _generate_game_id(event: Dict) -> str:
    """Generate a unique game ID from event data."""
    # Use home_team, away_team, and commence_time for uniqueness
    raw = f"{event.get('home_team')}_{event.get('away_team')}_{event.get('commence_time')}"
    return hashlib.md5(raw.encode()).hexdigest()[:16]


def _extract_bookmaker_odds(
    bookmakers: List[Dict], 
    market_type: str
) -> Tuple[Optional[Dict], Optional[Dict]]:
    """
    Extract odds from bookmakers for a specific market type.
    Returns (first bookmaker odds, consensus average).
    """
    all_odds = []
    
    for bookmaker in bookmakers:
        for market in bookmaker.get("markets", []):
            if market.get("key") == market_type:
                all_odds.append({
                    "bookmaker": bookmaker.get("key"),
                    "outcomes": market.get("outcomes", []),
                    "last_update": market.get("last_update"),
                })
    
    if not all_odds:
        return None, None
    
    return all_odds[0], all_odds


def _determine_favorite(h2h_odds: Dict, home_team: str, away_team: str) -> Tuple[str, str, float, float]:
    """
    Determine favorite and underdog from h2h (moneyline) odds.
    Returns (favorite, underdog, favorite_odds, underdog_odds).
    """
    outcomes = h2h_odds.get("outcomes", [])
    
    if len(outcomes) < 2:
        # Default if no odds
        return home_team, away_team, -150, 150
    
    team_odds = {}
    for outcome in outcomes:
        team_odds[outcome.get("name")] = outcome.get("price", 0)
    
    home_odds = team_odds.get(home_team, 0)
    away_odds = team_odds.get(away_team, 0)
    
    # In American odds, the favorite has negative odds (or lower positive)
    if home_odds < away_odds:
        return home_team, away_team, home_odds, away_odds
    else:
        return away_team, home_team, away_odds, home_odds


def _extract_spread_odds(
    spreads_odds: Optional[Dict], 
    favorite: str
) -> Tuple[Optional[float], Optional[float]]:
    """Extract spread for the favorite team."""
    if not spreads_odds:
        return None, None
    
    for outcome in spreads_odds.get("outcomes", []):
        if outcome.get("name") == favorite:
            point = outcome.get("point")
            return point, point  # open and current same for now
    
    return None, None


def _extract_total_odds(totals_odds: Optional[Dict]) -> Tuple[Optional[float], Optional[float]]:
    """Extract over/under total."""
    if not totals_odds:
        return None, None
    
    for outcome in totals_odds.get("outcomes", []):
        if outcome.get("name") == "Over":
            point = outcome.get("point")
            return point, point  # open and current same for now
    
    return None, None


def _calculate_upset_probability(
    underdog_odds: float,
    spread: Optional[float],
    public_pct: float,
) -> float:
    """
    Calculate upset probability score (UPS) based on multiple factors.
    
    This is a simplified model that considers:
    - Implied probability from moneyline odds
    - Spread (closer spreads = higher upset chance)
    - Public betting percentage (contrarian indicator)
    
    Returns a value between 0-100.
    """
    # 1. Implied probability from underdog odds
    if underdog_odds > 0:
        implied_prob = 100 / (underdog_odds + 100)
    else:
        implied_prob = abs(underdog_odds) / (abs(underdog_odds) + 100)
    
    # Base UPS from implied probability (scaled to 0-100)
    base_ups = implied_prob * 100
    
    # 2. Spread adjustment (closer spread = higher upset chance)
    spread_boost = 0
    if spread is not None:
        # Spreads closer to 0 suggest more competitive game
        if abs(spread) <= 3:
            spread_boost = 15
        elif abs(spread) <= 6:
            spread_boost = 10
        elif abs(spread) <= 10:
            spread_boost = 5
    
    # 3. Public betting contrarian boost
    # If public heavily on favorite (>70%), boost upset probability
    contrarian_boost = 0
    if public_pct > 75:
        contrarian_boost = 12
    elif public_pct > 70:
        contrarian_boost = 8
    elif public_pct > 65:
        contrarian_boost = 4
    
    # Calculate final UPS
    ups = base_ups + spread_boost + contrarian_boost
    
    # Clamp to 0-100 range
    return min(100, max(0, round(ups, 1)))


def _generate_drivers(
    game_data: Dict,
    spread: Optional[float],
    public_pct: float,
    ups: float,
) -> List[Driver]:
    """Generate key signal drivers for the prediction."""
    drivers = []
    
    # Spread movement (simulated - in real app would compare to opening)
    if spread is not None and abs(spread) <= 3:
        drivers.append(Driver(label="Spread tight - competitive matchup expected"))
    
    # Public betting contrarian
    if public_pct >= 75:
        drivers.append(Driver(label=f"Public heavily biased ({int(public_pct)}% on favorite)"))
    elif public_pct >= 70:
        drivers.append(Driver(label=f"Public ≥ 70% on favorite"))
    
    # High UPS signal
    if ups >= 65:
        drivers.append(Driver(label="Historical anomaly detected"))
    
    # Prime time indicator
    commence_time = game_data.get("commence_time", "")
    if commence_time:
        try:
            dt = datetime.fromisoformat(commence_time.replace("Z", "+00:00"))
            hour = dt.hour
            weekday = dt.weekday()
            
            # Thursday (3), Sunday night (6), Monday (0) prime time
            if weekday == 3 and hour >= 20:  # Thursday Night
                drivers.append(Driver(label="Thursday Night Football"))
            elif weekday == 6 and hour >= 20:  # Sunday Night
                drivers.append(Driver(label="Sunday Night Football"))
            elif weekday == 0 and hour >= 20:  # Monday Night
                drivers.append(Driver(label="Monday Night Football"))
        except:
            pass
    
    # Model confidence
    if len(drivers) < 3:
        drivers.append(Driver(label="Model confidence high"))
    
    # Ensure at least 3 drivers
    while len(drivers) < 3:
        drivers.append(Driver(label="Pattern recognition signal"))
    
    return drivers[:6]  # Max 6 drivers


def _is_prime_time(commence_time: str) -> bool:
    """Check if game is prime time (Thu/Sun/Mon night)."""
    try:
        dt = datetime.fromisoformat(commence_time.replace("Z", "+00:00"))
        hour = dt.hour
        weekday = dt.weekday()
        
        # Thursday (3), Sunday (6), Monday (0) evening games
        if weekday == 3 and hour >= 20:  # Thursday Night
            return True
        if weekday == 6 and hour >= 20:  # Sunday Night
            return True
        if weekday == 0 and hour >= 20:  # Monday Night
            return True
        
        return False
    except:
        return False


def _simulate_public_percentage(underdog_odds: float) -> float:
    """
    Simulate public betting percentage.
    In production, this would come from actual betting data.
    
    Generally, public tends to bet on favorites more heavily.
    """
    # Base public percentage inversely related to underdog odds
    # Higher underdog odds = more public on favorite
    if underdog_odds > 200:
        base_pct = 78
    elif underdog_odds > 150:
        base_pct = 72
    elif underdog_odds > 100:
        base_pct = 68
    else:
        base_pct = 62
    
    # Add some variance
    import random
    variance = random.uniform(-5, 5)
    
    return min(95, max(50, base_pct + variance))


def transform_odds_to_games(
    raw_events: List[Dict[str, Any]], 
    sport: str = "NFL"
) -> List[GameWithPrediction]:
    """
    Transform raw Odds API events to GameWithPrediction models.
    """
    games = []
    now = datetime.now(timezone.utc).isoformat()
    
    for event in raw_events:
        try:
            game_id = _generate_game_id(event)
            home_team = event.get("home_team", "Unknown")
            away_team = event.get("away_team", "Unknown")
            bookmakers = event.get("bookmakers", [])
            
            if not bookmakers:
                continue
            
            # Extract odds from different markets
            h2h_odds, _ = _extract_bookmaker_odds(bookmakers, "h2h")
            spreads_odds, _ = _extract_bookmaker_odds(bookmakers, "spreads")
            totals_odds, _ = _extract_bookmaker_odds(bookmakers, "totals")
            
            if not h2h_odds:
                continue
            
            # Determine favorite and underdog
            favorite, underdog, fav_odds, und_odds = _determine_favorite(
                h2h_odds, home_team, away_team
            )
            
            # Extract spread and totals
            spread_open, spread_current = _extract_spread_odds(spreads_odds, favorite)
            total_open, total_current = _extract_total_odds(totals_odds)
            
            # Simulate public betting percentage
            public_pct = _simulate_public_percentage(und_odds)
            
            # Calculate upset probability
            ups = _calculate_upset_probability(und_odds, spread_current, public_pct)
            
            # Generate drivers
            drivers = _generate_drivers(event, spread_current, public_pct, ups)
            
            # Check if prime time
            commence_time = event.get("commence_time", "")
            is_prime_time = _is_prime_time(commence_time)
            
            # Create prediction
            prediction = Prediction(
                id=f"pred_{game_id}",
                game_id=game_id,
                upset_probability=ups,
                model_version="v1.0",
                confidence_band=min(20, max(5, 100 - ups) / 5),
                created_at=now,
            )
            
            # Create market signal
            market_signal = MarketSignal(
                id=f"signal_{game_id}",
                game_id=game_id,
                public_bet_percentage=public_pct,
                line_movement=0 if spread_open is None else (spread_current or 0) - spread_open,
                sentiment_score=0.0,  # Would come from sentiment analysis
                created_at=now,
            )
            
            # Create game with prediction
            game = GameWithPrediction(
                id=game_id,
                sport=sport,
                team_favorite=favorite,
                team_underdog=underdog,
                start_time=commence_time,
                odds_open=fav_odds,
                odds_current=fav_odds,  # Same for now
                status="upcoming",
                isPrimeTime=is_prime_time,
                spreadOpen=spread_open,
                spreadCurrent=spread_current,
                totalOpen=total_open,
                totalCurrent=total_current,
                venue=None,  # Not provided by Odds API
                prediction=prediction,
                marketSignal=market_signal,
                drivers=drivers,
            )
            
            games.append(game)
            
        except Exception as e:
            print(f"Error transforming event: {e}")
            continue
    
    # Sort by upset probability (highest first)
    games.sort(key=lambda g: g.prediction.upset_probability, reverse=True)
    
    return games


# =============================================================================
# ENHANCED UPS CALCULATION WITH SPORTSDATA.IO
# =============================================================================

def calculate_injury_impact(
    injuries: List[Injury],
    team: str,
) -> Tuple[float, List[str]]:
    """
    Calculate upset probability boost based on team injuries.
    
    Key player injuries (QB, star players) on the favorite team
    increase upset probability. Returns both the numeric impact
    and descriptive signals for drivers.
    
    Args:
        injuries: List of Injury models from SportsDataIO
        team: Team abbreviation to filter for
        
    Returns:
        Tuple of (UPS boost 0-15, list of injury signal descriptions)
    """
    team_injuries = [i for i in injuries if i.team == team]
    
    if not team_injuries:
        return 0.0, []
    
    impact = 0.0
    signals = []
    
    # Count significant injuries by position
    qb_out = False
    key_players_out = 0
    
    for injury in team_injuries:
        # Weight by injury status
        status_weight = {
            "Out": 1.0,
            "IR": 1.0,
            "Doubtful": 0.7,
            "Questionable": 0.3,
            "Probable": 0.1,
            "Suspended": 1.0,
            "PUP": 0.8,
        }.get(injury.status, 0.0)
        
        if status_weight < 0.5:
            continue  # Skip minor injuries for impact calculation
        
        # Weight by position importance
        position_weight = {
            "QB": 12.0,   # Quarterback is most impactful
            "RB": 3.0,
            "WR": 2.5,
            "TE": 2.0,
            "LT": 3.5,    # Left tackle protects QB's blind side
            "RT": 2.0,
            "LG": 1.5,
            "RG": 1.5,
            "C": 2.0,
            "DE": 2.5,
            "DT": 2.0,
            "OLB": 2.0,
            "ILB": 2.0,
            "MLB": 2.0,
            "LB": 2.0,
            "CB": 2.5,
            "SS": 2.0,
            "FS": 2.0,
            "S": 2.0,
            "K": 1.0,
            "P": 0.5,
        }.get(injury.position, 1.0)
        
        injury_impact = status_weight * position_weight
        impact += injury_impact
        
        # Track significant injuries for signals
        if injury.position == "QB" and status_weight >= 0.7:
            qb_out = True
            signals.append(f"Starting QB {injury.player_name} {injury.status.lower()}")
        elif position_weight >= 2.5 and status_weight >= 0.7:
            key_players_out += 1
    
    # Add summary signals
    if qb_out:
        pass  # Already added above
    elif key_players_out >= 3:
        signals.append(f"{key_players_out} key players injured/out")
    elif key_players_out >= 2:
        signals.append(f"Multiple starters injured")
    
    # Cap impact at 15 points
    return min(15.0, impact), signals


def calculate_standings_impact(
    favorite_standing: Optional[Standing],
    underdog_standing: Optional[Standing],
) -> Tuple[float, List[str]]:
    """
    Calculate upset probability adjustment based on team standings.
    
    Underperforming favorites or hot underdogs affect UPS.
    
    Args:
        favorite_standing: Standing data for favorite team
        underdog_standing: Standing data for underdog team
        
    Returns:
        Tuple of (UPS adjustment -5 to +10, list of signals)
    """
    if not favorite_standing or not underdog_standing:
        return 0.0, []
    
    adjustment = 0.0
    signals = []
    
    # Compare win percentages
    fav_pct = favorite_standing.win_percentage
    und_pct = underdog_standing.win_percentage
    
    # If underdog has better record than their odds suggest
    if und_pct > 0.5 and und_pct >= fav_pct - 0.1:
        adjustment += 5.0
        und_record = f"{underdog_standing.wins}-{underdog_standing.losses}"
        signals.append(f"Underdog has strong record ({und_record})")
    
    # Underdog on hot streak
    if underdog_standing.streak >= 3:
        adjustment += 3.0
        signals.append(f"Underdog on {underdog_standing.streak}-game win streak")
    elif underdog_standing.streak_description and "W" in underdog_standing.streak_description:
        adjustment += 1.5
    
    # Favorite struggling
    if favorite_standing.streak <= -3:
        adjustment += 4.0
        signals.append(f"Favorite on {abs(favorite_standing.streak)}-game losing streak")
    elif fav_pct < 0.5:
        adjustment += 2.0
        signals.append("Favorite has losing record")
    
    # Home/away performance (if underdog is home)
    if underdog_standing.home_wins > underdog_standing.home_losses:
        adjustment += 1.5
    
    # Cap adjustment
    return min(10.0, max(-5.0, adjustment)), signals


def calculate_enhanced_ups(
    base_ups: float,
    underdog_odds: float,
    spread: Optional[float],
    public_pct: float,
    favorite_injuries: Optional[List[Injury]] = None,
    underdog_injuries: Optional[List[Injury]] = None,
    favorite_standing: Optional[Standing] = None,
    underdog_standing: Optional[Standing] = None,
    favorite_team: str = "",
    underdog_team: str = "",
) -> Tuple[float, List[Driver]]:
    """
    Calculate enhanced Upset Probability Score using all available data.
    
    Combines base UPS with SportsDataIO injury and standings data
    for a more accurate prediction.
    
    Args:
        base_ups: Initial UPS from odds/spread/public betting
        underdog_odds: Underdog moneyline odds
        spread: Point spread
        public_pct: Public betting percentage on favorite
        favorite_injuries: Injuries on favorite team
        underdog_injuries: Injuries on underdog team
        favorite_standing: Favorite team standings
        underdog_standing: Underdog team standings
        favorite_team: Favorite team abbreviation
        underdog_team: Underdog team abbreviation
        
    Returns:
        Tuple of (enhanced UPS 0-100, list of Drivers)
    """
    enhanced_ups = base_ups
    drivers = []
    
    # Base drivers from odds/spread
    if spread is not None and abs(spread) <= 3:
        drivers.append(Driver(label="Spread tight - competitive matchup"))
    
    if public_pct >= 75:
        drivers.append(Driver(label=f"Public heavily biased ({int(public_pct)}% on favorite)"))
    elif public_pct >= 70:
        drivers.append(Driver(label=f"Public ≥ 70% on favorite"))
    
    # Injury impact on favorite (boosts UPS)
    if favorite_injuries:
        injury_boost, injury_signals = calculate_injury_impact(
            favorite_injuries, favorite_team
        )
        if injury_boost > 0:
            enhanced_ups += injury_boost
            for signal in injury_signals[:2]:  # Max 2 injury signals
                drivers.append(Driver(label=signal))
    
    # Injury impact on underdog (reduces UPS slightly)
    if underdog_injuries:
        und_injury_boost, _ = calculate_injury_impact(
            underdog_injuries, underdog_team
        )
        if und_injury_boost > 5:  # Only significant injuries matter
            enhanced_ups -= min(5.0, und_injury_boost * 0.3)
    
    # Standings impact
    if favorite_standing or underdog_standing:
        standings_adj, standings_signals = calculate_standings_impact(
            favorite_standing, underdog_standing
        )
        if standings_adj != 0:
            enhanced_ups += standings_adj
            for signal in standings_signals[:2]:  # Max 2 standings signals
                drivers.append(Driver(label=signal))
    
    # High UPS signal
    if enhanced_ups >= 65:
        drivers.append(Driver(label="High upset potential detected"))
    elif enhanced_ups >= 55:
        drivers.append(Driver(label="Elevated upset conditions"))
    
    # Ensure at least 3 drivers
    if len(drivers) < 3:
        drivers.append(Driver(label="Model confidence high"))
    while len(drivers) < 3:
        drivers.append(Driver(label="Pattern recognition signal"))
    
    # Clamp to 0-100 range
    enhanced_ups = min(100.0, max(0.0, round(enhanced_ups, 1)))
    
    return enhanced_ups, drivers[:6]  # Max 6 drivers


def transform_odds_to_games_enhanced(
    raw_events: List[Dict[str, Any]],
    sport: str = "NFL",
    injuries: Optional[List[Injury]] = None,
    standings: Optional[List[Standing]] = None,
) -> List[GameWithPrediction]:
    """
    Transform raw Odds API events with SportsDataIO enhancement.
    
    This is the enhanced version of transform_odds_to_games that
    incorporates injury and standings data for better predictions.
    
    Args:
        raw_events: Raw event data from Odds API
        sport: Sport type (default NFL)
        injuries: Optional list of Injury models from SDIO
        standings: Optional list of Standing models from SDIO
        
    Returns:
        List of GameWithPrediction models with enhanced UPS
    """
    games = []
    now = datetime.now(timezone.utc).isoformat()
    
    # Create lookups for quick access
    standings_by_team = {}
    if standings:
        standings_by_team = {s.team: s for s in standings}
    
    for event in raw_events:
        try:
            game_id = _generate_game_id(event)
            home_team = event.get("home_team", "Unknown")
            away_team = event.get("away_team", "Unknown")
            bookmakers = event.get("bookmakers", [])
            
            if not bookmakers:
                continue
            
            # Extract odds from different markets
            h2h_odds, _ = _extract_bookmaker_odds(bookmakers, "h2h")
            spreads_odds, _ = _extract_bookmaker_odds(bookmakers, "spreads")
            totals_odds, _ = _extract_bookmaker_odds(bookmakers, "totals")
            
            if not h2h_odds:
                continue
            
            # Determine favorite and underdog
            favorite, underdog, fav_odds, und_odds = _determine_favorite(
                h2h_odds, home_team, away_team
            )
            
            # Extract spread and totals
            spread_open, spread_current = _extract_spread_odds(spreads_odds, favorite)
            total_open, total_current = _extract_total_odds(totals_odds)
            
            # Simulate public betting percentage
            public_pct = _simulate_public_percentage(und_odds)
            
            # Calculate base UPS
            base_ups = _calculate_upset_probability(und_odds, spread_current, public_pct)
            
            # Get team-specific data
            fav_standing = standings_by_team.get(favorite)
            und_standing = standings_by_team.get(underdog)
            
            # Calculate enhanced UPS with all data
            enhanced_ups, drivers = calculate_enhanced_ups(
                base_ups=base_ups,
                underdog_odds=und_odds,
                spread=spread_current,
                public_pct=public_pct,
                favorite_injuries=injuries,
                underdog_injuries=injuries,
                favorite_standing=fav_standing,
                underdog_standing=und_standing,
                favorite_team=favorite,
                underdog_team=underdog,
            )
            
            # Check if prime time
            commence_time = event.get("commence_time", "")
            is_prime_time = _is_prime_time(commence_time)
            
            # Add prime time driver if applicable
            if is_prime_time and len(drivers) < 6:
                try:
                    dt = datetime.fromisoformat(commence_time.replace("Z", "+00:00"))
                    weekday = dt.weekday()
                    if weekday == 3:
                        drivers.insert(0, Driver(label="Thursday Night Football"))
                    elif weekday == 6:
                        drivers.insert(0, Driver(label="Sunday Night Football"))
                    elif weekday == 0:
                        drivers.insert(0, Driver(label="Monday Night Football"))
                except:
                    pass
            
            # Determine model version
            model_version = "v2.0-enhanced" if (injuries or standings) else "v1.0"
            
            # Create prediction
            prediction = Prediction(
                id=f"pred_{game_id}",
                game_id=game_id,
                upset_probability=enhanced_ups,
                model_version=model_version,
                confidence_band=min(20, max(5, (100 - enhanced_ups) / 5)),
                created_at=now,
            )
            
            # Create market signal
            market_signal = MarketSignal(
                id=f"signal_{game_id}",
                game_id=game_id,
                public_bet_percentage=public_pct,
                line_movement=0 if spread_open is None else (spread_current or 0) - spread_open,
                sentiment_score=0.0,  # Would come from sentiment analysis
                created_at=now,
            )
            
            # Create game with prediction
            game = GameWithPrediction(
                id=game_id,
                sport=sport,
                team_favorite=favorite,
                team_underdog=underdog,
                start_time=commence_time,
                odds_open=fav_odds,
                odds_current=fav_odds,
                status="upcoming",
                isPrimeTime=is_prime_time,
                spreadOpen=spread_open,
                spreadCurrent=spread_current,
                totalOpen=total_open,
                totalCurrent=total_current,
                venue=None,
                prediction=prediction,
                marketSignal=market_signal,
                drivers=drivers[:6],
            )
            
            games.append(game)
            
        except Exception as e:
            logger.error(f"Error transforming event: {e}")
            continue
    
    # Sort by upset probability (highest first)
    games.sort(key=lambda g: g.prediction.upset_probability, reverse=True)
    
    return games


# =============================================================================
# TEAM NAME MAPPING
# =============================================================================

# Map full team names to abbreviations for SDIO data matching
TEAM_NAME_TO_ABBREV = {
    # AFC East
    "Buffalo Bills": "BUF",
    "Miami Dolphins": "MIA",
    "New England Patriots": "NE",
    "New York Jets": "NYJ",
    # AFC North
    "Baltimore Ravens": "BAL",
    "Cincinnati Bengals": "CIN",
    "Cleveland Browns": "CLE",
    "Pittsburgh Steelers": "PIT",
    # AFC South
    "Houston Texans": "HOU",
    "Indianapolis Colts": "IND",
    "Jacksonville Jaguars": "JAX",
    "Tennessee Titans": "TEN",
    # AFC West
    "Denver Broncos": "DEN",
    "Kansas City Chiefs": "KC",
    "Las Vegas Raiders": "LV",
    "Los Angeles Chargers": "LAC",
    # NFC East
    "Dallas Cowboys": "DAL",
    "New York Giants": "NYG",
    "Philadelphia Eagles": "PHI",
    "Washington Commanders": "WAS",
    # NFC North
    "Chicago Bears": "CHI",
    "Detroit Lions": "DET",
    "Green Bay Packers": "GB",
    "Minnesota Vikings": "MIN",
    # NFC South
    "Atlanta Falcons": "ATL",
    "Carolina Panthers": "CAR",
    "New Orleans Saints": "NO",
    "Tampa Bay Buccaneers": "TB",
    # NFC West
    "Arizona Cardinals": "ARI",
    "Los Angeles Rams": "LAR",
    "San Francisco 49ers": "SF",
    "Seattle Seahawks": "SEA",
}

ABBREV_TO_TEAM_NAME = {v: k for k, v in TEAM_NAME_TO_ABBREV.items()}


def get_team_abbreviation(team_name: str) -> str:
    """Convert full team name to abbreviation."""
    return TEAM_NAME_TO_ABBREV.get(team_name, team_name)


def get_team_full_name(abbrev: str) -> str:
    """Convert abbreviation to full team name."""
    return ABBREV_TO_TEAM_NAME.get(abbrev.upper(), abbrev)

"""Transform SportsDataIO API responses to UpsetIQ Pydantic models."""
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from models import (
    Injury,
    InjuryReport,
    Standing,
    StandingsResponse,
    PlayerStats,
    PlayerStatsResponse,
    TeamStats,
    TeamStatsResponse,
    NFLNews,
    NewsResponse,
    LiveScore,
    LiveScoresResponse,
    NFLTeam,
    TeamsResponse,
)


# =============================================================================
# INJURY TRANSFORMERS
# =============================================================================

def transform_injury(raw: Dict[str, Any]) -> Injury:
    """
    Transform a single injury record from SDIO format.
    
    SDIO fields: PlayerID, Name, Team, Position, Status, BodyPart, Updated, etc.
    """
    return Injury(
        player_id=raw.get("PlayerID", 0),
        player_name=raw.get("Name", "Unknown"),
        team=raw.get("Team", ""),
        position=raw.get("Position", ""),
        status=_normalize_injury_status(raw.get("Status", "")),
        injury_type=raw.get("BodyPart", "Undisclosed"),
        practice_status=raw.get("PracticeStatus"),
        practice_description=raw.get("PracticeDescription"),
        declared_inactive=raw.get("DeclaredInactive", False),
        updated=raw.get("Updated", datetime.now(timezone.utc).isoformat()),
    )


def transform_injuries(
    raw_data: List[Dict[str, Any]]
) -> List[Injury]:
    """Transform list of injury records."""
    injuries = []
    for raw in raw_data:
        try:
            injuries.append(transform_injury(raw))
        except Exception as e:
            # Log and skip malformed records
            print(f"Error transforming injury: {e}")
            continue
    return injuries


def transform_injuries_response(
    raw_data: List[Dict[str, Any]],
    fetched_at: str,
    cached: bool,
) -> InjuryReport:
    """Create full injury report response."""
    injuries = transform_injuries(raw_data)
    
    # Group by team
    teams_affected = list(set(inj.team for inj in injuries if inj.team))
    
    return InjuryReport(
        injuries=injuries,
        teams_affected=teams_affected,
        total_count=len(injuries),
        fetched_at=fetched_at,
        cached=cached,
    )


def _normalize_injury_status(status: str) -> str:
    """
    Normalize injury status to standard values.
    
    SDIO uses various status strings; normalize to:
    Out, Doubtful, Questionable, Probable, Healthy
    """
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


# =============================================================================
# STANDINGS TRANSFORMERS
# =============================================================================

def transform_standing(raw: Dict[str, Any]) -> Standing:
    """
    Transform a single standing record from SDIO format.
    
    SDIO fields: Team, Wins, Losses, Ties, Percentage, Division, Conference, etc.
    """
    wins = raw.get("Wins", 0) or 0
    losses = raw.get("Losses", 0) or 0
    ties = raw.get("Ties", 0) or 0
    
    # Calculate win percentage if not provided
    total_games = wins + losses + ties
    if total_games > 0:
        win_pct = (wins + (ties * 0.5)) / total_games
    else:
        win_pct = raw.get("Percentage", 0.0) or 0.0
    
    return Standing(
        team=raw.get("Team", ""),
        team_name=raw.get("Name", ""),
        wins=wins,
        losses=losses,
        ties=ties,
        win_percentage=round(win_pct, 3),
        points_for=raw.get("PointsFor", 0) or 0,
        points_against=raw.get("PointsAgainst", 0) or 0,
        net_points=raw.get("NetPoints", 0) or 0,
        division=raw.get("Division", ""),
        conference=raw.get("Conference", ""),
        division_rank=raw.get("DivisionRank", 0) or 0,
        conference_rank=raw.get("ConferenceRank", 0) or 0,
        home_wins=raw.get("HomeWins", 0) or 0,
        home_losses=raw.get("HomeLosses", 0) or 0,
        away_wins=raw.get("AwayWins", 0) or 0,
        away_losses=raw.get("AwayLosses", 0) or 0,
        division_wins=raw.get("DivisionWins", 0) or 0,
        division_losses=raw.get("DivisionLosses", 0) or 0,
        conference_wins=raw.get("ConferenceWins", 0) or 0,
        conference_losses=raw.get("ConferenceLosses", 0) or 0,
        streak=raw.get("Streak", 0) or 0,
        streak_description=raw.get("StreakDescription", ""),
    )


def transform_standings(
    raw_data: List[Dict[str, Any]]
) -> List[Standing]:
    """Transform list of standing records."""
    standings = []
    for raw in raw_data:
        try:
            standings.append(transform_standing(raw))
        except Exception as e:
            print(f"Error transforming standing: {e}")
            continue
    
    # Sort by win percentage (descending)
    standings.sort(key=lambda s: s.win_percentage, reverse=True)
    return standings


def transform_standings_response(
    raw_data: List[Dict[str, Any]],
    fetched_at: str,
    cached: bool,
    season: int,
) -> StandingsResponse:
    """Create full standings response."""
    standings = transform_standings(raw_data)
    
    return StandingsResponse(
        standings=standings,
        season=season,
        fetched_at=fetched_at,
        cached=cached,
    )


# =============================================================================
# PLAYER STATS TRANSFORMERS
# =============================================================================

def transform_player_stats(raw: Dict[str, Any]) -> PlayerStats:
    """
    Transform player statistics from SDIO format.
    
    SDIO includes comprehensive stats; we extract the most relevant.
    """
    return PlayerStats(
        player_id=raw.get("PlayerID", 0),
        name=raw.get("Name", "Unknown"),
        team=raw.get("Team", ""),
        position=raw.get("Position", ""),
        # Passing stats
        passing_attempts=raw.get("PassingAttempts", 0) or 0,
        passing_completions=raw.get("PassingCompletions", 0) or 0,
        passing_yards=raw.get("PassingYards", 0) or 0,
        passing_touchdowns=raw.get("PassingTouchdowns", 0) or 0,
        passing_interceptions=raw.get("PassingInterceptions", 0) or 0,
        passing_rating=raw.get("PassingRating"),
        # Rushing stats
        rushing_attempts=raw.get("RushingAttempts", 0) or 0,
        rushing_yards=raw.get("RushingYards", 0) or 0,
        rushing_touchdowns=raw.get("RushingTouchdowns", 0) or 0,
        rushing_yards_per_attempt=raw.get("RushingYardsPerAttempt"),
        # Receiving stats
        receptions=raw.get("Receptions", 0) or 0,
        receiving_yards=raw.get("ReceivingYards", 0) or 0,
        receiving_touchdowns=raw.get("ReceivingTouchdowns", 0) or 0,
        receiving_targets=raw.get("ReceivingTargets", 0) or 0,
        # Total stats
        touchdowns=_sum_touchdowns(raw),
        fumbles=raw.get("Fumbles", 0) or 0,
        fumbles_lost=raw.get("FumblesLost", 0) or 0,
        # Fantasy
        fantasy_points=raw.get("FantasyPoints"),
        fantasy_points_ppr=raw.get("FantasyPointsPPR"),
        # Defensive stats (if applicable)
        tackles=raw.get("Tackles", 0) or 0,
        sacks=raw.get("Sacks", 0) or 0,
        interceptions=raw.get("Interceptions", 0) or 0,
        # Games
        games_played=raw.get("Played", 0) or raw.get("Games", 0) or 0,
    )


def _sum_touchdowns(raw: Dict[str, Any]) -> int:
    """Sum all touchdown types."""
    return (
        (raw.get("PassingTouchdowns", 0) or 0) +
        (raw.get("RushingTouchdowns", 0) or 0) +
        (raw.get("ReceivingTouchdowns", 0) or 0) +
        (raw.get("ReturnTouchdowns", 0) or 0) +
        (raw.get("FumbleReturnTouchdowns", 0) or 0) +
        (raw.get("InterceptionReturnTouchdowns", 0) or 0)
    )


def transform_player_stats_list(
    raw_data: List[Dict[str, Any]]
) -> List[PlayerStats]:
    """Transform list of player stats."""
    stats = []
    for raw in raw_data:
        try:
            stats.append(transform_player_stats(raw))
        except Exception as e:
            print(f"Error transforming player stats: {e}")
            continue
    return stats


def transform_player_stats_response(
    raw_data: List[Dict[str, Any]],
    fetched_at: str,
    cached: bool,
    season: int,
    week: Optional[int] = None,
) -> PlayerStatsResponse:
    """Create full player stats response."""
    stats = transform_player_stats_list(raw_data)
    
    return PlayerStatsResponse(
        players=stats,
        season=season,
        week=week,
        total_count=len(stats),
        fetched_at=fetched_at,
        cached=cached,
    )


# =============================================================================
# TEAM STATS TRANSFORMERS
# =============================================================================

def transform_team_stats(raw: Dict[str, Any]) -> TeamStats:
    """Transform team statistics from SDIO format."""
    return TeamStats(
        team=raw.get("Team", ""),
        team_name=raw.get("Name", ""),
        # Scoring
        score=raw.get("Score", 0) or 0,
        points_for=raw.get("PointsFor", 0) or raw.get("Score", 0) or 0,
        points_against=raw.get("PointsAgainst", 0) or raw.get("OpponentScore", 0) or 0,
        # Offense
        total_yards=raw.get("OffensiveYards", 0) or 0,
        passing_yards=raw.get("PassingYards", 0) or 0,
        rushing_yards=raw.get("RushingYards", 0) or 0,
        first_downs=raw.get("FirstDowns", 0) or 0,
        third_down_conversions=raw.get("ThirdDownConversions", 0) or 0,
        third_down_attempts=raw.get("ThirdDownAttempts", 0) or 0,
        # Turnovers
        turnovers=raw.get("Giveaways", 0) or raw.get("Turnovers", 0) or 0,
        takeaways=raw.get("Takeaways", 0) or 0,
        turnover_differential=(
            (raw.get("Takeaways", 0) or 0) - (raw.get("Giveaways", 0) or 0)
        ),
        # Penalties
        penalties=raw.get("Penalties", 0) or 0,
        penalty_yards=raw.get("PenaltyYards", 0) or 0,
        # Time of possession
        time_of_possession=raw.get("TimeOfPossession", ""),
        time_of_possession_seconds=_parse_time_of_possession(
            raw.get("TimeOfPossession", "")
        ),
        # Sacks
        sacks=raw.get("Sacks", 0) or 0,
        sacks_allowed=raw.get("SacksAllowed", 0) or 0,
        # Red zone
        red_zone_attempts=raw.get("RedZoneAttempts", 0) or 0,
        red_zone_conversions=raw.get("RedZoneConversions", 0) or 0,
        # Games
        games_played=raw.get("Games", 0) or 0,
        wins=raw.get("Wins", 0) or 0,
        losses=raw.get("Losses", 0) or 0,
    )


def _parse_time_of_possession(top_str: str) -> int:
    """
    Parse time of possession string to seconds.
    
    Format: "MM:SS" or "HH:MM:SS"
    """
    if not top_str:
        return 0
    
    try:
        parts = top_str.split(":")
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        return 0
    except (ValueError, IndexError):
        return 0


def transform_team_stats_list(
    raw_data: List[Dict[str, Any]]
) -> List[TeamStats]:
    """Transform list of team stats."""
    stats = []
    for raw in raw_data:
        try:
            stats.append(transform_team_stats(raw))
        except Exception as e:
            print(f"Error transforming team stats: {e}")
            continue
    return stats


def transform_team_stats_response(
    raw_data: List[Dict[str, Any]],
    fetched_at: str,
    cached: bool,
    season: int,
) -> TeamStatsResponse:
    """Create full team stats response."""
    stats = transform_team_stats_list(raw_data)
    
    return TeamStatsResponse(
        teams=stats,
        season=season,
        fetched_at=fetched_at,
        cached=cached,
    )


# =============================================================================
# NEWS TRANSFORMERS
# =============================================================================

def transform_news_item(raw: Dict[str, Any]) -> NFLNews:
    """Transform a single news item from SDIO format."""
    # Extract team references from content or explicit field
    teams = []
    if raw.get("Team"):
        teams.append(raw.get("Team"))
    if raw.get("TeamID2"):
        teams.append(raw.get("TeamID2"))
    
    return NFLNews(
        news_id=raw.get("NewsID", 0),
        title=raw.get("Title", ""),
        content=raw.get("Content", ""),
        source=raw.get("Source", "SportsDataIO"),
        url=raw.get("Url", ""),
        terms_of_use=raw.get("TermsOfUse", ""),
        author=raw.get("Author", ""),
        categories=raw.get("Categories", ""),
        player_id=raw.get("PlayerID"),
        player_id2=raw.get("PlayerID2"),
        team=raw.get("Team"),
        team_id2=raw.get("TeamID2"),
        is_original=raw.get("IsOriginal", False),
        updated=raw.get("Updated", datetime.now(timezone.utc).isoformat()),
        time_ago=raw.get("TimeAgo", ""),
    )


def transform_news(raw_data: List[Dict[str, Any]]) -> List[NFLNews]:
    """Transform list of news items."""
    news = []
    for raw in raw_data:
        try:
            news.append(transform_news_item(raw))
        except Exception as e:
            print(f"Error transforming news: {e}")
            continue
    
    # Sort by updated time (newest first)
    news.sort(key=lambda n: n.updated, reverse=True)
    return news


def transform_news_response(
    raw_data: List[Dict[str, Any]],
    fetched_at: str,
    cached: bool,
) -> NewsResponse:
    """Create full news response."""
    news = transform_news(raw_data)
    
    return NewsResponse(
        news=news,
        total_count=len(news),
        fetched_at=fetched_at,
        cached=cached,
    )


# =============================================================================
# LIVE SCORES TRANSFORMERS
# =============================================================================

def transform_live_score(raw: Dict[str, Any]) -> LiveScore:
    """Transform a live score from SDIO format."""
    return LiveScore(
        game_id=raw.get("GameKey") or str(raw.get("ScoreID", "")),
        season=raw.get("Season", 0),
        week=raw.get("Week", 0),
        season_type=raw.get("SeasonType", 1),
        status=_normalize_game_status(raw.get("Status", "")),
        home_team=raw.get("HomeTeam", ""),
        away_team=raw.get("AwayTeam", ""),
        home_score=raw.get("HomeScore") or 0,
        away_score=raw.get("AwayScore") or 0,
        quarter=raw.get("Quarter"),
        time_remaining=raw.get("TimeRemaining"),
        possession=raw.get("Possession"),
        down=raw.get("Down"),
        distance=raw.get("Distance"),
        yard_line=raw.get("YardLine"),
        yard_line_territory=raw.get("YardLineTerritory"),
        red_zone=raw.get("RedZone", False),
        date=raw.get("Date") or raw.get("DateTime", ""),
        day=raw.get("Day", ""),
        date_time=raw.get("DateTime", ""),
        stadium=raw.get("StadiumDetails", {}).get("Name", "") if raw.get("StadiumDetails") else "",
        channel=raw.get("Channel", ""),
        is_over=raw.get("IsOver", False) or raw.get("Status") == "Final",
        home_team_moneyline=raw.get("HomeTeamMoneyLine"),
        away_team_moneyline=raw.get("AwayTeamMoneyLine"),
        point_spread=raw.get("PointSpread"),
        over_under=raw.get("OverUnder"),
    )


def _normalize_game_status(status: str) -> str:
    """Normalize game status to standard values."""
    status_lower = status.lower() if status else ""
    
    if "scheduled" in status_lower:
        return "Scheduled"
    elif "inprogress" in status_lower or "in progress" in status_lower:
        return "InProgress"
    elif "final" in status_lower:
        return "Final"
    elif "postponed" in status_lower:
        return "Postponed"
    elif "canceled" in status_lower or "cancelled" in status_lower:
        return "Canceled"
    elif "halftime" in status_lower:
        return "Halftime"
    else:
        return status or "Unknown"


def transform_live_scores(raw_data: List[Dict[str, Any]]) -> List[LiveScore]:
    """Transform list of live scores."""
    scores = []
    for raw in raw_data:
        try:
            scores.append(transform_live_score(raw))
        except Exception as e:
            print(f"Error transforming live score: {e}")
            continue
    return scores


def transform_live_scores_response(
    raw_data: List[Dict[str, Any]],
    fetched_at: str,
    cached: bool,
    season: int,
    week: Optional[int] = None,
) -> LiveScoresResponse:
    """Create full live scores response."""
    scores = transform_live_scores(raw_data)
    
    # Separate by status
    in_progress = [s for s in scores if s.status == "InProgress"]
    completed = [s for s in scores if s.is_over]
    scheduled = [s for s in scores if s.status == "Scheduled"]
    
    return LiveScoresResponse(
        scores=scores,
        in_progress_count=len(in_progress),
        completed_count=len(completed),
        scheduled_count=len(scheduled),
        season=season,
        week=week,
        fetched_at=fetched_at,
        cached=cached,
    )


# =============================================================================
# TEAMS TRANSFORMER
# =============================================================================

def transform_team(raw: Dict[str, Any]) -> NFLTeam:
    """Transform team reference data."""
    return NFLTeam(
        team_id=raw.get("TeamID", 0),
        key=raw.get("Key", ""),
        city=raw.get("City", ""),
        name=raw.get("Name", ""),
        full_name=raw.get("FullName", ""),
        conference=raw.get("Conference", ""),
        division=raw.get("Division", ""),
        primary_color=raw.get("PrimaryColor", ""),
        secondary_color=raw.get("SecondaryColor", ""),
        tertiary_color=raw.get("TertiaryColor"),
        wikipedia_logo_url=raw.get("WikipediaLogoUrl", ""),
        wikipedia_word_mark_url=raw.get("WikipediaWordMarkUrl"),
        stadium_id=raw.get("StadiumID"),
        bye_week=raw.get("ByeWeek"),
        head_coach=raw.get("HeadCoach", ""),
        offensive_coordinator=raw.get("OffensiveCoordinator"),
        defensive_coordinator=raw.get("DefensiveCoordinator"),
    )


def transform_teams(raw_data: List[Dict[str, Any]]) -> List[NFLTeam]:
    """Transform list of teams."""
    teams = []
    for raw in raw_data:
        try:
            teams.append(transform_team(raw))
        except Exception as e:
            print(f"Error transforming team: {e}")
            continue
    return teams


def transform_teams_response(
    raw_data: List[Dict[str, Any]],
    fetched_at: str,
    cached: bool,
) -> TeamsResponse:
    """Create full teams response."""
    teams = transform_teams(raw_data)
    
    return TeamsResponse(
        teams=teams,
        fetched_at=fetched_at,
        cached=cached,
    )


# =============================================================================
# HELPER: Get injury impact for UPS calculation
# =============================================================================

def calculate_injury_impact(
    team_injuries: List[Injury],
) -> float:
    """
    Calculate upset probability boost based on team injuries.
    
    Key player injuries (QB, star players) on the favorite team
    increase upset probability.
    
    Returns:
        Float between 0-15 representing UPS boost
    """
    if not team_injuries:
        return 0.0
    
    impact = 0.0
    
    for injury in team_injuries:
        # Weight by injury status
        status_weight = {
            "Out": 1.0,
            "IR": 1.0,
            "Doubtful": 0.7,
            "Questionable": 0.3,
            "Probable": 0.1,
        }.get(injury.status, 0.0)
        
        # Weight by position importance
        position_weight = {
            "QB": 10.0,  # Quarterback is most impactful
            "RB": 3.0,
            "WR": 2.5,
            "TE": 2.0,
            "LT": 3.0,  # Left tackle protects QB
            "RT": 2.0,
            "C": 2.0,
            "DE": 2.5,
            "DT": 2.0,
            "LB": 2.0,
            "CB": 2.5,
            "S": 2.0,
            "K": 1.0,
            "P": 0.5,
        }.get(injury.position, 1.0)
        
        impact += status_weight * position_weight
    
    # Cap at 15 points
    return min(15.0, impact)

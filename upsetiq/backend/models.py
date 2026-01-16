"""Pydantic models matching frontend TypeScript types."""
from typing import Optional, List, Literal
from pydantic import BaseModel
from datetime import datetime


Sport = Literal["NBA", "NFL", "MLB", "NHL", "Soccer", "CFB"]
GameStatus = Literal["upcoming", "live", "completed"]
InjuryStatus = Literal["Out", "Doubtful", "Questionable", "Probable", "IR", "PUP", "Suspended", "Unknown"]


class Driver(BaseModel):
    """Key signal/driver for a game prediction."""
    label: str


class Prediction(BaseModel):
    """Model prediction for a game."""
    id: str
    game_id: str
    upset_probability: float  # 0-100
    model_version: str = "v1.0"
    confidence_band: float
    created_at: str


class MarketSignal(BaseModel):
    """Market data signals for a game."""
    id: str
    game_id: str
    public_bet_percentage: float  # % of public bets on favorite (0-100)
    line_movement: float  # change in line
    sentiment_score: float  # -1 to 1
    created_at: str


class Game(BaseModel):
    """Base game data."""
    id: str
    sport: Sport
    team_favorite: str
    team_underdog: str
    start_time: str  # ISO datetime string
    odds_open: float  # Opening moneyline (American odds)
    odds_current: float  # Current moneyline
    status: GameStatus = "upcoming"
    # NFL-specific optional fields
    isPrimeTime: Optional[bool] = None
    spreadOpen: Optional[float] = None
    spreadCurrent: Optional[float] = None
    totalOpen: Optional[float] = None
    totalCurrent: Optional[float] = None
    venue: Optional[str] = None


class GameWithPrediction(Game):
    """Game with prediction and market signal data."""
    prediction: Prediction
    marketSignal: MarketSignal
    drivers: Optional[List[Driver]] = None


class GamesResponse(BaseModel):
    """Response for list of games."""
    games: List[GameWithPrediction]
    fetched_at: str
    cached: bool = False


# =============================================================================
# SPORTSDATA.IO MODELS - INJURIES
# =============================================================================

class Injury(BaseModel):
    """NFL player injury report."""
    player_id: int
    player_name: str
    team: str
    position: str
    status: str  # Out, Doubtful, Questionable, Probable, IR, PUP, Suspended
    injury_type: str  # Body part affected
    practice_status: Optional[str] = None
    practice_description: Optional[str] = None
    declared_inactive: bool = False
    updated: str


class InjuryReport(BaseModel):
    """Response for injury report."""
    injuries: List[Injury]
    teams_affected: List[str]
    total_count: int
    fetched_at: str
    cached: bool = False


# =============================================================================
# SPORTSDATA.IO MODELS - STANDINGS
# =============================================================================

class Standing(BaseModel):
    """NFL team standing."""
    team: str  # Team abbreviation (e.g., "KC", "PHI")
    team_name: str = ""  # Full team name
    wins: int
    losses: int
    ties: int = 0
    win_percentage: float
    points_for: int = 0
    points_against: int = 0
    net_points: int = 0
    division: str
    conference: str
    division_rank: int = 0
    conference_rank: int = 0
    # Home/Away splits
    home_wins: int = 0
    home_losses: int = 0
    away_wins: int = 0
    away_losses: int = 0
    # Division/Conference records
    division_wins: int = 0
    division_losses: int = 0
    conference_wins: int = 0
    conference_losses: int = 0
    # Streak info
    streak: int = 0
    streak_description: str = ""


class StandingsResponse(BaseModel):
    """Response for NFL standings."""
    standings: List[Standing]
    season: int
    fetched_at: str
    cached: bool = False


# =============================================================================
# SPORTSDATA.IO MODELS - PLAYER STATS
# =============================================================================

class PlayerStats(BaseModel):
    """NFL player statistics."""
    player_id: int
    name: str
    team: str
    position: str
    # Passing
    passing_attempts: int = 0
    passing_completions: int = 0
    passing_yards: int = 0
    passing_touchdowns: int = 0
    passing_interceptions: int = 0
    passing_rating: Optional[float] = None
    # Rushing
    rushing_attempts: int = 0
    rushing_yards: int = 0
    rushing_touchdowns: int = 0
    rushing_yards_per_attempt: Optional[float] = None
    # Receiving
    receptions: int = 0
    receiving_yards: int = 0
    receiving_touchdowns: int = 0
    receiving_targets: int = 0
    # Totals
    touchdowns: int = 0
    fumbles: int = 0
    fumbles_lost: int = 0
    # Fantasy
    fantasy_points: Optional[float] = None
    fantasy_points_ppr: Optional[float] = None
    # Defensive
    tackles: int = 0
    sacks: float = 0
    interceptions: int = 0
    # Games
    games_played: int = 0


class PlayerStatsResponse(BaseModel):
    """Response for player statistics."""
    players: List[PlayerStats]
    season: int
    week: Optional[int] = None
    total_count: int
    fetched_at: str
    cached: bool = False


# =============================================================================
# SPORTSDATA.IO MODELS - TEAM STATS
# =============================================================================

class TeamStats(BaseModel):
    """NFL team statistics."""
    team: str  # Team abbreviation
    team_name: str = ""
    # Scoring
    score: int = 0
    points_for: int = 0
    points_against: int = 0
    # Offense
    total_yards: int = 0
    passing_yards: int = 0
    rushing_yards: int = 0
    first_downs: int = 0
    third_down_conversions: int = 0
    third_down_attempts: int = 0
    # Turnovers
    turnovers: int = 0
    takeaways: int = 0
    turnover_differential: int = 0
    # Penalties
    penalties: int = 0
    penalty_yards: int = 0
    # Time of possession
    time_of_possession: str = ""
    time_of_possession_seconds: int = 0
    # Sacks
    sacks: float = 0
    sacks_allowed: float = 0
    # Red zone
    red_zone_attempts: int = 0
    red_zone_conversions: int = 0
    # Record
    games_played: int = 0
    wins: int = 0
    losses: int = 0


class TeamStatsResponse(BaseModel):
    """Response for team statistics."""
    teams: List[TeamStats]
    season: int
    fetched_at: str
    cached: bool = False


# =============================================================================
# SPORTSDATA.IO MODELS - NEWS
# =============================================================================

class NFLNews(BaseModel):
    """NFL news article."""
    news_id: int
    title: str
    content: str
    source: str = "SportsDataIO"
    url: str = ""
    terms_of_use: str = ""
    author: str = ""
    categories: str = ""
    player_id: Optional[int] = None
    player_id2: Optional[int] = None
    team: Optional[str] = None
    team_id2: Optional[str] = None
    is_original: bool = False
    updated: str
    time_ago: str = ""


class NewsResponse(BaseModel):
    """Response for NFL news."""
    news: List[NFLNews]
    total_count: int
    fetched_at: str
    cached: bool = False


# =============================================================================
# SPORTSDATA.IO MODELS - LIVE SCORES
# =============================================================================

class LiveScore(BaseModel):
    """Live NFL game score."""
    game_id: str
    season: int
    week: int
    season_type: int = 1  # 1=Regular, 2=Preseason, 3=Postseason
    status: str  # Scheduled, InProgress, Final, Postponed, Canceled, Halftime
    home_team: str
    away_team: str
    home_score: int = 0
    away_score: int = 0
    quarter: Optional[str] = None
    time_remaining: Optional[str] = None
    possession: Optional[str] = None
    down: Optional[int] = None
    distance: Optional[int] = None
    yard_line: Optional[int] = None
    yard_line_territory: Optional[str] = None
    red_zone: bool = False
    date: str
    day: str = ""
    date_time: str = ""
    stadium: str = ""
    channel: str = ""
    is_over: bool = False
    # Betting lines
    home_team_moneyline: Optional[int] = None
    away_team_moneyline: Optional[int] = None
    point_spread: Optional[float] = None
    over_under: Optional[float] = None


class LiveScoresResponse(BaseModel):
    """Response for live scores."""
    scores: List[LiveScore]
    in_progress_count: int = 0
    completed_count: int = 0
    scheduled_count: int = 0
    season: int
    week: Optional[int] = None
    fetched_at: str
    cached: bool = False


# =============================================================================
# SPORTSDATA.IO MODELS - TEAMS (Reference)
# =============================================================================

class NFLTeam(BaseModel):
    """NFL team reference data."""
    team_id: int
    key: str  # Team abbreviation (e.g., "KC")
    city: str
    name: str  # Team name (e.g., "Chiefs")
    full_name: str  # Full name (e.g., "Kansas City Chiefs")
    conference: str  # AFC or NFC
    division: str  # East, West, North, South
    primary_color: str = ""
    secondary_color: str = ""
    tertiary_color: Optional[str] = None
    wikipedia_logo_url: str = ""
    wikipedia_word_mark_url: Optional[str] = None
    stadium_id: Optional[int] = None
    bye_week: Optional[int] = None
    head_coach: str = ""
    offensive_coordinator: Optional[str] = None
    defensive_coordinator: Optional[str] = None


class TeamsResponse(BaseModel):
    """Response for NFL teams."""
    teams: List[NFLTeam]
    fetched_at: str
    cached: bool = False


# =============================================================================
# ENHANCED GAME MODEL WITH SDIO DATA
# =============================================================================

class EnhancedGameData(BaseModel):
    """Additional game context from SportsDataIO."""
    favorite_injuries: List[Injury] = []
    underdog_injuries: List[Injury] = []
    favorite_record: Optional[Standing] = None
    underdog_record: Optional[Standing] = None
    injury_impact_score: float = 0.0  # UPS boost from injuries


class GameWithEnhancedPrediction(GameWithPrediction):
    """Game with prediction and enhanced SDIO data."""
    enhanced_data: Optional[EnhancedGameData] = None

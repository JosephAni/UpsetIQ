# Services package
"""
UpsetIQ Services Module

This package contains API clients and data transformers for external data sources:

- odds_api: The Odds API client for live betting odds
- sportsdata_io: SportsDataIO client for NFL data (injuries, standings, stats)
- transformer: Odds API data transformation and UPS calculation
- sdio_transformer: SportsDataIO data transformation
"""

from services.odds_api import (
    get_games_with_predictions,
    fetch_odds_from_api,
)

from services.sportsdata_io import (
    get_injuries,
    get_injuries_by_team,
    get_standings,
    get_player_season_stats,
    get_player_stats_by_week,
    get_team_season_stats,
    get_news,
    get_news_by_team,
    get_live_scores,
    get_scores_by_date,
    get_teams,
    get_players,
    get_schedules,
    get_current_season,
    get_current_week,
    clear_cache,
    get_cache_stats,
)

from services.transformer import (
    transform_odds_to_games,
    transform_odds_to_games_enhanced,
    calculate_enhanced_ups,
    calculate_injury_impact,
    calculate_standings_impact,
    get_team_abbreviation,
    get_team_full_name,
)

from services.sdio_transformer import (
    transform_injuries_response,
    transform_standings_response,
    transform_player_stats_response,
    transform_team_stats_response,
    transform_news_response,
    transform_live_scores_response,
    transform_teams_response,
    transform_injuries,
    transform_standings,
)

__all__ = [
    # Odds API
    "get_games_with_predictions",
    "fetch_odds_from_api",
    # SportsDataIO
    "get_injuries",
    "get_injuries_by_team",
    "get_standings",
    "get_player_season_stats",
    "get_player_stats_by_week",
    "get_team_season_stats",
    "get_news",
    "get_news_by_team",
    "get_live_scores",
    "get_scores_by_date",
    "get_teams",
    "get_players",
    "get_schedules",
    "get_current_season",
    "get_current_week",
    "clear_cache",
    "get_cache_stats",
    # Transformers
    "transform_odds_to_games",
    "transform_odds_to_games_enhanced",
    "calculate_enhanced_ups",
    "calculate_injury_impact",
    "calculate_standings_impact",
    "get_team_abbreviation",
    "get_team_full_name",
    "transform_injuries_response",
    "transform_standings_response",
    "transform_player_stats_response",
    "transform_team_stats_response",
    "transform_news_response",
    "transform_live_scores_response",
    "transform_teams_response",
    "transform_injuries",
    "transform_standings",
]
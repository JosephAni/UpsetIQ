"""FastAPI backend for UpsetIQ - Live Upset Intelligence."""
import os
import logging
from datetime import datetime, timezone
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from models import (
    GameWithPrediction,
    GamesResponse,
    Sport,
    InjuryReport,
    StandingsResponse,
    PlayerStatsResponse,
    TeamStatsResponse,
    NewsResponse,
    LiveScoresResponse,
    TeamsResponse,
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Pipeline scheduler (imported lazily to handle optional dependencies)
_scheduler_started = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """App lifespan manager - handles startup and shutdown."""
    global _scheduler_started
    
    # Startup
    logger.info("Starting UpsetIQ API...")
    
    # Start pipeline scheduler if enabled
    if os.getenv("ENABLE_PIPELINE", "true").lower() == "true":
        try:
            from services.pipeline import start_scheduler, stop_scheduler
            scheduler = start_scheduler()
            _scheduler_started = True
            logger.info("Pipeline scheduler started")
        except ImportError as e:
            logger.warning(f"Pipeline scheduler not available: {e}")
        except Exception as e:
            logger.error(f"Failed to start pipeline scheduler: {e}")
    else:
        logger.info("Pipeline scheduler disabled (ENABLE_PIPELINE=false)")
    
    yield
    
    # Shutdown
    logger.info("Shutting down UpsetIQ API...")
    
    if _scheduler_started:
        try:
            from services.pipeline import stop_scheduler
            stop_scheduler()
            logger.info("Pipeline scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")


app = FastAPI(
    title="UpsetIQ API",
    description="Live Upset Intelligence - Sports betting insights powered by data. "
                "Combines odds data with comprehensive NFL statistics from SportsDataIO. "
                "Now with scheduled data pipeline for real-time updates.",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware for React Native app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your app's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# MOUNT SOCKET.IO (if available)
# =============================================================================

try:
    from services.websocket_server import get_socket_app
    socket_app = get_socket_app()
    if socket_app:
        app.mount("/ws", socket_app)
        logger.info("Socket.IO mounted at /ws")
except ImportError:
    logger.info("Socket.IO not available")


# =============================================================================
# HEALTH & STATUS
# =============================================================================

@app.get("/health", tags=["Status"])
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "3.0.0",
        "pipeline_enabled": _scheduler_started,
    }


@app.get("/cache/stats", tags=["Status"])
def cache_stats():
    """Get cache statistics for monitoring."""
    from services.sportsdata_io import get_cache_stats as sdio_cache_stats
    
    return {
        "sportsdata_io": sdio_cache_stats(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# =============================================================================
# PIPELINE CONTROL
# =============================================================================

@app.get("/pipeline/status", tags=["Pipeline"])
def get_pipeline_status():
    """
    Get status of the data pipeline scheduler.
    
    Returns job schedules, last run times, and health information.
    """
    if not _scheduler_started:
        return {
            "status": "disabled",
            "message": "Pipeline scheduler is not running",
        }
    
    try:
        from services.pipeline import get_job_status, is_scheduler_running
        
        return {
            "status": "running" if is_scheduler_running() else "stopped",
            "jobs": get_job_status(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error(f"Error getting pipeline status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/pipeline/jobs/{job_id}/run", tags=["Pipeline"])
def trigger_job(job_id: str):
    """
    Manually trigger a pipeline job to run immediately.
    
    - **job_id**: Job identifier (odds_snapshot, schedule_refresh, injury_update, etc.)
    """
    if not _scheduler_started:
        raise HTTPException(status_code=400, detail="Pipeline scheduler not running")
    
    try:
        from services.pipeline import run_job_now
        
        success = run_job_now(job_id)
        
        if success:
            return {
                "status": "triggered",
                "job_id": job_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        else:
            raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/pipeline/runs", tags=["Pipeline"])
def get_pipeline_runs(
    job_name: Optional[str] = Query(None, description="Filter by job name"),
    limit: int = Query(20, description="Maximum number of runs to return"),
):
    """
    Get recent pipeline run history.
    
    - **job_name**: Optional filter by job name
    - **limit**: Maximum runs to return
    
    Returns execution history for monitoring and debugging.
    """
    try:
        from services.supabase_client import get_recent_pipeline_runs, is_supabase_configured
        
        if not is_supabase_configured():
            return {
                "runs": [],
                "message": "Supabase not configured - no run history available",
            }
        
        runs = get_recent_pipeline_runs(job_name, limit)
        
        return {
            "runs": runs,
            "count": len(runs),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error(f"Error getting pipeline runs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# ALERTS
# =============================================================================

@app.get("/alerts/subscriptions", tags=["Alerts"])
def get_subscriptions(
    user_id: str = Query(..., description="User ID to get subscriptions for"),
):
    """
    Get alert subscriptions for a user.
    
    - **user_id**: User identifier
    """
    try:
        from services.supabase_client import get_user_subscriptions, is_supabase_configured
        
        if not is_supabase_configured():
            raise HTTPException(status_code=503, detail="Supabase not configured")
        
        subs = get_user_subscriptions(user_id)
        
        return {
            "subscriptions": subs,
            "count": len(subs),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting subscriptions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/alerts/subscribe", tags=["Alerts"])
def create_subscription(
    user_id: str = Query(..., description="User ID"),
    subscription_type: str = Query(..., description="Type: ups_threshold, team, game, all_upsets"),
    target_id: Optional[str] = Query(None, description="Team abbreviation or game ID"),
    ups_threshold: float = Query(65.0, description="UPS threshold for alerts"),
    push_token: Optional[str] = Query(None, description="Push notification token"),
    push_provider: Optional[str] = Query(None, description="Push provider: firebase, expo"),
):
    """
    Create a new alert subscription.
    
    Subscription types:
    - **ups_threshold**: Alert when any game exceeds threshold
    - **team**: Alert for specific team games
    - **game**: Alert for a specific game
    - **all_upsets**: Alert for all high upset probability games
    """
    try:
        from services.supabase_client import create_subscription as db_create_sub, is_supabase_configured
        
        if not is_supabase_configured():
            raise HTTPException(status_code=503, detail="Supabase not configured")
        
        sub = db_create_sub(
            user_id=user_id,
            subscription_type=subscription_type,
            target_id=target_id,
            ups_threshold=ups_threshold,
            push_token=push_token,
            push_provider=push_provider,
        )
        
        if sub:
            return {
                "status": "created",
                "subscription": sub,
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to create subscription")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating subscription: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/alerts/high-ups", tags=["Alerts"])
def get_high_ups_games(
    min_ups: float = Query(60.0, description="Minimum UPS score"),
    sport: str = Query("NFL", description="Sport to filter by"),
    limit: int = Query(20, description="Maximum games to return"),
):
    """
    Get games with high upset probability scores.
    
    - **min_ups**: Minimum UPS threshold (default 60)
    - **sport**: Sport filter (default NFL)
    - **limit**: Maximum games to return
    
    Returns games sorted by UPS score descending.
    """
    try:
        from services.supabase_client import get_high_ups_games as db_high_ups, is_supabase_configured
        
        if not is_supabase_configured():
            # Fallback to in-memory calculation
            from services.odds_api import get_games_with_predictions
            
            games, _, _ = get_games_with_predictions(sport)
            high_ups = [
                g.model_dump() for g in games
                if g.prediction.upset_probability >= min_ups
            ]
            high_ups.sort(key=lambda x: x["prediction"]["upset_probability"], reverse=True)
            
            return {
                "games": high_ups[:limit],
                "count": len(high_ups),
                "source": "live",
            }
        
        games = db_high_ups(min_ups, sport, limit)
        
        return {
            "games": games,
            "count": len(games),
            "source": "database",
        }
    except Exception as e:
        logger.error(f"Error getting high UPS games: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# SENTIMENT
# =============================================================================

@app.get("/sentiment/team/{team}", tags=["Sentiment"])
def get_team_sentiment(
    team: str,
    hours: int = Query(24, description="Hours of history to include"),
):
    """
    Get sentiment analysis for a specific team.
    
    - **team**: Team abbreviation (e.g., KC, PHI)
    - **hours**: Hours of history (default 24)
    
    Returns aggregated sentiment from Reddit and Twitter.
    """
    try:
        from services.supabase_client import get_team_sentiment_history, is_supabase_configured
        
        if not is_supabase_configured():
            return {
                "team": team,
                "sentiment": None,
                "message": "Supabase not configured - no sentiment data available",
            }
        
        reddit_sentiment = get_team_sentiment_history(team, hours, "reddit")
        twitter_sentiment = get_team_sentiment_history(team, hours, "twitter")
        
        return {
            "team": team,
            "hours": hours,
            "reddit": reddit_sentiment,
            "twitter": twitter_sentiment,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error(f"Error getting sentiment for {team}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# GAMES & PREDICTIONS (Odds API)
# =============================================================================

@app.get("/games", response_model=GamesResponse, tags=["Games"])
def list_games(sport: Optional[str] = Query("NFL", description="Sport to filter by")):
    """
    List all games with predictions for a given sport.
    
    - **sport**: Filter by sport (NFL, NBA, MLB, NHL, Soccer, CFB)
    
    Returns games with upset probability scores (UPS), market signals,
    and key prediction drivers.
    """
    from services.odds_api import get_games_with_predictions
    
    try:
        games, fetched_at, cached = get_games_with_predictions(sport)
        return GamesResponse(
            games=games,
            fetched_at=fetched_at,
            cached=cached,
        )
    except Exception as e:
        logger.error(f"Error fetching games: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/games/{game_id}", response_model=GameWithPrediction, tags=["Games"])
def get_game(game_id: str):
    """
    Get a single game by ID.
    
    - **game_id**: Unique game identifier
    """
    from services.odds_api import get_games_with_predictions
    
    try:
        # Get all games and find the one with matching ID
        games, _, _ = get_games_with_predictions("NFL")
        
        for game in games:
            if game.id == game_id:
                return game
        
        raise HTTPException(status_code=404, detail="Game not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching game {game_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# INJURIES (SportsDataIO)
# =============================================================================

@app.get("/injuries", response_model=InjuryReport, tags=["SportsDataIO"])
def get_injuries(
    season: Optional[int] = Query(None, description="NFL season year (defaults to current)"),
    week: Optional[int] = Query(None, description="Week number (optional)"),
    team: Optional[str] = Query(None, description="Filter by team abbreviation (e.g., KC, PHI)"),
):
    """
    Get current NFL injury reports.
    
    - **season**: NFL season year (e.g., 2025)
    - **week**: Optional week number for week-specific injuries
    - **team**: Optional team abbreviation to filter results
    
    Injury statuses: Out, Doubtful, Questionable, Probable, IR, PUP, Suspended
    """
    from services.sportsdata_io import get_injuries, get_current_season
    from services.sdio_transformer import transform_injuries_response
    
    try:
        if season is None:
            season = get_current_season()
        
        raw_data, fetched_at, cached = get_injuries(season, week)
        
        # Filter by team if specified
        if team:
            raw_data = [inj for inj in raw_data if inj.get("Team", "").upper() == team.upper()]
        
        return transform_injuries_response(raw_data, fetched_at, cached)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching injuries: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/injuries/{team}", response_model=InjuryReport, tags=["SportsDataIO"])
def get_team_injuries(
    team: str,
    season: Optional[int] = Query(None, description="NFL season year"),
):
    """
    Get injuries for a specific team.
    
    - **team**: Team abbreviation (e.g., KC, PHI, SF)
    - **season**: NFL season year (defaults to current)
    """
    from services.sportsdata_io import get_injuries_by_team, get_current_season
    from services.sdio_transformer import transform_injuries_response
    
    try:
        if season is None:
            season = get_current_season()
        
        raw_data = get_injuries_by_team(team, season)
        fetched_at = datetime.now(timezone.utc).isoformat()
        
        return transform_injuries_response(raw_data, fetched_at, False)
    except Exception as e:
        logger.error(f"Error fetching injuries for {team}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# STANDINGS (SportsDataIO)
# =============================================================================

@app.get("/standings", response_model=StandingsResponse, tags=["SportsDataIO"])
def get_standings(
    season: Optional[int] = Query(None, description="NFL season year"),
    conference: Optional[str] = Query(None, description="Filter by conference (AFC or NFC)"),
    division: Optional[str] = Query(None, description="Filter by division (East, West, North, South)"),
):
    """
    Get NFL standings for a season.
    
    - **season**: NFL season year (defaults to current)
    - **conference**: Optional filter by AFC or NFC
    - **division**: Optional filter by division
    
    Returns teams sorted by win percentage with division/conference rankings.
    """
    from services.sportsdata_io import get_standings, get_current_season
    from services.sdio_transformer import transform_standings_response
    
    try:
        if season is None:
            season = get_current_season()
        
        raw_data, fetched_at, cached = get_standings(season)
        
        # Apply filters
        if conference:
            raw_data = [s for s in raw_data if s.get("Conference", "").upper() == conference.upper()]
        if division:
            raw_data = [s for s in raw_data if s.get("Division", "").upper() == division.upper()]
        
        return transform_standings_response(raw_data, fetched_at, cached, season)
    except Exception as e:
        logger.error(f"Error fetching standings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# PLAYER STATISTICS (SportsDataIO)
# =============================================================================

@app.get("/players/stats", response_model=PlayerStatsResponse, tags=["SportsDataIO"])
def get_player_stats(
    season: Optional[int] = Query(None, description="NFL season year"),
    week: Optional[int] = Query(None, description="Week number for weekly stats"),
    team: Optional[str] = Query(None, description="Filter by team abbreviation"),
    position: Optional[str] = Query(None, description="Filter by position (QB, RB, WR, TE, etc.)"),
    limit: int = Query(100, description="Maximum number of players to return"),
):
    """
    Get NFL player statistics.
    
    - **season**: NFL season year (defaults to current)
    - **week**: Optional week number for game-by-game stats
    - **team**: Optional team filter
    - **position**: Optional position filter (QB, RB, WR, TE, K, DEF, etc.)
    - **limit**: Maximum players to return (default 100)
    
    Returns comprehensive offensive and defensive stats.
    """
    from services.sportsdata_io import (
        get_player_season_stats,
        get_player_stats_by_week,
        get_current_season,
    )
    from services.sdio_transformer import transform_player_stats_response
    
    try:
        if season is None:
            season = get_current_season()
        
        if week:
            raw_data, fetched_at, cached = get_player_stats_by_week(season, week)
        else:
            raw_data, fetched_at, cached = get_player_season_stats(season)
        
        # Apply filters
        if team:
            raw_data = [p for p in raw_data if p.get("Team", "").upper() == team.upper()]
        if position:
            raw_data = [p for p in raw_data if p.get("Position", "").upper() == position.upper()]
        
        # Apply limit
        raw_data = raw_data[:limit]
        
        return transform_player_stats_response(raw_data, fetched_at, cached, season, week)
    except Exception as e:
        logger.error(f"Error fetching player stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# TEAM STATISTICS (SportsDataIO)
# =============================================================================

@app.get("/teams/stats", response_model=TeamStatsResponse, tags=["SportsDataIO"])
def get_team_stats(
    season: Optional[int] = Query(None, description="NFL season year"),
):
    """
    Get NFL team statistics for a season.
    
    - **season**: NFL season year (defaults to current)
    
    Returns team-level offensive, defensive, and turnover statistics.
    """
    from services.sportsdata_io import get_team_season_stats, get_current_season
    from services.sdio_transformer import transform_team_stats_response
    
    try:
        if season is None:
            season = get_current_season()
        
        raw_data, fetched_at, cached = get_team_season_stats(season)
        
        return transform_team_stats_response(raw_data, fetched_at, cached, season)
    except Exception as e:
        logger.error(f"Error fetching team stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/teams", response_model=TeamsResponse, tags=["SportsDataIO"])
def get_teams():
    """
    Get all NFL teams reference data.
    
    Returns team details including colors, stadium, coach info, and bye weeks.
    """
    from services.sportsdata_io import get_teams
    from services.sdio_transformer import transform_teams_response
    
    try:
        raw_data, fetched_at, cached = get_teams()
        return transform_teams_response(raw_data, fetched_at, cached)
    except Exception as e:
        logger.error(f"Error fetching teams: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# NEWS (SportsDataIO)
# =============================================================================

@app.get("/news", response_model=NewsResponse, tags=["SportsDataIO"])
def get_news(
    team: Optional[str] = Query(None, description="Filter by team abbreviation"),
    limit: int = Query(50, description="Maximum number of articles"),
):
    """
    Get latest NFL news.
    
    - **team**: Optional team filter for team-specific news
    - **limit**: Maximum articles to return (default 50)
    
    Returns news articles sorted by most recent first.
    """
    from services.sportsdata_io import get_news, get_news_by_team
    from services.sdio_transformer import transform_news_response
    
    try:
        if team:
            raw_data, fetched_at, cached = get_news_by_team(team)
        else:
            raw_data, fetched_at, cached = get_news()
        
        # Apply limit
        raw_data = raw_data[:limit]
        
        return transform_news_response(raw_data, fetched_at, cached)
    except Exception as e:
        logger.error(f"Error fetching news: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# LIVE SCORES (SportsDataIO)
# =============================================================================

@app.get("/scores/live", response_model=LiveScoresResponse, tags=["SportsDataIO"])
def get_live_scores(
    season: Optional[int] = Query(None, description="NFL season year"),
    week: Optional[int] = Query(None, description="Week number"),
):
    """
    Get live NFL game scores.
    
    - **season**: NFL season year (defaults to current)
    - **week**: Optional week number (defaults to current week)
    
    Returns real-time scores including quarter, time remaining,
    possession, and field position for in-progress games.
    """
    from services.sportsdata_io import get_live_scores, get_current_season, get_current_week
    from services.sdio_transformer import transform_live_scores_response
    
    try:
        if season is None:
            season = get_current_season()
        
        if week is None:
            week = get_current_week(season)
        
        raw_data, fetched_at, cached = get_live_scores(season, week)
        
        return transform_live_scores_response(raw_data, fetched_at, cached, season, week)
    except Exception as e:
        logger.error(f"Error fetching live scores: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/scores/date/{date}", response_model=LiveScoresResponse, tags=["SportsDataIO"])
def get_scores_by_date(date: str):
    """
    Get scores for a specific date.
    
    - **date**: Date string in YYYY-MM-DD format
    
    Returns all games scheduled for the specified date.
    """
    from services.sportsdata_io import get_scores_by_date, get_current_season
    from services.sdio_transformer import transform_live_scores_response
    
    try:
        season = get_current_season()
        raw_data, fetched_at, cached = get_scores_by_date(date)
        
        return transform_live_scores_response(raw_data, fetched_at, cached, season, None)
    except Exception as e:
        logger.error(f"Error fetching scores for {date}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# ENHANCED GAMES (Combined Odds + SDIO Data)
# =============================================================================

@app.get("/games/enhanced", tags=["Games"])
def get_enhanced_games(
    sport: str = Query("NFL", description="Sport (currently only NFL supported)"),
    include_injuries: bool = Query(True, description="Include injury data"),
    include_standings: bool = Query(True, description="Include team standings"),
):
    """
    Get games with enhanced data from SportsDataIO.
    
    Combines Odds API game data with:
    - Current injuries for both teams
    - Team standings and records
    - Injury-adjusted upset probability
    
    This endpoint provides the most comprehensive game context for predictions.
    """
    from services.odds_api import get_games_with_predictions
    from services.sportsdata_io import get_injuries, get_standings, get_current_season
    from services.sdio_transformer import transform_injuries, transform_standings, calculate_injury_impact
    
    try:
        # Get base games with predictions
        games, fetched_at, cached = get_games_with_predictions(sport)
        season = get_current_season()
        
        # Get supplementary data
        injuries_data = []
        standings_data = []
        
        if include_injuries:
            try:
                raw_injuries, _, _ = get_injuries(season)
                injuries_data = transform_injuries(raw_injuries)
            except Exception as e:
                logger.warning(f"Could not fetch injuries: {e}")
        
        if include_standings:
            try:
                raw_standings, _, _ = get_standings(season)
                standings_data = transform_standings(raw_standings)
            except Exception as e:
                logger.warning(f"Could not fetch standings: {e}")
        
        # Create standings lookup
        standings_by_team = {s.team: s for s in standings_data}
        
        # Enhance each game
        enhanced_games = []
        for game in games:
            game_dict = game.model_dump()
            
            # Get team injuries
            fav_injuries = [i for i in injuries_data if i.team == game.team_favorite]
            und_injuries = [i for i in injuries_data if i.team == game.team_underdog]
            
            # Calculate injury impact on favorite (boosts upset probability)
            injury_boost = calculate_injury_impact(fav_injuries)
            
            # Add enhanced data
            game_dict["enhanced_data"] = {
                "favorite_injuries": [i.model_dump() for i in fav_injuries[:5]],  # Top 5
                "underdog_injuries": [i.model_dump() for i in und_injuries[:5]],
                "favorite_record": standings_by_team.get(game.team_favorite, {}).model_dump() 
                    if game.team_favorite in standings_by_team else None,
                "underdog_record": standings_by_team.get(game.team_underdog, {}).model_dump()
                    if game.team_underdog in standings_by_team else None,
                "injury_impact_score": injury_boost,
            }
            
            # Adjust UPS based on injuries
            if injury_boost > 0:
                adjusted_ups = min(100, game.prediction.upset_probability + injury_boost)
                game_dict["prediction"]["upset_probability"] = round(adjusted_ups, 1)
                game_dict["prediction"]["model_version"] = "v2.0-injury-adjusted"
            
            enhanced_games.append(game_dict)
        
        return {
            "games": enhanced_games,
            "fetched_at": fetched_at,
            "cached": cached,
            "enhanced": True,
        }
    except Exception as e:
        logger.error(f"Error fetching enhanced games: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run("main:app", host=host, port=port, reload=True)

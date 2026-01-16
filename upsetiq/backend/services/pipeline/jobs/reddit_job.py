"""Reddit sentiment job - collects and analyzes NFL sentiment from Reddit."""
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List

from services.sentiment.reddit_client import get_reddit_client, TEAM_SUBREDDITS
from services.sentiment.analyzer import (
    analyze_batch,
    aggregate_sentiment,
    extract_team_mentions,
)
from services.supabase_client import (
    insert_sentiment_scores_batch,
    pipeline_run_context,
    is_supabase_configured,
)

logger = logging.getLogger(__name__)


def process_subreddit_posts(
    posts: List[Dict[str, Any]],
    subreddit: str,
    target_type: str = "team",
    target_id: str = "NFL"
) -> Dict[str, Any]:
    """
    Process posts from a subreddit and compute sentiment.
    
    Args:
        posts: List of post dictionaries
        subreddit: Subreddit name
        target_type: "team" or "game"
        target_id: Team abbreviation or game ID
        
    Returns:
        Sentiment record for database
    """
    if not posts:
        return None
    
    # Extract text from posts
    texts = []
    for post in posts:
        # Combine title and selftext
        text = post.get("title", "")
        if post.get("selftext"):
            text += " " + post["selftext"]
        if text:
            texts.append(text)
    
    if not texts:
        return None
    
    # Analyze sentiment
    results = analyze_batch(texts)
    aggregated = aggregate_sentiment(results)
    
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(hours=2)
    
    return {
        "target_type": target_type,
        "target_id": target_id,
        "sport": "NFL",
        "sentiment_score": aggregated["compound"],
        "positive_count": aggregated["positive_count"],
        "negative_count": aggregated["negative_count"],
        "neutral_count": aggregated["neutral_count"],
        "total_posts": aggregated["total_count"],
        "compound_score": aggregated["compound"],
        "subjectivity": aggregated.get("subjectivity", 0),
        "source": "reddit",
        "subreddit": subreddit,
        "window_start": window_start.isoformat(),
        "window_end": now.isoformat(),
    }


async def run_reddit_sentiment() -> Dict[str, Any]:
    """
    Run the Reddit sentiment job.
    
    Collects posts from NFL and team subreddits, analyzes sentiment,
    and stores results in Supabase.
    
    Returns:
        Job result summary
    """
    logger.info("Starting Reddit sentiment job")
    
    client = get_reddit_client()
    
    if not client.is_available:
        logger.warning("Reddit client not available - skipping job")
        return {
            "status": "skipped",
            "reason": "Reddit credentials not configured",
        }
    
    sentiment_records = []
    posts_processed = 0
    errors = []
    
    use_supabase = is_supabase_configured()
    
    try:
        # 1. Process main r/nfl subreddit
        logger.info("Fetching r/nfl posts")
        nfl_posts = client.get_subreddit_posts("nfl", limit=100)
        posts_processed += len(nfl_posts)
        
        if nfl_posts:
            record = process_subreddit_posts(
                nfl_posts,
                subreddit="nfl",
                target_type="team",
                target_id="NFL"
            )
            if record:
                sentiment_records.append(record)
        
        # 2. Process team subreddits
        logger.info("Fetching team subreddit posts")
        for team, subreddit in TEAM_SUBREDDITS.items():
            try:
                posts = client.get_subreddit_posts(subreddit, limit=30)
                posts_processed += len(posts)
                
                if posts:
                    record = process_subreddit_posts(
                        posts,
                        subreddit=subreddit,
                        target_type="team",
                        target_id=team
                    )
                    if record:
                        sentiment_records.append(record)
            
            except Exception as e:
                error_msg = f"Error processing r/{subreddit}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        # 3. Extract team mentions from r/nfl for cross-team analysis
        logger.info("Analyzing team mentions in r/nfl")
        team_mentions = {}
        
        for post in nfl_posts:
            text = f"{post.get('title', '')} {post.get('selftext', '')}"
            mentioned_teams = extract_team_mentions(text)
            
            for team in mentioned_teams:
                if team not in team_mentions:
                    team_mentions[team] = []
                team_mentions[team].append(text)
        
        # Analyze mentions per team
        for team, mentions in team_mentions.items():
            if len(mentions) >= 3:  # Only if enough mentions
                results = analyze_batch(mentions)
                aggregated = aggregate_sentiment(results)
                
                now = datetime.now(timezone.utc)
                record = {
                    "target_type": "team",
                    "target_id": team,
                    "sport": "NFL",
                    "sentiment_score": aggregated["compound"],
                    "positive_count": aggregated["positive_count"],
                    "negative_count": aggregated["negative_count"],
                    "neutral_count": aggregated["neutral_count"],
                    "total_posts": aggregated["total_count"],
                    "compound_score": aggregated["compound"],
                    "source": "reddit",
                    "subreddit": "nfl_mentions",
                    "window_start": (now - timedelta(hours=2)).isoformat(),
                    "window_end": now.isoformat(),
                }
                sentiment_records.append(record)
        
        # 4. Store in Supabase
        if use_supabase and sentiment_records:
            with pipeline_run_context("reddit_sentiment", "reddit") as run:
                inserted = insert_sentiment_scores_batch(sentiment_records)
                
                run["records_processed"] = posts_processed
                run["records_created"] = inserted
                run["metadata"] = {
                    "subreddits_processed": len(TEAM_SUBREDDITS) + 1,
                    "team_mentions_analyzed": len(team_mentions),
                    "errors": errors,
                }
                
                logger.info(f"Inserted {inserted} sentiment records")
        
        else:
            logger.warning("Supabase not configured - sentiment data not stored")
    
    except Exception as e:
        logger.error(f"Reddit sentiment job failed: {e}")
        raise
    
    result = {
        "status": "completed" if not errors else "completed_with_errors",
        "posts_processed": posts_processed,
        "sentiment_records": len(sentiment_records),
        "team_mentions": len(team_mentions) if 'team_mentions' in locals() else 0,
        "errors": errors,
    }
    
    logger.info(f"Reddit sentiment job completed: {result}")
    return result

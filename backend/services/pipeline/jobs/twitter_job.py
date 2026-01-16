"""Twitter/X sentiment job - collects and analyzes NFL sentiment from Twitter."""
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List

from services.sentiment.twitter_client import get_twitter_client, TEAM_HANDLES
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


def process_tweets(
    tweets: List[Dict[str, Any]],
    target_type: str = "team",
    target_id: str = "NFL"
) -> Dict[str, Any]:
    """
    Process tweets and compute sentiment.
    
    Args:
        tweets: List of tweet dictionaries
        target_type: "team" or "game"
        target_id: Team abbreviation or game ID
        
    Returns:
        Sentiment record for database
    """
    if not tweets:
        return None
    
    # Extract text from tweets
    texts = [tweet.get("text", "") for tweet in tweets if tweet.get("text")]
    
    if not texts:
        return None
    
    # Analyze sentiment
    results = analyze_batch(texts)
    aggregated = aggregate_sentiment(results)
    
    # Calculate engagement-weighted sentiment
    total_engagement = 0
    weighted_sentiment = 0
    
    for i, tweet in enumerate(tweets):
        if i < len(results):
            engagement = (
                tweet.get("likes", 0) +
                tweet.get("retweets", 0) * 2 +
                tweet.get("replies", 0)
            )
            total_engagement += engagement
            weighted_sentiment += results[i].compound * engagement
    
    engagement_weighted_score = (
        weighted_sentiment / total_engagement
        if total_engagement > 0
        else aggregated["compound"]
    )
    
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
        "compound_score": engagement_weighted_score,
        "subjectivity": aggregated.get("subjectivity", 0),
        "source": "twitter",
        "window_start": window_start.isoformat(),
        "window_end": now.isoformat(),
    }


async def run_twitter_sentiment() -> Dict[str, Any]:
    """
    Run the Twitter/X sentiment job.
    
    Collects tweets about NFL and teams, analyzes sentiment,
    and stores results in Supabase.
    
    Returns:
        Job result summary
    """
    logger.info("Starting Twitter sentiment job")
    
    client = get_twitter_client()
    
    if not client.is_available:
        logger.warning("Twitter client not available - skipping job")
        return {
            "status": "skipped",
            "reason": "Twitter credentials not configured",
        }
    
    sentiment_records = []
    tweets_processed = 0
    errors = []
    
    use_supabase = is_supabase_configured()
    
    try:
        # 1. General NFL tweets
        logger.info("Fetching general NFL tweets")
        nfl_tweets = client.get_nfl_tweets(max_results=100, hours_back=24)
        tweets_processed += len(nfl_tweets)
        
        if nfl_tweets:
            record = process_tweets(
                nfl_tweets,
                target_type="team",
                target_id="NFL"
            )
            if record:
                sentiment_records.append(record)
        
        # 2. Team-specific tweets
        logger.info("Fetching team-specific tweets")
        teams_to_process = list(TEAM_HANDLES.keys())[:16]  # Limit to avoid rate limits
        
        for team in teams_to_process:
            try:
                team_tweets = client.get_team_tweets(
                    team,
                    max_results=30,
                    hours_back=24
                )
                tweets_processed += len(team_tweets)
                
                if team_tweets:
                    record = process_tweets(
                        team_tweets,
                        target_type="team",
                        target_id=team
                    )
                    if record:
                        sentiment_records.append(record)
            
            except Exception as e:
                error_msg = f"Error processing tweets for {team}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        # 3. NFL news/reporter tweets
        logger.info("Fetching NFL news tweets")
        try:
            news_tweets = client.get_nfl_news_tweets(max_results=50)
            tweets_processed += len(news_tweets)
            
            if news_tweets:
                record = process_tweets(
                    news_tweets,
                    target_type="team",
                    target_id="NFL_NEWS"
                )
                if record:
                    record["subreddit"] = "nfl_reporters"  # Reuse field for source
                    sentiment_records.append(record)
        except Exception as e:
            logger.error(f"Error fetching news tweets: {e}")
        
        # 4. Analyze team mentions in general NFL tweets
        logger.info("Analyzing team mentions in tweets")
        team_mentions = {}
        
        for tweet in nfl_tweets:
            text = tweet.get("text", "")
            mentioned_teams = extract_team_mentions(text)
            
            for team in mentioned_teams:
                if team not in team_mentions:
                    team_mentions[team] = []
                team_mentions[team].append(tweet)
        
        # Process team mentions
        for team, mentions in team_mentions.items():
            if len(mentions) >= 5:  # Only if enough mentions
                record = process_tweets(
                    mentions,
                    target_type="team",
                    target_id=team
                )
                if record:
                    record["subreddit"] = "twitter_mentions"
                    sentiment_records.append(record)
        
        # 5. Store in Supabase
        if use_supabase and sentiment_records:
            with pipeline_run_context("twitter_sentiment", "twitter") as run:
                inserted = insert_sentiment_scores_batch(sentiment_records)
                
                run["records_processed"] = tweets_processed
                run["records_created"] = inserted
                run["metadata"] = {
                    "teams_processed": len(teams_to_process),
                    "team_mentions_analyzed": len(team_mentions),
                    "errors": errors,
                }
                
                logger.info(f"Inserted {inserted} sentiment records")
        
        else:
            logger.warning("Supabase not configured - sentiment data not stored")
    
    except Exception as e:
        logger.error(f"Twitter sentiment job failed: {e}")
        raise
    
    result = {
        "status": "completed" if not errors else "completed_with_errors",
        "tweets_processed": tweets_processed,
        "sentiment_records": len(sentiment_records),
        "team_mentions": len(team_mentions) if 'team_mentions' in locals() else 0,
        "errors": errors,
    }
    
    logger.info(f"Twitter sentiment job completed: {result}")
    return result

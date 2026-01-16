"""Twitter/X API client for sentiment collection using Tweepy."""
import os
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Twitter configuration
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")

# NFL-related accounts to monitor
NFL_ACCOUNTS = [
    "NFL",
    "NFLFantasy",
    "AdamSchefter",
    "RapSheet",
    "FieldYates",
    "JayGlazer",
]

# Team Twitter handles
TEAM_HANDLES = {
    "ARI": "AZCardinals",
    "ATL": "AtlantaFalcons",
    "BAL": "Ravens",
    "BUF": "BuffaloBills",
    "CAR": "Panthers",
    "CHI": "ChicagoBears",
    "CIN": "Bengals",
    "CLE": "Browns",
    "DAL": "dlowhawks",
    "DEN": "Broncos",
    "DET": "Lions",
    "GB": "packers",
    "HOU": "HoustonTexans",
    "IND": "Colts",
    "JAX": "Jaguars",
    "KC": "Chiefs",
    "LV": "Raiders",
    "LAC": "chargers",
    "LAR": "RamsNFL",
    "MIA": "MiamiDolphins",
    "MIN": "Vikings",
    "NE": "Patriots",
    "NO": "Saints",
    "NYG": "Giants",
    "NYJ": "nyjets",
    "PHI": "Eagles",
    "PIT": "steelers",
    "SF": "49ers",
    "SEA": "Seahawks",
    "TB": "Buccaneers",
    "TEN": "Titans",
    "WAS": "Commanders",
}


class TwitterClient:
    """Client for fetching Twitter/X posts for sentiment analysis."""
    
    def __init__(self):
        """Initialize Twitter client."""
        self._client = None
        self._initialized = False
    
    def _init_client(self):
        """Lazy initialize Tweepy client."""
        if self._initialized:
            return
        
        if not TWITTER_BEARER_TOKEN:
            logger.warning("Twitter bearer token not configured")
            self._initialized = True
            return
        
        try:
            import tweepy
            
            self._client = tweepy.Client(
                bearer_token=TWITTER_BEARER_TOKEN,
                wait_on_rate_limit=True,
            )
            self._initialized = True
            logger.info("Twitter client initialized")
        except ImportError:
            logger.error("Tweepy not installed")
            self._initialized = True
        except Exception as e:
            logger.error(f"Error initializing Twitter client: {e}")
            self._initialized = True
    
    @property
    def is_available(self) -> bool:
        """Check if Twitter client is available."""
        self._init_client()
        return self._client is not None
    
    def search_recent_tweets(
        self,
        query: str,
        max_results: int = 100,
        hours_back: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Search for recent tweets matching a query.
        
        Args:
            query: Search query (supports Twitter search operators)
            max_results: Maximum tweets to return (10-100 per request)
            hours_back: Hours to look back
            
        Returns:
            List of tweet dictionaries
        """
        self._init_client()
        
        if not self._client:
            return []
        
        tweets = []
        
        try:
            # Calculate start time
            start_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)
            
            # Add -is:retweet to avoid duplicates
            full_query = f"{query} -is:retweet lang:en"
            
            response = self._client.search_recent_tweets(
                query=full_query,
                max_results=min(max_results, 100),
                start_time=start_time,
                tweet_fields=["created_at", "public_metrics", "author_id", "lang"],
                expansions=["author_id"],
                user_fields=["username", "public_metrics"],
            )
            
            if response.data:
                # Build user lookup
                users = {}
                if response.includes and "users" in response.includes:
                    for user in response.includes["users"]:
                        users[user.id] = {
                            "username": user.username,
                            "followers": user.public_metrics.get("followers_count", 0)
                            if user.public_metrics else 0,
                        }
                
                for tweet in response.data:
                    user_info = users.get(tweet.author_id, {})
                    
                    tweets.append({
                        "id": tweet.id,
                        "text": tweet.text,
                        "author_id": tweet.author_id,
                        "username": user_info.get("username", ""),
                        "followers": user_info.get("followers", 0),
                        "created_at": tweet.created_at.isoformat() if tweet.created_at else None,
                        "retweets": tweet.public_metrics.get("retweet_count", 0)
                            if tweet.public_metrics else 0,
                        "likes": tweet.public_metrics.get("like_count", 0)
                            if tweet.public_metrics else 0,
                        "replies": tweet.public_metrics.get("reply_count", 0)
                            if tweet.public_metrics else 0,
                        "query": query,
                    })
        
        except Exception as e:
            logger.error(f"Error searching tweets for '{query}': {e}")
        
        return tweets
    
    def get_user_tweets(
        self,
        username: str,
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Fetch recent tweets from a specific user.
        
        Args:
            username: Twitter username (without @)
            max_results: Maximum tweets
            
        Returns:
            List of tweet dictionaries
        """
        self._init_client()
        
        if not self._client:
            return []
        
        tweets = []
        
        try:
            # First get user ID
            user = self._client.get_user(username=username)
            
            if not user.data:
                logger.warning(f"User not found: {username}")
                return []
            
            user_id = user.data.id
            
            # Get user's tweets
            response = self._client.get_users_tweets(
                id=user_id,
                max_results=min(max_results, 100),
                tweet_fields=["created_at", "public_metrics"],
                exclude=["retweets"],
            )
            
            if response.data:
                for tweet in response.data:
                    tweets.append({
                        "id": tweet.id,
                        "text": tweet.text,
                        "username": username,
                        "created_at": tweet.created_at.isoformat() if tweet.created_at else None,
                        "retweets": tweet.public_metrics.get("retweet_count", 0)
                            if tweet.public_metrics else 0,
                        "likes": tweet.public_metrics.get("like_count", 0)
                            if tweet.public_metrics else 0,
                    })
        
        except Exception as e:
            logger.error(f"Error fetching tweets for @{username}: {e}")
        
        return tweets
    
    def get_nfl_tweets(
        self,
        max_results: int = 100,
        hours_back: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Fetch NFL-related tweets.
        
        Args:
            max_results: Max tweets total
            hours_back: Hours to look back
            
        Returns:
            List of tweets
        """
        queries = [
            "#NFL",
            "NFL game",
            "NFL upset",
        ]
        
        all_tweets = []
        seen_ids = set()
        
        for query in queries:
            tweets = self.search_recent_tweets(
                query,
                max_results=max_results // len(queries),
                hours_back=hours_back,
            )
            
            for tweet in tweets:
                if tweet["id"] not in seen_ids:
                    all_tweets.append(tweet)
                    seen_ids.add(tweet["id"])
        
        return all_tweets
    
    def get_team_tweets(
        self,
        team: str,
        max_results: int = 50,
        hours_back: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Fetch tweets about a specific team.
        
        Args:
            team: Team abbreviation
            max_results: Max tweets
            hours_back: Hours to look back
            
        Returns:
            List of tweets
        """
        team_handle = TEAM_HANDLES.get(team.upper())
        
        queries = [
            f"#{team.upper()}",
        ]
        
        if team_handle:
            queries.append(f"@{team_handle}")
        
        all_tweets = []
        seen_ids = set()
        
        for query in queries:
            tweets = self.search_recent_tweets(
                query,
                max_results=max_results // len(queries),
                hours_back=hours_back,
            )
            
            for tweet in tweets:
                if tweet["id"] not in seen_ids:
                    all_tweets.append(tweet)
                    seen_ids.add(tweet["id"])
        
        return all_tweets
    
    def get_game_tweets(
        self,
        team1: str,
        team2: str,
        max_results: int = 50,
        hours_back: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Fetch tweets about a specific game matchup.
        
        Args:
            team1: First team abbreviation
            team2: Second team abbreviation
            max_results: Max tweets
            hours_back: Hours to look back
            
        Returns:
            List of tweets
        """
        queries = [
            f"{team1.upper()} vs {team2.upper()}",
            f"#{team1.upper()} #{team2.upper()}",
        ]
        
        all_tweets = []
        seen_ids = set()
        
        for query in queries:
            tweets = self.search_recent_tweets(
                query,
                max_results=max_results // len(queries),
                hours_back=hours_back,
            )
            
            for tweet in tweets:
                if tweet["id"] not in seen_ids:
                    all_tweets.append(tweet)
                    seen_ids.add(tweet["id"])
        
        return all_tweets
    
    def get_nfl_news_tweets(
        self,
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Fetch tweets from NFL news/reporter accounts.
        
        Args:
            max_results: Max tweets per account
            
        Returns:
            List of tweets
        """
        all_tweets = []
        
        for account in NFL_ACCOUNTS[:5]:  # Limit to avoid rate limits
            tweets = self.get_user_tweets(account, max_results=max_results // len(NFL_ACCOUNTS))
            all_tweets.extend(tweets)
        
        return all_tweets


# Singleton instance
_twitter_client: Optional[TwitterClient] = None


def get_twitter_client() -> TwitterClient:
    """Get or create Twitter client singleton."""
    global _twitter_client
    
    if _twitter_client is None:
        _twitter_client = TwitterClient()
    
    return _twitter_client

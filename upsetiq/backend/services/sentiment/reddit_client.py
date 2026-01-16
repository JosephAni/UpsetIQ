"""Reddit API client for sentiment collection using PRAW."""
import os
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Reddit configuration
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "UpsetIQ/1.0")

# NFL subreddits to monitor
NFL_SUBREDDITS = [
    "nfl",           # Main NFL subreddit
    "fantasyfootball",  # Fantasy context
]

# Team-specific subreddits
TEAM_SUBREDDITS = {
    "ARI": "AZCardinals",
    "ATL": "falcons",
    "BAL": "ravens",
    "BUF": "buffalobills",
    "CAR": "panthers",
    "CHI": "CHIBears",
    "CIN": "bengals",
    "CLE": "Browns",
    "DAL": "cowboys",
    "DEN": "DenverBroncos",
    "DET": "detroitlions",
    "GB": "GreenBayPackers",
    "HOU": "Texans",
    "IND": "Colts",
    "JAX": "Jaguars",
    "KC": "KansasCityChiefs",
    "LV": "raiders",
    "LAC": "Chargers",
    "LAR": "LosAngelesRams",
    "MIA": "miamidolphins",
    "MIN": "minnesotavikings",
    "NE": "Patriots",
    "NO": "Saints",
    "NYG": "NYGiants",
    "NYJ": "nyjets",
    "PHI": "eagles",
    "PIT": "steelers",
    "SF": "49ers",
    "SEA": "Seahawks",
    "TB": "buccaneers",
    "TEN": "Tennesseetitans",
    "WAS": "Commanders",
}


class RedditClient:
    """Client for fetching Reddit posts and comments for sentiment analysis."""
    
    def __init__(self):
        """Initialize Reddit client."""
        self._reddit = None
        self._initialized = False
    
    def _init_reddit(self):
        """Lazy initialize PRAW Reddit instance."""
        if self._initialized:
            return
        
        if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
            logger.warning("Reddit credentials not configured")
            self._initialized = True
            return
        
        try:
            import praw
            
            self._reddit = praw.Reddit(
                client_id=REDDIT_CLIENT_ID,
                client_secret=REDDIT_CLIENT_SECRET,
                user_agent=REDDIT_USER_AGENT,
            )
            self._initialized = True
            logger.info("Reddit client initialized")
        except ImportError:
            logger.error("PRAW not installed")
            self._initialized = True
        except Exception as e:
            logger.error(f"Error initializing Reddit client: {e}")
            self._initialized = True
    
    @property
    def is_available(self) -> bool:
        """Check if Reddit client is available."""
        self._init_reddit()
        return self._reddit is not None
    
    def get_subreddit_posts(
        self,
        subreddit: str,
        limit: int = 50,
        time_filter: str = "day",
        sort: str = "hot"
    ) -> List[Dict[str, Any]]:
        """
        Fetch posts from a subreddit.
        
        Args:
            subreddit: Subreddit name (without r/)
            limit: Max posts to fetch
            time_filter: One of 'hour', 'day', 'week', 'month', 'year', 'all'
            sort: One of 'hot', 'new', 'top', 'rising'
            
        Returns:
            List of post dictionaries
        """
        self._init_reddit()
        
        if not self._reddit:
            return []
        
        posts = []
        
        try:
            sub = self._reddit.subreddit(subreddit)
            
            # Get posts based on sort method
            if sort == "hot":
                submissions = sub.hot(limit=limit)
            elif sort == "new":
                submissions = sub.new(limit=limit)
            elif sort == "top":
                submissions = sub.top(time_filter=time_filter, limit=limit)
            elif sort == "rising":
                submissions = sub.rising(limit=limit)
            else:
                submissions = sub.hot(limit=limit)
            
            for post in submissions:
                posts.append({
                    "id": post.id,
                    "title": post.title,
                    "selftext": post.selftext,
                    "score": post.score,
                    "upvote_ratio": post.upvote_ratio,
                    "num_comments": post.num_comments,
                    "author": str(post.author) if post.author else "[deleted]",
                    "created_utc": datetime.fromtimestamp(
                        post.created_utc, tz=timezone.utc
                    ).isoformat(),
                    "subreddit": subreddit,
                    "url": post.url,
                    "is_self": post.is_self,
                    "link_flair_text": post.link_flair_text,
                })
        
        except Exception as e:
            logger.error(f"Error fetching posts from r/{subreddit}: {e}")
        
        return posts
    
    def get_post_comments(
        self,
        post_id: str,
        limit: int = 100,
        depth: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Fetch comments from a post.
        
        Args:
            post_id: Reddit post ID
            limit: Max comments to fetch
            depth: Comment tree depth to traverse
            
        Returns:
            List of comment dictionaries
        """
        self._init_reddit()
        
        if not self._reddit:
            return []
        
        comments = []
        
        try:
            submission = self._reddit.submission(id=post_id)
            submission.comments.replace_more(limit=0)  # Skip "more comments"
            
            for comment in submission.comments.list()[:limit]:
                comments.append({
                    "id": comment.id,
                    "body": comment.body,
                    "score": comment.score,
                    "author": str(comment.author) if comment.author else "[deleted]",
                    "created_utc": datetime.fromtimestamp(
                        comment.created_utc, tz=timezone.utc
                    ).isoformat(),
                    "post_id": post_id,
                    "is_submitter": comment.is_submitter,
                })
        
        except Exception as e:
            logger.error(f"Error fetching comments for post {post_id}: {e}")
        
        return comments
    
    def search_subreddit(
        self,
        subreddit: str,
        query: str,
        limit: int = 50,
        time_filter: str = "day"
    ) -> List[Dict[str, Any]]:
        """
        Search posts in a subreddit.
        
        Args:
            subreddit: Subreddit to search
            query: Search query
            limit: Max results
            time_filter: Time filter
            
        Returns:
            List of matching posts
        """
        self._init_reddit()
        
        if not self._reddit:
            return []
        
        posts = []
        
        try:
            sub = self._reddit.subreddit(subreddit)
            
            for post in sub.search(query, time_filter=time_filter, limit=limit):
                posts.append({
                    "id": post.id,
                    "title": post.title,
                    "selftext": post.selftext,
                    "score": post.score,
                    "upvote_ratio": post.upvote_ratio,
                    "num_comments": post.num_comments,
                    "created_utc": datetime.fromtimestamp(
                        post.created_utc, tz=timezone.utc
                    ).isoformat(),
                    "subreddit": subreddit,
                })
        
        except Exception as e:
            logger.error(f"Error searching r/{subreddit}: {e}")
        
        return posts
    
    def get_nfl_posts(
        self,
        limit: int = 50,
        include_team_subs: bool = True
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetch posts from NFL-related subreddits.
        
        Args:
            limit: Posts per subreddit
            include_team_subs: Include team-specific subreddits
            
        Returns:
            Dict mapping subreddit to posts
        """
        all_posts = {}
        
        # Main NFL subreddits
        for sub in NFL_SUBREDDITS:
            posts = self.get_subreddit_posts(sub, limit=limit)
            if posts:
                all_posts[sub] = posts
        
        # Team subreddits (optional)
        if include_team_subs:
            for team, sub in TEAM_SUBREDDITS.items():
                posts = self.get_subreddit_posts(sub, limit=limit // 2)
                if posts:
                    all_posts[f"team_{team}"] = posts
        
        return all_posts
    
    def get_team_posts(
        self,
        team: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Fetch posts for a specific team.
        
        Args:
            team: Team abbreviation (e.g., "KC")
            limit: Max posts
            
        Returns:
            List of posts
        """
        team_sub = TEAM_SUBREDDITS.get(team.upper())
        
        if not team_sub:
            logger.warning(f"No subreddit mapped for team: {team}")
            return []
        
        return self.get_subreddit_posts(team_sub, limit=limit)
    
    def get_game_mentions(
        self,
        team1: str,
        team2: str,
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Search for posts mentioning a specific game matchup.
        
        Args:
            team1: First team abbreviation
            team2: Second team abbreviation
            limit: Max posts
            
        Returns:
            List of posts mentioning the matchup
        """
        # Build search query
        queries = [
            f"{team1} vs {team2}",
            f"{team1} {team2}",
            f"{team2} vs {team1}",
        ]
        
        all_posts = []
        seen_ids = set()
        
        for query in queries:
            posts = self.search_subreddit("nfl", query, limit=limit // len(queries))
            for post in posts:
                if post["id"] not in seen_ids:
                    all_posts.append(post)
                    seen_ids.add(post["id"])
        
        return all_posts


# Singleton instance
_reddit_client: Optional[RedditClient] = None


def get_reddit_client() -> RedditClient:
    """Get or create Reddit client singleton."""
    global _reddit_client
    
    if _reddit_client is None:
        _reddit_client = RedditClient()
    
    return _reddit_client

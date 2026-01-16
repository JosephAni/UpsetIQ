"""Sentiment analysis using VADER and TextBlob."""
import logging
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

# Lazy imports for sentiment libraries
_vader_analyzer = None
_textblob_available = False


def _get_vader():
    """Lazy load VADER sentiment analyzer."""
    global _vader_analyzer
    
    if _vader_analyzer is None:
        try:
            from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
            _vader_analyzer = SentimentIntensityAnalyzer()
            logger.info("VADER sentiment analyzer loaded")
        except ImportError:
            logger.warning("vaderSentiment not installed")
            _vader_analyzer = False
    
    return _vader_analyzer if _vader_analyzer else None


def _check_textblob():
    """Check if TextBlob is available."""
    global _textblob_available
    
    try:
        from textblob import TextBlob
        _textblob_available = True
    except ImportError:
        _textblob_available = False
        logger.warning("TextBlob not installed")
    
    return _textblob_available


@dataclass
class SentimentResult:
    """Result of sentiment analysis on a piece of text."""
    text: str
    
    # VADER scores (-1 to 1)
    compound: float = 0.0
    positive: float = 0.0
    negative: float = 0.0
    neutral: float = 0.0
    
    # TextBlob scores
    polarity: float = 0.0  # -1 to 1
    subjectivity: float = 0.0  # 0 to 1
    
    # Classification
    label: str = "neutral"  # positive, negative, neutral
    confidence: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "compound": self.compound,
            "positive": self.positive,
            "negative": self.negative,
            "neutral": self.neutral,
            "polarity": self.polarity,
            "subjectivity": self.subjectivity,
            "label": self.label,
            "confidence": self.confidence,
        }


def analyze_sentiment(text: str) -> SentimentResult:
    """
    Analyze sentiment of a single text.
    
    Uses VADER for social media optimized sentiment and
    TextBlob for additional polarity/subjectivity metrics.
    
    Args:
        text: Text to analyze
        
    Returns:
        SentimentResult with scores
    """
    if not text or not text.strip():
        return SentimentResult(text="")
    
    result = SentimentResult(text=text[:500])  # Truncate for storage
    
    # VADER analysis
    vader = _get_vader()
    if vader:
        scores = vader.polarity_scores(text)
        result.compound = scores["compound"]
        result.positive = scores["pos"]
        result.negative = scores["neg"]
        result.neutral = scores["neu"]
    
    # TextBlob analysis
    if _check_textblob():
        try:
            from textblob import TextBlob
            blob = TextBlob(text)
            result.polarity = blob.sentiment.polarity
            result.subjectivity = blob.sentiment.subjectivity
        except Exception as e:
            logger.warning(f"TextBlob analysis failed: {e}")
    
    # Classify sentiment
    result.label, result.confidence = _classify_sentiment(result)
    
    return result


def _classify_sentiment(result: SentimentResult) -> tuple:
    """
    Classify sentiment as positive, negative, or neutral.
    
    Returns:
        Tuple of (label, confidence)
    """
    compound = result.compound
    
    # Thresholds tuned for social media
    if compound >= 0.05:
        label = "positive"
        confidence = min(1.0, compound)
    elif compound <= -0.05:
        label = "negative"
        confidence = min(1.0, abs(compound))
    else:
        label = "neutral"
        confidence = 1.0 - abs(compound) * 10  # More neutral = more confident
    
    return label, round(confidence, 3)


def analyze_batch(texts: List[str]) -> List[SentimentResult]:
    """
    Analyze sentiment for a batch of texts.
    
    Args:
        texts: List of texts to analyze
        
    Returns:
        List of SentimentResult objects
    """
    return [analyze_sentiment(text) for text in texts]


def aggregate_sentiment(results: List[SentimentResult]) -> Dict[str, Any]:
    """
    Aggregate sentiment across multiple texts.
    
    Args:
        results: List of SentimentResult objects
        
    Returns:
        Aggregated sentiment metrics
    """
    if not results:
        return {
            "compound": 0.0,
            "polarity": 0.0,
            "positive_count": 0,
            "negative_count": 0,
            "neutral_count": 0,
            "total_count": 0,
            "label": "neutral",
        }
    
    total = len(results)
    
    # Count by label
    positive_count = sum(1 for r in results if r.label == "positive")
    negative_count = sum(1 for r in results if r.label == "negative")
    neutral_count = sum(1 for r in results if r.label == "neutral")
    
    # Average scores
    avg_compound = sum(r.compound for r in results) / total
    avg_polarity = sum(r.polarity for r in results) / total
    avg_subjectivity = sum(r.subjectivity for r in results) / total
    
    # Overall label
    if positive_count > negative_count and positive_count > neutral_count:
        label = "positive"
    elif negative_count > positive_count and negative_count > neutral_count:
        label = "negative"
    else:
        label = "neutral"
    
    return {
        "compound": round(avg_compound, 4),
        "polarity": round(avg_polarity, 4),
        "subjectivity": round(avg_subjectivity, 4),
        "positive_count": positive_count,
        "negative_count": negative_count,
        "neutral_count": neutral_count,
        "total_count": total,
        "positive_ratio": round(positive_count / total, 4),
        "negative_ratio": round(negative_count / total, 4),
        "label": label,
    }


# NFL team name variations for text matching
NFL_TEAM_KEYWORDS = {
    "ARI": ["cardinals", "arizona", "cards"],
    "ATL": ["falcons", "atlanta", "dirty birds"],
    "BAL": ["ravens", "baltimore"],
    "BUF": ["bills", "buffalo"],
    "CAR": ["panthers", "carolina"],
    "CHI": ["bears", "chicago"],
    "CIN": ["bengals", "cincinnati", "cincy"],
    "CLE": ["browns", "cleveland"],
    "DAL": ["cowboys", "dallas", "dak"],
    "DEN": ["broncos", "denver"],
    "DET": ["lions", "detroit"],
    "GB": ["packers", "green bay", "pack"],
    "HOU": ["texans", "houston"],
    "IND": ["colts", "indianapolis", "indy"],
    "JAX": ["jaguars", "jacksonville", "jags"],
    "KC": ["chiefs", "kansas city", "kc"],
    "LV": ["raiders", "las vegas", "vegas"],
    "LAC": ["chargers", "la chargers"],
    "LAR": ["rams", "la rams"],
    "MIA": ["dolphins", "miami", "phins"],
    "MIN": ["vikings", "minnesota", "vikes"],
    "NE": ["patriots", "new england", "pats"],
    "NO": ["saints", "new orleans"],
    "NYG": ["giants", "new york giants"],
    "NYJ": ["jets", "new york jets"],
    "PHI": ["eagles", "philadelphia", "philly"],
    "PIT": ["steelers", "pittsburgh"],
    "SF": ["49ers", "san francisco", "niners"],
    "SEA": ["seahawks", "seattle", "hawks"],
    "TB": ["buccaneers", "tampa bay", "bucs"],
    "TEN": ["titans", "tennessee"],
    "WAS": ["commanders", "washington"],
}


def extract_team_mentions(text: str) -> List[str]:
    """
    Extract NFL team mentions from text.
    
    Args:
        text: Text to search
        
    Returns:
        List of team abbreviations found
    """
    text_lower = text.lower()
    teams_found = []
    
    for team, keywords in NFL_TEAM_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                if team not in teams_found:
                    teams_found.append(team)
                break
    
    return teams_found

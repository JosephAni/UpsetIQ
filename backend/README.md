# UpsetIQ Backend API

FastAPI backend for UpsetIQ - Live Upset Intelligence for sports betting insights.

## Features

- **Odds API Integration**: Live odds data from the-odds-api.com
- **SportsDataIO Integration**: Comprehensive NFL data including:
  - Injuries with impact analysis
  - Team standings and records
  - Player statistics
  - Team statistics
  - Live scores
  - NFL news
- **Upset Probability Score (UPS)**: Enhanced predictions using multiple data sources
- **Data Pipeline**: Scheduled data collection with APScheduler
- **Sentiment Analysis**: Reddit and Twitter/X sentiment tracking
- **Real-time Alerts**: WebSocket and push notification delivery
- **In-memory Caching**: Efficient data fetching with configurable TTL

## Setup

### 1. Create Virtual Environment

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Create a `.env` file with your API keys:

```text
# Required API Keys
ODDS_API_KEY=your_odds_api_key
SPORTSDATAIO_KEY=your_sportsdata_key

# Database (for pipeline features)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_service_role_key

# Optional: Sentiment Analysis
REDDIT_CLIENT_ID=your_reddit_id
REDDIT_CLIENT_SECRET=your_reddit_secret
TWITTER_BEARER_TOKEN=your_twitter_token

# Server
HOST=0.0.0.0
PORT=8000
ENABLE_PIPELINE=true
```

### 4. Run Database Migrations (Optional)

If using Supabase, run the migration script in your project's SQL editor:

```bash
cat migrations/001_pipeline_tables.sql
```

### 5. Run the Server

```bash
python main.py
```

Or with uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Status

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Health check with pipeline status |
| `GET /cache/stats` | Cache statistics for monitoring |

### Pipeline Control

| Endpoint | Description |
|----------|-------------|
| `GET /pipeline/status` | Get scheduler and job status |
| `POST /pipeline/jobs/{job_id}/run` | Manually trigger a job |
| `GET /pipeline/runs` | Get recent pipeline run history |

### Alerts

| Endpoint | Description |
|----------|-------------|
| `GET /alerts/subscriptions` | Get user's alert subscriptions |
| `POST /alerts/subscribe` | Create new alert subscription |
| `GET /alerts/high-ups` | Get high upset probability games |

### Sentiment

| Endpoint | Description |
|----------|-------------|
| `GET /sentiment/team/{team}` | Get sentiment analysis for a team |

### Games & Predictions (Odds API)

| Endpoint | Description |
|----------|-------------|
| `GET /games?sport=NFL` | List games with UPS predictions |
| `GET /games/{game_id}` | Get single game details |
| `GET /games/enhanced` | Games with full SDIO enhancement |

### Injuries (SportsDataIO)

| Endpoint | Description |
|----------|-------------|
| `GET /injuries` | Current NFL injury reports |
| `GET /injuries/{team}` | Injuries for specific team |

### Standings (SportsDataIO)

| Endpoint | Description |
|----------|-------------|
| `GET /standings` | NFL standings |

### Player Statistics (SportsDataIO)

| Endpoint | Description |
|----------|-------------|
| `GET /players/stats` | Player statistics |

### Team Statistics (SportsDataIO)

| Endpoint | Description |
|----------|-------------|
| `GET /teams/stats` | Team season statistics |
| `GET /teams` | Team reference data |

### News (SportsDataIO)

| Endpoint | Description |
|----------|-------------|
| `GET /news` | Latest NFL news |

### Live Scores (SportsDataIO)

| Endpoint | Description |
|----------|-------------|
| `GET /scores/live` | Live game scores |
| `GET /scores/date/{date}` | Scores by date (YYYY-MM-DD) |

## Architecture

```text
backend/
├── main.py                      # FastAPI app and endpoints
├── models.py                    # Pydantic models
├── migrations/
│   └── 001_pipeline_tables.sql  # Supabase database schema
├── services/
│   ├── odds_api.py              # Odds API client with caching
│   ├── sportsdata_io.py         # SportsDataIO client with caching
│   ├── sdio_transformer.py      # SDIO data transformation
│   ├── transformer.py           # UPS calculation and data transform
│   ├── supabase_client.py       # Supabase database operations
│   ├── websocket_server.py      # Socket.IO real-time server
│   ├── webhook.py               # Push notification service
│   ├── sentiment/
│   │   ├── analyzer.py          # VADER/TextBlob sentiment
│   │   ├── reddit_client.py     # Reddit API (PRAW)
│   │   └── twitter_client.py    # Twitter/X API (Tweepy)
│   └── pipeline/
│       ├── scheduler.py         # APScheduler configuration
│       ├── feature_builder.py   # ML feature extraction
│       ├── model_scorer.py      # UPS model scoring
│       ├── alert_engine.py      # Alert detection and delivery
│       └── jobs/
│           ├── odds_job.py      # Odds snapshot job
│           ├── schedule_job.py  # Schedule refresh job
│           ├── injury_job.py    # Injury update job
│           ├── reddit_job.py    # Reddit sentiment job
│           └── twitter_job.py   # Twitter sentiment job
├── requirements.txt             # Python dependencies
└── .env                         # Environment variables (not in git)
```

## Data Pipeline

The pipeline runs on a schedule to collect, process, and analyze data:

| Job | Interval | Description |
|-----|----------|-------------|
| Odds Snapshot | 15 min | Capture live odds for line movement analysis |
| Schedule Refresh | Daily 6AM | Update game schedules |
| Injury Update | 6 hours | Refresh injury reports |
| Reddit Sentiment | 2 hours | Collect NFL subreddit sentiment |
| Twitter Sentiment | 2 hours | Collect Twitter/X sentiment |
| Feature Build | 20 min | Build ML features from data |
| Model Scoring | 25 min | Calculate UPS scores |
| Alert Processing | 5 min | Detect thresholds and send alerts |

### Pipeline Data Flow

```text
┌────────────┐   ┌────────────┐   ┌────────────┐
│ Odds API   │   │  Reddit    │   │  Twitter   │
└─────┬──────┘   └─────┬──────┘   └─────┬──────┘
      │                │                │
      ▼                ▼                ▼
┌─────────────────────────────────────────────┐
│              APScheduler Jobs               │
└─────────────────────┬───────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────┐
│              Supabase Storage               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│  │   Odds   │ │Sentiment │ │ Injuries │    │
│  └──────────┘ └──────────┘ └──────────┘    │
└─────────────────────┬───────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────┐
│            Feature Builder                  │
│  (Combines all data into ML features)       │
└─────────────────────┬───────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────┐
│              Model Scorer                   │
│  (Calculates UPS with all signals)          │
└─────────────────────┬───────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────┐
│             Alert Engine                    │
│  ┌──────────────┐  ┌─────────────────┐     │
│  │  WebSocket   │  │ Push Notification│     │
│  └──────────────┘  └─────────────────┘     │
└─────────────────────────────────────────────┘
```

## Enhanced UPS Calculation

The Upset Probability Score (UPS) v2.1 uses multiple factors:

1. **Base Probability** (from Odds API)
   - Implied probability from moneyline odds
   - Spread tightness adjustment

2. **Injury Impact** (from SportsDataIO)
   - Position-weighted impact (QB highest)
   - Status weighting (Out > Doubtful > Questionable)

3. **Sentiment Analysis** (from Reddit/Twitter)
   - Contrarian indicator when public heavily favors one side
   - Volume metrics

4. **Line Movement** (from historical odds)
   - Sharp money detection
   - Movement toward underdog

5. **Record Analysis** (from SportsDataIO)
   - Hot/cold streaks
   - Win percentage differential

## Real-time Features

### WebSocket Alerts

Connect to `/ws` for real-time updates:

```javascript
const socket = io('http://localhost:8000/ws');

// Subscribe to NFL alerts
socket.emit('subscribe_sport', { sport: 'NFL' });

// Subscribe to specific team
socket.emit('subscribe_team', { team: 'KC' });

// Subscribe to specific game
socket.emit('subscribe_game', { game_id: 'abc123' });

// Listen for alerts
socket.on('ups_alert', (data) => {
  console.log('UPS Alert:', data);
});
```

### Push Notifications

Supported providers:
- Firebase Cloud Messaging (FCM)
- Expo Push Notifications

## Caching

Each data type has its own cache TTL:

| Data Type | TTL | Rationale |
|-----------|-----|-----------|
| Schedules | 1 hour | Rarely changes |
| Injuries | 15 min | Updated frequently on game days |
| Standings | 1 hour | Updates after games |
| Player Stats | 1 hour | Aggregated data |
| Team Stats | 1 hour | Aggregated data |
| News | 5 min | Breaking news matters |
| Live Scores | 1 min | Real-time data |
| Teams | 24 hours | Reference data |

## API Keys

### Required

- **The Odds API**: <https://the-odds-api.com/> (Free: 500 requests/month)
- **SportsDataIO**: <https://sportsdata.io/> (NFL data)

### Optional (for full pipeline)

- **Supabase**: <https://supabase.com/> (Database storage)
- **Reddit API**: <https://www.reddit.com/prefs/apps> (Sentiment)
- **Twitter API**: <https://developer.twitter.com> (Sentiment)
- **Firebase**: <https://firebase.google.com/> (Push notifications)

## Interactive Docs

Once the server is running:

- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>

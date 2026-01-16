# UpsetIQ

**Live Upset Intelligence** - Sports betting insights powered by data analytics and machine learning.

UpsetIQ identifies high-probability upset opportunities by analyzing odds movements, injury reports, team performance, and market sentiment.

## Project Structure

```text
upsetiq/
├── frontend/              # React Native mobile app
│   ├── src/              # Source code
│   ├── ios/              # iOS native code
│   ├── android/          # Android native code
│   └── README.md         # Frontend documentation
│
├── backend/              # FastAPI Python backend
│   ├── services/         # API clients & transformers
│   ├── main.py          # API endpoints
│   ├── models.py        # Pydantic models
│   └── README.md        # Backend documentation
│
└── docs/                 # Planning & design docs
    ├── MVP-features.md
    ├── product-architecture.md
    └── ...
```

## Quick Start

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Add API keys to .env
# ODDS_API_KEY=your_key
# SPORTSDATAIO_KEY=your_key

python main.py
```

API available at <http://localhost:8000>

### Frontend

```bash
cd frontend
npm install
npx expo start
```

## Features

- **Upset Probability Score (UPS)**: Proprietary algorithm combining odds, injuries, and team performance
- **Real-time Data**: Live odds from The Odds API, comprehensive NFL data from SportsDataIO
- **Injury Impact Analysis**: Quantifies how key player injuries affect upset probability
- **Market Signals**: Tracks public betting percentages and line movements
- **Multi-sport Support**: NFL, NBA, MLB, NHL, College Football, Soccer

## Data Sources

| Source       | Data                                                 |
|--------------|------------------------------------------------------|
| The Odds API | Live betting odds, spreads, totals                   |
| SportsDataIO | Injuries, standings, player/team stats, news, scores |

## Tech Stack

### Frontend Stack

- React Native + Expo
- TypeScript
- NativeWind (Tailwind CSS)
- React Navigation

### Backend Stack

- FastAPI (Python)
- Pydantic for validation
- In-memory caching (Redis-ready)

## License

Proprietary - All rights reserved

# Product Architecture

Data Layer
 ├── Sports Data APIs (scores, odds, injuries)
 ├── Public Sentiment (Twitter / Reddit / forums)
 ├── Betting Market Data (line movement, spreads)

ML Layer
 ├── Feature Engineering Pipeline
 ├── Upset Probability Model
 ├── Bias Detection Model

Backend
 ├── FastAPI services
 ├── Prediction engine
 ├── Alert engine

Frontend
 ├── Next.js Dashboard
 ├── Real-time updates
 ├── User leaderboard

Storage
 ├── Postgres (users, predictions, history)
 ├── Object store (model artifacts)

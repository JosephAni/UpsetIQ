# MVP Features

🧮 Game Board

Shows:

Favorite vs Underdog

Upset Probability

Key signals

🚨 Upset Alerts

When UPS > threshold → notify users.

🏆 Leaderboard

Points for correct upset calls.

👤 User Profiles

Track accuracy & ranking.

🧱 2. MVP Technical Specification
Frontend

Next.js 14

Tailwind CSS

Recharts / Plotly for graphs

Auth: Clerk or NextAuth

Backend

FastAPI

PostgreSQL

Redis (real-time alerts)

WebSockets for live updates

ML Pipeline

Python

LightGBM / XGBoost

Daily retraining

Feature store (Feast optional)

Data

Odds API

SportsDataIO

Twitter/X sentiment pipeline

Reddit ingestion

Deployment

Vercel (frontend)

GCP Cloud Run (backend + ML)

Supabase / Neon (DB)

Security

JWT auth

Rate limiting

API key encryption

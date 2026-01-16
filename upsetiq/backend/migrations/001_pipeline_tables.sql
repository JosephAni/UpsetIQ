-- UpsetIQ Pipeline Tables Migration
-- Run this in Supabase SQL Editor or via migration tool

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- ODDS SNAPSHOTS
-- Historical odds data captured at intervals
-- ============================================

CREATE TABLE IF NOT EXISTS odds_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    game_id VARCHAR(50) NOT NULL,
    sport VARCHAR(20) NOT NULL,
    
    -- Teams
    home_team VARCHAR(100) NOT NULL,
    away_team VARCHAR(100) NOT NULL,
    favorite VARCHAR(100),
    underdog VARCHAR(100),
    
    -- Moneyline odds
    home_moneyline INTEGER,
    away_moneyline INTEGER,
    favorite_odds INTEGER,
    underdog_odds INTEGER,
    
    -- Spread
    spread DECIMAL(5, 2),
    spread_odds_home INTEGER,
    spread_odds_away INTEGER,
    
    -- Totals
    total DECIMAL(5, 2),
    over_odds INTEGER,
    under_odds INTEGER,
    
    -- Source info
    bookmaker VARCHAR(50),
    source VARCHAR(50) DEFAULT 'odds_api',
    
    -- Timestamps
    captured_at TIMESTAMPTZ DEFAULT NOW(),
    game_start_time TIMESTAMPTZ,
    
    -- Indexes for efficient queries
    CONSTRAINT unique_snapshot UNIQUE (game_id, bookmaker, captured_at)
);

CREATE INDEX IF NOT EXISTS idx_odds_snapshots_game ON odds_snapshots(game_id);
CREATE INDEX IF NOT EXISTS idx_odds_snapshots_sport ON odds_snapshots(sport);
CREATE INDEX IF NOT EXISTS idx_odds_snapshots_captured ON odds_snapshots(captured_at DESC);
CREATE INDEX IF NOT EXISTS idx_odds_snapshots_game_time ON odds_snapshots(game_id, captured_at DESC);

-- ============================================
-- SENTIMENT SCORES
-- Reddit and X/Twitter sentiment by team/game
-- ============================================

CREATE TABLE IF NOT EXISTS sentiment_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Target (can be team or game)
    target_type VARCHAR(20) NOT NULL CHECK (target_type IN ('team', 'game')),
    target_id VARCHAR(100) NOT NULL,  -- Team abbreviation or game_id
    sport VARCHAR(20) NOT NULL DEFAULT 'NFL',
    
    -- Sentiment metrics
    sentiment_score DECIMAL(5, 4) CHECK (sentiment_score >= -1 AND sentiment_score <= 1),
    positive_count INTEGER DEFAULT 0,
    negative_count INTEGER DEFAULT 0,
    neutral_count INTEGER DEFAULT 0,
    total_posts INTEGER DEFAULT 0,
    
    -- Compound scores
    compound_score DECIMAL(5, 4),  -- VADER compound
    subjectivity DECIMAL(5, 4),    -- TextBlob subjectivity
    
    -- Source
    source VARCHAR(20) NOT NULL CHECK (source IN ('reddit', 'twitter', 'combined')),
    subreddit VARCHAR(100),  -- For Reddit: r/nfl, r/KansasCityChiefs, etc.
    
    -- Time window
    window_start TIMESTAMPTZ NOT NULL,
    window_end TIMESTAMPTZ NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT unique_sentiment UNIQUE (target_type, target_id, source, window_start)
);

CREATE INDEX IF NOT EXISTS idx_sentiment_target ON sentiment_scores(target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_sentiment_source ON sentiment_scores(source);
CREATE INDEX IF NOT EXISTS idx_sentiment_created ON sentiment_scores(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_sentiment_window ON sentiment_scores(window_start DESC);

-- ============================================
-- PIPELINE RUNS
-- Track job executions for monitoring
-- ============================================

CREATE TABLE IF NOT EXISTS pipeline_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Job identification
    job_name VARCHAR(50) NOT NULL,
    job_type VARCHAR(30) NOT NULL,  -- odds, schedule, injury, reddit, twitter, feature, score, alert
    
    -- Execution details
    status VARCHAR(20) NOT NULL CHECK (status IN ('running', 'completed', 'failed', 'skipped')),
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    duration_seconds DECIMAL(10, 3),
    
    -- Results
    records_processed INTEGER DEFAULT 0,
    records_created INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    
    -- Error tracking
    error_message TEXT,
    error_traceback TEXT,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pipeline_runs_job ON pipeline_runs(job_name);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_status ON pipeline_runs(status);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_started ON pipeline_runs(started_at DESC);

-- ============================================
-- ALERT QUEUE
-- Pending and sent alerts
-- ============================================

CREATE TABLE IF NOT EXISTS alert_queue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Alert target
    user_id UUID,  -- NULL for broadcast alerts
    game_id VARCHAR(50),
    sport VARCHAR(20) DEFAULT 'NFL',
    
    -- Alert content
    alert_type VARCHAR(30) NOT NULL CHECK (alert_type IN (
        'ups_threshold', 'injury_update', 'odds_movement', 
        'sentiment_shift', 'game_starting', 'upset_occurred'
    )),
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    
    -- UPS data (for threshold alerts)
    ups_score DECIMAL(5, 2),
    previous_ups DECIMAL(5, 2),
    threshold DECIMAL(5, 2),
    
    -- Delivery status
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN (
        'pending', 'sent', 'delivered', 'failed', 'expired'
    )),
    delivery_method VARCHAR(20) CHECK (delivery_method IN ('push', 'websocket', 'webhook', 'email')),
    
    -- Delivery tracking
    sent_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    last_error TEXT,
    
    -- Priority (higher = more urgent)
    priority INTEGER DEFAULT 5 CHECK (priority >= 1 AND priority <= 10),
    
    -- Expiration
    expires_at TIMESTAMPTZ,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_alert_queue_status ON alert_queue(status);
CREATE INDEX IF NOT EXISTS idx_alert_queue_user ON alert_queue(user_id);
CREATE INDEX IF NOT EXISTS idx_alert_queue_game ON alert_queue(game_id);
CREATE INDEX IF NOT EXISTS idx_alert_queue_priority ON alert_queue(priority DESC, created_at);
CREATE INDEX IF NOT EXISTS idx_alert_queue_pending ON alert_queue(status, priority DESC) WHERE status = 'pending';

-- ============================================
-- USER ALERT SUBSCRIPTIONS
-- User preferences for alerts
-- ============================================

CREATE TABLE IF NOT EXISTS alert_subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    
    -- Subscription type
    subscription_type VARCHAR(30) NOT NULL CHECK (subscription_type IN (
        'ups_threshold', 'team', 'game', 'all_upsets'
    )),
    
    -- Target (team abbreviation, game_id, or NULL for all)
    target_id VARCHAR(100),
    sport VARCHAR(20) DEFAULT 'NFL',
    
    -- Threshold settings
    ups_threshold DECIMAL(5, 2) DEFAULT 65.0,
    
    -- Delivery preferences
    push_enabled BOOLEAN DEFAULT TRUE,
    websocket_enabled BOOLEAN DEFAULT TRUE,
    email_enabled BOOLEAN DEFAULT FALSE,
    
    -- Device tokens for push
    push_token TEXT,
    push_provider VARCHAR(20) CHECK (push_provider IN ('firebase', 'expo', 'apns')),
    
    -- Status
    active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT unique_subscription UNIQUE (user_id, subscription_type, target_id)
);

CREATE INDEX IF NOT EXISTS idx_subscriptions_user ON alert_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_active ON alert_subscriptions(active) WHERE active = TRUE;
CREATE INDEX IF NOT EXISTS idx_subscriptions_type ON alert_subscriptions(subscription_type);

-- ============================================
-- GAME FEATURES
-- Pre-computed features for ML model
-- ============================================

CREATE TABLE IF NOT EXISTS game_features (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    game_id VARCHAR(50) NOT NULL,
    sport VARCHAR(20) NOT NULL DEFAULT 'NFL',
    
    -- Team info
    favorite VARCHAR(100) NOT NULL,
    underdog VARCHAR(100) NOT NULL,
    
    -- Odds features
    opening_spread DECIMAL(5, 2),
    current_spread DECIMAL(5, 2),
    spread_movement DECIMAL(5, 2),
    opening_moneyline INTEGER,
    current_moneyline INTEGER,
    moneyline_movement INTEGER,
    implied_probability DECIMAL(5, 4),
    
    -- Public betting
    public_favorite_pct DECIMAL(5, 2),
    public_underdog_pct DECIMAL(5, 2),
    sharp_money_indicator DECIMAL(5, 4),
    
    -- Injury features
    favorite_injury_score DECIMAL(5, 2),
    underdog_injury_score DECIMAL(5, 2),
    qb_injury_favorite BOOLEAN DEFAULT FALSE,
    qb_injury_underdog BOOLEAN DEFAULT FALSE,
    key_players_out_favorite INTEGER DEFAULT 0,
    key_players_out_underdog INTEGER DEFAULT 0,
    
    -- Sentiment features
    favorite_sentiment DECIMAL(5, 4),
    underdog_sentiment DECIMAL(5, 4),
    sentiment_differential DECIMAL(5, 4),
    reddit_volume_favorite INTEGER DEFAULT 0,
    reddit_volume_underdog INTEGER DEFAULT 0,
    twitter_volume_favorite INTEGER DEFAULT 0,
    twitter_volume_underdog INTEGER DEFAULT 0,
    
    -- Team performance
    favorite_win_pct DECIMAL(5, 4),
    underdog_win_pct DECIMAL(5, 4),
    favorite_ats_record DECIMAL(5, 4),  -- Against the spread
    underdog_ats_record DECIMAL(5, 4),
    favorite_streak INTEGER,
    underdog_streak INTEGER,
    
    -- Situational
    is_prime_time BOOLEAN DEFAULT FALSE,
    is_divisional BOOLEAN DEFAULT FALSE,
    is_rivalry BOOLEAN DEFAULT FALSE,
    rest_days_favorite INTEGER,
    rest_days_underdog INTEGER,
    
    -- Computed UPS
    ups_score DECIMAL(5, 2),
    ups_confidence DECIMAL(5, 4),
    model_version VARCHAR(20),
    
    -- Timestamps
    computed_at TIMESTAMPTZ DEFAULT NOW(),
    game_start_time TIMESTAMPTZ,
    
    CONSTRAINT unique_game_features UNIQUE (game_id, computed_at)
);

CREATE INDEX IF NOT EXISTS idx_game_features_game ON game_features(game_id);
CREATE INDEX IF NOT EXISTS idx_game_features_sport ON game_features(sport);
CREATE INDEX IF NOT EXISTS idx_game_features_ups ON game_features(ups_score DESC);
CREATE INDEX IF NOT EXISTS idx_game_features_computed ON game_features(computed_at DESC);

-- ============================================
-- FUNCTIONS AND TRIGGERS
-- ============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
DROP TRIGGER IF EXISTS update_alert_queue_updated_at ON alert_queue;
CREATE TRIGGER update_alert_queue_updated_at
    BEFORE UPDATE ON alert_queue
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_subscriptions_updated_at ON alert_subscriptions;
CREATE TRIGGER update_subscriptions_updated_at
    BEFORE UPDATE ON alert_subscriptions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- ROW LEVEL SECURITY (Enable when ready)
-- ============================================

-- Alert subscriptions: users can only manage their own
-- ALTER TABLE alert_subscriptions ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY "Users can view own subscriptions" ON alert_subscriptions FOR SELECT USING (auth.uid() = user_id);
-- CREATE POLICY "Users can create own subscriptions" ON alert_subscriptions FOR INSERT WITH CHECK (auth.uid() = user_id);
-- CREATE POLICY "Users can update own subscriptions" ON alert_subscriptions FOR UPDATE USING (auth.uid() = user_id);
-- CREATE POLICY "Users can delete own subscriptions" ON alert_subscriptions FOR DELETE USING (auth.uid() = user_id);

-- Public read access for odds, sentiment, features
-- ALTER TABLE odds_snapshots ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY "Odds snapshots are publicly readable" ON odds_snapshots FOR SELECT USING (true);

-- ALTER TABLE sentiment_scores ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY "Sentiment scores are publicly readable" ON sentiment_scores FOR SELECT USING (true);

-- ALTER TABLE game_features ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY "Game features are publicly readable" ON game_features FOR SELECT USING (true);

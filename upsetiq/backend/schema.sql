-- UpsetIQ Database Schema
-- For future Supabase/Postgres migration

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- USERS & AUTHENTICATION
-- ============================================

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    username VARCHAR(100),
    avatar_url TEXT,
    subscription_tier VARCHAR(20) DEFAULT 'free' CHECK (subscription_tier IN ('free', 'pro', 'premium')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_subscription ON users(subscription_tier);

-- ============================================
-- GAMES
-- ============================================

CREATE TABLE games (
    id VARCHAR(50) PRIMARY KEY,
    sport VARCHAR(20) NOT NULL CHECK (sport IN ('NFL', 'NBA', 'MLB', 'NHL', 'Soccer', 'CFB')),
    team_favorite VARCHAR(100) NOT NULL,
    team_underdog VARCHAR(100) NOT NULL,
    start_time TIMESTAMPTZ NOT NULL,
    status VARCHAR(20) DEFAULT 'upcoming' CHECK (status IN ('upcoming', 'live', 'completed')),
    
    -- Opening odds
    odds_open DECIMAL(10, 2),
    spread_open DECIMAL(5, 2),
    total_open DECIMAL(5, 2),
    
    -- Current odds (updated frequently)
    odds_current DECIMAL(10, 2),
    spread_current DECIMAL(5, 2),
    total_current DECIMAL(5, 2),
    
    -- Metadata
    is_prime_time BOOLEAN DEFAULT FALSE,
    venue VARCHAR(200),
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- External IDs for data reconciliation
    external_id VARCHAR(100),
    data_source VARCHAR(50)
);

CREATE INDEX idx_games_sport ON games(sport);
CREATE INDEX idx_games_start_time ON games(start_time);
CREATE INDEX idx_games_status ON games(status);
CREATE INDEX idx_games_sport_status ON games(sport, status);

-- ============================================
-- PREDICTIONS
-- ============================================

CREATE TABLE predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    game_id VARCHAR(50) NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    
    -- Model output
    upset_probability DECIMAL(5, 2) NOT NULL CHECK (upset_probability >= 0 AND upset_probability <= 100),
    confidence_band DECIMAL(5, 2),
    model_version VARCHAR(20) DEFAULT 'v1.0',
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Ensure one prediction per game per model version
    UNIQUE(game_id, model_version)
);

CREATE INDEX idx_predictions_game ON predictions(game_id);
CREATE INDEX idx_predictions_ups ON predictions(upset_probability DESC);

-- ============================================
-- MARKET SIGNALS
-- ============================================

CREATE TABLE market_signals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    game_id VARCHAR(50) NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    
    -- Betting market data
    public_bet_percentage DECIMAL(5, 2) CHECK (public_bet_percentage >= 0 AND public_bet_percentage <= 100),
    line_movement DECIMAL(5, 2),
    sentiment_score DECIMAL(4, 3) CHECK (sentiment_score >= -1 AND sentiment_score <= 1),
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_market_signals_game ON market_signals(game_id);

-- ============================================
-- PREDICTION DRIVERS
-- ============================================

CREATE TABLE prediction_drivers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prediction_id UUID NOT NULL REFERENCES predictions(id) ON DELETE CASCADE,
    label TEXT NOT NULL,
    weight DECIMAL(3, 2) DEFAULT 1.0,
    sort_order INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_drivers_prediction ON prediction_drivers(prediction_id);

-- ============================================
-- USER PICKS
-- ============================================

CREATE TABLE user_picks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    game_id VARCHAR(50) NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    
    -- Pick details
    picked_underdog BOOLEAN NOT NULL,
    result VARCHAR(20) DEFAULT 'pending' CHECK (result IN ('win', 'loss', 'pending', 'push')),
    points_earned INT DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- One pick per user per game
    UNIQUE(user_id, game_id)
);

CREATE INDEX idx_picks_user ON user_picks(user_id);
CREATE INDEX idx_picks_game ON user_picks(game_id);
CREATE INDEX idx_picks_result ON user_picks(result);

-- ============================================
-- ALERTS
-- ============================================

CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    game_id VARCHAR(50) NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    
    -- Alert configuration
    threshold DECIMAL(5, 2) NOT NULL CHECK (threshold >= 0 AND threshold <= 100),
    triggered BOOLEAN DEFAULT FALSE,
    triggered_at TIMESTAMPTZ,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- One alert per user per game
    UNIQUE(user_id, game_id)
);

CREATE INDEX idx_alerts_user ON alerts(user_id);
CREATE INDEX idx_alerts_triggered ON alerts(triggered);

-- ============================================
-- LEADERBOARD VIEW
-- ============================================

CREATE OR REPLACE VIEW leaderboard AS
SELECT
    u.id AS user_id,
    u.username,
    u.avatar_url,
    COUNT(p.id) AS total_picks,
    COUNT(CASE WHEN p.result = 'win' THEN 1 END) AS correct_picks,
    ROUND(
        COUNT(CASE WHEN p.result = 'win' THEN 1 END)::DECIMAL / 
        NULLIF(COUNT(CASE WHEN p.result IN ('win', 'loss') THEN 1 END), 0) * 100,
        1
    ) AS accuracy,
    SUM(COALESCE(p.points_earned, 0)) AS total_points,
    RANK() OVER (ORDER BY SUM(COALESCE(p.points_earned, 0)) DESC) AS rank
FROM users u
LEFT JOIN user_picks p ON u.id = p.user_id
GROUP BY u.id, u.username, u.avatar_url
ORDER BY total_points DESC;

-- ============================================
-- UPDATED_AT TRIGGER
-- ============================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_games_updated_at
    BEFORE UPDATE ON games
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- For Supabase - enable when migrating
-- ============================================

-- Users can only read/update their own data
-- ALTER TABLE users ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY "Users can view own profile" ON users FOR SELECT USING (auth.uid() = id);
-- CREATE POLICY "Users can update own profile" ON users FOR UPDATE USING (auth.uid() = id);

-- User picks - users can only see and create their own
-- ALTER TABLE user_picks ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY "Users can view own picks" ON user_picks FOR SELECT USING (auth.uid() = user_id);
-- CREATE POLICY "Users can create own picks" ON user_picks FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Alerts - users can only manage their own
-- ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY "Users can view own alerts" ON alerts FOR SELECT USING (auth.uid() = user_id);
-- CREATE POLICY "Users can create own alerts" ON alerts FOR INSERT WITH CHECK (auth.uid() = user_id);
-- CREATE POLICY "Users can delete own alerts" ON alerts FOR DELETE USING (auth.uid() = user_id);

-- Games, predictions, market_signals are public read
-- ALTER TABLE games ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY "Games are publicly readable" ON games FOR SELECT USING (true);

-- ALTER TABLE predictions ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY "Predictions are publicly readable" ON predictions FOR SELECT USING (true);

-- ALTER TABLE market_signals ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY "Market signals are publicly readable" ON market_signals FOR SELECT USING (true);

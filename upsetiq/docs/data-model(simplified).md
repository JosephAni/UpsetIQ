# Data Model (Simplified)

.USERS
id
email
password_hash
subscription_tier
created_at

.GAMES
id
sport
team_favorite
team_underdog
start_time
odds_open
odds_current

.PREDICTIONS
id
game_id
upset_probability
model_version
confidence_band
created_at

.USER_PICKS
-SQL
user_id
game_id
picked_underdog
result
points_earned

.MARKET_SIGNALS
ngnix
game_id
public_bet_percentage
line_movement
sentiment_score

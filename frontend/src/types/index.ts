// TypeScript interfaces matching data-model(simplified).md

export type SubscriptionTier = 'free' | 'pro' | 'premium';

export interface User {
  id: string;
  email: string;
  password_hash: string;
  subscription_tier: SubscriptionTier;
  created_at: string;
  username?: string;
  avatar_url?: string;
}

export type Sport = 'NBA' | 'NFL' | 'MLB' | 'NHL' | 'Soccer' | 'CFB';

export interface Game {
  id: string;
  sport: Sport;
  team_favorite: string;
  team_underdog: string;
  start_time: string;
  odds_open: number;
  odds_current: number;
  status?: 'upcoming' | 'live' | 'completed';
  // NFL-specific optional fields
  isPrimeTime?: boolean;
  spreadOpen?: number;
  spreadCurrent?: number;
  totalOpen?: number;
  totalCurrent?: number;
}

export interface Prediction {
  id: string;
  game_id: string;
  upset_probability: number; // 0-100
  model_version: string;
  confidence_band: number;
  created_at: string;
}

export interface UserPick {
  id: string;
  user_id: string;
  game_id: string;
  picked_underdog: boolean;
  result?: 'win' | 'loss' | 'pending';
  points_earned: number;
  created_at: string;
}

export interface MarketSignal {
  id: string;
  game_id: string;
  public_bet_percentage: number; // % of public bets on favorite
  line_movement: number; // change in line
  sentiment_score: number; // -1 to 1
  created_at: string;
}

export interface GameWithPrediction extends Game {
  prediction: Prediction;
  marketSignal: MarketSignal;
  drivers?: Array<{ label: string }>; // Key signals/drivers for the game
}

export type LeaderboardPeriod = 'weekly' | 'monthly' | 'all-time';

export interface LeaderboardEntry {
  rank: number;
  user: User;
  accuracy: number; // percentage
  points: number;
  total_picks: number;
  correct_picks: number;
}

export type AlertThreshold = number; // UPS threshold (0-100)

export interface Alert {
  id: string;
  game_id: string;
  user_id: string;
  threshold: AlertThreshold;
  triggered: boolean;
  created_at: string;
}

export interface FilterState {
  sport?: Sport;
  date?: Date;
  confidenceThreshold: number; // minimum UPS to show (default 0)
  // NFL-specific filters
  minUpsPct?: number; // UPS threshold for NFL (default 55)
  onlyPrimeTime?: boolean; // Show only prime time games
  // NBA-specific filters
  onlyNationalTv?: boolean; // Show only national TV games
  // MLB-specific filters
  onlyHighStakes?: boolean; // Show only high-stakes games
  // NHL-specific filters
  onlyMarquee?: boolean; // Show only marquee matchups
  // Soccer-specific filters
  onlyFeatured?: boolean; // Show only featured matches
  // CFB-specific filters
  onlyTopGames?: boolean; // Show only top games
}

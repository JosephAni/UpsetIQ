import { 
  User, 
  Game, 
  Prediction, 
  UserPick, 
  MarketSignal, 
  GameWithPrediction,
  LeaderboardEntry,
  Sport 
} from '../types';

// Mock Users
export const mockUsers: User[] = [
  {
    id: '1',
    email: 'alex@example.com',
    password_hash: 'hashed',
    subscription_tier: 'pro',
    created_at: '2024-01-15T10:00:00Z',
    username: 'Alex',
    avatar_url: undefined,
  },
  {
    id: '2',
    email: 'you@example.com',
    password_hash: 'hashed',
    subscription_tier: 'free',
    created_at: '2024-01-20T10:00:00Z',
    username: 'You',
    avatar_url: undefined,
  },
  {
    id: '3',
    email: 'chris@example.com',
    password_hash: 'hashed',
    subscription_tier: 'premium',
    created_at: '2024-01-10T10:00:00Z',
    username: 'Chris',
    avatar_url: undefined,
  },
];

// Mock Games
const now = new Date();
const today = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 12, 0, 0); // Today at noon
const tomorrow = new Date(today.getTime() + 24 * 60 * 60 * 1000);
const dayAfter = new Date(today.getTime() + 48 * 60 * 60 * 1000);
const day3 = new Date(today.getTime() + 3 * 24 * 60 * 60 * 1000);
const day4 = new Date(today.getTime() + 4 * 24 * 60 * 60 * 1000);
const day5 = new Date(today.getTime() + 5 * 24 * 60 * 60 * 1000);

// Helper to create date for specific day and time (for prime time games)
const createDateTime = (daysFromNow: number, hours: number, minutes: number = 0) => {
  const date = new Date(today.getTime() + daysFromNow * 24 * 60 * 60 * 1000);
  date.setHours(hours, minutes, 0, 0);
  return date.toISOString();
};

export const mockGames: Game[] = [
  // NBA games
  {
    id: '1',
    sport: 'NBA',
    team_favorite: 'Lakers',
    team_underdog: 'Nuggets',
    start_time: tomorrow.toISOString(),
    odds_open: -150,
    odds_current: -140,
    status: 'upcoming',
  },
  {
    id: '2',
    sport: 'NBA',
    team_favorite: 'Celtics',
    team_underdog: 'Heat',
    start_time: tomorrow.toISOString(),
    odds_open: -180,
    odds_current: -165,
    status: 'upcoming',
  },
  {
    id: '4',
    sport: 'NBA',
    team_favorite: 'Warriors',
    team_underdog: 'Grizzlies',
    start_time: dayAfter.toISOString(),
    odds_open: -120,
    odds_current: -105,
    status: 'upcoming',
  },
  // NFL games - spread across different days
  {
    id: '3',
    sport: 'NFL',
    team_favorite: 'Chiefs',
    team_underdog: 'Bills',
    start_time: createDateTime(5, 20, 20), // Sunday night (prime time)
    odds_open: -165,
    odds_current: -125,
    status: 'upcoming',
    isPrimeTime: true,
    spreadOpen: -3.5,
    spreadCurrent: -1.5,
    totalOpen: 47.5,
    totalCurrent: 45.0,
  },
  {
    id: '5',
    sport: 'NFL',
    team_favorite: 'Ravens',
    team_underdog: 'Steelers',
    start_time: createDateTime(1, 13, 0), // Tuesday afternoon
    odds_open: -160,
    odds_current: -145,
    status: 'upcoming',
    isPrimeTime: false,
    spreadOpen: -6.5,
    spreadCurrent: -5.0,
    totalOpen: 44.5,
    totalCurrent: 46.0,
  },
  {
    id: '6',
    sport: 'NFL',
    team_favorite: 'Eagles',
    team_underdog: 'Cowboys',
    start_time: createDateTime(2, 13, 0), // Wednesday afternoon
    odds_open: -140,
    odds_current: -120,
    status: 'upcoming',
    isPrimeTime: false,
    spreadOpen: -4.5,
    spreadCurrent: -3.0,
    totalOpen: 48.5,
    totalCurrent: 49.5,
  },
  {
    id: '7',
    sport: 'NFL',
    team_favorite: '49ers',
    team_underdog: 'Rams',
    start_time: createDateTime(3, 20, 15), // Thursday night (prime time)
    odds_open: -180,
    odds_current: -155,
    status: 'upcoming',
    isPrimeTime: true,
    spreadOpen: -7.0,
    spreadCurrent: -5.5,
    totalOpen: 46.0,
    totalCurrent: 47.5,
  },
  {
    id: '8',
    sport: 'NFL',
    team_favorite: 'Packers',
    team_underdog: 'Lions',
    start_time: createDateTime(4, 13, 0), // Friday afternoon
    odds_open: -120,
    odds_current: -105,
    status: 'upcoming',
    isPrimeTime: false,
    spreadOpen: -2.5,
    spreadCurrent: -1.0,
    totalOpen: 52.5,
    totalCurrent: 51.0,
  },
  {
    id: '9',
    sport: 'NFL',
    team_favorite: 'Dolphins',
    team_underdog: 'Jets',
    start_time: createDateTime(5, 13, 0), // Saturday afternoon
    odds_open: -150,
    odds_current: -135,
    status: 'upcoming',
    isPrimeTime: false,
    spreadOpen: -5.0,
    spreadCurrent: -4.0,
    totalOpen: 43.5,
    totalCurrent: 44.5,
  },
  {
    id: '10',
    sport: 'NFL',
    team_favorite: 'Bengals',
    team_underdog: 'Browns',
    start_time: createDateTime(6, 20, 20), // Monday night (prime time)
    odds_open: -135,
    odds_current: -115,
    status: 'upcoming',
    isPrimeTime: true,
    spreadOpen: -3.0,
    spreadCurrent: -2.0,
    totalOpen: 45.0,
    totalCurrent: 46.5,
  },
];

// Mock Predictions
export const mockPredictions: Prediction[] = [
  // NBA predictions
  {
    id: '1',
    game_id: '1',
    upset_probability: 67, // High risk
    model_version: 'v1.0',
    confidence_band: 12,
    created_at: new Date().toISOString(),
  },
  {
    id: '2',
    game_id: '2',
    upset_probability: 71, // High risk
    model_version: 'v1.0',
    confidence_band: 15,
    created_at: new Date().toISOString(),
  },
  {
    id: '4',
    game_id: '4',
    upset_probability: 45, // Low
    model_version: 'v1.0',
    confidence_band: 8,
    created_at: new Date().toISOString(),
  },
  // NFL predictions with varied UPS values
  {
    id: '3',
    game_id: '3',
    upset_probability: 62, // High risk - Prime Time
    model_version: 'v1.0',
    confidence_band: 10,
    created_at: new Date().toISOString(),
  },
  {
    id: '5',
    game_id: '5',
    upset_probability: 55, // Medium
    model_version: 'v1.0',
    confidence_band: 11,
    created_at: new Date().toISOString(),
  },
  {
    id: '6',
    game_id: '6',
    upset_probability: 58, // Medium
    model_version: 'v1.0',
    confidence_band: 9,
    created_at: new Date().toISOString(),
  },
  {
    id: '7',
    game_id: '7',
    upset_probability: 65, // High risk - Prime Time
    model_version: 'v1.0',
    confidence_band: 13,
    created_at: new Date().toISOString(),
  },
  {
    id: '8',
    game_id: '8',
    upset_probability: 52, // Medium
    model_version: 'v1.0',
    confidence_band: 10,
    created_at: new Date().toISOString(),
  },
  {
    id: '9',
    game_id: '9',
    upset_probability: 48, // Low
    model_version: 'v1.0',
    confidence_band: 8,
    created_at: new Date().toISOString(),
  },
  {
    id: '10',
    game_id: '10',
    upset_probability: 70, // High risk - Prime Time
    model_version: 'v1.0',
    confidence_band: 14,
    created_at: new Date().toISOString(),
  },
];

// Mock Market Signals
export const mockMarketSignals: MarketSignal[] = [
  // NBA signals
  {
    id: '1',
    game_id: '1',
    public_bet_percentage: 82, // 82% of public bets on Lakers
    line_movement: -10, // Line moved 10 points toward underdog
    sentiment_score: -0.3,
    created_at: new Date().toISOString(),
  },
  {
    id: '2',
    game_id: '2',
    public_bet_percentage: 75,
    line_movement: -15,
    sentiment_score: -0.2,
    created_at: new Date().toISOString(),
  },
  {
    id: '4',
    game_id: '4',
    public_bet_percentage: 55,
    line_movement: -15,
    sentiment_score: -0.1,
    created_at: new Date().toISOString(),
  },
  // NFL signals
  {
    id: '3',
    game_id: '3',
    public_bet_percentage: 78, // High public bias - Prime Time
    line_movement: -40, // Line moved 2.0 points (in spread terms)
    sentiment_score: -0.3,
    created_at: new Date().toISOString(),
  },
  {
    id: '5',
    game_id: '5',
    public_bet_percentage: 71,
    line_movement: -15,
    sentiment_score: -0.15,
    created_at: new Date().toISOString(),
  },
  {
    id: '6',
    game_id: '6',
    public_bet_percentage: 72,
    line_movement: -15,
    sentiment_score: -0.2,
    created_at: new Date().toISOString(),
  },
  {
    id: '7',
    game_id: '7',
    public_bet_percentage: 76, // High public bias - Prime Time
    line_movement: -15,
    sentiment_score: -0.25,
    created_at: new Date().toISOString(),
  },
  {
    id: '8',
    game_id: '8',
    public_bet_percentage: 65,
    line_movement: -15,
    sentiment_score: -0.1,
    created_at: new Date().toISOString(),
  },
  {
    id: '9',
    game_id: '9',
    public_bet_percentage: 68,
    line_movement: -10,
    sentiment_score: -0.1,
    created_at: new Date().toISOString(),
  },
  {
    id: '10',
    game_id: '10',
    public_bet_percentage: 74, // High public bias - Prime Time
    line_movement: -10,
    sentiment_score: -0.2,
    created_at: new Date().toISOString(),
  },
];

// Combine games with predictions and market signals
export const mockGamesWithPredictions: GameWithPrediction[] = mockGames.map(game => {
  const prediction = mockPredictions.find(p => p.game_id === game.id);
  const marketSignal = mockMarketSignals.find(m => m.game_id === game.id);
  
  if (!prediction || !marketSignal) {
    throw new Error(`Missing data for game ${game.id}`);
  }
  
  // Generate drivers based on game data
  const drivers: Array<{ label: string }> = [];
  
  if (game.sport === 'NFL') {
    if (game.spreadOpen !== undefined && game.spreadCurrent !== undefined) {
      const spreadMovement = game.spreadCurrent - game.spreadOpen;
      if (Math.abs(spreadMovement) >= 1.0) {
        drivers.push({ 
          label: `Spread moved ${Math.abs(spreadMovement).toFixed(1)} points ${spreadMovement > 0 ? 'vs' : 'toward'} favorite` 
        });
      }
    }
    
    if (marketSignal.public_bet_percentage >= 70) {
      drivers.push({ label: 'Public ≥ 70% on favorite' });
    }
    
    if (game.isPrimeTime) {
      drivers.push({ label: 'Prime time game' });
    }
  }
  
  // Add general signals
  if (marketSignal.line_movement < -10) {
    drivers.push({ label: 'Line movement against favorite' });
  }
  
  if (prediction.upset_probability > 65) {
    drivers.push({ label: 'Historical anomaly detected' });
  }
  
  // Ensure at least 3 drivers
  while (drivers.length < 3) {
    drivers.push({ label: 'Model confidence high' });
  }
  
  return {
    ...game,
    prediction,
    marketSignal,
    drivers: drivers.slice(0, 6), // Up to 6 drivers
  };
});

// Mock User Picks
export const mockUserPicks: UserPick[] = [
  {
    id: '1',
    user_id: '1',
    game_id: '1',
    picked_underdog: true,
    result: 'pending',
    points_earned: 0,
    created_at: new Date().toISOString(),
  },
  {
    id: '2',
    user_id: '2',
    game_id: '2',
    picked_underdog: false,
    result: 'pending',
    points_earned: 0,
    created_at: new Date().toISOString(),
  },
];

// Mock Leaderboard Entries
export const mockLeaderboardEntries: LeaderboardEntry[] = [
  {
    rank: 1,
    user: mockUsers[0],
    accuracy: 74,
    points: 1280,
    total_picks: 50,
    correct_picks: 37,
  },
  {
    rank: 2,
    user: mockUsers[1],
    accuracy: 71,
    points: 1190,
    total_picks: 45,
    correct_picks: 32,
  },
  {
    rank: 3,
    user: mockUsers[2],
    accuracy: 68,
    points: 1050,
    total_picks: 40,
    correct_picks: 27,
  },
];

// Helper function to get key signals for a game
export const getKeySignals = (game: GameWithPrediction): string[] => {
  // Use drivers if available, otherwise generate from market signals
  if (game.drivers && game.drivers.length > 0) {
    return game.drivers.slice(0, 3).map(d => d.label);
  }
  
  const signals: string[] = [];
  
  if (game.marketSignal.line_movement < -10) {
    signals.push('Line movement against favorite');
  }
  
  if (game.marketSignal.public_bet_percentage > 75) {
    signals.push('High public bias detected');
  }
  
  if (game.prediction.upset_probability > 65) {
    signals.push('Historical anomaly detected');
  }
  
  // Ensure we always return 3 signals
  while (signals.length < 3) {
    signals.push('Model confidence high');
  }
  
  return signals.slice(0, 3);
};

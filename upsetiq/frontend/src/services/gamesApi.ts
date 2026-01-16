/**
 * Games API service - handles all game-related API calls.
 */
import { api } from './api';
import type { GameWithPrediction, Sport } from '../types';

// API Response types
interface GamesApiResponse {
  games: ApiGame[];
  fetched_at: string;
  cached: boolean;
}

interface ApiGame {
  id: string;
  sport: string;
  team_favorite: string;
  team_underdog: string;
  start_time: string;
  odds_open: number;
  odds_current: number;
  status: 'upcoming' | 'live' | 'completed';
  isPrimeTime?: boolean;
  spreadOpen?: number;
  spreadCurrent?: number;
  totalOpen?: number;
  totalCurrent?: number;
  venue?: string;
  prediction: {
    id: string;
    game_id: string;
    upset_probability: number;
    model_version: string;
    confidence_band: number;
    created_at: string;
  };
  marketSignal: {
    id: string;
    game_id: string;
    public_bet_percentage: number;
    line_movement: number;
    sentiment_score: number;
    created_at: string;
  };
  drivers?: Array<{ label: string }>;
}

/**
 * Transform API response to match frontend types.
 */
function transformApiGame(apiGame: ApiGame): GameWithPrediction {
  return {
    id: apiGame.id,
    sport: apiGame.sport as Sport,
    team_favorite: apiGame.team_favorite,
    team_underdog: apiGame.team_underdog,
    start_time: apiGame.start_time,
    odds_open: apiGame.odds_open,
    odds_current: apiGame.odds_current,
    status: apiGame.status,
    isPrimeTime: apiGame.isPrimeTime,
    spreadOpen: apiGame.spreadOpen,
    spreadCurrent: apiGame.spreadCurrent,
    totalOpen: apiGame.totalOpen,
    totalCurrent: apiGame.totalCurrent,
    prediction: {
      id: apiGame.prediction.id,
      game_id: apiGame.prediction.game_id,
      upset_probability: apiGame.prediction.upset_probability,
      model_version: apiGame.prediction.model_version,
      confidence_band: apiGame.prediction.confidence_band,
      created_at: apiGame.prediction.created_at,
    },
    marketSignal: {
      id: apiGame.marketSignal.id,
      game_id: apiGame.marketSignal.game_id,
      public_bet_percentage: apiGame.marketSignal.public_bet_percentage,
      line_movement: apiGame.marketSignal.line_movement,
      sentiment_score: apiGame.marketSignal.sentiment_score,
      created_at: apiGame.marketSignal.created_at,
    },
    drivers: apiGame.drivers,
  };
}

/**
 * Fetch all games for a given sport.
 */
export async function fetchGames(sport: Sport = 'NFL'): Promise<{
  games: GameWithPrediction[];
  fetchedAt: string;
  cached: boolean;
}> {
  const response = await api.get<GamesApiResponse>('/games', { sport });
  
  return {
    games: response.games.map(transformApiGame),
    fetchedAt: response.fetched_at,
    cached: response.cached,
  };
}

/**
 * Fetch a single game by ID.
 */
export async function fetchGameById(gameId: string): Promise<GameWithPrediction> {
  const response = await api.get<ApiGame>(`/games/${gameId}`);
  return transformApiGame(response);
}

/**
 * Games API object for convenient access.
 */
export const gamesApi = {
  fetchGames,
  fetchGameById,
};

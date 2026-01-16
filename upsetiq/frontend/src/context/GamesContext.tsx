import React, { createContext, useContext, useState, useMemo, useEffect, useCallback, ReactNode } from 'react';
import { GameWithPrediction, FilterState, Sport } from '../types';
import { fetchGames } from '../services/gamesApi';
import { mockGamesWithPredictions } from '../data/mockData';

interface GamesContextType {
  games: GameWithPrediction[];
  filteredGames: GameWithPrediction[];
  filter: FilterState;
  setFilter: (filter: FilterState) => void;
  getGameById: (id: string) => GameWithPrediction | undefined;
  // API state
  loading: boolean;
  error: string | null;
  fetchedAt: string | null;
  cached: boolean;
  // Actions
  refreshGames: () => Promise<void>;
}

const GamesContext = createContext<GamesContextType | undefined>(undefined);

// Configuration
const USE_API = true; // Set to false to use mock data
const AUTO_REFRESH_INTERVAL = 5 * 60 * 1000; // 5 minutes

export const GamesProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [games, setGames] = useState<GameWithPrediction[]>(USE_API ? [] : mockGamesWithPredictions);
  const [filter, setFilter] = useState<FilterState>({
    confidenceThreshold: 0,
    sport: 'NFL', // Default to NFL
  });
  
  // API state
  const [loading, setLoading] = useState(USE_API);
  const [error, setError] = useState<string | null>(null);
  const [fetchedAt, setFetchedAt] = useState<string | null>(null);
  const [cached, setCached] = useState(false);

  /**
   * Fetch games from the API.
   */
  const refreshGames = useCallback(async () => {
    if (!USE_API) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const sport = filter.sport || 'NFL';
      const result = await fetchGames(sport);
      
      setGames(result.games);
      setFetchedAt(result.fetchedAt);
      setCached(result.cached);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch games';
      setError(errorMessage);
      
      // Fall back to mock data on error if we have no games
      if (games.length === 0) {
        console.warn('API failed, falling back to mock data');
        setGames(mockGamesWithPredictions);
      }
    } finally {
      setLoading(false);
    }
  }, [filter.sport, games.length]);

  // Initial fetch and refetch when sport changes
  useEffect(() => {
    if (USE_API) {
      refreshGames();
    }
  }, [filter.sport]); // Refetch when sport filter changes

  // Auto-refresh interval
  useEffect(() => {
    if (!USE_API) return;
    
    const interval = setInterval(() => {
      refreshGames();
    }, AUTO_REFRESH_INTERVAL);
    
    return () => clearInterval(interval);
  }, [refreshGames]);

  const filteredGames = useMemo(() => {
    return games.filter((game) => {
      // Filter by sport
      if (filter.sport && game.sport !== filter.sport) {
        return false;
      }

      // For NFL, use minUpsPct if specified, otherwise use confidenceThreshold
      if (game.sport === 'NFL' && filter.minUpsPct !== undefined) {
        if (game.prediction.upset_probability < filter.minUpsPct) {
          return false;
        }
      } else {
        // Filter by confidence threshold for non-NFL
        if (game.prediction.upset_probability < filter.confidenceThreshold) {
          return false;
        }
      }

      // NFL prime time filter
      if (game.sport === 'NFL' && filter.onlyPrimeTime && !game.isPrimeTime) {
        return false;
      }

      // Filter by date (if specified)
      if (filter.date) {
        const gameDate = new Date(game.start_time);
        const filterDate = new Date(filter.date);
        if (
          gameDate.getDate() !== filterDate.getDate() ||
          gameDate.getMonth() !== filterDate.getMonth() ||
          gameDate.getFullYear() !== filterDate.getFullYear()
        ) {
          return false;
        }
      }

      return true;
    });
  }, [games, filter]);

  const getGameById = (id: string) => {
    return games.find((game) => game.id === id);
  };

  return (
    <GamesContext.Provider
      value={{
        games,
        filteredGames,
        filter,
        setFilter,
        getGameById,
        loading,
        error,
        fetchedAt,
        cached,
        refreshGames,
      }}
    >
      {children}
    </GamesContext.Provider>
  );
};

export const useGames = () => {
  const context = useContext(GamesContext);
  if (!context) {
    throw new Error('useGames must be used within a GamesProvider');
  }
  return context;
};

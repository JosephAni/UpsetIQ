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

      // Use minUpsPct if specified (for all sports with sport-specific filters), otherwise use confidenceThreshold
      if (filter.minUpsPct !== undefined) {
        if (game.prediction.upset_probability < filter.minUpsPct) {
          return false;
        }
      } else {
        // Filter by confidence threshold
        if (game.prediction.upset_probability < filter.confidenceThreshold) {
          return false;
        }
      }

      // NFL prime time filter
      if (game.sport === 'NFL' && filter.onlyPrimeTime && !game.isPrimeTime) {
        return false;
      }

      // NBA national TV filter (using highest UPS games as proxy)
      // Note: You may want to add an isNationalTv field to Game type later
      if (game.sport === 'NBA' && filter.onlyNationalTv) {
        // For now, assume top 30% of games by UPS are "national TV"
        const allNbaGames = games.filter(g => g.sport === 'NBA');
        const sorted = [...allNbaGames].sort((a, b) => b.prediction.upset_probability - a.prediction.upset_probability);
        const threshold = sorted[Math.floor(sorted.length * 0.3)]?.prediction.upset_probability ?? 0;
        if (game.prediction.upset_probability < threshold) {
          return false;
        }
      }

      // MLB high-stakes filter (using highest UPS games as proxy)
      if (game.sport === 'MLB' && filter.onlyHighStakes) {
        const allMlbGames = games.filter(g => g.sport === 'MLB');
        const sorted = [...allMlbGames].sort((a, b) => b.prediction.upset_probability - a.prediction.upset_probability);
        const threshold = sorted[Math.floor(sorted.length * 0.3)]?.prediction.upset_probability ?? 0;
        if (game.prediction.upset_probability < threshold) {
          return false;
        }
      }

      // NHL marquee filter (using highest UPS games as proxy)
      if (game.sport === 'NHL' && filter.onlyMarquee) {
        const allNhlGames = games.filter(g => g.sport === 'NHL');
        const sorted = [...allNhlGames].sort((a, b) => b.prediction.upset_probability - a.prediction.upset_probability);
        const threshold = sorted[Math.floor(sorted.length * 0.3)]?.prediction.upset_probability ?? 0;
        if (game.prediction.upset_probability < threshold) {
          return false;
        }
      }

      // Soccer featured filter (using highest UPS games as proxy)
      if (game.sport === 'Soccer' && filter.onlyFeatured) {
        const allSoccerGames = games.filter(g => g.sport === 'Soccer');
        const sorted = [...allSoccerGames].sort((a, b) => b.prediction.upset_probability - a.prediction.upset_probability);
        const threshold = sorted[Math.floor(sorted.length * 0.3)]?.prediction.upset_probability ?? 0;
        if (game.prediction.upset_probability < threshold) {
          return false;
        }
      }

      // CFB top games filter (using highest UPS games as proxy)
      if (game.sport === 'CFB' && filter.onlyTopGames) {
        const allCfbGames = games.filter(g => g.sport === 'CFB');
        const sorted = [...allCfbGames].sort((a, b) => b.prediction.upset_probability - a.prediction.upset_probability);
        const threshold = sorted[Math.floor(sorted.length * 0.3)]?.prediction.upset_probability ?? 0;
        if (game.prediction.upset_probability < threshold) {
          return false;
        }
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

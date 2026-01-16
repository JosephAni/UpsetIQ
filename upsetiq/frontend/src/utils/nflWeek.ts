import type { Game, GameWithPrediction } from '../types';

export type WeekGroup = { label: string; games: GameWithPrediction[] };

/**
 * Groups NFL games by day of the week, only showing days that have games
 * Adapted to use existing GameWithPrediction type structure
 */
export function groupGamesByDayThisWeek(games: GameWithPrediction[]): WeekGroup[] {
  const byDay = new Map<string, GameWithPrediction[]>();

  for (const g of games) {
    if (g.sport !== 'NFL') continue;
    
    const d = new Date(g.start_time);
    const label = d.toLocaleDateString(undefined, { 
      weekday: 'long', 
      month: 'short', 
      day: 'numeric' 
    });

    const arr = byDay.get(label) ?? [];
    arr.push(g);
    byDay.set(label, arr);
  }

  // Sort games within each day by upset_probability desc (highest UPS first)
  const groups: WeekGroup[] = [...byDay.entries()].map(([label, arr]) => ({
    label,
    games: arr.sort((a, b) => b.prediction.upset_probability - a.prediction.upset_probability)
  }));

  // Sort groups chronologically by first game time
  groups.sort((a, b) => {
    const ta = new Date(a.games[0]?.start_time ?? 0).getTime();
    const tb = new Date(b.games[0]?.start_time ?? 0).getTime();
    return ta - tb;
  });

  return groups;
}

/**
 * Filters NFL games by UPS threshold and optionally prime time only
 * Adapted to work with existing GameWithPrediction structure
 */
export function filterNflGames(
  games: GameWithPrediction[], 
  minUpsPct: number, 
  onlyPrimeTime: boolean
): GameWithPrediction[] {
  return games.filter((g) => {
    if (g.sport !== 'NFL') return false;
    
    // Filter by UPS threshold (prediction.upset_probability is 0-100)
    if (g.prediction.upset_probability < minUpsPct) return false;
    
    // Filter by prime time if requested
    if (onlyPrimeTime && !g.isPrimeTime) return false;
    
    return true;
  });
}

/**
 * Gets prime time NFL games (Thu/Sun/Mon night)
 * Sorted by highest UPS first, limited to top results
 */
export function getPrimeTimeGames(
  games: GameWithPrediction[], 
  limit: number = 3
): GameWithPrediction[] {
  return games
    .filter((g) => g.sport === 'NFL' && g.isPrimeTime)
    .sort((a, b) => b.prediction.upset_probability - a.prediction.upset_probability)
    .slice(0, limit);
}

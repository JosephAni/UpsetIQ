import type { GameWithPrediction, Sport } from '../types';

export type DayGroup = { label: string; games: GameWithPrediction[] };

/**
 * Groups games by day of the week for any sport
 */
export function groupGamesByDay(games: GameWithPrediction[], sport: Sport): DayGroup[] {
  const byDay = new Map<string, GameWithPrediction[]>();

  for (const g of games) {
    if (g.sport !== sport) continue;
    
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
  const groups: DayGroup[] = [...byDay.entries()].map(([label, arr]) => ({
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
 * Groups games by this week (next 7 days) for any sport
 */
export function groupGamesByDayThisWeek(games: GameWithPrediction[], sport: Sport): DayGroup[] {
  const now = new Date();
  const weekFromNow = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);
  
  const thisWeekGames = games.filter((g) => {
    if (g.sport !== sport) return false;
    const gameDate = new Date(g.start_time);
    return gameDate >= now && gameDate <= weekFromNow;
  });
  
  return groupGamesByDay(thisWeekGames, sport);
}

/**
 * NBA-specific: Groups games by today's slate, tomorrow, etc.
 */
export function groupNbaGamesByDay(games: GameWithPrediction[]): DayGroup[] {
  return groupGamesByDayThisWeek(games, 'NBA');
}

/**
 * NBA-specific: Gets national TV games (featured matchups)
 */
export function getNationalTvGames(
  games: GameWithPrediction[],
  limit: number = 5
): GameWithPrediction[] {
  // Assuming national TV games are those with highest UPS or special matchups
  // You can add a flag to Game type later if needed
  return games
    .filter((g) => g.sport === 'NBA')
    .sort((a, b) => b.prediction.upset_probability - a.prediction.upset_probability)
    .slice(0, limit);
}

/**
 * MLB-specific: Groups games by day with series grouping
 */
export function groupMlbGamesByDay(games: GameWithPrediction[]): DayGroup[] {
  return groupGamesByDayThisWeek(games, 'MLB');
}

/**
 * MLB-specific: Gets high-stakes games (division races, playoff implications)
 */
export function getHighStakesGames(
  games: GameWithPrediction[],
  limit: number = 5
): GameWithPrediction[] {
  // High stakes typically have higher UPS
  return games
    .filter((g) => g.sport === 'MLB')
    .sort((a, b) => b.prediction.upset_probability - a.prediction.upset_probability)
    .slice(0, limit);
}

/**
 * NHL-specific: Groups games by day
 */
export function groupNhlGamesByDay(games: GameWithPrediction[]): DayGroup[] {
  return groupGamesByDayThisWeek(games, 'NHL');
}

/**
 * NHL-specific: Gets marquee matchups (rivalries, playoff implications)
 */
export function getMarqueeGames(
  games: GameWithPrediction[],
  limit: number = 5
): GameWithPrediction[] {
  return games
    .filter((g) => g.sport === 'NHL')
    .sort((a, b) => b.prediction.upset_probability - a.prediction.upset_probability)
    .slice(0, limit);
}

/**
 * Soccer-specific: Groups games by day
 */
export function groupSoccerGamesByDay(games: GameWithPrediction[]): DayGroup[] {
  return groupGamesByDayThisWeek(games, 'Soccer');
}

/**
 * Soccer-specific: Gets featured matches (top leagues, cup games)
 */
export function getFeaturedMatches(
  games: GameWithPrediction[],
  limit: number = 5
): GameWithPrediction[] {
  return games
    .filter((g) => g.sport === 'Soccer')
    .sort((a, b) => b.prediction.upset_probability - a.prediction.upset_probability)
    .slice(0, limit);
}

/**
 * CFB-specific: Groups games by day with week grouping
 */
export function groupCfbGamesByDay(games: GameWithPrediction[]): DayGroup[] {
  return groupGamesByDayThisWeek(games, 'CFB');
}

/**
 * CFB-specific: Gets top games (ranked matchups, rivalry games)
 */
export function getTopGames(
  games: GameWithPrediction[],
  limit: number = 5
): GameWithPrediction[] {
  return games
    .filter((g) => g.sport === 'CFB')
    .sort((a, b) => b.prediction.upset_probability - a.prediction.upset_probability)
    .slice(0, limit);
}

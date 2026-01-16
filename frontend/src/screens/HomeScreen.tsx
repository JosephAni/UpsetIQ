import React, { useMemo } from 'react';
import {
  View,
  Text,
  FlatList,
  ScrollView,
  TouchableOpacity,
  SafeAreaView,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { FilterBar } from '../components/FilterBar';
import { NflFilters } from '../components/NflFilters';
import { NbaFilters } from '../components/NbaFilters';
import { MlbFilters } from '../components/MlbFilters';
import { NhlFilters } from '../components/NhlFilters';
import { SoccerFilters } from '../components/SoccerFilters';
import { CfbFilters } from '../components/CfbFilters';
import { UpsetCard } from '../components/cards/UpsetCard';
import { useGames } from '../context/GamesContext';
import { useAlerts } from '../context/AlertsContext';
import type { GameWithPrediction } from '../types';
import { groupGamesByDayThisWeek, getPrimeTimeGames } from '../utils/nflWeek';
import {
  groupNbaGamesByDay,
  getNationalTvGames,
  groupMlbGamesByDay,
  getHighStakesGames,
  groupNhlGamesByDay,
  getMarqueeGames,
  groupSoccerGamesByDay,
  getFeaturedMatches,
  groupCfbGamesByDay,
  getTopGames,
} from '../utils/sportUtils';

type RootStackParamList = {
  Home: undefined;
  GameDetail: { gameId: string };
  Alerts: undefined;
};

type HomeScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'Home'>;

export const HomeScreen: React.FC = () => {
  const navigation = useNavigation<HomeScreenNavigationProp>();
  const { 
    filteredGames, 
    filter, 
    setFilter, 
    loading, 
    error, 
    fetchedAt, 
    cached, 
    refreshGames 
  } = useGames();
  const { addAlert } = useAlerts();

  const currentSport = filter.sport;
  const isNflMode = currentSport === 'NFL';
  const isNbaMode = currentSport === 'NBA';
  const isMlbMode = currentSport === 'MLB';
  const isNhlMode = currentSport === 'NHL';
  const isSoccerMode = currentSport === 'Soccer';
  const isCfbMode = currentSport === 'CFB';
  const isSportMode = isNflMode || isNbaMode || isMlbMode || isNhlMode || isSoccerMode || isCfbMode;

  // Sport-specific filter state
  const minUpsPct = filter.minUpsPct ?? 55;
  const onlyPrimeTime = filter.onlyPrimeTime ?? false;
  const onlyNationalTv = filter.onlyNationalTv ?? false;
  const onlyHighStakes = filter.onlyHighStakes ?? false;
  const onlyMarquee = filter.onlyMarquee ?? false;
  const onlyFeatured = filter.onlyFeatured ?? false;
  const onlyTopGames = filter.onlyTopGames ?? false;

  const handleCardPress = (gameId: string) => {
    navigation.navigate('GameDetail', { gameId });
  };

  const handleTrack = (gameId: string) => {
    console.log('Track game:', gameId);
  };

  const handleAlert = (gameId: string) => {
    const game = filteredGames.find((g) => g.id === gameId);
    if (game) {
      addAlert(gameId, game.prediction.upset_probability);
    }
  };

  const handleAlertsPress = () => {
    navigation.navigate('Alerts');
  };

  const handleNflFilterChange = (newMinUpsPct: number, newOnlyPrimeTime: boolean) => {
    setFilter({
      ...filter,
      minUpsPct: newMinUpsPct,
      onlyPrimeTime: newOnlyPrimeTime,
    });
  };

  const handleNbaFilterChange = (newMinUpsPct: number, newOnlyNationalTv: boolean) => {
    setFilter({
      ...filter,
      minUpsPct: newMinUpsPct,
      onlyNationalTv: newOnlyNationalTv,
    });
  };

  const handleMlbFilterChange = (newMinUpsPct: number, newOnlyHighStakes: boolean) => {
    setFilter({
      ...filter,
      minUpsPct: newMinUpsPct,
      onlyHighStakes: newOnlyHighStakes,
    });
  };

  const handleNhlFilterChange = (newMinUpsPct: number, newOnlyMarquee: boolean) => {
    setFilter({
      ...filter,
      minUpsPct: newMinUpsPct,
      onlyMarquee: newOnlyMarquee,
    });
  };

  const handleSoccerFilterChange = (newMinUpsPct: number, newOnlyFeatured: boolean) => {
    setFilter({
      ...filter,
      minUpsPct: newMinUpsPct,
      onlyFeatured: newOnlyFeatured,
    });
  };

  const handleCfbFilterChange = (newMinUpsPct: number, newOnlyTopGames: boolean) => {
    setFilter({
      ...filter,
      minUpsPct: newMinUpsPct,
      onlyTopGames: newOnlyTopGames,
    });
  };

  // NFL weekly grouping
  const nflGroups = useMemo(() => {
    if (!isNflMode) return [];
    return groupGamesByDayThisWeek(filteredGames);
  }, [isNflMode, filteredGames]);

  const primeTimeGames = useMemo(() => {
    if (!isNflMode) return [];
    return getPrimeTimeGames(filteredGames);
  }, [isNflMode, filteredGames]);

  // NBA grouping
  const nbaGroups = useMemo(() => {
    if (!isNbaMode) return [];
    return groupNbaGamesByDay(filteredGames);
  }, [isNbaMode, filteredGames]);

  const nationalTvGames = useMemo(() => {
    if (!isNbaMode) return [];
    return getNationalTvGames(filteredGames);
  }, [isNbaMode, filteredGames]);

  // MLB grouping
  const mlbGroups = useMemo(() => {
    if (!isMlbMode) return [];
    return groupMlbGamesByDay(filteredGames);
  }, [isMlbMode, filteredGames]);

  const highStakesGames = useMemo(() => {
    if (!isMlbMode) return [];
    return getHighStakesGames(filteredGames);
  }, [isMlbMode, filteredGames]);

  // NHL grouping
  const nhlGroups = useMemo(() => {
    if (!isNhlMode) return [];
    return groupNhlGamesByDay(filteredGames);
  }, [isNhlMode, filteredGames]);

  const marqueeGames = useMemo(() => {
    if (!isNhlMode) return [];
    return getMarqueeGames(filteredGames);
  }, [isNhlMode, filteredGames]);

  // Soccer grouping
  const soccerGroups = useMemo(() => {
    if (!isSoccerMode) return [];
    return groupSoccerGamesByDay(filteredGames);
  }, [isSoccerMode, filteredGames]);

  const featuredMatches = useMemo(() => {
    if (!isSoccerMode) return [];
    return getFeaturedMatches(filteredGames);
  }, [isSoccerMode, filteredGames]);

  // CFB grouping
  const cfbGroups = useMemo(() => {
    if (!isCfbMode) return [];
    return groupCfbGamesByDay(filteredGames);
  }, [isCfbMode, filteredGames]);

  const topGames = useMemo(() => {
    if (!isCfbMode) return [];
    return getTopGames(filteredGames);
  }, [isCfbMode, filteredGames]);

  // Format fetched time for display
  const lastUpdated = useMemo(() => {
    if (!fetchedAt) return null;
    try {
      const date = new Date(fetchedAt);
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return null;
    }
  }, [fetchedAt]);

  // Loading state component
  const renderLoading = () => (
    <View className="flex-1 items-center justify-center py-20">
      <ActivityIndicator size="large" color="#5B8CFF" />
      <Text className="text-base text-text-muted mt-4">Loading games...</Text>
    </View>
  );

  // Error state component
  const renderError = () => (
    <View className="flex-1 items-center justify-center py-20 px-8">
      <Text className="text-4xl mb-4">⚠️</Text>
      <Text className="text-lg text-text-primary text-center font-semibold mb-2">
        Unable to load games
      </Text>
      <Text className="text-sm text-text-muted text-center mb-6">
        {error}
      </Text>
      <TouchableOpacity
        className="bg-primary px-6 py-3 rounded-lg"
        onPress={refreshGames}
        activeOpacity={0.8}
      >
        <Text className="text-white font-semibold">Try Again</Text>
      </TouchableOpacity>
    </View>
  );

  // Empty state component
  const renderEmpty = () => {
    const emoji = isNflMode ? '🏈' : isNbaMode ? '🏀' : isMlbMode ? '⚾' : isNhlMode ? '🏒' : isSoccerMode ? '⚽' : isCfbMode ? '🏈' : '📊';
    return (
      <View className="items-center py-8">
        <Text className="text-4xl mb-4">{emoji}</Text>
        <Text className="text-base text-text-muted text-center">
          {isSportMode 
            ? `No ${currentSport} games match your filters` 
            : 'No games available for this sport'}
        </Text>
      </View>
    );
  };

  // Generic sport view renderer
  const renderSportView = (
    featuredGames: GameWithPrediction[],
    groups: Array<{ label: string; games: GameWithPrediction[] }>,
    featuredTitle: string
  ) => {
    if (loading && filteredGames.length === 0) {
      return renderLoading();
    }

    if (error && filteredGames.length === 0) {
      return renderError();
    }

    return (
      <ScrollView
        contentContainerStyle={{ padding: 16 }}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={loading}
            onRefresh={refreshGames}
            tintColor="#5B8CFF"
            colors={['#5B8CFF']}
          />
        }
      >
        <View className="gap-4">
          {/* Featured Games Section */}
          {featuredGames.length > 0 && (
            <View className="gap-3">
              <Text className="text-base font-extrabold text-text-primary">
                {featuredTitle}
              </Text>
              {featuredGames.map((game) => (
                <UpsetCard
                  key={game.id}
                  game={game}
                  onPress={() => handleCardPress(game.id)}
                  onTrack={() => handleTrack(game.id)}
                  onAlert={() => handleAlert(game.id)}
                />
              ))}
            </View>
          )}

          {/* Day-by-Day Sections */}
          {groups.map((group) => (
            <View key={group.label} className="gap-3">
              <Text className="text-base font-extrabold text-text-primary">
                {group.label}
              </Text>
              {group.games.map((game) => (
                <UpsetCard
                  key={game.id}
                  game={game}
                  onPress={() => handleCardPress(game.id)}
                  onTrack={() => handleTrack(game.id)}
                  onAlert={() => handleAlert(game.id)}
                />
              ))}
            </View>
          ))}

          {groups.length === 0 && featuredGames.length === 0 && renderEmpty()}
        </View>
      </ScrollView>
    );
  };

  const renderNflView = () => {
    return renderSportView(primeTimeGames, nflGroups, 'Prime Time Risk');
  };

  const renderNbaView = () => {
    return renderSportView(nationalTvGames, nbaGroups, 'National TV Games');
  };

  const renderMlbView = () => {
    return renderSportView(highStakesGames, mlbGroups, 'High-Stakes Games');
  };

  const renderNhlView = () => {
    return renderSportView(marqueeGames, nhlGroups, 'Marquee Matchups');
  };

  const renderSoccerView = () => {
    return renderSportView(featuredMatches, soccerGroups, 'Featured Matches');
  };

  const renderCfbView = () => {
    return renderSportView(topGames, cfbGroups, 'Top Games');
  };

  const renderRegularView = () => {
    if (loading && filteredGames.length === 0) {
      return renderLoading();
    }

    if (error && filteredGames.length === 0) {
      return renderError();
    }

    return (
      <FlatList
        data={filteredGames}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <UpsetCard
            game={item}
            onPress={() => handleCardPress(item.id)}
            onTrack={() => handleTrack(item.id)}
            onAlert={() => handleAlert(item.id)}
          />
        )}
        contentContainerStyle={{ padding: 16 }}
        showsVerticalScrollIndicator={false}
        ListEmptyComponent={renderEmpty}
        refreshControl={
          <RefreshControl
            refreshing={loading}
            onRefresh={refreshGames}
            tintColor="#5B8CFF"
            colors={['#5B8CFF']}
          />
        }
      />
    );
  };

  return (
    <SafeAreaView className="flex-1 bg-background">
      {/* Header */}
      <View className="p-4 items-center border-b border-border">
        <View className="flex-row justify-between items-baseline w-full">
          <Text className="text-xl font-semibold text-text-primary tracking-wider">
            UpsetIQ
          </Text>
          <View className="flex-row items-center gap-2">
            {cached && (
              <View className="bg-warning/20 px-2 py-0.5 rounded">
                <Text className="text-xs text-warning">Cached</Text>
              </View>
            )}
            {lastUpdated && (
              <Text className="text-xs text-text-muted">
                Updated {lastUpdated}
              </Text>
            )}
          </View>
        </View>
        {isSportMode && currentSport && (
          <Text className="text-xs text-text-muted self-start mt-1">
            {currentSport} • This week
          </Text>
        )}
      </View>

      <FilterBar onFilterChange={setFilter} currentFilter={filter} />

      {/* Sport-specific Filters */}
      {isNflMode && (
        <NflFilters
          minUpsPct={minUpsPct}
          setMinUpsPct={(value) => handleNflFilterChange(value, onlyPrimeTime)}
          onlyPrimeTime={onlyPrimeTime}
          setOnlyPrimeTime={(value) => handleNflFilterChange(minUpsPct, value)}
        />
      )}
      {isNbaMode && (
        <NbaFilters
          minUpsPct={minUpsPct}
          setMinUpsPct={(value) => handleNbaFilterChange(value, onlyNationalTv)}
          onlyNationalTv={onlyNationalTv}
          setOnlyNationalTv={(value) => handleNbaFilterChange(minUpsPct, value)}
        />
      )}
      {isMlbMode && (
        <MlbFilters
          minUpsPct={minUpsPct}
          setMinUpsPct={(value) => handleMlbFilterChange(value, onlyHighStakes)}
          onlyHighStakes={onlyHighStakes}
          setOnlyHighStakes={(value) => handleMlbFilterChange(minUpsPct, value)}
        />
      )}
      {isNhlMode && (
        <NhlFilters
          minUpsPct={minUpsPct}
          setMinUpsPct={(value) => handleNhlFilterChange(value, onlyMarquee)}
          onlyMarquee={onlyMarquee}
          setOnlyMarquee={(value) => handleNhlFilterChange(minUpsPct, value)}
        />
      )}
      {isSoccerMode && (
        <SoccerFilters
          minUpsPct={minUpsPct}
          setMinUpsPct={(value) => handleSoccerFilterChange(value, onlyFeatured)}
          onlyFeatured={onlyFeatured}
          setOnlyFeatured={(value) => handleSoccerFilterChange(minUpsPct, value)}
        />
      )}
      {isCfbMode && (
        <CfbFilters
          minUpsPct={minUpsPct}
          setMinUpsPct={(value) => handleCfbFilterChange(value, onlyTopGames)}
          onlyTopGames={onlyTopGames}
          setOnlyTopGames={(value) => handleCfbFilterChange(minUpsPct, value)}
        />
      )}

      {/* Conditionally render sport-specific view or regular flat list */}
      {isNflMode ? renderNflView() : 
       isNbaMode ? renderNbaView() :
       isMlbMode ? renderMlbView() :
       isNhlMode ? renderNhlView() :
       isSoccerMode ? renderSoccerView() :
       isCfbMode ? renderCfbView() :
       renderRegularView()}

      {/* Floating Alerts Button */}
      <TouchableOpacity
        className="absolute bottom-8 right-4 w-14 h-14 rounded-full bg-primary items-center justify-center"
        onPress={handleAlertsPress}
        activeOpacity={0.8}
        style={{
          shadowColor: '#5B8CFF',
          shadowOffset: { width: 0, height: 4 },
          shadowOpacity: 0.3,
          shadowRadius: 8,
          elevation: 8,
        }}
      >
        <Text className="text-2xl">🚨</Text>
      </TouchableOpacity>
    </SafeAreaView>
  );
};

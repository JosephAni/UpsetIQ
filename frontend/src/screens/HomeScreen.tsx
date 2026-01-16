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
import { UpsetCard } from '../components/cards/UpsetCard';
import { useGames } from '../context/GamesContext';
import { useAlerts } from '../context/AlertsContext';
import { groupGamesByDayThisWeek, getPrimeTimeGames } from '../utils/nflWeek';

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

  const isNflMode = filter.sport === 'NFL';

  // NFL-specific filter state
  const minUpsPct = filter.minUpsPct ?? 55;
  const onlyPrimeTime = filter.onlyPrimeTime ?? false;

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

  // NFL weekly grouping
  const nflGroups = useMemo(() => {
    if (!isNflMode) return [];
    return groupGamesByDayThisWeek(filteredGames);
  }, [isNflMode, filteredGames]);

  const primeTimeGames = useMemo(() => {
    if (!isNflMode) return [];
    return getPrimeTimeGames(filteredGames);
  }, [isNflMode, filteredGames]);

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
  const renderEmpty = () => (
    <View className="items-center py-8">
      <Text className="text-4xl mb-4">🏈</Text>
      <Text className="text-base text-text-muted text-center">
        {isNflMode 
          ? 'No NFL games match your filters' 
          : 'No games available for this sport'}
      </Text>
    </View>
  );

  const renderNflView = () => {
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
          {/* Prime Time Risk Section */}
          {primeTimeGames.length > 0 && (
            <View className="gap-3">
              <Text className="text-base font-extrabold text-text-primary">
                Prime Time Risk
              </Text>
              {primeTimeGames.map((game) => (
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
          {nflGroups.map((group) => (
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

          {nflGroups.length === 0 && primeTimeGames.length === 0 && renderEmpty()}
        </View>
      </ScrollView>
    );
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
        {isNflMode && (
          <Text className="text-xs text-text-muted self-start mt-1">
            NFL • This week
          </Text>
        )}
      </View>

      <FilterBar onFilterChange={setFilter} currentFilter={filter} />

      {/* NFL Filters - only show when NFL is selected */}
      {isNflMode && (
        <NflFilters
          minUpsPct={minUpsPct}
          setMinUpsPct={(value) => handleNflFilterChange(value, onlyPrimeTime)}
          onlyPrimeTime={onlyPrimeTime}
          setOnlyPrimeTime={(value) => handleNflFilterChange(minUpsPct, value)}
        />
      )}

      {/* Conditionally render NFL weekly view or regular flat list */}
      {isNflMode ? renderNflView() : renderRegularView()}

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

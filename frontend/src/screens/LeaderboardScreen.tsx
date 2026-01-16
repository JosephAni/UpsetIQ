import React, { useState } from 'react';
import {
  View,
  Text,
  FlatList,
  SafeAreaView,
  TouchableOpacity,
} from 'react-native';
import { mockLeaderboardEntries } from '../data/mockData';
import { LeaderboardPeriod } from '../types';

const periods: LeaderboardPeriod[] = ['weekly', 'monthly', 'all-time'];

export const LeaderboardScreen: React.FC = () => {
  const [selectedPeriod, setSelectedPeriod] = useState<LeaderboardPeriod>('all-time');

  const entries = mockLeaderboardEntries;

  const renderEntry = ({ item, index }: { item: typeof entries[0]; index: number }) => {
    const isCurrentUser = index === 1;

    return (
      <View
        className={`flex-row items-center bg-card p-4 rounded-2xl mb-2 ${
          isCurrentUser ? 'border-2 border-primary' : ''
        }`}
      >
        <View className="w-10 items-center">
          <View
            className={`w-8 h-8 rounded-full items-center justify-center ${
              index < 3 ? 'bg-warning' : 'bg-border'
            }`}
          >
            <Text
              className={`text-sm font-semibold ${
                index < 3 ? 'text-text-primary' : 'text-text-muted'
              }`}
            >
              {item.rank}
            </Text>
          </View>
        </View>

        <View className="ml-2">
          <View className="w-12 h-12 rounded-full bg-primary items-center justify-center">
            <Text className="text-lg font-semibold text-text-primary">
              {item.user.username?.[0]?.toUpperCase() || 'U'}
            </Text>
          </View>
        </View>

        <View className="flex-1 ml-4">
          <Text className="text-base text-text-primary font-semibold mb-1">
            {item.user.username}
          </Text>
          <Text className="text-sm text-text-muted">
            {item.correct_picks}/{item.total_picks} picks
          </Text>
        </View>

        <View className="items-end">
          <Text className="text-xl font-bold text-primary mb-1">{item.accuracy}%</Text>
          <Text className="text-sm text-text-muted">{item.points} pts</Text>
        </View>
      </View>
    );
  };

  return (
    <SafeAreaView className="flex-1 bg-background">
      <View className="p-4 items-center border-b border-border">
        <Text className="text-2xl font-semibold text-text-primary">Leaderboard</Text>
      </View>

      {/* Period Selector */}
      <View className="flex-row p-4 gap-2">
        {periods.map((period) => (
          <TouchableOpacity
            key={period}
            className={`flex-1 py-2 px-4 rounded-2xl items-center border ${
              selectedPeriod === period
                ? 'bg-primary border-primary'
                : 'bg-card border-border'
            }`}
            onPress={() => setSelectedPeriod(period)}
          >
            <Text
              className={`text-base font-medium ${
                selectedPeriod === period ? 'text-text-primary font-semibold' : 'text-text-muted'
              }`}
            >
              {period.charAt(0).toUpperCase() + period.slice(1)}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <FlatList
        data={entries}
        keyExtractor={(item) => item.user.id}
        renderItem={renderEntry}
        contentContainerStyle={{ padding: 16 }}
      />
    </SafeAreaView>
  );
};

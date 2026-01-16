import React from 'react';
import {
  View,
  Text,
  ScrollView,
  SafeAreaView,
} from 'react-native';
import { useUser } from '../context/UserContext';
import { mockUserPicks } from '../data/mockData';

export const ProfileScreen: React.FC = () => {
  const { currentUser } = useUser();

  if (!currentUser) {
    return (
      <SafeAreaView className="flex-1 bg-background">
        <Text className="text-base text-text-primary text-center mt-8">
          Please log in to view profile
        </Text>
      </SafeAreaView>
    );
  }

  const totalPicks = mockUserPicks.length;
  const correctPicks = mockUserPicks.filter((pick) => pick.result === 'win').length;
  const accuracy = totalPicks > 0 ? Math.round((correctPicks / totalPicks) * 100) : 0;

  return (
    <SafeAreaView className="flex-1 bg-background">
      <ScrollView className="flex-1">
        <View className="items-center p-8 border-b border-border">
          <View className="w-20 h-20 rounded-full bg-primary items-center justify-center mb-4">
            <Text className="text-4xl font-bold text-text-primary">
              {currentUser.username?.[0]?.toUpperCase() || 'U'}
            </Text>
          </View>
          <Text className="text-xl font-semibold text-text-primary mb-2">
            {currentUser.username || currentUser.email}
          </Text>
          <View className="px-4 py-1 rounded-full bg-primary">
            <Text className="text-sm text-text-primary font-semibold">
              {currentUser.subscription_tier.toUpperCase()}
            </Text>
          </View>
        </View>

        {/* Accuracy Stats */}
        <View className="p-4">
          <Text className="text-lg font-semibold text-text-primary mb-4">Accuracy</Text>
          <View className="flex-row gap-4">
            <View className="flex-1 bg-card p-4 rounded-2xl items-center">
              <Text className="text-4xl font-bold text-primary mb-1">{accuracy}%</Text>
              <Text className="text-sm text-text-muted">Accuracy</Text>
            </View>
            <View className="flex-1 bg-card p-4 rounded-2xl items-center">
              <Text className="text-4xl font-bold text-primary mb-1">{totalPicks}</Text>
              <Text className="text-sm text-text-muted">Total Picks</Text>
            </View>
            <View className="flex-1 bg-card p-4 rounded-2xl items-center">
              <Text className="text-4xl font-bold text-primary mb-1">{correctPicks}</Text>
              <Text className="text-sm text-text-muted">Correct</Text>
            </View>
          </View>
        </View>

        {/* Accuracy Chart Placeholder */}
        <View className="p-4 mt-2">
          <Text className="text-lg font-semibold text-text-primary mb-4">Accuracy Over Time</Text>
          <View className="bg-card p-8 rounded-2xl items-center min-h-[200px] justify-center">
            <Text className="text-base text-text-primary mb-1">
              Chart visualization will appear here
            </Text>
            <Text className="text-sm text-text-muted">
              (Chart library integration pending)
            </Text>
          </View>
        </View>

        {/* Pick History */}
        <View className="p-4">
          <Text className="text-lg font-semibold text-text-primary mb-4">Recent Picks</Text>
          {mockUserPicks.length > 0 ? (
            mockUserPicks.map((pick) => (
              <View
                key={pick.id}
                className="flex-row justify-between items-center bg-card p-4 rounded-2xl mb-2"
              >
                <View className="flex-1">
                  <Text className="text-base text-text-primary mb-1">Game #{pick.game_id}</Text>
                  <Text className="text-sm text-text-muted">
                    {new Date(pick.created_at).toLocaleDateString()}
                  </Text>
                </View>
                <View className="items-end">
                  <Text
                    className={`text-base font-semibold mb-1 ${
                      pick.result === 'win'
                        ? 'text-success'
                        : pick.result === 'loss'
                        ? 'text-danger'
                        : 'text-text-muted'
                    }`}
                  >
                    {pick.result === 'win'
                      ? '✓ Win'
                      : pick.result === 'loss'
                      ? '✗ Loss'
                      : 'Pending'}
                  </Text>
                  {pick.points_earned > 0 && (
                    <Text className="text-sm text-primary">+{pick.points_earned} pts</Text>
                  )}
                </View>
              </View>
            ))
          ) : (
            <Text className="text-base text-text-muted text-center p-8">No picks yet</Text>
          )}
        </View>

        {/* Referral Section */}
        <View className="p-4 mb-8">
          <Text className="text-lg font-semibold text-text-primary mb-4">Referral Code</Text>
          <View className="bg-card p-4 rounded-2xl items-center mb-2">
            <Text className="text-xl font-semibold text-primary tracking-widest">
              {currentUser.username?.toUpperCase().slice(0, 6) || 'USER01'}
            </Text>
          </View>
          <Text className="text-sm text-text-muted text-center">
            Share this code with friends to earn rewards!
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

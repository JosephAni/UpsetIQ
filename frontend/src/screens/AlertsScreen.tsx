import React from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  SafeAreaView,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import { useAlerts } from '../context/AlertsContext';
import { useGames } from '../context/GamesContext';
import { AlertPill } from '../components/AlertPill';

type RootStackParamList = {
  Alerts: undefined;
  GameDetail: { gameId: string };
};

type AlertsScreenNavigationProp = StackNavigationProp<RootStackParamList, 'Alerts'>;

export const AlertsScreen: React.FC = () => {
  const navigation = useNavigation<AlertsScreenNavigationProp>();
  const { alerts, removeAlert } = useAlerts();
  const { getGameById } = useGames();

  const handleAlertPress = (gameId: string) => {
    navigation.navigate('GameDetail', { gameId });
  };

  const renderAlert = ({ item }: { item: typeof alerts[0] }) => {
    const game = getGameById(item.game_id);
    if (!game) return null;

    const ups = game.prediction.upset_probability;
    const riskLevel = ups > 65 ? 'high' : ups > 50 ? 'medium' : 'low';
    const isTriggered = ups >= item.threshold;

    return (
      <TouchableOpacity
        className="bg-card p-4 rounded-2xl mb-4 border border-border"
        onPress={() => handleAlertPress(item.game_id)}
        activeOpacity={0.8}
      >
        <View className="flex-row justify-between items-start mb-4">
          <View className="flex-1">
            <Text className="text-lg font-semibold text-text-primary mb-1">
              {game.team_favorite} vs {game.team_underdog}
            </Text>
            <Text className="text-sm text-text-muted">{game.sport}</Text>
          </View>
          <AlertPill
            riskLevel={riskLevel}
            text={isTriggered ? 'TRIGGERED' : 'WATCHING'}
          />
        </View>

        <View className="mb-4">
          <Text className="text-base text-text-primary mb-1">
            Current UPS: <Text className="font-semibold text-primary">{ups}%</Text>
          </Text>
          <Text className="text-base text-text-primary mb-1">
            Alert Threshold: <Text className="font-semibold text-primary">{item.threshold}%</Text>
          </Text>
          {isTriggered && (
            <Text className="text-base text-danger font-semibold mt-1">
              ⚠️ Alert threshold exceeded!
            </Text>
          )}
        </View>

        <TouchableOpacity
          className="py-2 px-4 rounded-lg bg-danger items-center"
          onPress={() => removeAlert(item.id)}
        >
          <Text className="text-base text-text-primary font-semibold">Remove Alert</Text>
        </TouchableOpacity>
      </TouchableOpacity>
    );
  };

  return (
    <SafeAreaView className="flex-1 bg-background">
      <View className="p-4 border-b border-border">
        <Text className="text-2xl font-semibold text-text-primary mb-1">Upset Alerts</Text>
        <Text className="text-sm text-text-muted">
          Get notified when games exceed your risk threshold
        </Text>
      </View>

      {alerts.length === 0 ? (
        <View className="flex-1 items-center justify-center p-8">
          <Text className="text-6xl mb-4">🚨</Text>
          <Text className="text-xl font-semibold text-text-primary mb-1">No active alerts</Text>
          <Text className="text-base text-text-muted text-center">
            Set alerts on games from the home feed or game details
          </Text>
        </View>
      ) : (
        <FlatList
          data={alerts}
          keyExtractor={(item) => item.id}
          renderItem={renderAlert}
          contentContainerStyle={{ padding: 16 }}
        />
      )}
    </SafeAreaView>
  );
};

import React, { useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  SafeAreaView,
} from 'react-native';
import { useRoute, useNavigation, RouteProp } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import { useGames } from '../context/GamesContext';
import { useAlerts } from '../context/AlertsContext';
import { BiasVsRealityMeter } from '../components/BiasVsRealityMeter';
import { AlertPill } from '../components/AlertPill';
import { getKeySignals } from '../data/mockData';

type RootStackParamList = {
  GameDetail: { gameId: string };
};

type GameDetailRouteProp = RouteProp<RootStackParamList, 'GameDetail'>;
type GameDetailNavigationProp = StackNavigationProp<RootStackParamList, 'GameDetail'>;

type TabType = 'Summary' | 'Signals' | 'History' | 'Community';

export const GameDetailScreen: React.FC = () => {
  const route = useRoute<GameDetailRouteProp>();
  const navigation = useNavigation<GameDetailNavigationProp>();
  const { gameId } = route.params;
  const { getGameById } = useGames();
  const { getAlertsForGame, addAlert, removeAlert } = useAlerts();
  const [activeTab, setActiveTab] = useState<TabType>('Summary');
  const [alertThreshold] = useState(65);

  const game = getGameById(gameId);
  const alerts = getAlertsForGame(gameId);

  if (!game) {
    return (
      <SafeAreaView className="flex-1 bg-background">
        <Text className="text-base text-text-primary text-center mt-8">Game not found</Text>
      </SafeAreaView>
    );
  }

  const ups = game.prediction.upset_probability;
  const riskLevel = ups > 65 ? 'high' : ups > 50 ? 'medium' : 'low';
  const keySignals = getKeySignals(game);
  const publicPercentage = game.marketSignal.public_bet_percentage;
  const modelPercentage = 100 - ups;

  const tabs: TabType[] = ['Summary', 'Signals', 'History', 'Community'];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'Summary':
        return (
          <View className="p-4">
            <Text className="text-lg font-semibold text-text-primary mb-4 mt-6">Game Overview</Text>
            <Text className="text-base text-text-primary mb-2">
              <Text className="font-semibold">Favorite:</Text> {game.team_favorite}
            </Text>
            <Text className="text-base text-text-primary mb-2">
              <Text className="font-semibold">Underdog:</Text> {game.team_underdog}
            </Text>
            <Text className="text-base text-text-primary mb-2">
              <Text className="font-semibold">Sport:</Text> {game.sport}
            </Text>
            <Text className="text-base text-text-primary mb-2">
              <Text className="font-semibold">Start Time:</Text>{' '}
              {new Date(game.start_time).toLocaleString()}
            </Text>

            <View className="items-center my-6 py-4">
              <Text className="text-sm text-text-muted mb-1">Upset Probability</Text>
              <Text className="text-4xl font-bold font-mono text-danger">{ups}%</Text>
            </View>

            {/* NFL Spread/Total Info */}
            {game.sport === 'NFL' && (
              <View className="flex-row justify-between mb-4">
                <Text className="text-xs text-text-muted">
                  Spread {game.spreadOpen !== undefined ? game.spreadOpen.toFixed(1) : '—'} → {game.spreadCurrent !== undefined ? game.spreadCurrent.toFixed(1) : '—'}
                </Text>
                <Text className="text-xs text-text-muted">
                  Total {game.totalOpen !== undefined ? game.totalOpen.toFixed(1) : '—'} → {game.totalCurrent !== undefined ? game.totalCurrent.toFixed(1) : '—'}
                </Text>
              </View>
            )}

            <BiasVsRealityMeter
              publicPercentage={publicPercentage}
              modelPercentage={modelPercentage}
            />
          </View>
        );

      case 'Signals':
        return (
          <View className="p-4">
            <Text className="text-lg font-semibold text-text-primary mb-4 mt-6">Key Signals</Text>
            {keySignals.map((signal, index) => (
              <View key={index} className="flex-row mb-2">
                <Text className="text-base text-primary mr-1">•</Text>
                <Text className="text-base text-text-primary flex-1">{signal}</Text>
              </View>
            ))}

            <Text className="text-lg font-semibold text-text-primary mb-4 mt-6">Market Data</Text>
            <Text className="text-base text-text-primary mb-2">
              <Text className="font-semibold">Public Bet %:</Text> {publicPercentage}%
            </Text>
            <Text className="text-base text-text-primary mb-2">
              <Text className="font-semibold">Line Movement:</Text>{' '}
              {game.marketSignal.line_movement > 0 ? '+' : ''}
              {game.marketSignal.line_movement}
            </Text>
            <Text className="text-base text-text-primary mb-2">
              <Text className="font-semibold">Sentiment Score:</Text>{' '}
              {game.marketSignal.sentiment_score.toFixed(2)}
            </Text>
          </View>
        );

      case 'History':
        return (
          <View className="p-4">
            <Text className="text-lg font-semibold text-text-primary mb-4 mt-6">Historical Matchups</Text>
            <Text className="text-base text-text-primary">
              Historical data will appear here when available.
            </Text>
          </View>
        );

      case 'Community':
        return (
          <View className="p-4">
            <Text className="text-lg font-semibold text-text-primary mb-4 mt-6">Community Picks</Text>
            <Text className="text-base text-text-primary">
              Community picks and discussions will appear here.
            </Text>
          </View>
        );

      default:
        return null;
    }
  };

  return (
    <SafeAreaView className="flex-1 bg-background">
      <ScrollView className="flex-1">
        <View className="p-4 flex-row justify-between items-center">
          <Text className="text-xl font-semibold text-text-primary flex-1">
            {game.team_favorite} vs {game.team_underdog}
          </Text>
          <AlertPill
            riskLevel={riskLevel}
            text={riskLevel === 'high' ? 'HIGH RISK' : riskLevel === 'medium' ? 'MEDIUM' : 'LOW'}
          />
        </View>

        {/* Tabs */}
        <View className="flex-row border-b border-border px-4">
          {tabs.map((tab) => (
            <TouchableOpacity
              key={tab}
              className={`py-4 px-2 mr-4 border-b-2 ${
                activeTab === tab ? 'border-primary' : 'border-transparent'
              }`}
              onPress={() => setActiveTab(tab)}
            >
              <Text
                className={`text-base ${
                  activeTab === tab ? 'text-primary font-semibold' : 'text-text-muted'
                }`}
              >
                {tab}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {renderTabContent()}

        {/* Alert Configuration */}
        <View className="p-4 mt-6 bg-card m-4 rounded-lg">
          <Text className="text-lg font-semibold text-text-primary mb-4">Alert Settings</Text>
          <Text className="text-base text-text-primary mb-4">
            Get notified when UPS exceeds {alertThreshold}%
          </Text>
          <TouchableOpacity
            className="bg-primary p-4 rounded-lg items-center mt-4"
            onPress={() => {
              if (alerts.length > 0) {
                alerts.forEach((alert) => removeAlert(alert.id));
              } else {
                addAlert(gameId, alertThreshold);
              }
            }}
          >
            <Text className="text-base text-text-primary font-semibold">
              {alerts.length > 0 ? 'Remove Alert' : 'Set Alert'}
            </Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

import React from 'react';
import { View, Text } from 'react-native';

export type RiskLevel = 'high' | 'medium' | 'low';

interface AlertPillProps {
  riskLevel: RiskLevel;
  text: string;
}

export const AlertPill: React.FC<AlertPillProps> = ({ riskLevel, text }) => {
  const riskColors = {
    high: 'bg-danger',
    medium: 'bg-warning',
    low: 'bg-success',
  };

  const riskIcons = {
    high: '🔥',
    medium: '⚠️',
    low: '✓',
  };

  return (
    <View className={`flex-row items-center px-4 py-1 rounded-full gap-1 ${riskColors[riskLevel]}`}>
      <Text className="text-sm">{riskIcons[riskLevel]}</Text>
      <Text className="text-sm text-text-primary font-semibold">{text}</Text>
    </View>
  );
};

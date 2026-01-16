import React from 'react';
import { View, Text } from 'react-native';

interface BiasVsRealityMeterProps {
  publicPercentage: number;
  modelPercentage: number;
}

export const BiasVsRealityMeter: React.FC<BiasVsRealityMeterProps> = ({
  publicPercentage,
  modelPercentage,
}) => {
  const delta = publicPercentage - modelPercentage;

  return (
    <View className="my-2">
      <View className="flex-row items-center gap-4">
        {/* Public Bar */}
        <View className="flex-1">
          <Text className="text-sm text-text-muted mb-1">Public</Text>
          <View className="h-2 bg-border rounded-sm overflow-hidden mb-1">
            <View
              className="h-full bg-warning rounded-sm"
              style={{ width: `${publicPercentage}%` }}
            />
          </View>
          <Text className="text-sm text-text-primary font-semibold">{publicPercentage}%</Text>
        </View>

        {/* Delta Display */}
        <View className="items-center justify-center px-1">
          <Text className="text-sm text-text-muted">Δ</Text>
          <Text
            className={`text-xl font-bold ${delta > 20 ? 'text-danger' : 'text-warning'}`}
          >
            {delta > 0 ? '+' : ''}{delta.toFixed(0)}%
          </Text>
        </View>

        {/* Model Bar */}
        <View className="flex-1">
          <Text className="text-sm text-text-muted mb-1">Model</Text>
          <View className="h-2 bg-border rounded-sm overflow-hidden mb-1">
            <View
              className="h-full bg-primary rounded-sm"
              style={{ width: `${modelPercentage}%` }}
            />
          </View>
          <Text className="text-sm text-text-primary font-semibold">{modelPercentage}%</Text>
        </View>
      </View>
    </View>
  );
};

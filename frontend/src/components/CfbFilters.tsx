import React from 'react';
import { View, Text, Switch } from 'react-native';
import Slider from '@react-native-community/slider';

interface CfbFiltersProps {
  minUpsPct: number;
  setMinUpsPct: (v: number) => void;
  onlyTopGames: boolean;
  setOnlyTopGames: (v: boolean) => void;
}

export const CfbFilters: React.FC<CfbFiltersProps> = ({
  minUpsPct,
  setMinUpsPct,
  onlyTopGames,
  setOnlyTopGames,
}) => {
  return (
    <View className="gap-3 p-4 bg-card border-b border-border">
      <View className="flex-row justify-between items-center">
        <Text className="text-sm text-text-muted">UPS threshold</Text>
        <Text className="text-sm text-text-primary font-extrabold">{minUpsPct}%+</Text>
      </View>

      <Slider
        value={minUpsPct}
        minimumValue={40}
        maximumValue={80}
        step={1}
        onValueChange={setMinUpsPct}
        minimumTrackTintColor="#5B8CFF"
        maximumTrackTintColor="#1F2937"
        thumbTintColor="#5B8CFF"
      />

      <View className="flex-row justify-between items-center">
        <Text className="text-sm text-text-muted">Top games only</Text>
        <Switch
          value={onlyTopGames}
          onValueChange={setOnlyTopGames}
          trackColor={{ false: '#1F2937', true: '#5B8CFF' }}
          thumbColor={onlyTopGames ? '#F9FAFB' : '#9CA3AF'}
        />
      </View>
    </View>
  );
};

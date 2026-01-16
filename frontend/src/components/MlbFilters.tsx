import React from 'react';
import { View, Text, Switch } from 'react-native';
import Slider from '@react-native-community/slider';

interface MlbFiltersProps {
  minUpsPct: number;
  setMinUpsPct: (v: number) => void;
  onlyHighStakes: boolean;
  setOnlyHighStakes: (v: boolean) => void;
}

export const MlbFilters: React.FC<MlbFiltersProps> = ({
  minUpsPct,
  setMinUpsPct,
  onlyHighStakes,
  setOnlyHighStakes,
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
        <Text className="text-sm text-text-muted">High-stakes games only</Text>
        <Switch
          value={onlyHighStakes}
          onValueChange={setOnlyHighStakes}
          trackColor={{ false: '#1F2937', true: '#5B8CFF' }}
          thumbColor={onlyHighStakes ? '#F9FAFB' : '#9CA3AF'}
        />
      </View>
    </View>
  );
};

import React from 'react';
import { View, Text, Switch } from 'react-native';
import Slider from '@react-native-community/slider';

interface SoccerFiltersProps {
  minUpsPct: number;
  setMinUpsPct: (v: number) => void;
  onlyFeatured: boolean;
  setOnlyFeatured: (v: boolean) => void;
}

export const SoccerFilters: React.FC<SoccerFiltersProps> = ({
  minUpsPct,
  setMinUpsPct,
  onlyFeatured,
  setOnlyFeatured,
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
        <Text className="text-sm text-text-muted">Featured matches only</Text>
        <Switch
          value={onlyFeatured}
          onValueChange={setOnlyFeatured}
          trackColor={{ false: '#1F2937', true: '#5B8CFF' }}
          thumbColor={onlyFeatured ? '#F9FAFB' : '#9CA3AF'}
        />
      </View>
    </View>
  );
};

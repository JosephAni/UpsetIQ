import React, { useState } from 'react';
import { View, Text, TouchableOpacity, ScrollView } from 'react-native';
import { Sport, FilterState } from '../types';

interface FilterBarProps {
  onFilterChange: (filter: FilterState) => void;
  currentFilter: FilterState;
}

const SPORTS: Sport[] = ['NBA', 'NFL', 'MLB', 'NHL', 'Soccer', 'CFB'];

export const FilterBar: React.FC<FilterBarProps> = ({
  onFilterChange,
  currentFilter,
}) => {
  const [selectedSport, setSelectedSport] = useState<Sport | undefined>(
    currentFilter.sport
  );

  const handleSportSelect = (sport: Sport) => {
    const newSport = selectedSport === sport ? undefined : sport;
    setSelectedSport(newSport);
    onFilterChange({
      ...currentFilter,
      sport: newSport,
    });
  };

  return (
    <View className="bg-card border-b border-border py-2">
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        className="flex-grow-0"
        contentContainerStyle={{ paddingHorizontal: 16, gap: 8, alignItems: 'center' }}
      >
        {/* Sport Filters */}
        <TouchableOpacity
          className={`
            px-4 py-1 rounded-full border
            ${!selectedSport ? 'bg-primary border-primary' : 'bg-background border-border'}
          `}
          onPress={() => {
            setSelectedSport(undefined);
            onFilterChange({
              ...currentFilter,
              sport: undefined,
            });
          }}
        >
          <Text
            className={`
              text-sm font-medium
              ${!selectedSport ? 'text-text-primary font-semibold' : 'text-text-muted'}
            `}
          >
            All Sports
          </Text>
        </TouchableOpacity>

        {SPORTS.map((sport) => (
          <TouchableOpacity
            key={sport}
            className={`
              px-4 py-1 rounded-full border
              ${selectedSport === sport ? 'bg-primary border-primary' : 'bg-background border-border'}
            `}
            onPress={() => handleSportSelect(sport)}
          >
            <Text
              className={`
                text-sm font-medium
                ${selectedSport === sport ? 'text-text-primary font-semibold' : 'text-text-muted'}
              `}
            >
              {sport}
            </Text>
          </TouchableOpacity>
        ))}

        {/* Confidence Threshold */}
        <View className="px-4 py-1 rounded-full bg-background border border-border">
          <Text className="text-sm text-text-primary font-medium">
            Confidence &gt; {currentFilter.confidenceThreshold}%
          </Text>
        </View>
      </ScrollView>
    </View>
  );
};

import React, { useEffect, useState } from 'react';
import { View, Text, TouchableOpacity } from 'react-native';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { BiasVsRealityMeter } from '../BiasVsRealityMeter';
import { AlertPill, RiskLevel } from '../AlertPill';
import { GameWithPrediction } from '../../types';
import { getKeySignals } from '../../data/mockData';

// Conditionally import reanimated - will be undefined if version mismatch
let Animated: any;
let useSharedValue: any;
let useAnimatedStyle: any;
let withRepeat: any;
let withTiming: any;
let interpolate: any;

try {
  const reanimated = require('react-native-reanimated');
  Animated = reanimated.default;
  useSharedValue = reanimated.useSharedValue;
  useAnimatedStyle = reanimated.useAnimatedStyle;
  withRepeat = reanimated.withRepeat;
  withTiming = reanimated.withTiming;
  interpolate = reanimated.interpolate;
} catch (error) {
  // Reanimated not available or version mismatch - continue without animations
  console.warn('Reanimated not available, animations will be disabled');
}

interface UpsetCardProps {
  game: GameWithPrediction;
  onPress: () => void;
  onTrack: () => void;
  onAlert: () => void;
}

export const UpsetCard: React.FC<UpsetCardProps> = ({
  game,
  onPress,
  onTrack,
  onAlert,
}) => {
  const ups = game.prediction.upset_probability;
  const isHighRisk = ups > 65;
  const riskLevel: RiskLevel = ups > 65 ? 'high' : ups > 50 ? 'medium' : 'low';
  
  const keySignals = getKeySignals(game);
  const publicPercentage = game.marketSignal.public_bet_percentage;
  const modelPercentage = 100 - ups;
  const [reanimatedAvailable] = useState(() => {
    try {
      return !!useSharedValue && !!useAnimatedStyle;
    } catch {
      return false;
    }
  });

  // Animated glow effect for high-risk cards (only if reanimated is available)
  const glowOpacity = reanimatedAvailable ? useSharedValue(0) : null;
  
  useEffect(() => {
    if (reanimatedAvailable && glowOpacity) {
      if (isHighRisk) {
        glowOpacity.value = withRepeat(
          withTiming(1, { duration: 2000 }),
          -1,
          true
        );
      } else {
        glowOpacity.value = 0;
      }
    }
  }, [isHighRisk, reanimatedAvailable]);

  const animatedGlowStyle = reanimatedAvailable && glowOpacity 
    ? useAnimatedStyle(() => {
        const opacity = interpolate(glowOpacity.value, [0, 1], [0.3, 0.8]);
        return {
          shadowColor: '#FF4D4F',
          shadowOffset: { width: 0, height: 0 },
          shadowOpacity: opacity,
          shadowRadius: 15,
          elevation: 10,
        };
      })
    : null;

  const WrapperComponent = reanimatedAvailable && Animated ? Animated.View : View;

  return (
    <TouchableOpacity onPress={onPress} activeOpacity={0.9}>
      <WrapperComponent style={isHighRisk && animatedGlowStyle ? animatedGlowStyle : {}}>
        <Card glow={isHighRisk} className="mb-4">
          {/* Header */}
          <View className="flex-row justify-between items-start mb-4">
            <View className="flex-1">
              <Text className="text-sm text-text-muted mb-1">{game.sport}</Text>
              <Text className="text-lg font-semibold text-text-primary">
                {game.team_favorite} vs {game.team_underdog}
              </Text>
              {/* NFL Spread/Total Movement */}
              {game.sport === 'NFL' && (
                <View className="flex-row justify-between gap-3 mt-2">
                  <Text className="text-xs text-text-muted">
                    Spread: {game.spreadOpen !== undefined ? game.spreadOpen.toFixed(1) : '—'} → {game.spreadCurrent !== undefined ? game.spreadCurrent.toFixed(1) : '—'}
                  </Text>
                  <Text className="text-xs text-text-muted">
                    Total: {game.totalOpen !== undefined ? game.totalOpen.toFixed(1) : '—'} → {game.totalCurrent !== undefined ? game.totalCurrent.toFixed(1) : '—'}
                  </Text>
                </View>
              )}
            </View>
            <AlertPill
              riskLevel={riskLevel}
              text={isHighRisk ? 'HIGH RISK' : riskLevel === 'medium' ? 'MEDIUM' : 'LOW'}
            />
          </View>

          {/* UPS Display - Large and centered */}
          <View className="items-center my-6 py-4">
            <Text className="text-sm text-text-muted mb-1">Upset Probability</Text>
            <Text
              className="text-5xl font-bold font-mono"
              style={{ color: isHighRisk ? '#FF4D4F' : '#5B8CFF' }}
            >
              {ups}%
            </Text>
          </View>

          {/* Bias vs Reality Meter */}
          <View className="my-4">
            <BiasVsRealityMeter
              publicPercentage={publicPercentage}
              modelPercentage={modelPercentage}
            />
          </View>

          {/* Key Signals - 3 bullets */}
          <View className="my-4">
            <Text className="text-sm text-text-muted mb-1">Key Signals:</Text>
            {keySignals.map((signal, index) => (
              <View key={index} className="flex-row items-center mt-1">
                <Text className="text-base text-primary mr-1">•</Text>
                <Text className="text-base text-text-primary flex-1">{signal}</Text>
              </View>
            ))}
          </View>

          {/* Action Buttons */}
          <View className="flex-row gap-4 mt-4">
            <Button
              title="Track"
              onPress={onTrack}
              variant="secondary"
              className="flex-1"
            />
            <Button
              title="Alert Me"
              onPress={onAlert}
              variant="primary"
              className="flex-1"
            />
          </View>
        </Card>
      </WrapperComponent>
    </TouchableOpacity>
  );
};

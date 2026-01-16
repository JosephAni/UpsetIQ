import React from 'react';
import { View } from 'react-native';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  glow?: boolean;
}

export const Card: React.FC<CardProps> = ({ children, className = '', glow = false }) => {
  return (
    <View
      className={`
        bg-card rounded-2xl p-4 border border-border
        ${glow ? 'border-glow border-2 shadow-lg' : ''}
        ${className}
      `}
      style={glow ? {
        shadowColor: '#FF4D4F',
        shadowOffset: { width: 0, height: 0 },
        shadowOpacity: 0.8,
        shadowRadius: 10,
        elevation: 8,
      } : undefined}
    >
      {children}
    </View>
  );
};

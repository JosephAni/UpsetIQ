import React from 'react';
import { TouchableOpacity, Text, ActivityIndicator } from 'react-native';

interface ButtonProps {
  title: string;
  onPress: () => void;
  variant?: 'primary' | 'secondary' | 'danger';
  disabled?: boolean;
  loading?: boolean;
  className?: string;
}

export const Button: React.FC<ButtonProps> = ({
  title,
  onPress,
  variant = 'primary',
  disabled = false,
  loading = false,
  className = '',
}) => {
  const variantClasses = {
    primary: 'bg-primary',
    secondary: 'bg-card',
    danger: 'bg-danger',
  };

  const textColorClass = 'text-text-primary';

  return (
    <TouchableOpacity
      className={`
        px-6 py-4 rounded-2xl items-center justify-center min-h-[48px]
        ${variantClasses[variant]}
        ${disabled || loading ? 'opacity-50' : ''}
        ${className}
      `}
      onPress={onPress}
      disabled={disabled || loading}
      activeOpacity={0.8}
    >
      {loading ? (
        <ActivityIndicator color="#F9FAFB" />
      ) : (
        <Text className={`text-base font-semibold ${textColorClass}`}>
          {title}
        </Text>
      )}
    </TouchableOpacity>
  );
};

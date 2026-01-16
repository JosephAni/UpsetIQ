import React from 'react';
import { Text } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { HomeScreen } from '../screens/HomeScreen';
import { GameDetailScreen } from '../screens/GameDetailScreen';
import { LeaderboardScreen } from '../screens/LeaderboardScreen';
import { ProfileScreen } from '../screens/ProfileScreen';
import { AlertsScreen } from '../screens/AlertsScreen';

export type RootStackParamList = {
  MainTabs: undefined;
  GameDetail: { gameId: string };
};

export type TabParamList = {
  Home: undefined;
  Leaderboard: undefined;
  Profile: undefined;
  Alerts: undefined;
};

const Stack = createNativeStackNavigator<RootStackParamList>();
const Tab = createBottomTabNavigator<TabParamList>();

const TabNavigator = () => {
  return (
    <Tab.Navigator
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: '#5B8CFF',
        tabBarInactiveTintColor: '#9CA3AF',
        tabBarStyle: {
          backgroundColor: '#111827',
          borderTopColor: '#1F2937',
          borderTopWidth: 1,
        },
        tabBarLabelStyle: {
          fontSize: 14,
          fontWeight: '500',
        },
      }}
    >
      <Tab.Screen
        name="Home"
        component={HomeScreen}
        options={{
          tabBarIcon: ({ color }) => <TabIcon emoji="🏠" color={color} />,
          tabBarLabel: 'Home',
        }}
      />
      <Tab.Screen
        name="Leaderboard"
        component={LeaderboardScreen}
        options={{
          tabBarIcon: ({ color }) => <TabIcon emoji="🏆" color={color} />,
          tabBarLabel: 'Leaderboard',
        }}
      />
      <Tab.Screen
        name="Alerts"
        component={AlertsScreen}
        options={{
          tabBarIcon: ({ color }) => <TabIcon emoji="🚨" color={color} />,
          tabBarLabel: 'Alerts',
        }}
      />
      <Tab.Screen
        name="Profile"
        component={ProfileScreen}
        options={{
          tabBarIcon: ({ color }) => <TabIcon emoji="👤" color={color} />,
          tabBarLabel: 'Profile',
        }}
      />
    </Tab.Navigator>
  );
};

const TabIcon: React.FC<{ emoji: string; color: string }> = ({ emoji }) => {
  return <Text style={{ fontSize: 24 }}>{emoji}</Text>;
};

export const AppNavigator = () => {
  return (
    <NavigationContainer
      theme={{
        dark: true,
        colors: {
          primary: '#5B8CFF',
          background: '#0B0F1A',
          card: '#111827',
          text: '#F9FAFB',
          border: '#1F2937',
          notification: '#FF4D4F',
        },
        fonts: {
          regular: {
            fontFamily: 'System',
            fontWeight: '400',
          },
          medium: {
            fontFamily: 'System',
            fontWeight: '500',
          },
          bold: {
            fontFamily: 'System',
            fontWeight: '700',
          },
          heavy: {
            fontFamily: 'System',
            fontWeight: '800',
          },
        },
      }}
    >
      <Stack.Navigator
        screenOptions={{
          headerStyle: {
            backgroundColor: '#111827',
          },
          headerTintColor: '#F9FAFB',
          headerTitleStyle: {
            fontSize: 18,
            fontWeight: '600',
          },
        }}
      >
        <Stack.Screen
          name="MainTabs"
          component={TabNavigator}
          options={{ headerShown: false }}
        />
        <Stack.Screen
          name="GameDetail"
          component={GameDetailScreen}
          options={{
            title: 'Game Details',
            presentation: 'card',
          }}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
};

import React, { useEffect } from 'react';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import './global.css';
import { GamesProvider } from './src/context/GamesContext';
import { UserProvider } from './src/context/UserContext';
import { AlertsProvider } from './src/context/AlertsContext';
import { AppNavigator } from './src/navigation/AppNavigator';
import { requestPermissions } from './src/services/notifications';

export default function App() {
  useEffect(() => {
    // Request notification permissions on app start
    requestPermissions().catch((error) => {
      console.error('Failed to request notification permissions:', error);
    });
  }, []);

  return (
    <SafeAreaProvider>
      <GamesProvider>
        <UserProvider>
          <AlertsProvider>
            <StatusBar style="light" backgroundColor="#0B0F1A" />
            <AppNavigator />
          </AlertsProvider>
        </UserProvider>
      </GamesProvider>
    </SafeAreaProvider>
  );
}

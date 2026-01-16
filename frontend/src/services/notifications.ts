import * as Notifications from 'expo-notifications';
import { Alert } from '../types';

// Configure notification handler
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

export const requestPermissions = async (): Promise<boolean> => {
  try {
    const { status: existingStatus } = await Notifications.getPermissionsAsync();
    let finalStatus = existingStatus;

    if (existingStatus !== 'granted') {
      const { status } = await Notifications.requestPermissionsAsync();
      finalStatus = status;
    }

    return finalStatus === 'granted';
  } catch (error) {
    console.error('Error requesting notification permissions:', error);
    return false;
  }
};

export const scheduleAlertNotification = async (
  alert: Alert,
  gameInfo: { favorite: string; underdog: string; ups: number }
): Promise<string | null> => {
  try {
    const hasPermission = await requestPermissions();
    if (!hasPermission) {
      console.warn('Notification permissions not granted');
      return null;
    }

    // For now, we'll schedule a notification that triggers when the threshold is met
    // In a real app, this would be handled by the backend monitoring system
    const notificationId = await Notifications.scheduleNotificationAsync({
      content: {
        title: '🚨 Upset Alert Triggered!',
        body: `${gameInfo.underdog} has ${gameInfo.ups}% upset probability vs ${gameInfo.favorite}`,
        data: { alertId: alert.id, gameId: alert.game_id },
        sound: true,
      },
      trigger: null, // In real app, this would trigger based on real-time updates
    });

    return notificationId;
  } catch (error) {
    console.error('Error scheduling notification:', error);
    return null;
  }
};

export const cancelNotification = async (notificationId: string): Promise<void> => {
  try {
    await Notifications.cancelScheduledNotificationAsync(notificationId);
  } catch (error) {
    console.error('Error canceling notification:', error);
  }
};

// Mock function to check if alerts should trigger
// In real app, this would be called periodically or via WebSocket updates
export const checkAlerts = async (
  alerts: Alert[],
  getGameUps: (gameId: string) => number | undefined
): Promise<void> => {
  for (const alert of alerts) {
    if (alert.triggered) continue;

    const currentUps = getGameUps(alert.game_id);
    if (currentUps && currentUps >= alert.threshold) {
      // Trigger notification
      // This is a mock - in real app, you'd get game info from your data source
      await scheduleAlertNotification(
        alert,
        {
          favorite: 'Team A',
          underdog: 'Team B',
          ups: currentUps,
        }
      );
    }
  }
};

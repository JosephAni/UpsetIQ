import React, { createContext, useContext, useState, ReactNode } from 'react';
import { Alert, AlertThreshold } from '../types';

interface AlertsContextType {
  alerts: Alert[];
  addAlert: (gameId: string, threshold: AlertThreshold) => void;
  removeAlert: (alertId: string) => void;
  getAlertsForGame: (gameId: string) => Alert[];
}

const AlertsContext = createContext<AlertsContextType | undefined>(undefined);

export const AlertsProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [alerts, setAlerts] = useState<Alert[]>([]);

  const addAlert = (gameId: string, threshold: AlertThreshold) => {
    const newAlert: Alert = {
      id: `alert-${Date.now()}`,
      game_id: gameId,
      user_id: 'current-user', // Would come from user context
      threshold,
      triggered: false,
      created_at: new Date().toISOString(),
    };
    setAlerts((prev) => [...prev, newAlert]);
  };

  const removeAlert = (alertId: string) => {
    setAlerts((prev) => prev.filter((alert) => alert.id !== alertId));
  };

  const getAlertsForGame = (gameId: string) => {
    return alerts.filter((alert) => alert.game_id === gameId);
  };

  return (
    <AlertsContext.Provider
      value={{
        alerts,
        addAlert,
        removeAlert,
        getAlertsForGame,
      }}
    >
      {children}
    </AlertsContext.Provider>
  );
};

export const useAlerts = () => {
  const context = useContext(AlertsContext);
  if (!context) {
    throw new Error('useAlerts must be used within an AlertsProvider');
  }
  return context;
};

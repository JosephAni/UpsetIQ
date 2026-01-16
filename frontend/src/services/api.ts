/**
 * Base API client for UpsetIQ backend communication.
 */

// Declare __DEV__ for TypeScript (React Native global)
declare const __DEV__: boolean;

// Use localhost for development, production URL when deployed
// For iOS simulator, use localhost. For Android emulator, use 10.0.2.2
import { Platform } from 'react-native';

const getApiBaseUrl = () => {
  if (typeof __DEV__ !== 'undefined' && __DEV__) {
    // Development mode
    if (Platform.OS === 'android') {
      return 'http://10.0.2.2:8000'; // Android emulator
    }
    return 'http://localhost:8000'; // iOS simulator
  }
  return 'https://api.upsetiq.com'; // Production URL
};

const API_BASE_URL = getApiBaseUrl();

interface ApiError {
  message: string;
  status: number;
  detail?: string;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  /**
   * Make a GET request to the API.
   */
  async get<T>(endpoint: string, params?: Record<string, string>): Promise<T> {
    const url = new URL(`${this.baseUrl}${endpoint}`);
    
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        url.searchParams.append(key, value);
      });
    }

    try {
      const response = await fetch(url.toString(), {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw {
          message: errorData.detail || `HTTP ${response.status}`,
          status: response.status,
          detail: errorData.detail,
        } as ApiError;
      }

      return response.json();
    } catch (error) {
      if ((error as ApiError).status) {
        throw error;
      }
      // Network error or other fetch error
      throw {
        message: 'Network error - please check your connection',
        status: 0,
        detail: (error as Error).message,
      } as ApiError;
    }
  }

  /**
   * Make a POST request to the API.
   */
  async post<T>(endpoint: string, data?: unknown): Promise<T> {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: data ? JSON.stringify(data) : undefined,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw {
          message: errorData.detail || `HTTP ${response.status}`,
          status: response.status,
          detail: errorData.detail,
        } as ApiError;
      }

      return response.json();
    } catch (error) {
      if ((error as ApiError).status) {
        throw error;
      }
      throw {
        message: 'Network error - please check your connection',
        status: 0,
        detail: (error as Error).message,
      } as ApiError;
    }
  }

  /**
   * Health check endpoint.
   */
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    return this.get('/health');
  }
}

// Export singleton instance
export const api = new ApiClient();

// Export types
export type { ApiError };

// Export for custom base URL (e.g., testing)
export { ApiClient };

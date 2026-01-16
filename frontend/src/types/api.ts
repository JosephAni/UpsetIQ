/**
 * API-related type definitions.
 */

// Generic API state for async operations
export interface AsyncState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

// API response metadata
export interface ApiMetadata {
  fetchedAt: string;
  cached: boolean;
}

// Health check response
export interface HealthCheckResponse {
  status: string;
  timestamp: string;
}

// Error response from API
export interface ApiErrorResponse {
  detail: string;
  status_code?: number;
}

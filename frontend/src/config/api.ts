/**
 * API Configuration Module.
 *
 * Centralized configuration for all API endpoints. Supports environment-based
 * configuration via Vite's import.meta.env for different deployment environments
 * (development, staging, production).
 *
 * Environment Variables:
 *   VITE_API_BASE_URL: Base URL for the backend API (required in production).
 *     - Development: Falls back to http://localhost:8000 if not set
 *     - Production: MUST be set via GitHub Actions secrets during build
 *
 * Usage:
 *   Import endpoints: import { API_ENDPOINTS } from './config/api';
 *   Use in fetch: fetch(API_ENDPOINTS.START, { method: 'POST', ... });
 *
 * @module config/api
 */

// Base URL for API requests
// In development: Falls back to localhost if not set
// In production: Fails fast if VITE_API_BASE_URL is missing
const getApiBaseUrl = (): string => {
  const envUrl = import.meta.env.VITE_API_BASE_URL;
  const isDevelopment =
    import.meta.env.DEV || import.meta.env.MODE === "development";

  if (envUrl) {
    return envUrl;
  }

  // Development fallback
  if (isDevelopment) {
    return "http://localhost:8000";
  }

  // Production: Fail fast if missing
  throw new Error(
    "VITE_API_BASE_URL environment variable is required in production. " +
      "Please set it in your build environment (e.g., GitHub Actions secrets)."
  );
};

const API_BASE_URL = getApiBaseUrl();

/**
 * API Endpoints Configuration.
 *
 * Complete list of all API endpoints used by the application. All endpoints
 * are constructed using the API_BASE_URL, ensuring consistent configuration
 * across environments.
 */
export const API_ENDPOINTS = {
  /** Legacy endpoint for submitting form data (kept for backward compatibility) */
  SUBMIT_FORM: `${API_BASE_URL}/api/endpoint`,
  /** Start pipeline asynchronously and get job_id */
  START: `${API_BASE_URL}/api/start`,
  /** Get current progress (poll this endpoint periodically) */
  PROGRESS: `${API_BASE_URL}/api/progress`,
  /** Cancel a running pipeline */
  CANCEL: `${API_BASE_URL}/api/cancel`,
  /** Download the generated document */
  DOWNLOAD: `${API_BASE_URL}/api/download`,
} as const;

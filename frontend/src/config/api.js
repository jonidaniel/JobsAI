/**
 * API Configuration
 *
 * Centralized API endpoint configuration.
 * Supports environment variables via Vite's import.meta.env for different environments.
 *
 * Environment Variable:
 * - VITE_API_BASE_URL: Base URL for the backend API (defaults to localhost:8000)
 *
 * Usage:
 * Set VITE_API_BASE_URL in .env file:
 *   VITE_API_BASE_URL=https://api.production.com
 */

// Base URL for API requests
// Falls back to localhost for development if env variable is not set
const API_BASE_URL =
  // import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
  import.meta.env.VITE_API_BASE_URL ||
  "https://knccck3mck.execute-api.eu-north-1.amazonaws.com/prod";

/**
 * API Endpoints
 *
 * All available API endpoints for the application.
 */
export const API_ENDPOINTS = {
  /** Legacy endpoint for submitting form data (kept for backward compatibility) */
  SUBMIT_FORM: `${API_BASE_URL}/api/endpoint`,
  /** Start pipeline asynchronously and get job_id */
  START: `${API_BASE_URL}/api/start`,
  /** Stream progress updates via Server-Sent Events */
  PROGRESS: `${API_BASE_URL}/api/progress`,
  /** Cancel a running pipeline */
  CANCEL: `${API_BASE_URL}/api/cancel`,
  /** Download the generated document */
  DOWNLOAD: `${API_BASE_URL}/api/download`,
};

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
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

/**
 * API Endpoints
 *
 * All available API endpoints for the application.
 */
export const API_ENDPOINTS = {
  /** Endpoint for submitting form data and generating job search document */
  SUBMIT_FORM: `${API_BASE_URL}/api/endpoint`,
};

// Export base URL for other uses if needed
export { API_BASE_URL };

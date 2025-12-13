/**
 * API Configuration Module.
 *
 * Centralized configuration for all API endpoints. Supports environment-based
 * configuration via Vite's import.meta.env for different deployment environments
 * (development, staging, production).
 *
 * Environment Variables:
 *   VITE_API_BASE_URL: Base URL for the backend API.
 *     - Development: http://localhost:8000 (if not set)
 *     - Production: Set in GitHub Actions secrets and injected during build
 *
 * Usage:
 *   Import endpoints: import { API_ENDPOINTS } from './config/api';
 *   Use in fetch: fetch(API_ENDPOINTS.START, { method: 'POST', ... });
 *
 * @module config/api
 */

// Base URL for API requests
// Falls back to localhost for development if env variable is not set
const API_BASE_URL =
  // import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
  import.meta.env.VITE_API_BASE_URL ||
  "https://knccck3mck.execute-api.eu-north-1.amazonaws.com/prod";

/**
 * API Endpoints Configuration.
 *
 * Complete list of all API endpoints used by the application. All endpoints
 * are constructed using the API_BASE_URL, ensuring consistent configuration
 * across environments.
 *
 * @constant {Object<string, string>}
 * @property {string} SUBMIT_FORM - Legacy synchronous endpoint (POST /api/endpoint).
 *   Kept for backward compatibility. Returns document directly.
 * @property {string} START - Start pipeline asynchronously (POST /api/start).
 *   Returns job_id for progress tracking.
 * @property {string} PROGRESS - Get pipeline progress (GET /api/progress/{job_id}).
 *   Poll this endpoint every 1-2 seconds for progress updates.
 * @property {string} CANCEL - Cancel running pipeline (POST /api/cancel/{job_id}).
 *   Sets cancellation flag in DynamoDB.
 * @property {string} DOWNLOAD - Get download URL (GET /api/download/{job_id}).
 *   Returns presigned S3 URL for document download.
 */
export const API_ENDPOINTS = {
  /** @type {string} Legacy endpoint for submitting form data (kept for backward compatibility) */
  SUBMIT_FORM: `${API_BASE_URL}/api/endpoint`,
  /** @type {string} Start pipeline asynchronously and get job_id */
  START: `${API_BASE_URL}/api/start`,
  /** @type {string} Get current progress (poll this endpoint periodically) */
  PROGRESS: `${API_BASE_URL}/api/progress`,
  /** @type {string} Cancel a running pipeline */
  CANCEL: `${API_BASE_URL}/api/cancel`,
  /** @type {string} Download the generated document */
  DOWNLOAD: `${API_BASE_URL}/api/download`,
};

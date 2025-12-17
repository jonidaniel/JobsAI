/**
 * Converts technical error objects into user-friendly error messages.
 *
 * Provides centralized error message handling for the application. Maps various
 * error types (network errors, HTTP status codes, validation errors) to
 * user-friendly messages that can be displayed to end users.
 *
 * Error Type Mapping:
 * - Network/TypeError (fetch failures): Connection error message
 * - HTTP 404: Endpoint not found message
 * - HTTP 500: Server error message
 * - HTTP 400: Invalid request message
 * - Other server errors: Generic server error with details
 * - Unknown errors: Generic unexpected error message
 *
 * @param error - The error object from fetch, validation, or other operations.
 *   Should have a message property that may contain status codes or error types.
 *
 * @returns User-friendly error message suitable for display in UI.
 *
 * @example
 * try {
 *   await fetch(url);
 * } catch (error) {
 *   const message = getErrorMessage(error);
 *   setError(message); // Display to user
 * }
 */
export function getErrorMessage(error: Error | unknown): string {
  // Handle non-Error objects
  if (!(error instanceof Error)) {
    return "An unexpected error occurred. Please try again.";
  }

  // Check for rate limit errors first
  if (
    error.message.includes("Server error: 429") ||
    error.message.includes("Rate limit exceeded") ||
    error.message.includes("too_many_requests")
  ) {
    // Return a special marker that indicates rate limit (will be handled in component)
    return "RATE_LIMIT_EXCEEDED";
  }
  if (error instanceof TypeError && error.message.includes("fetch")) {
    return "Unable to connect to the server. Please check your internet connection and try again.";
  }
  if (error.message.includes("Server error: 404")) {
    return "The requested endpoint was not found. Please contact support.";
  }
  if (error.message.includes("Server error: 500")) {
    return "The server encountered an error. Please try again later.";
  }
  if (error.message.includes("Server error: 400")) {
    return "Invalid request. Please check your answers and try again.";
  }
  if (error.message.includes("Server error")) {
    return `Server error occurred. Please try again later. (${error.message})`;
  }
  return "An unexpected error occurred. Please try again.";
}

import { useState, useEffect, useRef } from "react";
import QuestionSets from "./QuestionSets";
import { API_ENDPOINTS } from "../config/api";
import "../styles/search.css";

/**
 * Search Component
 *
 * Main component for the search/questionnaire section.
 * Responsibilities:
 * - Renders QuestionSets component
 * - Manages form submission to backend API
 * - Handles file download from server response
 * - Displays error and success messages
 * - Manages submission state to prevent double-submission
 *
 * Form data flow:
 * QuestionSets -> onFormDataChange callback -> formData state -> handleSubmit -> API
 */
export default function Search() {
  // Submission state management
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  // Form data received from QuestionSets component via callback
  const [formData, setFormData] = useState({});

  // Ref to track timeout for auto-dismissing success message
  const successTimeoutRef = useRef(null);

  /**
   * Converts technical error objects into user-friendly error messages
   *
   * @param {Error} error - The error object from fetch or other operations
   * @returns {string} User-friendly error message
   */
  const getErrorMessage = (error) => {
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
  };

  /**
   * Handles form submission
   *
   * Process:
   * 1. Prevents default form behavior and double submission
   * 2. Filters form data to remove empty values
   * 3. Sends POST request to backend API
   * 4. Downloads the returned .docx file
   * 5. Shows success/error messages
   *
   * @param {Event} e - Form submit event
   */
  const handleSubmit = async (e) => {
    e.preventDefault();
    e.stopPropagation();

    // Prevent double submission
    if (isSubmitting) {
      return;
    }

    // Clear previous errors and success messages
    setError(null);
    setSuccess(false);
    setIsSubmitting(true);

    /**
     * Filter form data to only include non-empty values
     * - Strings: Include if trimmed value is not empty
     * - Numbers: Include if value is not 0 (sliders default to 0)
     * - Arrays: Include if array has at least one element (checkboxes)
     */
    const result = {};
    Object.entries(formData).forEach(([key, value]) => {
      if (typeof value === "string" && value.trim() !== "") {
        result[key] = value.trim();
      } else if (typeof value === "number" && value !== 0) {
        result[key] = value;
      } else if (Array.isArray(value) && value.length > 0) {
        result[key] = value;
      }
    });

    // Send to backend and download document
    try {
      // Send POST request with form data
      const response = await fetch(API_ENDPOINTS.SUBMIT_FORM, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(result),
      });

      // Check if request was successful
      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      // Get the response as a blob (binary data for .docx file)
      const blob = await response.blob();

      // Extract filename from Content-Disposition header if available
      // Format: "attachment; filename=\"document.docx\""
      const contentDisposition = response.headers.get("Content-Disposition");
      let filename = "document.docx"; // default fallback
      if (contentDisposition) {
        const match = contentDisposition.match(/filename="?(.+)"?/);
        if (match && match[1]) filename = match[1];
      }

      // Create a temporary URL for the blob
      const url = window.URL.createObjectURL(blob);

      // Programmatically trigger file download
      // Create temporary anchor element, click it, then remove it
      const download_link = document.createElement("a");
      download_link.href = url;
      download_link.download = filename;
      document.body.appendChild(download_link);
      download_link.click();
      download_link.remove();

      // Clean up the blob URL to free memory
      window.URL.revokeObjectURL(url);

      // Show success message
      setSuccess(true);
      setError(null);

      // Auto-dismiss success message after 5 seconds
      // Clear any existing timeout first to prevent multiple timers
      if (successTimeoutRef.current) {
        clearTimeout(successTimeoutRef.current);
      }
      successTimeoutRef.current = setTimeout(() => {
        setSuccess(false);
        successTimeoutRef.current = null;
      }, 5000);
    } catch (error) {
      console.error("Download failed:", error);
      setError(getErrorMessage(error));
      setSuccess(false);
    } finally {
      // Reset submission flag after request completes (success or error)
      setIsSubmitting(false);
    }
  };

  // Cleanup: Clear timeout if component unmounts
  useEffect(() => {
    return () => {
      if (successTimeoutRef.current) {
        clearTimeout(successTimeoutRef.current);
      }
    };
  }, []);

  return (
    <section id="search">
      <h2>Search</h2>
      <h3 className="text-3xl font-semibold text-white text-center">
        Answer questions in each category and we will find jobs relevant to you
      </h3>
      {/* Question sets component - manages all form inputs */}
      <QuestionSets onFormDataChange={setFormData} />

      {/* Error message - displayed when submission fails */}
      {error && (
        <div className="flex justify-center mt-4">
          <div
            className="bg-red-900 border border-red-700 text-red-100 px-6 py-3 rounded-lg shadow-lg max-w-2xl w-full"
            role="alert"
          >
            <div className="flex items-center">
              <svg
                className="w-5 h-5 mr-2 flex-shrink-0"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
              <div>
                <p className="font-semibold">Error</p>
                <p className="text-sm">{error}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Success message - displayed when document is successfully downloaded */}
      {success && (
        <div className="flex justify-center mt-4">
          <div
            className="bg-green-900 border border-green-700 text-green-100 px-6 py-3 rounded-lg shadow-lg max-w-2xl w-full"
            role="alert"
          >
            <div className="flex items-center">
              <svg
                className="w-5 h-5 mr-2 flex-shrink-0"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
              <div>
                <p className="font-semibold">Success!</p>
                <p className="text-sm">
                  Your document has been generated and downloaded.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Submit button - triggers form submission and document generation */}
      <div className="flex justify-center mt-6">
        <button
          id="submit-btn"
          onClick={handleSubmit}
          disabled={isSubmitting}
          className="text-3xl px-6 py-3 border border-white bg-transparent text-white font-semibold rounded-lg shadow disabled:opacity-50 disabled:cursor-not-allowed"
          aria-label="Submit form and generate job search document"
        >
          {isSubmitting ? "Finding Jobs..." : "Find Jobs"}
        </button>
      </div>
    </section>
  );
}

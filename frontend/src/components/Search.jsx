import { useState, useEffect, useRef } from "react";

import QuestionSets from "./QuestionSets";
import ErrorMessage from "./ErrorMessage";
import SuccessMessage from "./SuccessMessage";
import { API_ENDPOINTS } from "../config/api";
import { transformFormData } from "../utils/formDataTransform";
import { downloadBlob } from "../utils/fileDownload";
import { getErrorMessage } from "../utils/errorMessages";

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

    // Transform form data into grouped structure for backend API
    const result = transformFormData(formData);

    console.log("RESULT IN HANDLE_SUBMIT: ", result);

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

      // Download the file
      downloadBlob(blob, response.headers);

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
  // This is to prevent memory leaks
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
      {/* Question sets component with blue/gray background - contains all question sets and manages all form inputs */}
      <QuestionSets onFormDataChange={setFormData} />

      {/* Error message - displayed when submission fails */}
      {error && <ErrorMessage message={error} />}

      {/* Success message - displayed when document is successfully downloaded */}
      {success && <SuccessMessage />}

      {/* Black 'Find Jobs' submit button - triggers form submission and document generation */}
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

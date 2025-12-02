import { useState, useEffect, useRef, useCallback } from "react";

import QuestionSets from "./QuestionSetList";
import SuccessMessage from "./messages/SuccessMessage";
import ErrorMessage from "./messages/ErrorMessage";

import { API_ENDPOINTS } from "../config/api";

import { transformFormData } from "../utils/formDataTransform";
import { downloadBlob } from "../utils/fileDownload";
import { getErrorMessage } from "../utils/errorMessages";
import { validateGeneralQuestions } from "../utils/validation";

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

  // Validation errors for general questions
  const [validationErrors, setValidationErrors] = useState({});

  // Active question set index (for navigating to error location)
  const [activeQuestionSetIndex, setActiveQuestionSetIndex] =
    useState(undefined);

  /**
   * Handle form data changes
   * Memoized to prevent infinite loops in QuestionSets useEffect
   */
  const handleFormDataChange = useCallback((newFormData) => {
    setFormData(newFormData);
  }, []);

  /**
   * Clear validation errors when user fixes them
   * Runs separately from handleFormDataChange to avoid loops
   * Only runs when formData changes and there are existing errors
   */
  useEffect(() => {
    // Only validate if there are existing errors (user is fixing them)
    if (Object.keys(validationErrors).length > 0) {
      const validation = validateGeneralQuestions(formData);
      if (validation.isValid) {
        setValidationErrors({});
      } else {
        // Update validation errors to reflect current state
        // Only update if errors have actually changed to avoid loops
        const errorKeys = Object.keys(validation.errors).sort().join(",");
        const currentErrorKeys = Object.keys(validationErrors).sort().join(",");
        if (errorKeys !== currentErrorKeys) {
          setValidationErrors(validation.errors);
        }
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [formData]);

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

    // Validate general questions before submission
    const validation = validateGeneralQuestions(formData);
    if (!validation.isValid) {
      setValidationErrors(validation.errors);

      // Find the first error and navigate to the question set containing it
      const errorKeys = Object.keys(validation.errors);
      if (errorKeys.length > 0) {
        const firstErrorKey = errorKeys[0];

        // Map error keys to question set indices
        // General questions (job-level, job-boards, deep-mode, cover-letter-num, cover-letter-style) -> index 0
        // Additional info (additional-info) -> index 9
        let targetIndex = 0; // Default to general questions
        if (firstErrorKey === "additional-info") {
          targetIndex = 9;
        }
        // All other errors are in general questions (index 0)

        setActiveQuestionSetIndex(targetIndex);
      }
      return;
    }

    // Clear validation errors if validation passes
    setValidationErrors({});
    setActiveQuestionSetIndex(undefined); // Clear active index when validation passes
    setIsSubmitting(true);

    // Transform form data into grouped structure for backend API
    const result = transformFormData(formData);

    console.log(result);

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
        <i>We will find jobs for you.</i>
      </h3>
      <h3 className="text-3xl font-semibold text-white text-center">
        The way to make sure we find <i>the most relevant jobs</i> and{" "}
        <i>write the best cover letters</i> is to provide us with a dose of
        information.
      </h3>
      <h3 className="text-3xl font-semibold text-white text-center">
        <i>We don't ask you for any personal information.</i>
      </h3>
      <h3 className="text-3xl font-semibold text-white text-center">
        By answering as many questions as possible, you enable us to use all
        tools in our arsenal when we scrape jobs for you. This is how we find
        the gems. The questions are easy, and in most of them you just select
        the option that best describes you. Even if you felt like you didn't
        have much experience, be truthful -
      </h3>
      <h3 className="text-3xl font-semibold text-white text-center">
        <i>if there is a job matching your skills, we will find it.</i>
      </h3>
      <h3 className="text-3xl font-semibold text-white text-center">
        <i>Find Jobs</i> let's us start the search.
      </h3>
      {/* Question sets component with blue/gray background - contains all question sets and manages all form inputs */}
      <QuestionSets
        onFormDataChange={handleFormDataChange}
        validationErrors={validationErrors}
        activeIndex={activeQuestionSetIndex}
        onActiveIndexChange={setActiveQuestionSetIndex}
      />
      {/* Success message - displayed when document is successfully downloaded */}
      {success && <SuccessMessage />}
      {/* Error message - displayed when submission fails */}
      {error && <ErrorMessage message={error} />}
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

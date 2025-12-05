import { useState, useEffect, useRef, useCallback } from "react";

import QuestionSetList from "./QuestionSetList";
import SuccessMessage from "./messages/SuccessMessage";
import ErrorMessage from "./messages/ErrorMessage";

import { API_ENDPOINTS } from "../config/api";

import { transformFormData } from "../utils/formDataTransform";
import { downloadBlob } from "../utils/fileDownload";
import { getErrorMessage } from "../utils/errorMessages";
import { validateGeneralQuestions } from "../utils/validation";
import { GENERAL_QUESTION_KEYS } from "../config/generalQuestions";
import {
  SUCCESS_MESSAGE_TIMEOUT,
  SCROLL_OFFSET,
  SCROLL_DELAY,
} from "../config/constants";

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
  // Progress tracking for SSE
  const [currentPhase, setCurrentPhase] = useState(null);
  const [jobId, setJobId] = useState(null);
  const eventSourceRef = useRef(null);
  // Consolidated submission state ref
  // Tracks submission-related state that doesn't need to trigger re-renders
  const submissionState = useRef({
    justCompleted: false, // Track if we just completed a submission (to prevent scroll on remount)
    savedScrollPosition: null, // Store scroll position to restore after download
    hasSuccessfulSubmission: false, // Track if we've had a successful submission (to keep question sets hidden)
  });

  // Phase messages mapping
  const phaseMessages = {
    profiling: "Creating your profile...",
    searching: "Searching for jobs...",
    scoring: "Scoring the jobs...",
    analyzing: "Doing analysis...",
    generating: "Generating cover letters for you...",
  };

  // Form data received from QuestionSets component via callback
  const [formData, setFormData] = useState({});

  // Validation errors for general questions
  const [validationErrors, setValidationErrors] = useState({});

  // Active question set index (for navigating to error location)
  const [activeQuestionSetIndex, setActiveQuestionSetIndex] =
    useState(undefined);
  // Current question set index (tracked from QuestionSetList)
  const [currentQuestionSetIndex, setCurrentQuestionSetIndex] = useState(0);

  /**
   * Handles form data changes from QuestionSetList component
   * Memoized with useCallback to prevent infinite loops in QuestionSetList's useEffect
   *
   * @param {Object} newFormData - Complete form data object from QuestionSetList
   */
  const handleFormDataChange = useCallback((newFormData) => {
    setFormData(newFormData);
  }, []);

  /**
   * Clears validation errors when user fixes them
   * Runs separately from handleFormDataChange to avoid infinite loops
   * Only validates when formData changes and there are existing errors
   */
  useEffect(() => {
    // Only validate if there are existing errors (user is fixing them)
    if (Object.keys(validationErrors).length > 0) {
      const validation = validateGeneralQuestions(formData);
      if (validation.isValid) {
        setValidationErrors({});
      } else {
        // Update validation errors to reflect current state
        // Only update if errors have actually changed to avoid infinite loops
        const errorKeys = Object.keys(validation.errors).sort().join(",");
        const currentErrorKeys = Object.keys(validationErrors).sort().join(",");
        if (errorKeys !== currentErrorKeys) {
          setValidationErrors(validation.errors);
        }
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [formData]);

  // Ref to track timeout for auto-dismissing success message after download
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

    // If this is a "Find Again" click, navigate to question set 1 and reset
    if (submissionState.current.hasSuccessfulSubmission) {
      // Reset states
      setError(null);
      setSuccess(false);
      submissionState.current.justCompleted = false;
      submissionState.current.hasSuccessfulSubmission = false;
      // Navigate to question set 1 (index 0)
      setActiveQuestionSetIndex(0);
      // Scroll to question set 1 after a brief delay to ensure DOM is ready
      setTimeout(() => {
        const questionSetSection = document.querySelector('[data-index="0"]');
        if (questionSetSection) {
          const rect = questionSetSection.getBoundingClientRect();
          const targetPosition = window.scrollY + rect.top - SCROLL_OFFSET;
          window.scrollTo({
            top: targetPosition,
            behavior: "smooth",
          });
        }
      }, SCROLL_DELAY);
      return;
    }

    // Prevent double submission
    if (isSubmitting) {
      return;
    }

    // Clear previous errors and success messages
    setError(null);
    setSuccess(false);
    submissionState.current.justCompleted = false;
    // Reset successful submission flag when starting a new submission
    submissionState.current.hasSuccessfulSubmission = false;

    // Validate general questions before submission
    const validation = validateGeneralQuestions(formData);
    if (!validation.isValid) {
      setValidationErrors(validation.errors);

      // Check if the current question set has any errors
      const currentSetHasErrors = (() => {
        if (currentQuestionSetIndex === 0) {
          // Check if any general question has an error
          return GENERAL_QUESTION_KEYS.some((key) => validation.errors[key]);
        } else if (currentQuestionSetIndex === 9) {
          // Check if additional-info has an error
          return validation.errors["additional-info"] !== undefined;
        }
        return false;
      })();

      // Find the first error key
      const errorKeys = Object.keys(validation.errors);
      if (errorKeys.length > 0) {
        const firstErrorKey = errorKeys[0];

        // Only navigate if the current question set doesn't have errors
        // If it does have errors, stay on the current set
        if (!currentSetHasErrors) {
          // Map error keys to question set indices
          // General questions (job-level, job-boards, deep-mode, cover-letter-num, cover-letter-style) -> index 0
          // Additional info (additional-info) -> index 9
          let targetIndex = 0; // Default to general questions
          if (firstErrorKey === "additional-info") {
            targetIndex = 9;
          }
          // All other errors are in general questions (index 0)

          // Only navigate if the target index is different from the current visible one
          if (targetIndex !== currentQuestionSetIndex) {
            setActiveQuestionSetIndex(targetIndex);
          }
        }

        // Scroll to the first error question after a short delay to ensure DOM is ready
        setTimeout(() => {
          const errorQuestion = document.querySelector(
            `[data-question-key="${firstErrorKey}"]`
          );
          if (errorQuestion) {
            const rect = errorQuestion.getBoundingClientRect();
            const targetPosition = window.scrollY + rect.top - SCROLL_OFFSET;

            window.scrollTo({
              top: targetPosition,
              behavior: "smooth",
            });
          }
        }, SCROLL_DELAY + 50);
      }
      return;
    }

    // Clear validation errors if validation passes
    setValidationErrors({});
    setActiveQuestionSetIndex(undefined); // Clear active index when validation passes
    setIsSubmitting(true);
    setError(null);
    setSuccess(false);
    setCurrentPhase(null);

    // Transform form data into grouped structure for backend API
    const result = transformFormData(formData);

    // Send to backend using new SSE-based flow
    try {
      // Step 1: Start pipeline and get job_id
      const startResponse = await fetch(API_ENDPOINTS.START, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(result),
      });

      if (!startResponse.ok) {
        const errorData = await startResponse.json().catch(() => ({}));
        throw new Error(
          errorData.detail || `Server error: ${startResponse.status}`
        );
      }

      const { job_id } = await startResponse.json();
      setJobId(job_id);

      // Step 2: Connect to SSE progress stream
      const eventSource = new EventSource(
        `${API_ENDPOINTS.PROGRESS}/${job_id}`
      );
      eventSourceRef.current = eventSource;

      eventSource.onmessage = async (event) => {
        try {
          const data = JSON.parse(event.data);

          // Handle progress updates
          if (data.phase) {
            setCurrentPhase(data.phase);
          }

          // Handle completion
          if (data.status === "complete") {
            eventSource.close();
            eventSourceRef.current = null;

            // Download the document
            await downloadDocument(job_id, data.filename);

            // Show success message
            setSuccess(true);
            setError(null);
            submissionState.current.justCompleted = true;
            submissionState.current.hasSuccessfulSubmission = true;
            setIsSubmitting(false);
            setCurrentPhase(null);
            setJobId(null);

            // Auto-dismiss success message after timeout
            if (successTimeoutRef.current) {
              clearTimeout(successTimeoutRef.current);
            }
            successTimeoutRef.current = setTimeout(() => {
              setSuccess(false);
              successTimeoutRef.current = null;
            }, SUCCESS_MESSAGE_TIMEOUT);
          }
          // Handle errors
          else if (data.status === "error") {
            eventSource.close();
            eventSourceRef.current = null;
            setError(data.message || "An error occurred during processing");
            setIsSubmitting(false);
            setCurrentPhase(null);
            setJobId(null);
          }
          // Handle cancellation
          else if (data.status === "cancelled") {
            eventSource.close();
            eventSourceRef.current = null;
            setError("Pipeline was cancelled");
            setIsSubmitting(false);
            setCurrentPhase(null);
            setJobId(null);
          }
          // Handle SSE errors
          else if (data.error) {
            eventSource.close();
            eventSourceRef.current = null;
            setError(data.error);
            setIsSubmitting(false);
            setCurrentPhase(null);
            setJobId(null);
          }
        } catch (parseError) {
          console.error("Error parsing SSE event:", parseError);
        }
      };

      eventSource.onerror = (error) => {
        console.error("EventSource error:", error);
        eventSource.close();
        eventSourceRef.current = null;
        setError("Connection lost. Please try again.");
        setIsSubmitting(false);
        setCurrentPhase(null);
        setJobId(null);
      };
    } catch (error) {
      // Close EventSource if it was opened
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      setError(getErrorMessage(error));
      setSuccess(false);
      setIsSubmitting(false);
      setCurrentPhase(null);
      setJobId(null);
      submissionState.current.justCompleted = true;
    }
  };

  /**
   * Restores scroll position after component remounts and success message appears
   * Prevents page from jumping to top when download completes
   */
  useEffect(() => {
    if (!isSubmitting && submissionState.current.savedScrollPosition !== null) {
      const targetScroll = submissionState.current.savedScrollPosition;

      // Restore scroll position using requestAnimationFrame for smooth restoration
      const restoreScroll = () => {
        if (window.scrollY !== targetScroll) {
          window.scrollTo({
            top: targetScroll,
            behavior: "auto",
          });
        }
      };

      // Restore in next animation frame and after a brief delay to catch late DOM updates
      requestAnimationFrame(restoreScroll);
      const timeoutId = setTimeout(restoreScroll, SCROLL_DELAY);

      return () => clearTimeout(timeoutId);
    }
  }, [isSubmitting, success]);

  /**
   * Resets the submission completion flag after QuestionSetList has remounted
   * Ensures the skipInitialScroll prop is processed before resetting
   */
  useEffect(() => {
    if (!isSubmitting && submissionState.current.justCompleted) {
      // Reset the flag after a brief delay to ensure QuestionSetList has processed it
      const timeoutId = setTimeout(() => {
        submissionState.current.justCompleted = false;
        submissionState.current.savedScrollPosition = null; // Clear saved position
      }, 200);
      return () => clearTimeout(timeoutId);
    }
  }, [isSubmitting]);

  /**
   * Cleanup: Clear timeout and EventSource if component unmounts
   * Prevents memory leaks by clearing any pending timeouts and connections
   */
  useEffect(() => {
    return () => {
      if (successTimeoutRef.current) {
        clearTimeout(successTimeoutRef.current);
      }
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
    };
  }, []);

  /**
   * Handles pipeline cancellation
   * Sends cancel request to backend and closes SSE connection
   */
  const handleCancel = async () => {
    if (jobId && eventSourceRef.current) {
      try {
        await fetch(`${API_ENDPOINTS.CANCEL}/${jobId}`, {
          method: "POST",
        });
      } catch (error) {
        console.error("Error cancelling pipeline:", error);
      }
      eventSourceRef.current.close();
      eventSourceRef.current = null;
      setIsSubmitting(false);
      setCurrentPhase(null);
      setJobId(null);
      setError("Pipeline was cancelled");
    }
  };

  /**
   * Downloads the generated document
   * @param {string} jobId - Job identifier
   * @param {string} filename - Filename for the document (fallback if not in headers)
   */
  const downloadDocument = async (jobId, filename) => {
    try {
      const response = await fetch(`${API_ENDPOINTS.DOWNLOAD}/${jobId}`);

      if (!response.ok) {
        throw new Error(`Download failed: ${response.status}`);
      }

      // Save scroll position before download
      submissionState.current.savedScrollPosition =
        window.scrollY || window.pageYOffset;

      // Get the response as a blob
      const blob = await response.blob();

      // Download the file using response headers (which include Content-Disposition)
      // Fallback to provided filename if headers don't have it
      downloadBlob(blob, response.headers, filename);
    } catch (error) {
      console.error("Error downloading document:", error);
      throw error;
    }
  };

  return (
    <section id="search">
      <h2>Search</h2>
      {isSubmitting ? (
        // Loading state: show progress message
        <>
          <h3 className="text-base sm:text-xl md:text-2xl lg:text-3xl font-semibold text-white text-center">
            {currentPhase && phaseMessages[currentPhase]
              ? phaseMessages[currentPhase]
              : "Starting pipeline..."}
          </h3>
          <h3 className="text-base sm:text-xl md:text-2xl lg:text-3xl font-semibold text-white text-center">
            This might take a minute
          </h3>
        </>
      ) : submissionState.current.hasSuccessfulSubmission ? (
        // Success state: show completion message (stays visible even after success message disappears)
        <>
          <h3 className="text-base sm:text-xl md:text-2xl lg:text-3xl font-semibold text-white text-center">
            Here are your cover letters. Thank you very much.
          </h3>
        </>
      ) : (
        // Normal state: show full introductory text
        <>
          <h3 className="text-base sm:text-xl md:text-2xl lg:text-3xl font-semibold text-white text-center">
            <i>We will find jobs for you.</i>
          </h3>
          <h3 className="text-base sm:text-xl md:text-2xl lg:text-3xl font-semibold text-white text-center">
            And the way you can make sure we find <i>the most relevant jobs</i>{" "}
            and <i>write the best cover letters</i> is to provide us with a dose
            of information.
          </h3>
          <h3 className="text-base sm:text-xl md:text-2xl lg:text-3xl font-semibold text-white text-center">
            <i>We don't ask you for any personal information.</i>
          </h3>
          <h3 className="text-base sm:text-xl md:text-2xl lg:text-3xl font-semibold text-white text-center">
            By answering as many questions as possible, you enable us to use all
            tools in our arsenal when we scrape jobs for you. This is how we
            find the absolute gems. The questions are easy, and in most of them
            you just select the option that best describes you. Even if you felt
            like you didn't have much experience, be truthful -
          </h3>
          <h3 className="text-base sm:text-xl md:text-2xl lg:text-3xl font-semibold text-white text-center">
            <i>if there is a job matching your skills, we will find it.</i>
          </h3>
          <h3 className="text-base sm:text-xl md:text-2xl lg:text-3xl font-semibold text-white text-center">
            <i>Find Jobs</i> let's us start the search.
          </h3>
        </>
      )}
      {/* Question sets component with blue/gray background - contains all question sets and manages all form inputs */}
      {/* Only show question sets if not submitting AND not successfully completed */}
      {!isSubmitting &&
        !success &&
        !submissionState.current.hasSuccessfulSubmission && (
          <QuestionSetList
            onFormDataChange={handleFormDataChange}
            validationErrors={validationErrors}
            activeIndex={activeQuestionSetIndex}
            onActiveIndexChange={setActiveQuestionSetIndex}
            onCurrentIndexChange={setCurrentQuestionSetIndex}
            skipInitialScroll={submissionState.current.justCompleted}
          />
        )}
      {/* Success message - displayed when document is successfully downloaded */}
      {success && <SuccessMessage />}
      {/* Error message - displayed when submission fails */}
      {error && <ErrorMessage message={error} />}
      {/* Submit button and cancel button */}
      <div className="flex justify-center items-center gap-4 mt-6">
        <button
          id="submit-btn"
          onClick={handleSubmit}
          disabled={isSubmitting}
          className="text-lg sm:text-xl md:text-2xl lg:text-3xl px-4 sm:px-6 py-2 sm:py-3 border border-white bg-transparent text-white font-semibold rounded-lg shadow disabled:opacity-50 disabled:cursor-not-allowed"
          aria-label={
            submissionState.current.hasSuccessfulSubmission
              ? "Start a new job search"
              : "Submit form and generate job search document"
          }
        >
          {isSubmitting
            ? "Finding Jobs..."
            : submissionState.current.hasSuccessfulSubmission
            ? "Find Again"
            : "Find Jobs"}
        </button>
        {/* Cancel button - only show when pipeline is running */}
        {isSubmitting && jobId && (
          <button
            id="cancel-btn"
            onClick={handleCancel}
            className="text-base sm:text-lg md:text-xl lg:text-2xl px-3 sm:px-4 py-2 sm:py-3 border border-red-400 bg-transparent text-red-400 font-semibold rounded-lg shadow hover:bg-red-400 hover:text-white transition-colors"
            aria-label="Cancel the current job search"
          >
            Cancel
          </button>
        )}
      </div>
    </section>
  );
}

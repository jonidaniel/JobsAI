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
  // Track if we just completed a submission (to prevent scroll on remount)
  const justCompletedSubmission = useRef(false);
  // Store scroll position to restore after download
  const savedScrollPosition = useRef(null);
  // Track if we've had a successful submission (to keep question sets hidden)
  const hasSuccessfulSubmission = useRef(false);

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

    // If this is a "Find Again" click, navigate to question set 1 and reset
    if (hasSuccessfulSubmission.current) {
      // Reset states
      setError(null);
      setSuccess(false);
      justCompletedSubmission.current = false;
      hasSuccessfulSubmission.current = false;
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
    justCompletedSubmission.current = false;
    // Reset successful submission flag when starting a new submission
    hasSuccessfulSubmission.current = false;

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

    // Transform form data into grouped structure for backend API
    const result = transformFormData(formData);

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

      // Save scroll position before any state changes
      savedScrollPosition.current = window.scrollY || window.pageYOffset;

      // Download the file
      downloadBlob(blob, response.headers);

      // Show success message
      setSuccess(true);
      setError(null);
      justCompletedSubmission.current = true;
      hasSuccessfulSubmission.current = true;

      // Auto-dismiss success message after 5 seconds (but keep the text visible)
      // Clear any existing timeout first to prevent multiple timers
      if (successTimeoutRef.current) {
        clearTimeout(successTimeoutRef.current);
      }
      successTimeoutRef.current = setTimeout(() => {
        setSuccess(false); // Hide the green success message, but text stays via hasSuccessfulSubmission
        successTimeoutRef.current = null;
      }, SUCCESS_MESSAGE_TIMEOUT);
    } catch (error) {
      setError(getErrorMessage(error));
      setSuccess(false);
      justCompletedSubmission.current = true;
    } finally {
      // Reset submission flag after request completes (success or error)
      setIsSubmitting(false);
    }
  };

  // Restore scroll position after component remounts and success message appears
  useEffect(() => {
    if (!isSubmitting && savedScrollPosition.current !== null) {
      const targetScroll = savedScrollPosition.current;

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

  // Reset the submission completion flag after QuestionSetList has remounted
  useEffect(() => {
    if (!isSubmitting && justCompletedSubmission.current) {
      // Reset the flag after a brief delay to ensure QuestionSetList has processed it
      const timeoutId = setTimeout(() => {
        justCompletedSubmission.current = false;
        savedScrollPosition.current = null; // Clear saved position
      }, 200);
      return () => clearTimeout(timeoutId);
    }
  }, [isSubmitting]);

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
      {isSubmitting ? (
        // Loading state: show simplified message
        <>
          <h3 className="text-base sm:text-xl md:text-2xl lg:text-3xl font-semibold text-white text-center">
            Finding jobs for you right now
          </h3>
          <h3 className="text-base sm:text-xl md:text-2xl lg:text-3xl font-semibold text-white text-center">
            This might take a minute
          </h3>
        </>
      ) : hasSuccessfulSubmission.current ? (
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
      {!isSubmitting && !success && !hasSuccessfulSubmission.current && (
        <QuestionSetList
          onFormDataChange={handleFormDataChange}
          validationErrors={validationErrors}
          activeIndex={activeQuestionSetIndex}
          onActiveIndexChange={setActiveQuestionSetIndex}
          onCurrentIndexChange={setCurrentQuestionSetIndex}
          skipInitialScroll={justCompletedSubmission.current}
        />
      )}
      {/* Success message - displayed when document is successfully downloaded */}
      {success && <SuccessMessage />}
      {/* Error message - displayed when submission fails */}
      {error && <ErrorMessage message={error} />}
      {/* Black 'Find Jobs' / 'Find Again' submit button - triggers form submission and document generation */}
      <div className="flex justify-center mt-6">
        <button
          id="submit-btn"
          onClick={handleSubmit}
          disabled={isSubmitting}
          className="text-lg sm:text-xl md:text-2xl lg:text-3xl px-4 sm:px-6 py-2 sm:py-3 border border-white bg-transparent text-white font-semibold rounded-lg shadow disabled:opacity-50 disabled:cursor-not-allowed"
          aria-label={
            hasSuccessfulSubmission.current
              ? "Start a new job search"
              : "Submit form and generate job search document"
          }
        >
          {isSubmitting
            ? "Finding Jobs..."
            : hasSuccessfulSubmission.current
            ? "Find Again"
            : "Find Jobs"}
        </button>
      </div>
    </section>
  );
}

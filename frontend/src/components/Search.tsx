import { useState, useEffect, useRef, useCallback, useMemo } from "react";

import QuestionSetList from "./QuestionSetList";
import ErrorMessage from "./messages/ErrorMessage";

import { API_ENDPOINTS } from "../config/api";

import { transformFormData } from "../utils/formDataTransform";
import { getErrorMessage } from "../utils/errorMessages";
import { validateGeneralQuestions } from "../utils/validation";
import { GENERAL_QUESTION_KEYS } from "../config/generalQuestions";
import {
  SUCCESS_MESSAGE_TIMEOUT,
  SCROLL_OFFSET,
  SCROLL_DELAY,
} from "../config/constants";
import { usePipelinePolling } from "../hooks/usePipelinePolling";
import { useDownload } from "../hooks/useDownload";

import "../styles/search.css";
import type {
  FormData,
  ValidationErrors,
  PipelinePhase,
  DownloadInfo,
} from "../types";

// Phase messages mapping - moved outside component to avoid recreation on each render
const PHASE_MESSAGES: Record<PipelinePhase, string> = {
  profiling: "2/6 Creating your profile...",
  searching: "3/6 Searching for jobs...",
  scoring: "4/6 Scoring the jobs...",
  analyzing: "5/6 Doing analysis...",
  generating: "6/6 Generating cover letters...",
};

interface SubmissionState {
  justCompleted: boolean;
  savedScrollPosition: number | null;
  hasSuccessfulSubmission: boolean;
}

type DeliveryMethod = "email" | "download" | null;

/**
 * Search Component - Main Questionnaire and Pipeline Interface.
 *
 * This is the primary component for the JobsAI application. It manages the complete
 * user flow from questionnaire completion through pipeline execution to document download.
 */
export default function Search() {
  // Submission state management
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  // Progress tracking with polling
  const [currentPhase, setCurrentPhase] = useState<PipelinePhase | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  // Track current jobId in a ref to prevent stale polling updates
  const currentJobIdRef = useRef<string | null>(null);
  // Delivery method selection state
  const [showDeliveryMethodPrompt, setShowDeliveryMethodPrompt] =
    useState(false);
  const [deliveryMethod, setDeliveryMethod] = useState<DeliveryMethod>(null);
  const [email, setEmail] = useState("");
  const [emailError, setEmailError] = useState<string | null>(null);
  // Cancellation state
  const [isCancelled, setIsCancelled] = useState(false);
  // Download prompt state
  const [showDownloadPrompt, setShowDownloadPrompt] = useState(false);
  const [downloadInfo, setDownloadInfo] = useState<DownloadInfo | null>(null);
  const [declinedDocumentCount, setDeclinedDocumentCount] = useState<
    number | null
  >(null);
  const [hasDownloaded, setHasDownloaded] = useState(false);
  const [hasRespondedToPrompt, setHasRespondedToPrompt] = useState(false);
  const [isRateLimited, setIsRateLimited] = useState(false);
  // Consolidated submission state ref
  const submissionState = useRef<SubmissionState>({
    justCompleted: false,
    savedScrollPosition: null,
    hasSuccessfulSubmission: false,
  });

  // Form data received from QuestionSets component via callback
  const [formData, setFormData] = useState<FormData>({});

  // Validation errors for general questions
  const [validationErrors, setValidationErrors] = useState<ValidationErrors>(
    {}
  );

  // Active question set index (for navigating to error location)
  const [activeQuestionSetIndex, setActiveQuestionSetIndex] = useState<
    number | undefined
  >(undefined);
  // Current question set index (tracked from QuestionSetList)
  const [currentQuestionSetIndex, setCurrentQuestionSetIndex] = useState(0);

  /**
   * Scrolls to an element by selector with offset
   */
  const scrollToElement = useCallback(
    (selector: string, delay: number = SCROLL_DELAY): void => {
      setTimeout(() => {
        const element = document.querySelector(selector);
        if (element) {
          const rect = element.getBoundingClientRect();
          const targetPosition = window.scrollY + rect.top - SCROLL_OFFSET;
          window.scrollTo({
            top: targetPosition,
            behavior: "smooth",
          });
        }
      }, delay);
    },
    []
  );

  /**
   * Resets all form and submission state
   */
  const resetFormState = useCallback((includeSubmissionState = false): void => {
    setError(null);
    setSuccess(false);
    submissionState.current.justCompleted = false;
    submissionState.current.hasSuccessfulSubmission = false;
    setShowDownloadPrompt(false);
    setDownloadInfo(null);
    setDeclinedDocumentCount(null);
    setHasDownloaded(false);
    setHasRespondedToPrompt(false);
    setShowDeliveryMethodPrompt(false);
    setDeliveryMethod(null);
    setEmail("");
    setEmailError(null);
    setIsCancelled(false);
    setIsRateLimited(false);
    if (includeSubmissionState) {
      setIsSubmitting(false);
      setCurrentPhase(null);
      setJobId(null);
      currentJobIdRef.current = null;
    }
  }, []);

  /**
   * Handles form data changes from QuestionSetList component
   */
  const handleFormDataChange = useCallback((newFormData: FormData): void => {
    setFormData(newFormData);
  }, []);

  /**
   * Clears validation errors when user fixes them
   */
  useEffect(() => {
    // Only validate if there are existing errors (user is fixing them)
    if (Object.keys(validationErrors).length > 0) {
      const validation = validateGeneralQuestions(formData);
      if (validation.isValid) {
        setValidationErrors({});
      } else {
        // Update validation errors to reflect current state
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
  const successTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Memoize cover letter count to avoid repeated parseInt calls
  const coverLetterNumValue = formData["cover-letter-num"];
  const coverLetterCount = useMemo(() => {
    const value =
      typeof coverLetterNumValue === "string"
        ? coverLetterNumValue
        : String(coverLetterNumValue || "1");
    return parseInt(value, 10);
  }, [coverLetterNumValue]);

  // Custom hooks for polling and downloads
  const { startPolling, stopPolling } = usePipelinePolling({
    setCurrentPhase,
    setIsSubmitting,
    setError,
    setJobId,
    setDownloadInfo,
    setShowDownloadPrompt,
    setSuccess,
    submissionState,
    currentJobIdRef,
  });

  const { handleDownloadYes } = useDownload({
    downloadInfo,
    submissionState,
    successTimeoutRef,
    setShowDownloadPrompt,
    setDownloadInfo,
    setHasDownloaded,
    setHasRespondedToPrompt,
    setSuccess,
    setError,
  });

  /**
   * Handles form submission or button click
   */
  const handleSubmit = async (
    e?: React.FormEvent<HTMLFormElement> | React.MouseEvent<HTMLButtonElement>
  ): Promise<void> => {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }

    // If this is a "Find Again" click while submitting, just reset UI
    // (Note: email delivery should never be in submitting state, but handle it anyway)
    if (isSubmitting) {
      stopPolling();
      resetFormState(true);
      setActiveQuestionSetIndex(0);
      scrollToElement('[data-index="0"]');
      return;
    }

    // If this is a "Find Again" click (from successful submission or cancellation), navigate to question set 1 and reset
    if (submissionState.current.hasSuccessfulSubmission || isCancelled) {
      resetFormState(false);
      setActiveQuestionSetIndex(0);
      scrollToElement('[data-index="0"]');
      return;
    }

    // Clear previous errors and success messages
    setError(null);
    setSuccess(false);
    submissionState.current.justCompleted = false;
    submissionState.current.hasSuccessfulSubmission = false;
    setShowDownloadPrompt(false);
    setDownloadInfo(null);
    setDeclinedDocumentCount(null);
    setHasDownloaded(false);
    setDeliveryMethod(null);
    setEmail("");
    setEmailError(null);
    setIsCancelled(false);
    setIsRateLimited(false);

    // Validate general questions before submission
    const validation = validateGeneralQuestions(formData);
    if (!validation.isValid) {
      setValidationErrors(validation.errors);

      // Check if the current question set has any errors
      const currentSetHasErrors = (() => {
        if (currentQuestionSetIndex === 0) {
          return GENERAL_QUESTION_KEYS.some(
            (key) => validation.errors[key as string]
          );
        } else if (currentQuestionSetIndex === 9) {
          return validation.errors["additional-info"] !== undefined;
        }
        return false;
      })();

      // Find the first error key
      const errorKeys = Object.keys(validation.errors);
      if (errorKeys.length > 0) {
        const firstErrorKey = errorKeys[0];

        // Only navigate if the current question set doesn't have errors
        if (!currentSetHasErrors) {
          let targetIndex = 0;
          if (firstErrorKey === "additional-info") {
            targetIndex = 9;
          }

          if (targetIndex !== currentQuestionSetIndex) {
            setActiveQuestionSetIndex(targetIndex);
          }
        }

        scrollToElement(
          `[data-question-key="${firstErrorKey}"]`,
          SCROLL_DELAY + 50
        );
      }
      return;
    }

    // Clear validation errors if validation passes
    setValidationErrors({});
    setActiveQuestionSetIndex(undefined);

    // Show delivery method selection prompt instead of starting pipeline immediately
    setShowDeliveryMethodPrompt(true);
    setDeliveryMethod(null);
    setEmail("");
    setEmailError(null);
    setError(null);
    setSuccess(false);
  };

  /**
   * Validates email address format
   */
  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  /**
   * Handles the delivery method selection.
   */
  const handleDeliveryMethod = (method: "email" | "download"): void => {
    setDeliveryMethod(method);
    setEmailError(null);

    if (method === "download") {
      setShowDeliveryMethodPrompt(false);
      startPipeline();
    }
  };

  /**
   * Handles email submission when user clicks "Continue" after entering email
   */
  const handleEmailSubmit = async (): Promise<void> => {
    // Validate email
    if (!email || !email.trim()) {
      setEmailError("Email address is required");
      return;
    }

    if (!validateEmail(email)) {
      setEmailError("Please enter a valid email address");
      return;
    }

    // Clear errors and start pipeline
    setEmailError(null);
    setShowDeliveryMethodPrompt(false);
    await startPipeline();
  };

  /**
   * Starts the pipeline after delivery method is selected.
   */
  const startPipeline = async (): Promise<void> => {
    setIsSubmitting(true);
    setError(null);
    setSuccess(false);
    setCurrentPhase(null);

    // Transform form data into grouped structure for backend API
    const result = transformFormData(formData);

    // Add delivery method and email to payload
    if (deliveryMethod === "email") {
      (result as Record<string, unknown>).delivery_method = "email";
      (result as Record<string, unknown>).email = email;
    } else {
      (result as Record<string, unknown>).delivery_method = "download";
    }

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
        // Check if this is a rate limit error (429) BEFORE parsing JSON
        if (startResponse.status === 429) {
          console.log("Rate limit detected: 429 status code");
          setIsRateLimited(true);
          setError(null);
          setIsSubmitting(false);
          setShowDeliveryMethodPrompt(false);
          setDeliveryMethod(null);
          setEmail("");
          setEmailError(null);
          setCurrentPhase(null);
          setJobId(null);
          setDownloadInfo(null);
          setShowDownloadPrompt(false);
          setHasDownloaded(false);
          setHasRespondedToPrompt(false);
          setIsCancelled(false);
          submissionState.current.hasSuccessfulSubmission = false;
          submissionState.current.justCompleted = false;
          console.log("Rate limit state set, isRateLimited should be true");
          return;
        }
        // For other errors, parse JSON and throw
        const errorData = (await startResponse.json().catch(() => ({}))) as {
          error?: string;
          detail?: string;
        };
        if (
          errorData.error === "too_many_requests" ||
          errorData.detail?.includes("Rate limit exceeded")
        ) {
          setIsRateLimited(true);
          setError(null);
          setIsSubmitting(false);
          setShowDeliveryMethodPrompt(false);
          setDeliveryMethod(null);
          setEmail("");
          setEmailError(null);
          setCurrentPhase(null);
          setJobId(null);
          submissionState.current.hasSuccessfulSubmission = false;
          submissionState.current.justCompleted = false;
          return;
        }
        throw new Error(
          errorData.detail || `Server error: ${startResponse.status}`
        );
      }

      const { job_id } = (await startResponse.json()) as { job_id: string };

      // For email delivery: fire-and-forget, no polling, no UI updates
      if (deliveryMethod === "email") {
        // Reset UI state immediately - let pipeline run in background
        setIsSubmitting(false);
        setShowDeliveryMethodPrompt(false);
        setDeliveryMethod(null);
        setEmail("");
        setEmailError(null);
        setCurrentPhase(null);
        setJobId(null);
        currentJobIdRef.current = null;
        // Don't track this job at all - completely fire-and-forget
        return;
      }

      // For download delivery: track progress with polling
      setJobId(job_id);
      startPolling(job_id);
    } catch (error) {
      // Only handle errors for download delivery or rate limiting
      // For email delivery errors (except rate limit), fail silently
      if (deliveryMethod === "email") {
        // For email, only show rate limit errors, ignore everything else
        const errorMessage = getErrorMessage(error);
        if (errorMessage === "RATE_LIMIT_EXCEEDED" || isRateLimited) {
          setIsRateLimited(true);
          setError(null);
        }
        // Reset UI state even on error (except rate limit)
        setIsSubmitting(false);
        setShowDeliveryMethodPrompt(false);
        setDeliveryMethod(null);
        setEmail("");
        setEmailError(null);
        setCurrentPhase(null);
        setJobId(null);
        currentJobIdRef.current = null;
        return;
      }

      // For download delivery: handle all errors normally
      stopPolling();
      const errorMessage = getErrorMessage(error);
      if (errorMessage === "RATE_LIMIT_EXCEEDED") {
        setIsRateLimited(true);
        setError(null);
        setShowDeliveryMethodPrompt(false);
        setDeliveryMethod(null);
        setEmail("");
        setEmailError(null);
        submissionState.current.hasSuccessfulSubmission = false;
        submissionState.current.justCompleted = false;
      } else if (!isRateLimited) {
        setError(errorMessage);
      }
      setSuccess(false);
      setIsSubmitting(false);
      setCurrentPhase(null);
      setJobId(null);
      currentJobIdRef.current = null;
      submissionState.current.justCompleted = true;
    }
  };

  /**
   * Restores scroll position after component remounts and success message appears
   */
  useEffect(() => {
    if (!isSubmitting && submissionState.current.savedScrollPosition !== null) {
      const targetScroll = submissionState.current.savedScrollPosition;

      const restoreScroll = (): void => {
        if (window.scrollY !== targetScroll) {
          window.scrollTo({
            top: targetScroll,
            behavior: "auto",
          });
        }
      };

      requestAnimationFrame(restoreScroll);
      const timeoutId = setTimeout(restoreScroll, SCROLL_DELAY);

      return () => clearTimeout(timeoutId);
    }
  }, [isSubmitting, success]);

  /**
   * Resets the submission completion flag after QuestionSetList has remounted
   */
  useEffect(() => {
    if (!isSubmitting && submissionState.current.justCompleted) {
      const timeoutId = setTimeout(() => {
        submissionState.current.justCompleted = false;
        submissionState.current.savedScrollPosition = null;
      }, 200);
      return () => clearTimeout(timeoutId);
    }
  }, [isSubmitting]);

  /**
   * Cleanup: Clear timeout and polling interval if component unmounts
   */
  useEffect(() => {
    const timeoutRef = successTimeoutRef;
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      stopPolling();
    };
  }, [stopPolling]);

  /**
   * Handles pipeline cancellation
   */
  const handleCancel = async (): Promise<void> => {
    stopPolling();

    if (jobId) {
      try {
        await fetch(`${API_ENDPOINTS.CANCEL}/${jobId}`, {
          method: "POST",
        });
      } catch (error) {
        console.error("Error cancelling pipeline:", error);
      }
    }

    setIsSubmitting(false);
    setCurrentPhase(null);
    setJobId(null);
    currentJobIdRef.current = null;
    setShowDeliveryMethodPrompt(false);
    setIsCancelled(true);
    setError(null);
  };

  return (
    <section id="search">
      <h2>Search</h2>
      {isRateLimited ? (
        <>
          <h3 className="text-base sm:text-xl md:text-2xl lg:text-3xl font-semibold text-white text-center">
            You've made too many searches lately
            <br />
            Try again later
          </h3>
        </>
      ) : isSubmitting && deliveryMethod === "email" ? (
        <>
          <h3 className="text-base sm:text-xl md:text-2xl lg:text-3xl font-semibold text-white text-center">
            <i>Thank you very much for using JobsAI</i>
            <br />
            Expect the cover {coverLetterCount === 1 ? "letter" : "letters"} to
            drop in your inbox shortly
          </h3>
        </>
      ) : isSubmitting ? (
        <>
          <h3 className="text-base sm:text-xl md:text-2xl lg:text-3xl font-semibold text-white text-center">
            {currentPhase && PHASE_MESSAGES[currentPhase]
              ? PHASE_MESSAGES[currentPhase]
              : "1/6 Starting search..."}
          </h3>
          <h3 className="text-base sm:text-xl md:text-2xl lg:text-3xl font-semibold text-white text-center">
            This might take a few minutes
          </h3>
        </>
      ) : showDeliveryMethodPrompt ? (
        <>
          {!deliveryMethod ? (
            <>
              <h3 className="text-base sm:text-xl md:text-2xl lg:text-3xl font-semibold text-white text-center">
                Choose delivery method for the cover{" "}
                {coverLetterCount === 1 ? "letter" : "letters"}
              </h3>
              <div className="flex justify-center items-center gap-4 mt-6">
                <button
                  onClick={() => handleDeliveryMethod("email")}
                  className="text-base sm:text-lg md:text-xl lg:text-2xl px-3 sm:px-4 py-1.5 sm:py-2 border border-white bg-transparent text-white font-semibold rounded-lg shadow hover:bg-white hover:text-gray-800 transition-all"
                  aria-label="Via email when ready"
                >
                  Via email
                  <br />
                  when ready
                </button>
                <button
                  onClick={() => handleDeliveryMethod("download")}
                  className="text-base sm:text-lg md:text-xl lg:text-2xl px-3 sm:px-4 py-1.5 sm:py-2 border border-white bg-transparent text-white font-semibold rounded-lg shadow hover:bg-white hover:text-gray-800 transition-all"
                  aria-label="Via browser download (might take minutes)"
                >
                  Via browser download
                  <br />
                  (might take minutes)
                </button>
              </div>
            </>
          ) : deliveryMethod === "email" ? (
            <>
              <h3 className="text-base sm:text-xl md:text-2xl lg:text-3xl font-semibold text-white text-center">
                Enter your email address
              </h3>
              <div className="flex flex-col items-center gap-4 mt-6">
                <input
                  type="email"
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                    setEmailError(null);
                  }}
                  placeholder="your.email@example.com"
                  className="text-base sm:text-lg md:text-xl lg:text-2xl px-4 py-2 border border-white bg-transparent text-white placeholder-gray-400 rounded-lg shadow focus:outline-none focus:ring-2 focus:ring-white w-full max-w-md"
                  aria-label="Email address"
                  aria-invalid={emailError ? "true" : "false"}
                  aria-describedby={emailError ? "email-error" : undefined}
                />
                {emailError && (
                  <p
                    id="email-error"
                    className="text-sm sm:text-base text-red-400 text-center"
                  >
                    {emailError}
                  </p>
                )}
                <div className="flex justify-center items-center gap-4">
                  <button
                    onClick={() => {
                      setDeliveryMethod(null);
                      setEmail("");
                      setEmailError(null);
                    }}
                    className="text-base sm:text-lg md:text-xl lg:text-2xl px-3 sm:px-4 py-1.5 sm:py-2 border border-white bg-transparent text-white font-semibold rounded-lg shadow hover:bg-white hover:text-gray-800 transition-all"
                    aria-label="Go back to delivery method selection"
                  >
                    Back
                  </button>
                  <button
                    onClick={handleEmailSubmit}
                    className="text-base sm:text-lg md:text-xl lg:text-2xl px-3 sm:px-4 py-1.5 sm:py-2 border border-white bg-transparent text-white font-semibold rounded-lg shadow hover:bg-white hover:text-gray-800 transition-all"
                    aria-label="Continue with email delivery"
                  >
                    Continue
                  </button>
                </div>
              </div>
            </>
          ) : null}
        </>
      ) : showDownloadPrompt && downloadInfo ? (
        <>
          <h3 className="text-base sm:text-xl md:text-2xl lg:text-3xl font-semibold text-white text-center">
            All set! Generated {downloadInfo.filenames.length} cover letter
            {downloadInfo.filenames.length !== 1 ? "s" : ""}
          </h3>
          <div className="flex justify-center items-center gap-4 mt-6">
            <button
              onClick={handleDownloadYes}
              className="text-base sm:text-lg md:text-xl lg:text-2xl px-3 sm:px-4 py-1.5 sm:py-2 border border-white bg-transparent text-white font-semibold rounded-lg shadow hover:bg-white hover:text-gray-800 transition-all"
              aria-label="Download the cover letters"
            >
              Download
            </button>
          </div>
        </>
      ) : isCancelled ? (
        <>
          <h3 className="text-base sm:text-xl md:text-2xl lg:text-3xl font-semibold text-white text-center">
            You cancelled the job search
          </h3>
        </>
      ) : submissionState.current.hasSuccessfulSubmission &&
        deliveryMethod === "email" &&
        hasRespondedToPrompt ? (
        <>
          <h3 className="text-base sm:text-xl md:text-2xl lg:text-3xl font-semibold text-white text-center">
            Thank you very much for using JobsAI. Expect the cover{" "}
            {parseInt((formData["cover-letter-num"] as string) || "1", 10) === 1
              ? "letter"
              : "letters"}{" "}
            to drop in your inbox shortly
          </h3>
        </>
      ) : submissionState.current.hasSuccessfulSubmission &&
        hasRespondedToPrompt &&
        !hasDownloaded ? (
        <>
          <h3 className="text-base sm:text-xl md:text-2xl lg:text-3xl font-semibold text-white text-center">
            You turned down the{" "}
            {declinedDocumentCount === 1 ? "document" : "documents"}
          </h3>
        </>
      ) : submissionState.current.hasSuccessfulSubmission && hasDownloaded ? (
        <>
          <h3 className="text-base sm:text-xl md:text-2xl lg:text-3xl font-semibold text-white text-center">
            <i>Thank you very much for using JobsAI</i>
            <br />
            Feel free to do another search
          </h3>
        </>
      ) : (
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
      {/* Question sets component */}
      {!isSubmitting &&
        !showDeliveryMethodPrompt &&
        !isCancelled &&
        !success &&
        !isRateLimited &&
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
      {/* Error message */}
      {error && !isRateLimited && <ErrorMessage message={error} />}
      {/* Submit button and cancel button */}
      {!isRateLimited && (
        <div className="flex justify-center items-center gap-4 mt-6">
          {isCancelled && (
            <button
              id="submit-btn"
              onClick={handleSubmit}
              className="text-lg sm:text-xl md:text-2xl lg:text-3xl px-4 sm:px-6 py-2 sm:py-3 border border-white bg-transparent text-white font-semibold rounded-lg shadow disabled:opacity-50 disabled:cursor-not-allowed"
              aria-label="Start a new job search"
            >
              Find Again
            </button>
          )}
          {isSubmitting && deliveryMethod === "email" && (
            <button
              id="submit-btn"
              onClick={handleSubmit}
              className="text-lg sm:text-xl md:text-2xl lg:text-3xl px-4 sm:px-6 py-2 sm:py-3 border border-white bg-transparent text-white font-semibold rounded-lg shadow disabled:opacity-50 disabled:cursor-not-allowed"
              aria-label="Start a new job search"
            >
              Find Again
            </button>
          )}
          {!isSubmitting &&
            submissionState.current.hasSuccessfulSubmission &&
            deliveryMethod === "email" &&
            hasRespondedToPrompt && (
              <button
                id="submit-btn"
                onClick={handleSubmit}
                className="text-lg sm:text-xl md:text-2xl lg:text-3xl px-4 sm:px-6 py-2 sm:py-3 border border-white bg-transparent text-white font-semibold rounded-lg shadow disabled:opacity-50 disabled:cursor-not-allowed"
                aria-label="Start a new job search"
              >
                Find Again
              </button>
            )}
          {!isSubmitting &&
            !showDeliveryMethodPrompt &&
            !isCancelled &&
            (!submissionState.current.hasSuccessfulSubmission ||
              hasRespondedToPrompt) && (
              <form onSubmit={handleSubmit}>
                <button
                  id="submit-btn"
                  type="submit"
                  className="text-lg sm:text-xl md:text-2xl lg:text-3xl px-4 sm:px-6 py-2 sm:py-3 border border-white bg-transparent text-white font-semibold rounded-lg shadow disabled:opacity-50 disabled:cursor-not-allowed"
                  aria-label={
                    submissionState.current.hasSuccessfulSubmission &&
                    hasRespondedToPrompt
                      ? "Start a new job search"
                      : "Submit form and generate job search document"
                  }
                >
                  {submissionState.current.hasSuccessfulSubmission &&
                  hasRespondedToPrompt
                    ? "Find Again"
                    : "Find Jobs"}
                </button>
              </form>
            )}
          {isSubmitting && deliveryMethod !== "email" && (
            <button
              id="cancel-btn"
              onClick={handleCancel}
              className="text-base sm:text-lg md:text-xl lg:text-2xl px-3 sm:px-4 py-2 sm:py-3 border border-red-400 bg-transparent text-red-400 font-semibold rounded-lg shadow hover:bg-red-400 hover:text-white transition-all"
              aria-label="Cancel the current job search"
            >
              Cancel
            </button>
          )}
        </div>
      )}
    </section>
  );
}

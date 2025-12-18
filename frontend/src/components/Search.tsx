import { useState, useEffect, useRef, useCallback, useMemo } from "react";

import QuestionSetList from "./QuestionSetList";
import ErrorMessage from "./messages/ErrorMessage";
import DeliveryMethodSelector from "./delivery/DeliveryMethodSelector";
import ProgressTracker from "./progress/ProgressTracker";
import StatusMessages from "./status/StatusMessages";
import DownloadPrompt from "./download/DownloadPrompt";
import ActionButtons from "./actions/ActionButtons";

import { API_ENDPOINTS } from "../config/api";

import { validateGeneralQuestions } from "../utils/validation";
import { SCROLL_OFFSET, SCROLL_DELAY } from "../config/constants";
import { usePipelinePolling } from "../hooks/usePipelinePolling";
import { useDownload } from "../hooks/useDownload";
import { useFormSubmission } from "../hooks/useFormSubmission";

import "../styles/search.css";
import type {
  FormData,
  ValidationErrors,
  PipelinePhase,
  DownloadInfo,
} from "../types";
import type { DeliveryMethod } from "./delivery/types";

interface SubmissionState {
  justCompleted: boolean;
  savedScrollPosition: number | null;
  hasSuccessfulSubmission: boolean;
}

/**
 * Search Component - Main Questionnaire and Pipeline Interface.
 *
 * This is the primary component for the JobsAI application. It manages the complete
 * user flow from questionnaire completion through pipeline execution to document download.
 *
 * Responsibilities:
 * - Form validation and submission
 * - Delivery method selection (email vs browser download)
 * - Pipeline initiation and progress tracking
 * - Error handling and user feedback
 * - Document download management
 * - UI state management for all submission states
 *
 * State Management:
 * This component manages extensive state (15+ useState hooks) including:
 * - Submission state (isSubmitting, error, currentPhase, jobId)
 * - Delivery method state (deliveryMethod, email, emailError)
 * - Download state (downloadInfo, showDownloadPrompt, hasDownloaded)
 * - Form state (formData, validationErrors)
 * - UI state (showDeliveryMethodPrompt, isRateLimited, isCancelled)
 * - Submission state ref (justCompleted, savedScrollPosition, hasSuccessfulSubmission)
 *
 * Key Features:
 * - Client-side form validation before submission
 * - Async pipeline execution with progress polling (download delivery)
 * - Fire-and-forget email delivery (no polling, persistent UI message)
 * - Scroll position preservation during downloads
 * - Rate limit detection and user feedback
 * - Pipeline cancellation support
 *
 * Custom Hooks Used:
 * - usePipelinePolling: Polls backend for pipeline progress
 * - useDownload: Handles document downloads from S3
 *
 * Note: This component is large (800+ lines) and could benefit from being split
 * into smaller components (FormSubmission, DeliveryMethodSelector, ProgressTracker, etc.)
 */
export default function Search() {
  // Submission state management
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
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
    submissionState.current.justCompleted = false;
    submissionState.current.hasSuccessfulSubmission = false;
    setShowDownloadPrompt(false);
    setDownloadInfo(null);
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
    submissionState,
    currentJobIdRef,
  });

  const { handleDownloadYes } = useDownload({
    downloadInfo,
    submissionState,
    setShowDownloadPrompt,
    setDownloadInfo,
    setHasDownloaded,
    setHasRespondedToPrompt,
    setError,
  });

  // Form submission hook
  const {
    handleSubmit: handleFormSubmit,
    startPipeline,
    validateEmail,
  } = useFormSubmission({
    formData,
    deliveryMethod,
    email,
    currentQuestionSetIndex,
    isRateLimited,
    setError,
    setValidationErrors,
    setActiveQuestionSetIndex,
    setIsRateLimited,
    setShowDeliveryMethodPrompt,
    setDeliveryMethod,
    setEmail,
    setEmailError,
    setIsSubmitting,
    setCurrentPhase,
    setJobId,
    setDownloadInfo,
    setShowDownloadPrompt,
    setHasDownloaded,
    setHasRespondedToPrompt,
    setIsCancelled,
    submissionState,
    currentJobIdRef,
    startPolling,
    scrollToElement,
  });

  /**
   * Handles form submission or button click (wrapper for "Find Again" logic)
   */
  const handleSubmit = async (
    e?: React.FormEvent<HTMLFormElement> | React.MouseEvent<HTMLButtonElement>
  ): Promise<void> => {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }

    // If this is a "Find Again" click while submitting, just reset UI
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

    // Otherwise, delegate to form submission handler
    await handleFormSubmit(e);
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
   * Restores scroll position after component remounts
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
  }, [isSubmitting]);

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
   * Cleanup: Stop polling if component unmounts
   */
  useEffect(() => {
    return () => {
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

  // Determine what to render based on state
  const shouldShowProgressTracker =
    isSubmitting && deliveryMethod !== "email" && !isRateLimited;
  const shouldShowDeliverySelector = showDeliveryMethodPrompt && !isSubmitting;
  const shouldShowDownloadPrompt = showDownloadPrompt && downloadInfo;

  // Show status messages (intro text or other status messages) when:
  // - Initial state (not submitting, not cancelled, not rate limited, not successful)
  // - OR during email submission (to show thank you message)
  // - OR rate limited
  // - OR cancelled
  // - OR after successful download
  const shouldShowStatusMessages =
    (!isSubmitting &&
      !isCancelled &&
      !isRateLimited &&
      !submissionState.current.hasSuccessfulSubmission) ||
    (isSubmitting && deliveryMethod === "email") ||
    isRateLimited ||
    isCancelled ||
    (submissionState.current.hasSuccessfulSubmission && hasDownloaded);

  return (
    <section id="search">
      <h2>Search</h2>
      {shouldShowProgressTracker && (
        <ProgressTracker currentPhase={currentPhase} />
      )}
      {shouldShowDeliverySelector && (
        <DeliveryMethodSelector
          deliveryMethod={deliveryMethod}
          email={email}
          emailError={emailError}
          coverLetterCount={coverLetterCount}
          onMethodSelect={handleDeliveryMethod}
          onEmailChange={(newEmail) => {
            setEmail(newEmail);
            setEmailError(null);
          }}
          onEmailSubmit={handleEmailSubmit}
          onBack={() => {
            setDeliveryMethod(null);
            setEmail("");
            setEmailError(null);
          }}
        />
      )}
      {shouldShowDownloadPrompt && downloadInfo && (
        <DownloadPrompt
          filenameCount={downloadInfo.filenames.length}
          onDownload={handleDownloadYes}
        />
      )}
      {shouldShowStatusMessages && (
        <StatusMessages
          isRateLimited={isRateLimited}
          isSubmitting={isSubmitting}
          deliveryMethod={deliveryMethod}
          coverLetterCount={coverLetterCount}
          isCancelled={isCancelled}
          hasSuccessfulSubmission={
            submissionState.current.hasSuccessfulSubmission
          }
          hasDownloaded={hasDownloaded}
        />
      )}
      {/* Question sets component */}
      {!isSubmitting &&
        !showDeliveryMethodPrompt &&
        !isCancelled &&
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
        <ActionButtons
          isSubmitting={isSubmitting}
          deliveryMethod={deliveryMethod}
          isCancelled={isCancelled}
          hasSuccessfulSubmission={
            submissionState.current.hasSuccessfulSubmission
          }
          hasRespondedToPrompt={hasRespondedToPrompt}
          onSubmit={handleSubmit}
          onCancel={handleCancel}
        />
      )}
    </section>
  );
}

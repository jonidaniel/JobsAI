/**
 * useFormSubmission Hook
 *
 * Manages form submission logic including:
 * - Form validation
 * - API calls to start pipeline
 * - Error handling (rate limits, network errors, etc.)
 * - Delivery method handling (email vs download)
 *
 * This hook extracts the complex submission logic from the Search component
 * to improve maintainability and testability.
 */

import { useCallback } from "react";
import { API_ENDPOINTS } from "../config/api";
import { transformFormData } from "../utils/formDataTransform";
import { getErrorMessage } from "../utils/errorMessages";
import { validateGeneralQuestions } from "../utils/validation";
import { GENERAL_QUESTION_KEYS } from "../config/generalQuestions";
import type {
  FormData,
  ValidationErrors,
  PipelinePhase,
  DownloadInfo,
} from "../types";
import type { DeliveryMethod } from "../components/delivery/types";

interface UseFormSubmissionOptions {
  formData: FormData;
  deliveryMethod: DeliveryMethod;
  email: string;
  currentQuestionSetIndex: number;
  isRateLimited: boolean;
  setError: React.Dispatch<React.SetStateAction<string | null>>;
  setValidationErrors: React.Dispatch<React.SetStateAction<ValidationErrors>>;
  setActiveQuestionSetIndex: React.Dispatch<
    React.SetStateAction<number | undefined>
  >;
  setIsRateLimited: React.Dispatch<React.SetStateAction<boolean>>;
  setShowDeliveryMethodPrompt: React.Dispatch<React.SetStateAction<boolean>>;
  setDeliveryMethod: React.Dispatch<React.SetStateAction<DeliveryMethod>>;
  setEmail: React.Dispatch<React.SetStateAction<string>>;
  setEmailError: React.Dispatch<React.SetStateAction<string | null>>;
  setIsSubmitting: React.Dispatch<React.SetStateAction<boolean>>;
  setCurrentPhase: React.Dispatch<React.SetStateAction<PipelinePhase | null>>;
  setJobId: React.Dispatch<React.SetStateAction<string | null>>;
  setDownloadInfo: React.Dispatch<React.SetStateAction<DownloadInfo | null>>;
  setShowDownloadPrompt: React.Dispatch<React.SetStateAction<boolean>>;
  setHasDownloaded: React.Dispatch<React.SetStateAction<boolean>>;
  setHasRespondedToPrompt: React.Dispatch<React.SetStateAction<boolean>>;
  setIsCancelled: React.Dispatch<React.SetStateAction<boolean>>;
  submissionState: React.MutableRefObject<{
    justCompleted: boolean;
    savedScrollPosition: number | null;
    hasSuccessfulSubmission: boolean;
  }>;
  currentJobIdRef: React.MutableRefObject<string | null>;
  startPolling: (jobId: string) => void;
  scrollToElement: (selector: string, delay?: number) => void;
}

interface UseFormSubmissionReturn {
  handleSubmit: (
    e?: React.FormEvent<HTMLFormElement> | React.MouseEvent<HTMLButtonElement>
  ) => Promise<void>;
  startPipeline: () => Promise<void>;
  validateEmail: (email: string) => boolean;
}

/**
 * Validates email address format
 */
function validateEmailFormat(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * Resets rate limit state
 */
function resetRateLimitState(
  setIsRateLimited: (limited: boolean) => void,
  setError: (error: string | null) => void,
  setIsSubmitting: (submitting: boolean) => void,
  setShowDeliveryMethodPrompt: (show: boolean) => void,
  setDeliveryMethod: (method: DeliveryMethod) => void,
  setEmail: (email: string) => void,
  setEmailError: (error: string | null) => void,
  setCurrentPhase: (phase: PipelinePhase | null) => void,
  setJobId: (jobId: string | null) => void,
  currentJobIdRef: React.MutableRefObject<string | null>,
  submissionState: React.MutableRefObject<{
    justCompleted: boolean;
    hasSuccessfulSubmission: boolean;
  }>
): void {
  setIsRateLimited(true);
  setError(null);
  setIsSubmitting(false);
  setShowDeliveryMethodPrompt(false);
  setDeliveryMethod(null);
  setEmail("");
  setEmailError(null);
  setCurrentPhase(null);
  setJobId(null);
  currentJobIdRef.current = null;
  submissionState.current.hasSuccessfulSubmission = false;
  submissionState.current.justCompleted = false;
}

export function useFormSubmission({
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
}: UseFormSubmissionOptions): UseFormSubmissionReturn {
  const validateEmail = useCallback((email: string): boolean => {
    return validateEmailFormat(email);
  }, []);

  const startPipeline = useCallback(async (): Promise<void> => {
    setIsSubmitting(true);
    setError(null);
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
          resetRateLimitState(
            setIsRateLimited,
            setError,
            setIsSubmitting,
            setShowDeliveryMethodPrompt,
            setDeliveryMethod,
            setEmail,
            setEmailError,
            setCurrentPhase,
            setJobId,
            currentJobIdRef,
            submissionState
          );
          setDownloadInfo(null);
          setShowDownloadPrompt(false);
          setHasDownloaded(false);
          setHasRespondedToPrompt(false);
          setIsCancelled(false);
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
          resetRateLimitState(
            setIsRateLimited,
            setError,
            setIsSubmitting,
            setShowDeliveryMethodPrompt,
            setDeliveryMethod,
            setEmail,
            setEmailError,
            setCurrentPhase,
            setJobId,
            currentJobIdRef,
            submissionState
          );
          return;
        }
        throw new Error(
          errorData.detail || `Server error: ${startResponse.status}`
        );
      }

      const { job_id } = (await startResponse.json()) as { job_id: string };

      // For email delivery: fire-and-forget, no polling, but keep UI state
      if (deliveryMethod === "email") {
        // Keep isSubmitting and deliveryMethod set to show "Thank you..." message
        // Hide the delivery method prompt, but keep the rest of the state
        setShowDeliveryMethodPrompt(false);
        setEmailError(null);
        setCurrentPhase(null);
        setJobId(null);
        currentJobIdRef.current = null;
        // Don't poll - let pipeline run in background silently
        // Keep isSubmitting=true and deliveryMethod="email" to persist the UI message
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
          resetRateLimitState(
            setIsRateLimited,
            setError,
            setIsSubmitting,
            setShowDeliveryMethodPrompt,
            setDeliveryMethod,
            setEmail,
            setEmailError,
            setCurrentPhase,
            setJobId,
            currentJobIdRef,
            submissionState
          );
        } else {
          // For other errors, keep UI state (show "Thank you..." message)
          // User won't see the error, but UI stays in submitted state
          setShowDeliveryMethodPrompt(false);
          setEmailError(null);
          setCurrentPhase(null);
          setJobId(null);
          currentJobIdRef.current = null;
        }
        return;
      }

      // For download delivery: handle all errors normally
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
      setIsSubmitting(false);
      setCurrentPhase(null);
      setJobId(null);
      currentJobIdRef.current = null;
      submissionState.current.justCompleted = true;
    }
  }, [
    formData,
    deliveryMethod,
    email,
    isRateLimited,
    setIsSubmitting,
    setError,
    setCurrentPhase,
    setShowDeliveryMethodPrompt,
    setEmailError,
    setJobId,
    setDownloadInfo,
    setShowDownloadPrompt,
    setHasDownloaded,
    setHasRespondedToPrompt,
    setIsCancelled,
    setIsRateLimited,
    setDeliveryMethod,
    setEmail,
    currentJobIdRef,
    submissionState,
    startPolling,
  ]);

  const handleSubmit = useCallback(
    async (
      e?: React.FormEvent<HTMLFormElement> | React.MouseEvent<HTMLButtonElement>
    ): Promise<void> => {
      if (e) {
        e.preventDefault();
        e.stopPropagation();
      }

      // Clear previous errors
      setError(null);
      submissionState.current.justCompleted = false;
      submissionState.current.hasSuccessfulSubmission = false;
      setShowDownloadPrompt(false);
      setDownloadInfo(null);
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
            50 // SCROLL_DELAY + 50
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
    },
    [
      formData,
      currentQuestionSetIndex,
      setError,
      setValidationErrors,
      setActiveQuestionSetIndex,
      setShowDeliveryMethodPrompt,
      setDeliveryMethod,
      setEmail,
      setEmailError,
      setIsCancelled,
      setIsRateLimited,
      setShowDownloadPrompt,
      setDownloadInfo,
      setHasDownloaded,
      submissionState,
      scrollToElement,
    ]
  );

  return {
    handleSubmit,
    startPipeline,
    validateEmail,
  };
}

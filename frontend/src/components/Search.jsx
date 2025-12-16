import { useState, useEffect, useRef, useCallback } from "react";

import QuestionSetList from "./QuestionSetList";
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
 * Search Component - Main Questionnaire and Pipeline Interface.
 *
 * This is the primary component for the JobsAI application. It manages the complete
 * user flow from questionnaire completion through pipeline execution to document download.
 *
 * Responsibilities:
 * - Renders QuestionSetList component for form input
 * - Validates form data before submission
 * - Manages asynchronous pipeline execution via API
 * - Polls for progress updates during pipeline execution
 * - Handles document download from S3 using presigned URLs
 * - Displays error and success messages with auto-dismiss
 * - Manages submission state to prevent double-submission
 * - Handles cancellation of running pipelines
 *
 * Form Data Flow:
 *   QuestionSetList -> onFormDataChange -> formData state -> handleSubmit -> API
 *
 * Pipeline Flow:
 *   1. POST /api/start -> Receive job_id
 *   2. Poll GET /api/progress/{job_id} every 2 seconds
 *   3. When complete: GET /api/download/{job_id} -> Receive presigned S3 URL
 *   4. Download document directly from S3
 *
 * State Management:
 *   - formData: Complete form state from all question sets
 *   - isSubmitting: Prevents double-submission and shows loading state
 *   - jobId: Current pipeline job identifier for progress tracking
 *   - currentPhase: Current pipeline phase for progress display
 *   - error/success: User feedback messages
 *
 * @component
 * @returns {JSX.Element} The Search component with questionnaire and pipeline interface
 */
export default function Search() {
  // Submission state management
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  // Progress tracking with polling
  const [currentPhase, setCurrentPhase] = useState(null);
  const [jobId, setJobId] = useState(null);
  const pollingIntervalRef = useRef(null);
  // Delivery method selection state
  const [showDeliveryMethodPrompt, setShowDeliveryMethodPrompt] =
    useState(false);
  const [deliveryMethod, setDeliveryMethod] = useState(null); // "email" or "download"
  const [email, setEmail] = useState("");
  const [emailError, setEmailError] = useState(null);
  // Cancellation state
  const [isCancelled, setIsCancelled] = useState(false);
  // Download prompt state
  const [showDownloadPrompt, setShowDownloadPrompt] = useState(false);
  const [downloadInfo, setDownloadInfo] = useState(null); // { jobId, filenames }
  const [declinedDocumentCount, setDeclinedDocumentCount] = useState(null); // Store count when user declines
  const [hasDownloaded, setHasDownloaded] = useState(false); // Track if user has clicked "Yes"
  const [hasRespondedToPrompt, setHasRespondedToPrompt] = useState(false); // Track if user has responded (Yes or No)
  const [isRateLimited, setIsRateLimited] = useState(false); // Track if rate limit is exceeded
  // Consolidated submission state ref
  // Tracks submission-related state that doesn't need to trigger re-renders
  const submissionState = useRef({
    justCompleted: false, // Track if we just completed a submission (to prevent scroll on remount)
    savedScrollPosition: null, // Store scroll position to restore after download
    hasSuccessfulSubmission: false, // Track if we've had a successful submission (to keep question sets hidden)
  });

  // Phase messages mapping
  const phaseMessages = {
    profiling: "2/6 Creating your profile...",
    searching: "3/6 Searching for jobs...",
    scoring: "4/6 Scoring the jobs...",
    analyzing: "5/6 Doing analysis...",
    generating: "6/6 Generating cover letters...",
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

    // If this is a "Find Again" click while submitting (e.g., during email delivery), just reset UI
    // Do NOT cancel the running job - let it complete in the background
    if (isSubmitting) {
      // Stop polling for the current job (but don't send cancel request)
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
      // Reset UI state and allow new submission
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
      setIsSubmitting(false);
      setCurrentPhase(null);
      setJobId(null); // Clear jobId but don't cancel the job
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

    // If this is a "Find Again" click (from successful submission or cancellation), navigate to question set 1 and reset
    if (submissionState.current.hasSuccessfulSubmission || isCancelled) {
      // Reset states
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

    // Clear previous errors and success messages
    setError(null);
    setSuccess(false);
    submissionState.current.justCompleted = false;
    // Reset successful submission flag when starting a new submission
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
  const validateEmail = (email) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  /**
   * Handles the delivery method selection.
   * For "download", starts the pipeline immediately.
   * For "email", shows email input field.
   */
  const handleDeliveryMethod = (method) => {
    setDeliveryMethod(method);
    setEmailError(null);

    if (method === "download") {
      // Start the pipeline immediately
      setShowDeliveryMethodPrompt(false);
      startPipeline();
    } else if (method === "email") {
      // Show email input - don't hide prompt yet
      // User needs to enter email and click "Continue"
    }
  };

  /**
   * Handles email submission when user clicks "Continue" after entering email
   */
  const handleEmailSubmit = async () => {
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
   * Extracted from handleSubmit to be reusable.
   */
  const startPipeline = async () => {
    setIsSubmitting(true);
    setError(null);
    setSuccess(false);
    setCurrentPhase(null);

    // Transform form data into grouped structure for backend API
    const result = transformFormData(formData);

    // Add delivery method and email to payload
    if (deliveryMethod === "email") {
      result.delivery_method = "email";
      result.email = email;
    } else {
      result.delivery_method = "download";
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
          // Use a single batch update to ensure all states are set together
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
          // Clear submission state flags
          submissionState.current.hasSuccessfulSubmission = false;
          submissionState.current.justCompleted = false;
          console.log("Rate limit state set, isRateLimited should be true");
          // Don't parse JSON or throw error - just return
          return;
        }
        // For other errors, parse JSON and throw
        const errorData = await startResponse.json().catch(() => ({}));
        // Also check error message content in case status code check missed it
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

      const { job_id } = await startResponse.json();
      setJobId(job_id);

      // Step 2: Poll for progress updates
      const pollProgress = async () => {
        try {
          const response = await fetch(`${API_ENDPOINTS.PROGRESS}/${job_id}`);

          if (!response.ok) {
            if (response.status === 404) {
              setError("Job not found");
              setIsSubmitting(false);
              setCurrentPhase(null);
              setJobId(null);
              if (pollingIntervalRef.current) {
                clearInterval(pollingIntervalRef.current);
                pollingIntervalRef.current = null;
              }
              return;
            }
            throw new Error(`HTTP error! status: ${response.status}`);
          }

          const data = await response.json();

          // Handle progress updates
          if (data.progress && data.progress.phase) {
            setCurrentPhase(data.progress.phase);
          }

          // Handle completion
          if (data.status === "complete") {
            if (pollingIntervalRef.current) {
              clearInterval(pollingIntervalRef.current);
              pollingIntervalRef.current = null;
            }

            // Store download info and show prompt instead of auto-downloading
            const filenames =
              data.filenames && Array.isArray(data.filenames)
                ? data.filenames
                : [data.filename || "cover_letter.docx"];

            setDownloadInfo({
              jobId: job_id,
              filenames: filenames,
            });
            setShowDownloadPrompt(true);

            // Update submission state
            setSuccess(true);
            setError(null);
            submissionState.current.justCompleted = true;
            submissionState.current.hasSuccessfulSubmission = true;
            setIsSubmitting(false);
            setCurrentPhase(null);
            setJobId(null);
          }
          // Handle errors
          else if (data.status === "error") {
            if (pollingIntervalRef.current) {
              clearInterval(pollingIntervalRef.current);
              pollingIntervalRef.current = null;
            }
            setError(data.error || "An error occurred during processing");
            setIsSubmitting(false);
            setCurrentPhase(null);
            setJobId(null);
          }
          // Handle cancellation
          else if (data.status === "cancelled") {
            if (pollingIntervalRef.current) {
              clearInterval(pollingIntervalRef.current);
              pollingIntervalRef.current = null;
            }
            setError("Pipeline was cancelled");
            setIsSubmitting(false);
            setCurrentPhase(null);
            setJobId(null);
          }
          // Continue polling if still running
        } catch (error) {
          console.error("Error polling progress:", error);
          // Don't stop polling on network errors, just log them
        }
      };

      // Start polling immediately, then every 2 seconds
      pollProgress();
      pollingIntervalRef.current = setInterval(pollProgress, 2000);
    } catch (error) {
      // Stop polling if it was started
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
      // Check if error message indicates rate limit (fallback check)
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
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    };
  }, []);

  /**
   * Handles pipeline cancellation
   * Sends cancel request to backend and stops polling
   * Can be called even if jobId isn't set yet (cancels before pipeline starts)
   */
  const handleCancel = async () => {
    // Stop polling if it's running
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }

    // If we have a jobId, send cancel request to backend
    if (jobId) {
      try {
        await fetch(`${API_ENDPOINTS.CANCEL}/${jobId}`, {
          method: "POST",
        });
      } catch (error) {
        console.error("Error cancelling pipeline:", error);
      }
    }

    // Reset state regardless of whether jobId exists
    setIsSubmitting(false);
    setCurrentPhase(null);
    setJobId(null);
    setShowDeliveryMethodPrompt(false);
    setIsCancelled(true);
    setError(null);
  };

  /**
   * Downloads the generated document(s).
   *
   * Handles both single document (backward compatibility) and multiple documents.
   * If multiple documents exist, downloads all of them sequentially.
   *
   * @param {string} jobId - Job identifier
   * @param {string|Array<string>} filenameOrFilenames - Single filename or array of filenames
   */
  const downloadDocument = async (jobId, filenameOrFilenames) => {
    try {
      const response = await fetch(`${API_ENDPOINTS.DOWNLOAD}/${jobId}`);

      if (!response.ok) {
        throw new Error(`Download failed: ${response.status}`);
      }

      // Save scroll position before download
      submissionState.current.savedScrollPosition =
        window.scrollY || window.pageYOffset;

      // Check if response contains presigned S3 URL(s)
      const contentType = response.headers.get("content-type");
      if (contentType && contentType.includes("application/json")) {
        const data = await response.json();

        // Handle multiple documents
        if (data.download_urls && Array.isArray(data.download_urls)) {
          // Download all documents sequentially
          for (let i = 0; i < data.download_urls.length; i++) {
            const item = data.download_urls[i];
            await downloadFromS3(item.url, item.filename);
            // Small delay between downloads to avoid browser blocking
            if (i < data.download_urls.length - 1) {
              await new Promise((resolve) => setTimeout(resolve, 500));
            }
          }
          return;
        }

        // Handle single document
        if (data.download_url) {
          await downloadFromS3(
            data.download_url,
            data.filename || filenameOrFilenames
          );
          return;
        }
      }

      // Fallback: Get the response as a blob (direct download from API Gateway)
      const blob = await response.blob();
      const filename = Array.isArray(filenameOrFilenames)
        ? filenameOrFilenames[0]
        : filenameOrFilenames;
      downloadBlob(blob, response.headers, filename);
    } catch (error) {
      console.error("Error downloading document:", error);
      throw error;
    }
  };

  /**
   * Downloads a single document from S3 using a presigned URL.
   *
   * @param {string} s3Url - Presigned S3 URL
   * @param {string} filename - Filename for the document
   */
  const downloadFromS3 = async (s3Url, filename) => {
    const s3Response = await fetch(s3Url);

    // Ensure we get the binary data correctly
    // Use arrayBuffer first to preserve binary integrity, then create blob with correct MIME type
    const arrayBuffer = await s3Response.arrayBuffer();
    const blob = new Blob([arrayBuffer], {
      type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    });

    // Use filename from parameter (more reliable than extracting from headers)
    downloadBlob(blob, s3Response.headers, filename);
  };

  /**
   * Handles the "Yes" button click in the download prompt.
   * Triggers the download and closes the prompt.
   */
  const handleDownloadYes = async () => {
    if (!downloadInfo) return;

    try {
      // Save scroll position before download
      submissionState.current.savedScrollPosition =
        window.scrollY || window.pageYOffset;

      // Download the document(s)
      if (downloadInfo.filenames.length > 1) {
        // Multiple documents
        await downloadDocument(downloadInfo.jobId, downloadInfo.filenames);
      } else {
        // Single document
        await downloadDocument(downloadInfo.jobId, downloadInfo.filenames[0]);
      }

      // Close the prompt and mark as downloaded
      setShowDownloadPrompt(false);
      setDownloadInfo(null);
      setHasDownloaded(true);
      setHasRespondedToPrompt(true);

      // Auto-dismiss success message after timeout
      if (successTimeoutRef.current) {
        clearTimeout(successTimeoutRef.current);
      }
      successTimeoutRef.current = setTimeout(() => {
        setSuccess(false);
        successTimeoutRef.current = null;
      }, SUCCESS_MESSAGE_TIMEOUT);
    } catch (error) {
      console.error("Error downloading document:", error);
      setError("Failed to download documents. Please try again.");
      setShowDownloadPrompt(false);
      setDownloadInfo(null);
    }
  };

  /**
   * Handles the "No" button click in the download prompt.
   * Closes the prompt without downloading.
   */
  const handleDownloadNo = () => {
    // Store document count before clearing downloadInfo
    const documentCount = downloadInfo?.filenames?.length || 1;
    setDeclinedDocumentCount(documentCount);
    setShowDownloadPrompt(false);
    setDownloadInfo(null);
    setHasRespondedToPrompt(true);

    // Auto-dismiss success message after timeout
    if (successTimeoutRef.current) {
      clearTimeout(successTimeoutRef.current);
    }
    successTimeoutRef.current = setTimeout(() => {
      setSuccess(false);
      successTimeoutRef.current = null;
    }, SUCCESS_MESSAGE_TIMEOUT);
  };

  return (
    <section id="search">
      <h2>Search</h2>
      {isRateLimited ? (
        // Rate limit exceeded: show only the rate limit message
        <>
          <h3 className="text-base sm:text-xl md:text-2xl lg:text-3xl font-semibold text-white text-center">
            You've made too many searches lately. Try again later.
          </h3>
        </>
      ) : isSubmitting && deliveryMethod === "email" ? (
        // Email delivery: show message instead of progress
        <>
          <h3 className="text-base sm:text-xl md:text-2xl lg:text-3xl font-semibold text-white text-center">
            Thank you very much for using JobsAI. Expect the cover{" "}
            {parseInt(formData["cover-letter-num"] || "1", 10) === 1
              ? "letter"
              : "letters"}{" "}
            to drop in your inbox shortly
          </h3>
        </>
      ) : isSubmitting ? (
        // Download delivery: show progress message
        <>
          <h3 className="text-base sm:text-xl md:text-2xl lg:text-3xl font-semibold text-white text-center">
            {currentPhase && phaseMessages[currentPhase]
              ? phaseMessages[currentPhase]
              : "1/6 Starting search..."}
          </h3>
          <h3 className="text-base sm:text-xl md:text-2xl lg:text-3xl font-semibold text-white text-center">
            This might take a few minutes
          </h3>
        </>
      ) : showDeliveryMethodPrompt ? (
        // Delivery method selection prompt
        <>
          {!deliveryMethod ? (
            // Initial selection: choose delivery method
            <>
              <h3 className="text-base sm:text-xl md:text-2xl lg:text-3xl font-semibold text-white text-center">
                How do you want the cover{" "}
                {parseInt(formData["cover-letter-num"] || "1", 10) === 1
                  ? "letter"
                  : "letters"}
                ?
              </h3>
              <div className="flex justify-center items-center gap-4 mt-6">
                <button
                  onClick={() => handleDeliveryMethod("email")}
                  className="text-base sm:text-lg md:text-xl lg:text-2xl px-3 sm:px-4 py-1.5 sm:py-2 border border-white bg-transparent text-white font-semibold rounded-lg shadow hover:bg-white hover:text-gray-800 transition-all"
                  aria-label="Receive cover letters via email"
                >
                  Via email
                </button>
                <button
                  onClick={() => handleDeliveryMethod("download")}
                  className="text-base sm:text-lg md:text-xl lg:text-2xl px-3 sm:px-4 py-1.5 sm:py-2 border border-white bg-transparent text-white font-semibold rounded-lg shadow hover:bg-white hover:text-gray-800 transition-all"
                  aria-label="Stay anonymous and download cover letters to browser"
                >
                  Stay anonymous and download{" "}
                  {parseInt(formData["cover-letter-num"] || "1", 10) === 1
                    ? "it"
                    : "them"}{" "}
                  to browser
                </button>
              </div>
            </>
          ) : deliveryMethod === "email" ? (
            // Email input: user selected email, now need email address
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
        // Download prompt state: show download prompt text
        <>
          <h3 className="text-base sm:text-xl md:text-2xl lg:text-3xl font-semibold text-white text-center">
            All set! Generated {downloadInfo.filenames.length} cover letter
            {downloadInfo.filenames.length !== 1 ? "s" : ""}
          </h3>
          <h3 className="text-base sm:text-xl md:text-2xl lg:text-3xl font-semibold text-white text-center">
            Would you like to download the{" "}
            {downloadInfo.filenames.length === 1 ? "file" : "files"}?
          </h3>
          <div className="flex justify-center items-center gap-4 mt-6">
            <button
              onClick={handleDownloadYes}
              className="text-base sm:text-lg md:text-xl lg:text-2xl px-3 sm:px-4 py-1.5 sm:py-2 border border-white bg-transparent text-white font-semibold rounded-lg shadow hover:bg-white hover:text-gray-800 transition-all"
              aria-label="Download the cover letters"
            >
              Yes
            </button>
            <button
              onClick={handleDownloadNo}
              className="text-base sm:text-lg md:text-xl lg:text-2xl px-3 sm:px-4 py-1.5 sm:py-2 border border-white bg-transparent text-white font-semibold rounded-lg shadow hover:bg-white hover:text-gray-800 transition-all"
              aria-label="Skip downloading"
            >
              No
            </button>
          </div>
        </>
      ) : isCancelled ? (
        // Cancellation state: show cancellation message
        <>
          <h3 className="text-base sm:text-xl md:text-2xl lg:text-3xl font-semibold text-white text-center">
            You cancelled the job search
          </h3>
        </>
      ) : submissionState.current.hasSuccessfulSubmission &&
        deliveryMethod === "email" &&
        hasRespondedToPrompt ? (
        // Email delivery complete: show completion message
        <>
          <h3 className="text-base sm:text-xl md:text-2xl lg:text-3xl font-semibold text-white text-center">
            Thank you very much for using JobsAI. Expect the cover{" "}
            {parseInt(formData["cover-letter-num"] || "1", 10) === 1
              ? "letter"
              : "letters"}{" "}
            to drop in your inbox shortly
          </h3>
        </>
      ) : submissionState.current.hasSuccessfulSubmission &&
        hasRespondedToPrompt &&
        !hasDownloaded ? (
        // User declined download: show message
        <>
          <h3 className="text-base sm:text-xl md:text-2xl lg:text-3xl font-semibold text-white text-center">
            You turned down the{" "}
            {declinedDocumentCount === 1 ? "document" : "documents"}
          </h3>
        </>
      ) : submissionState.current.hasSuccessfulSubmission && hasDownloaded ? (
        // Success state: show completion message (only after user has downloaded)
        <>
          <h3 className="text-base sm:text-xl md:text-2xl lg:text-3xl font-semibold text-white text-center">
            <i>Thank you very much for using JobsAI.</i>
            <br />
            Feel free to do another search
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
      {/* Only show question sets if not submitting AND not showing delivery method prompt AND not cancelled AND not successfully completed AND not rate limited */}
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
      {/* Error message - displayed when submission fails (but not for rate limit errors) */}
      {error && !isRateLimited && <ErrorMessage message={error} />}
      {/* Submit button and cancel button - hide when rate limited */}
      {!isRateLimited && (
        <div className="flex justify-center items-center gap-4 mt-6">
          {/* Show "Find Again" button when cancelled */}
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
          {/* Show "Find Again" button immediately when email delivery is selected */}
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
          {/* Show "Find Again" button when email delivery is complete */}
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
          {/* Only show submit button when NOT submitting and NOT showing delivery method prompt and NOT cancelled */}
          {/* Hide button entirely if there's a successful submission but user hasn't responded to download prompt yet */}
          {!isSubmitting &&
            !showDeliveryMethodPrompt &&
            !isCancelled &&
            (!submissionState.current.hasSuccessfulSubmission ||
              hasRespondedToPrompt) && (
              <button
                id="submit-btn"
                onClick={handleSubmit}
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
            )}
          {/* Cancel button - show immediately when submitting (only for download delivery) */}
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

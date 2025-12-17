import { useRef } from "react";
import { API_ENDPOINTS } from "../config/api";

/**
 * Custom hook for polling pipeline progress updates.
 *
 * Handles polling logic for job progress, including:
 * - Starting/stopping polling intervals
 * - Handling progress updates, completion, errors, and cancellation
 * - Preventing stale polling updates when jobs are replaced
 *
 * @param {Object} options - Configuration object
 * @param {Function} options.setCurrentPhase - State setter for current phase
 * @param {Function} options.setIsSubmitting - State setter for submitting state
 * @param {Function} options.setError - State setter for error messages
 * @param {Function} options.setJobId - State setter for job ID
 * @param {Function} options.setDownloadInfo - State setter for download info
 * @param {Function} options.setShowDownloadPrompt - State setter for download prompt visibility
 * @param {Function} options.setSuccess - State setter for success state
 * @param {Object} options.submissionState - Ref object for submission state
 * @param {Object} options.currentJobIdRef - Ref to track current job ID
 *
 * @returns {Object} Object containing polling control functions
 *   - startPolling: Function to start polling for a job ID
 *   - stopPolling: Function to stop polling
 */
export function usePipelinePolling({
  setCurrentPhase,
  setIsSubmitting,
  setError,
  setJobId,
  setDownloadInfo,
  setShowDownloadPrompt,
  setSuccess,
  submissionState,
  currentJobIdRef,
}) {
  const pollingIntervalRef = useRef(null);

  /**
   * Stops the polling interval if it's running.
   */
  const stopPolling = () => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
  };

  /**
   * Starts polling for progress updates for a given job ID.
   *
   * @param {string} job_id - Job ID to poll for
   */
  const startPolling = (job_id) => {
    // Update ref to track current job ID
    currentJobIdRef.current = job_id;

    // Poll for progress updates
    const pollProgress = async () => {
      try {
        // Check if this job is still the current one - ignore if job was replaced
        if (currentJobIdRef.current !== job_id) {
          // This polling is for an old job, stop it
          stopPolling();
          return;
        }

        const response = await fetch(`${API_ENDPOINTS.PROGRESS}/${job_id}`);

        if (!response.ok) {
          if (response.status === 404) {
            // Only update state if this is still the current job
            if (currentJobIdRef.current === job_id) {
              setError("Job not found");
              setIsSubmitting(false);
              setCurrentPhase(null);
              setJobId(null);
              currentJobIdRef.current = null;
            }
            stopPolling();
            return;
          }
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log("Poll response:", {
          job_id,
          status: data.status,
          progress: data.progress,
          has_progress: !!data.progress,
        });

        // Only update state if this is still the current job
        if (currentJobIdRef.current !== job_id) {
          return; // Job was replaced, ignore this response
        }

        // Handle progress updates
        if (data.progress && data.progress.phase) {
          console.log("Updating phase:", data.progress.phase);
          setCurrentPhase(data.progress.phase);
        }

        // Handle completion
        if (data.status === "complete") {
          // Only process completion if this is still the current job
          if (currentJobIdRef.current !== job_id) {
            return; // Job was replaced, ignore this response
          }

          stopPolling();

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
          currentJobIdRef.current = null;
        }
        // Handle errors
        else if (data.status === "error") {
          // Only process error if this is still the current job
          if (currentJobIdRef.current !== job_id) {
            return; // Job was replaced, ignore this response
          }

          stopPolling();
          setError(data.error || "An error occurred during processing");
          setIsSubmitting(false);
          setCurrentPhase(null);
          setJobId(null);
          currentJobIdRef.current = null;
        }
        // Handle cancellation
        else if (data.status === "cancelled") {
          // Only process cancellation if this is still the current job
          if (currentJobIdRef.current !== job_id) {
            return; // Job was replaced, ignore this response
          }

          stopPolling();
          setError("Pipeline was cancelled");
          setIsSubmitting(false);
          setCurrentPhase(null);
          setJobId(null);
          currentJobIdRef.current = null;
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
  };

  return {
    startPolling,
    stopPolling,
    pollingIntervalRef, // Expose ref for cleanup in parent component
  };
}

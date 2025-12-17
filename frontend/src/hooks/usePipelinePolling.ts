import { useRef, useCallback } from "react";
import { API_ENDPOINTS } from "../config/api";
import type { PipelinePhase, ProgressResponse, DownloadInfo } from "../types";

interface SubmissionState {
  justCompleted: boolean;
  savedScrollPosition: number | null;
  hasSuccessfulSubmission: boolean;
}

interface UsePipelinePollingOptions {
  setCurrentPhase: (phase: PipelinePhase | null) => void;
  setIsSubmitting: (isSubmitting: boolean) => void;
  setError: (error: string | null) => void;
  setJobId: (jobId: string | null) => void;
  setDownloadInfo: (info: DownloadInfo | null) => void;
  setShowDownloadPrompt: (show: boolean) => void;
  setSuccess: (success: boolean) => void;
  submissionState: React.MutableRefObject<SubmissionState>;
  currentJobIdRef: React.MutableRefObject<string | null>;
}

interface UsePipelinePollingReturn {
  startPolling: (job_id: string) => void;
  stopPolling: () => void;
}

/**
 * Custom hook for polling pipeline progress updates.
 *
 * Handles polling logic for job progress, including:
 * - Starting/stopping polling intervals
 * - Handling progress updates, completion, errors, and cancellation
 * - Preventing stale polling updates when jobs are replaced
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
}: UsePipelinePollingOptions): UsePipelinePollingReturn {
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  /**
   * Stops the polling interval if it's running.
   * Memoized to ensure stable reference for useEffect dependencies.
   */
  const stopPolling = useCallback(() => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
  }, []);

  /**
   * Starts polling for progress updates for a given job ID.
   *
   * @param job_id - Job ID to poll for
   */
  const startPolling = (job_id: string): void => {
    // Update ref to track current job ID
    currentJobIdRef.current = job_id;

    // Poll for progress updates
    const pollProgress = async (): Promise<void> => {
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

        const data = (await response.json()) as ProgressResponse;

        // Only update state if this is still the current job
        if (currentJobIdRef.current !== job_id) {
          return; // Job was replaced, ignore this response
        }

        // Handle progress updates
        if (data.progress && data.progress.phase) {
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
  };
}

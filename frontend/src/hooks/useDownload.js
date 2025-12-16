import { API_ENDPOINTS } from "../config/api";
import { downloadBlob } from "../utils/fileDownload";
import { SUCCESS_MESSAGE_TIMEOUT } from "../config/constants";

/**
 * Custom hook for handling document downloads.
 *
 * Handles downloading documents from S3 using presigned URLs, including:
 * - Single and multiple document downloads
 * - S3 presigned URL handling
 * - Fallback to direct blob download
 * - Scroll position preservation
 *
 * @param {Object} options - Configuration object
 * @param {Object|null} options.downloadInfo - Download info object with jobId and filenames
 * @param {Object} options.submissionState - Ref object for submission state
 * @param {Object} options.successTimeoutRef - Ref for success message timeout
 * @param {Function} options.setShowDownloadPrompt - State setter for download prompt visibility
 * @param {Function} options.setDownloadInfo - State setter for download info
 * @param {Function} options.setHasDownloaded - State setter for downloaded state
 * @param {Function} options.setHasRespondedToPrompt - State setter for prompt response state
 * @param {Function} options.setSuccess - State setter for success state
 * @param {Function} options.setError - State setter for error messages
 *
 * @returns {Object} Object containing download functions
 *   - downloadDocument: Function to download document(s) by jobId
 *   - downloadFromS3: Function to download from S3 presigned URL
 *   - handleDownloadYes: Function to handle download button click
 */
export function useDownload({
  downloadInfo,
  submissionState,
  successTimeoutRef,
  setShowDownloadPrompt,
  setDownloadInfo,
  setHasDownloaded,
  setHasRespondedToPrompt,
  setSuccess,
  setError,
}) {
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
   * Handles the download button click in the download prompt.
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

  return {
    downloadDocument,
    downloadFromS3,
    handleDownloadYes,
  };
}

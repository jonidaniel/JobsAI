import { API_ENDPOINTS } from "../config/api";
import { downloadBlob } from "../utils/fileDownload";
import type { DownloadInfo } from "../types";

interface SubmissionState {
  justCompleted: boolean;
  savedScrollPosition: number | null;
  hasSuccessfulSubmission: boolean;
}

interface UseDownloadOptions {
  downloadInfo: DownloadInfo | null;
  submissionState: React.MutableRefObject<SubmissionState>;
  setShowDownloadPrompt: (show: boolean) => void;
  setDownloadInfo: (info: DownloadInfo | null) => void;
  setHasDownloaded: (downloaded: boolean) => void;
  setHasRespondedToPrompt: (responded: boolean) => void;
  setError: (error: string | null) => void;
}

interface UseDownloadReturn {
  downloadDocument: (
    jobId: string,
    filenameOrFilenames: string | string[]
  ) => Promise<void>;
  downloadFromS3: (s3Url: string, filename: string) => Promise<void>;
  handleDownloadYes: () => Promise<void>;
}

interface DownloadResponse {
  download_url?: string;
  download_urls?: Array<{ url: string; filename: string }>;
  filename?: string;
}

/**
 * Custom hook for handling document downloads.
 *
 * Handles downloading documents from S3 using presigned URLs, including:
 * - Single and multiple document downloads
 * - S3 presigned URL handling
 * - Fallback to direct blob download
 * - Scroll position preservation
 */
export function useDownload({
  downloadInfo,
  submissionState,
  setShowDownloadPrompt,
  setDownloadInfo,
  setHasDownloaded,
  setHasRespondedToPrompt,
  setError,
}: UseDownloadOptions): UseDownloadReturn {
  /**
   * Downloads a single document from S3 using a presigned URL.
   *
   * @param s3Url - Presigned S3 URL
   * @param filename - Filename for the document
   */
  const downloadFromS3 = async (
    s3Url: string,
    filename: string
  ): Promise<void> => {
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
   * @param jobId - Job identifier
   * @param filenameOrFilenames - Single filename or array of filenames
   */
  const downloadDocument = async (
    jobId: string,
    filenameOrFilenames: string | string[]
  ): Promise<void> => {
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
        const data = (await response.json()) as DownloadResponse;

        // Handle multiple documents
        if (data.download_urls && Array.isArray(data.download_urls)) {
          // Download all documents sequentially
          for (let i = 0; i < data.download_urls.length; i++) {
            const item = data.download_urls[i];
            if (item) {
              await downloadFromS3(item.url, item.filename);
              // Small delay between downloads to avoid browser blocking
              if (i < data.download_urls.length - 1) {
                await new Promise<void>((resolve) => setTimeout(resolve, 500));
              }
            }
          }
          return;
        }

        // Handle single document
        if (data.download_url) {
          const filename =
            data.filename ||
            (Array.isArray(filenameOrFilenames)
              ? filenameOrFilenames[0]
              : filenameOrFilenames) ||
            "cover_letter.docx";
          await downloadFromS3(data.download_url, filename);
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
  const handleDownloadYes = async (): Promise<void> => {
    if (!downloadInfo) return;

    try {
      // Save scroll position before download
      submissionState.current.savedScrollPosition =
        window.scrollY || window.pageYOffset;

      // Download the document(s)
      if (downloadInfo.filenames.length > 1) {
        // Multiple documents
        await downloadDocument(downloadInfo.jobId, downloadInfo.filenames);
      } else if (
        downloadInfo.filenames.length === 1 &&
        downloadInfo.filenames[0]
      ) {
        // Single document
        await downloadDocument(downloadInfo.jobId, downloadInfo.filenames[0]);
      }

      // Close the prompt and mark as downloaded
      setShowDownloadPrompt(false);
      setDownloadInfo(null);
      setHasDownloaded(true);
      setHasRespondedToPrompt(true);
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

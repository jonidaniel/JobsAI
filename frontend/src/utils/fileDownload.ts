/**
 * Downloads a blob file to the user's device.
 *
 * Creates a temporary download link, triggers the browser download, and cleans up
 * resources. Handles filename extraction from Content-Disposition headers with support
 * for RFC 5987 encoding. Preserves scroll position during download to prevent page jumps.
 *
 * @param blob - The blob data to download (typically a Word document).
 * @param headers - Response headers object to extract filename from.
 *   Expected header: Content-Disposition with filename parameter.
 * @param defaultFilename - Default filename to use if not found in headers.
 *   This is typically provided from the API JSON response.
 *
 * @example
 * // Download a document from API response
 * const response = await fetch(downloadUrl);
 * const blob = await response.blob();
 * downloadBlob(blob, response.headers, "cover_letter.docx");
 *
 * @note
 * The function prioritizes the defaultFilename parameter over header extraction.
 * Filename extraction from headers only occurs if defaultFilename is the generic
 * "document.docx" value, ensuring API-provided filenames are always used.
 */
export function downloadBlob(
  blob: Blob,
  headers: Headers | null,
  defaultFilename: string = "document.docx"
): void {
  // Use the provided defaultFilename (from JSON response) as primary source
  // Only extract from headers if defaultFilename is not provided
  let filename = defaultFilename;

  // Extract filename from Content-Disposition header only if defaultFilename is the generic default
  if (filename === "document.docx" && headers) {
    const contentDisposition = headers.get("Content-Disposition");
    if (contentDisposition) {
      // Handle both quoted and unquoted filenames
      // Match: filename="file.docx" or filename=file.docx or filename*=UTF-8''file.docx
      // First try RFC 5987 format (filename*=encoding''value)
      const rfc5987Match = contentDisposition.match(/filename\*=([^;]+)/i);
      if (rfc5987Match && rfc5987Match[1]) {
        const rfc5987Value = rfc5987Match[1].trim();
        if (rfc5987Value.includes("''")) {
          // Extract and decode: UTF-8''test%20file.docx -> test file.docx
          const encoded = rfc5987Value.split("''")[1];
          filename = decodeURIComponent(encoded);
        } else {
          filename = rfc5987Value;
        }
      } else {
        // Fall back to standard format: filename="file.docx" or filename=file.docx
        const quotedMatch = contentDisposition.match(
          /filename=['"]?([^'";]+)['"]?/i
        );
        if (quotedMatch && quotedMatch[1]) {
          filename = quotedMatch[1].trim();
        }
      }
    }
  }

  // Create a temporary URL for the blob
  const url = window.URL.createObjectURL(blob);

  // Programmatically trigger file download
  // Create temporary anchor element, click it, then remove it
  const download_link = document.createElement("a");
  download_link.href = url;
  download_link.download = filename;
  // Hide the link completely to prevent any visual changes or scrolling
  download_link.style.display = "none";
  download_link.style.position = "absolute";
  download_link.style.left = "-9999px";
  download_link.style.top = "-9999px";
  download_link.style.visibility = "hidden";
  download_link.style.opacity = "0";
  download_link.setAttribute("aria-hidden", "true");
  document.body.appendChild(download_link);

  // Save scroll position right before click to restore if download causes scroll
  const scrollBeforeClick = window.scrollY || window.pageYOffset;

  download_link.click();

  // Immediately restore scroll position if it changed during download
  requestAnimationFrame(() => {
    if (window.scrollY !== scrollBeforeClick) {
      window.scrollTo(0, scrollBeforeClick);
    }
  });

  // Remove the link from DOM (use removeChild for compatibility with jsdom)
  if (download_link.remove) {
    download_link.remove();
  } else if (download_link.parentNode) {
    download_link.parentNode.removeChild(download_link);
  }

  // Clean up the blob URL to free memory
  window.URL.revokeObjectURL(url);
}

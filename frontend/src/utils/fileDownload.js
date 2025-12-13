/**
 * Downloads a blob file to the user's device
 *
 * Extracts filename from Content-Disposition header if available,
 * creates a temporary download link, triggers the download, and cleans up.
 *
 * @param {Blob} blob - The blob data to download
 * @param {Headers} headers - Response headers to extract filename from
 * @param {string} defaultFilename - Default filename if not found in headers (default: "document.docx")
 */
export function downloadBlob(blob, headers, defaultFilename = "document.docx") {
  // Use the provided defaultFilename (from JSON response) as primary source
  // Only extract from headers if defaultFilename is not provided
  let filename = defaultFilename;

  // Extract filename from Content-Disposition header only if defaultFilename is the generic default
  if (filename === "document.docx" && headers) {
    const contentDisposition = headers.get("Content-Disposition");
    if (contentDisposition) {
      // Handle both quoted and unquoted filenames
      // Match: filename="file.docx" or filename=file.docx or filename*=UTF-8''file.docx
      const quotedMatch = contentDisposition.match(
        /filename\*?=['"]?([^'";]+)['"]?/i
      );
      if (quotedMatch && quotedMatch[1]) {
        // Decode URL-encoded filename if present (RFC 5987 format: filename*=UTF-8''encoded)
        let extracted = quotedMatch[1];
        if (extracted.includes("''")) {
          extracted = decodeURIComponent(extracted.split("''")[1]);
        }
        filename = extracted.trim();
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

  download_link.remove();

  // Clean up the blob URL to free memory
  window.URL.revokeObjectURL(url);
}

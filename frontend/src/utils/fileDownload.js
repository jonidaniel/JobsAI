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
  // Extract filename from Content-Disposition header if available
  // Format: "attachment; filename=\"document.docx\""
  const contentDisposition = headers.get("Content-Disposition");
  let filename = defaultFilename;
  if (contentDisposition) {
    const match = contentDisposition.match(/filename="?(.+)"?/);
    if (match && match[1]) filename = match[1];
  }

  // Create a temporary URL for the blob
  const url = window.URL.createObjectURL(blob);

  // Programmatically trigger file download
  // Create temporary anchor element, click it, then remove it
  const download_link = document.createElement("a");
  download_link.href = url;
  download_link.download = filename;
  document.body.appendChild(download_link);
  download_link.click();
  download_link.remove();

  // Clean up the blob URL to free memory
  window.URL.revokeObjectURL(url);
}

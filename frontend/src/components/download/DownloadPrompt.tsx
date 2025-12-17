/**
 * DownloadPrompt Component
 *
 * Displays the download prompt after pipeline completion.
 * Shows the number of generated cover letters and a download button.
 */

interface DownloadPromptProps {
  filenameCount: number;
  onDownload: () => void;
}

export default function DownloadPrompt({
  filenameCount,
  onDownload,
}: DownloadPromptProps) {
  return (
    <>
      <h3 className="text-base sm:text-xl md:text-2xl lg:text-3xl font-semibold text-white text-center">
        All set! Generated {filenameCount} cover letter
        {filenameCount !== 1 ? "s" : ""}
      </h3>
      <div className="flex justify-center items-center gap-4 mt-6">
        <button
          onClick={onDownload}
          className="text-base sm:text-lg md:text-xl lg:text-2xl px-3 sm:px-4 py-1.5 sm:py-2 border border-white bg-transparent text-white font-semibold rounded-lg shadow hover:bg-white hover:text-gray-800 transition-all"
          aria-label="Download the cover letters"
        >
          Download
        </button>
      </div>
    </>
  );
}

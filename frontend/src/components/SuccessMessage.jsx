/**
 * SuccessMessage Component
 *
 * Displays a success message in a green alert box with a checkmark icon.
 * Used to confirm successful form submission and file download.
 */
export default function SuccessMessage() {
  return (
    <div className="flex justify-center mt-4">
      <div
        className="bg-green-900 border border-green-700 text-green-100 px-6 py-3 rounded-lg shadow-lg max-w-2xl w-full"
        role="alert"
      >
        <div className="flex items-center">
          <svg
            className="w-5 h-5 mr-2 flex-shrink-0"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
              clipRule="evenodd"
            />
          </svg>
          <div>
            <p className="font-semibold">Success!</p>
            <p className="text-sm">
              Your document has been generated and downloaded.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

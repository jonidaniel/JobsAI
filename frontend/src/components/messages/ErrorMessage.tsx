/**
 * ErrorMessage Component
 *
 * Displays an error message in a red alert box with an error icon.
 * Used to show user-friendly error messages when form submission fails.
 */

interface ErrorMessageProps {
  message: string;
}

export default function ErrorMessage({ message }: ErrorMessageProps) {
  return (
    <div className="flex justify-center mt-4">
      <div
        className="bg-red-900 border border-red-700 text-red-100 px-6 py-3 rounded-lg shadow-lg max-w-2xl w-full"
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
              d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
              clipRule="evenodd"
            />
          </svg>
          <div>
            <p className="font-semibold">Error</p>
            <p className="text-sm">{message}</p>
          </div>
        </div>
      </div>
    </div>
  );
}

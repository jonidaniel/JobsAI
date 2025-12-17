/**
 * ActionButtons Component
 *
 * Renders submit and cancel buttons based on the current application state.
 * Handles different button states: normal submission, "Find Again" after completion,
 * and cancellation during pipeline execution.
 */

interface ActionButtonsProps {
  isSubmitting: boolean;
  deliveryMethod: "email" | "download" | null;
  isCancelled: boolean;
  hasSuccessfulSubmission: boolean;
  hasRespondedToPrompt: boolean;
  onSubmit: () => void;
  onCancel: () => void;
}

export default function ActionButtons({
  isSubmitting,
  deliveryMethod,
  isCancelled,
  hasSuccessfulSubmission,
  hasRespondedToPrompt,
  onSubmit,
  onCancel,
}: ActionButtonsProps) {
  return (
    <div className="flex justify-center items-center gap-4 mt-6">
      {isCancelled && (
        <button
          id="submit-btn"
          onClick={onSubmit}
          className="text-lg sm:text-xl md:text-2xl lg:text-3xl px-4 sm:px-6 py-2 sm:py-3 border border-white bg-transparent text-white font-semibold rounded-lg shadow disabled:opacity-50 disabled:cursor-not-allowed"
          aria-label="Start a new job search"
        >
          Find Again
        </button>
      )}
      {isSubmitting && deliveryMethod === "email" && (
        <button
          id="submit-btn"
          onClick={onSubmit}
          className="text-lg sm:text-xl md:text-2xl lg:text-3xl px-4 sm:px-6 py-2 sm:py-3 border border-white bg-transparent text-white font-semibold rounded-lg shadow disabled:opacity-50 disabled:cursor-not-allowed"
          aria-label="Start a new job search"
        >
          Find Again
        </button>
      )}
      {!isSubmitting &&
        !isCancelled &&
        (!hasSuccessfulSubmission || hasRespondedToPrompt) && (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              onSubmit();
            }}
          >
            <button
              id="submit-btn"
              type="submit"
              className="text-lg sm:text-xl md:text-2xl lg:text-3xl px-4 sm:px-6 py-2 sm:py-3 border border-white bg-transparent text-white font-semibold rounded-lg shadow disabled:opacity-50 disabled:cursor-not-allowed"
              aria-label={
                hasSuccessfulSubmission && hasRespondedToPrompt
                  ? "Start a new job search"
                  : "Submit form and generate job search document"
              }
            >
              {hasSuccessfulSubmission && hasRespondedToPrompt
                ? "Find Again"
                : "Find Jobs"}
            </button>
          </form>
        )}
      {isSubmitting && deliveryMethod !== "email" && (
        <button
          id="cancel-btn"
          onClick={onCancel}
          className="text-base sm:text-lg md:text-xl lg:text-2xl px-3 sm:px-4 py-2 sm:py-3 border border-red-400 bg-transparent text-red-400 font-semibold rounded-lg shadow hover:bg-red-400 hover:text-white transition-all"
          aria-label="Cancel the current job search"
        >
          Cancel
        </button>
      )}
    </div>
  );
}

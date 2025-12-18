/**
 * StatusMessages Component
 *
 * Displays various status messages based on the current application state:
 * - Rate limit exceeded
 * - Email delivery confirmation
 * - Cancellation confirmation
 * - Success message after download
 * - Default intro message
 */

interface StatusMessagesProps {
  isRateLimited: boolean;
  isSubmitting: boolean;
  deliveryMethod: "email" | "download" | null;
  coverLetterCount: number;
  isCancelled: boolean;
  hasSuccessfulSubmission: boolean;
  hasDownloaded: boolean;
}

export default function StatusMessages({
  isRateLimited,
  isSubmitting,
  deliveryMethod,
  coverLetterCount,
  isCancelled,
  hasSuccessfulSubmission,
  hasDownloaded,
}: StatusMessagesProps) {
  if (isRateLimited) {
    return (
      <h3 className="text-base sm:text-xl md:text-2xl lg:text-3xl font-semibold text-white text-center">
        You've made too many searches lately
        <br />
        Try again later
      </h3>
    );
  }

  if (isSubmitting && deliveryMethod === "email") {
    return (
      <h3 className="text-base sm:text-xl md:text-2xl lg:text-3xl font-semibold text-white text-center">
        <i>Thank you very much for using JobsAI</i>
        <br />
        Expect the cover {coverLetterCount === 1 ? "letter" : "letters"} to drop
        in your inbox shortly
      </h3>
    );
  }

  if (isCancelled) {
    return (
      <h3 className="text-base sm:text-xl md:text-2xl lg:text-3xl font-semibold text-white text-center">
        You cancelled the job search
      </h3>
    );
  }

  if (hasSuccessfulSubmission && hasDownloaded) {
    return (
      <h3 className="text-base sm:text-xl md:text-2xl lg:text-3xl font-semibold text-white text-center">
        <i>Thank you very much for using JobsAI</i>
        <br />
        Feel free to do another search
      </h3>
    );
  }

  // Default intro message
  return (
    <>
      <h3 className="text-base sm:text-xl md:text-2xl lg:text-3xl font-semibold text-white text-center">
        <i>We will find jobs for you.</i>
      </h3>
      <h3 className="text-base sm:text-xl md:text-2xl lg:text-3xl font-semibold text-white text-center">
        And the way you can make sure we find <i>the most relevant jobs</i> and{" "}
        <i>write the best cover letters</i> is to provide us with a dose of
        information.
      </h3>
      <h3 className="text-base sm:text-xl md:text-2xl lg:text-3xl font-semibold text-white text-center">
        <i>We don't demand you for any personal information.</i>
      </h3>
      <h3 className="text-base sm:text-xl md:text-2xl lg:text-3xl font-semibold text-white text-center">
        By answering as many questions as possible, you enable us to use all
        tools in our arsenal when we scrape jobs for you. This is how we find
        the absolute gems. The questions are easy, and in most of them you just
        select the option that best describes you. Even if you felt like you
        didn't have much experience, be truthful -
      </h3>
      <h3 className="text-base sm:text-xl md:text-2xl lg:text-3xl font-semibold text-white text-center">
        <i>if there is a job matching your skills, we will find it.</i>
      </h3>
      <h3 className="text-base sm:text-xl md:text-2xl lg:text-3xl font-semibold text-white text-center">
        <i>Search</i> let's us start the search.
      </h3>
    </>
  );
}

/**
 * DeliveryMethodSelector Component
 *
 * Handles the delivery method selection UI for cover letters.
 * Allows users to choose between email delivery or browser download.
 *
 * Features:
 * - Two-button selection (email vs download)
 * - Email input form with validation
 * - Back button to return to method selection
 * - Email format validation
 */

import type { DeliveryMethod } from "./types.js";

interface DeliveryMethodSelectorProps {
  deliveryMethod: DeliveryMethod;
  email: string;
  emailError: string | null;
  coverLetterCount: number;
  onMethodSelect: (method: "email" | "download") => void;
  onEmailChange: (email: string) => void;
  onEmailSubmit: () => void;
  onBack: () => void;
}

export default function DeliveryMethodSelector({
  deliveryMethod,
  email,
  emailError,
  coverLetterCount,
  onMethodSelect,
  onEmailChange,
  onEmailSubmit,
  onBack,
}: DeliveryMethodSelectorProps) {
  if (!deliveryMethod) {
    return (
      <>
        <h3 className="text-base sm:text-xl md:text-2xl lg:text-3xl font-semibold text-white text-center">
          Choose delivery method for the cover{" "}
          {coverLetterCount === 1 ? "letter" : "letters"}
        </h3>
        <div className="flex justify-center items-center gap-4 mt-6">
          <button
            onClick={() => onMethodSelect("email")}
            className="text-base sm:text-lg md:text-xl lg:text-2xl px-3 sm:px-4 py-1.5 sm:py-2 border border-white bg-transparent text-white font-semibold rounded-lg shadow hover:bg-white hover:text-gray-800 transition-all"
            aria-label="Via email when ready"
          >
            Via email
            <br />
            when ready
          </button>
          <button
            onClick={() => onMethodSelect("download")}
            className="text-base sm:text-lg md:text-xl lg:text-2xl px-3 sm:px-4 py-1.5 sm:py-2 border border-white bg-transparent text-white font-semibold rounded-lg shadow hover:bg-white hover:text-gray-800 transition-all"
            aria-label="Via browser download (might take minutes)"
          >
            Via browser download
            <br />
            (might take minutes)
          </button>
        </div>
      </>
    );
  }

  if (deliveryMethod === "email") {
    return (
      <>
        <h3 className="text-base sm:text-xl md:text-2xl lg:text-3xl font-semibold text-white text-center">
          Enter your email address
        </h3>
        <div className="flex flex-col items-center gap-4 mt-6">
          <input
            type="email"
            value={email}
            onChange={(e) => onEmailChange(e.target.value)}
            placeholder="your.email@example.com"
            className="text-base sm:text-lg md:text-xl lg:text-2xl px-4 py-2 border border-white bg-transparent text-white placeholder-gray-400 rounded-lg shadow focus:outline-none focus:ring-2 focus:ring-white w-full max-w-md"
            aria-label="Email address"
            aria-invalid={emailError ? "true" : "false"}
            aria-describedby={emailError ? "email-error" : undefined}
          />
          {emailError && (
            <p
              id="email-error"
              className="text-sm sm:text-base text-red-400 text-center"
            >
              {emailError}
            </p>
          )}
          <div className="flex justify-center items-center gap-4">
            <button
              onClick={onBack}
              className="text-base sm:text-lg md:text-xl lg:text-2xl px-3 sm:px-4 py-1.5 sm:py-2 border border-white bg-transparent text-white font-semibold rounded-lg shadow hover:bg-white hover:text-gray-800 transition-all"
              aria-label="Go back to delivery method selection"
            >
              Back
            </button>
            <button
              onClick={onEmailSubmit}
              className="text-base sm:text-lg md:text-xl lg:text-2xl px-3 sm:px-4 py-1.5 sm:py-2 border border-white bg-transparent text-white font-semibold rounded-lg shadow hover:bg-white hover:text-gray-800 transition-all"
              aria-label="Continue with email delivery"
            >
              Continue
            </button>
          </div>
        </div>
      </>
    );
  }

  return null;
}

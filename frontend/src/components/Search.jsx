import { useState } from "react";
import QuestionSets from "./QuestionSets";
import { API_ENDPOINTS } from "../config/api";
import "../styles/search.css";

export default function Search() {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  // Get user-friendly error message
  const getErrorMessage = (error) => {
    if (error instanceof TypeError && error.message.includes("fetch")) {
      return "Unable to connect to the server. Please check your internet connection and try again.";
    }
    if (error.message.includes("Server error: 404")) {
      return "The requested endpoint was not found. Please contact support.";
    }
    if (error.message.includes("Server error: 500")) {
      return "The server encountered an error. Please try again later.";
    }
    if (error.message.includes("Server error: 400")) {
      return "Invalid request. Please check your answers and try again.";
    }
    if (error.message.includes("Server error")) {
      return `Server error occurred. Please try again later. (${error.message})`;
    }
    return "An unexpected error occurred. Please try again.";
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    e.stopPropagation();

    // Prevent double submission
    if (isSubmitting) {
      return;
    }

    // Clear previous errors and success messages
    setError(null);
    setSuccess(false);
    setIsSubmitting(true);

    // Collect form data
    const result = {};

    // Iterate over all slider questions
    document.querySelectorAll(".slider").forEach((slider) => {
      if (slider.value != 0) {
        const key = slider.dataset.key;
        result[key] = Number(slider.value);
      }
    });

    // Iterate over all checkbox questions (multiple choice)
    document.querySelectorAll(".checkbox-field").forEach((checkbox) => {
      if (checkbox.checked) {
        const key = checkbox.dataset.key;
        const value = checkbox.dataset.value;
        // Store as array if multiple selections, or as single value
        if (!result[key]) {
          result[key] = [];
        }
        result[key].push(value);
      }
    });

    // Iterate over all text field questions
    document.querySelectorAll(".text-field").forEach((textField) => {
      if (textField.value != "") {
        const key = textField.dataset.key;
        result[key] = textField.value.trim();
      }
    });

    // Send to backend and download document
    try {
      const response = await fetch(API_ENDPOINTS.SUBMIT_FORM, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(result),
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      // Get the response as a blob (binary)
      const blob = await response.blob();

      // Get the filename from Content-Disposition header if available
      const contentDisposition = response.headers.get("Content-Disposition");
      let filename = "document.docx"; // default fallback
      if (contentDisposition) {
        const match = contentDisposition.match(/filename="?(.+)"?/);
        if (match && match[1]) filename = match[1];
      }

      // Create a temporary URL for the blob
      const url = window.URL.createObjectURL(blob);

      // Create a temporary link element to trigger download
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();

      // Clean up the blob URL
      window.URL.revokeObjectURL(url);

      // Show success message
      setSuccess(true);
      setError(null);
    } catch (error) {
      console.error("Download failed:", error);
      setError(getErrorMessage(error));
      setSuccess(false);
    } finally {
      // Reset submission flag after request completes
      setIsSubmitting(false);
    }
  };

  return (
    <section id="search">
      <h2>Search</h2>
      <h3 className="text-3xl font-semibold text-white text-center">
        Answer questions in each category and we will find jobs relevant to you
      </h3>
      <QuestionSets />
      {/* Error message */}
      {error && (
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
                <p className="text-sm">{error}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Success message */}
      {success && (
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
      )}

      {/* Submit button */}
      <div className="flex justify-center mt-6">
        <button
          id="submit-btn"
          onClick={handleSubmit}
          disabled={isSubmitting}
          className="text-3xl px-6 py-3 border border-white bg-transparent text-white font-semibold rounded-lg shadow disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSubmitting ? "Finding Jobs..." : "Find Jobs"}
        </button>
      </div>
    </section>
  );
}

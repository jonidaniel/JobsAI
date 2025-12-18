/**
 * Integration Tests for Search Component
 *
 * Tests complete user flows end-to-end:
 * - Complete form submission flow (validation → delivery selection → pipeline → download)
 * - Complete email delivery flow
 * - Error recovery and retry flows
 * - Rate limiting flow
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Search from "../Search";
import { API_ENDPOINTS } from "../../config/api";

// Mock dependencies
vi.mock("../../components/QuestionSetList", () => ({
  default: ({ onFormDataChange, validationErrors }) => (
    <div data-testid="question-set-list">
      <button
        onClick={() =>
          onFormDataChange({
            "job-level": ["Expert-level"],
            "job-boards": ["Duunitori"],
            "deep-mode": "Yes",
            "cover-letter-num": "1",
            "cover-letter-style": ["Professional"],
            "additional-info": "Test description",
          })
        }
      >
        Fill Form
      </button>
      {Object.keys(validationErrors).length > 0 && (
        <div data-testid="validation-errors">
          {Object.keys(validationErrors).join(", ")}
        </div>
      )}
    </div>
  ),
}));

vi.mock("../../components/messages/ErrorMessage", () => ({
  default: ({ message }) => <div data-testid="error-message">{message}</div>,
}));

vi.mock("../../utils/fileDownload", () => ({
  downloadBlob: vi.fn(),
}));

describe("Search Component - Integration Tests", () => {
  let fetchMock;

  beforeEach(() => {
    window.fetch = vi.fn();
    fetchMock = window.fetch;
    window.scrollTo = vi.fn();
    window.URL.createObjectURL = vi.fn(() => "blob:mock-url");
    window.URL.revokeObjectURL = vi.fn();
  });

  afterEach(() => {
    vi.clearAllMocks();
    vi.clearAllTimers();
  });

  describe("Complete download delivery flow", () => {
    it("should complete full flow: form → delivery selection → pipeline → download", async () => {
      const user = userEvent.setup();
      let pollCount = 0;

      fetchMock.mockImplementation((url) => {
        if (url === API_ENDPOINTS.START) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ job_id: "test-job-id" }),
          });
        }
        if (url.includes(API_ENDPOINTS.PROGRESS)) {
          pollCount++;
          // Simulate progress updates
          if (pollCount === 1) {
            return Promise.resolve({
              ok: true,
              json: async () => ({
                status: "running",
                progress: {
                  phase: "profiling",
                  message: "Creating your profile...",
                },
              }),
            });
          }
          if (pollCount === 2) {
            return Promise.resolve({
              ok: true,
              json: async () => ({
                status: "running",
                progress: {
                  phase: "searching",
                  message: "Searching for jobs...",
                },
              }),
            });
          }
          // Complete after a few polls
          return Promise.resolve({
            ok: true,
            json: async () => ({
              status: "complete",
              filename: "cover_letter.docx",
            }),
          });
        }
        if (url === `${API_ENDPOINTS.DOWNLOAD}/test-job-id`) {
          return Promise.resolve({
            ok: true,
            headers: new Headers({ "content-type": "application/json" }),
            json: async () => ({
              download_url: "https://s3.amazonaws.com/test-url",
              filename: "cover_letter.docx",
            }),
          });
        }
        if (url === "https://s3.amazonaws.com/test-url") {
          return Promise.resolve({
            ok: true,
            arrayBuffer: async () => new ArrayBuffer(8),
            headers: new Headers(),
          });
        }
        return Promise.reject(new Error(`Unexpected URL: ${url}`));
      });

      render(<Search />);

      // Step 1: Fill form
      const fillButton = screen.getByText("Fill Form");
      await user.click(fillButton);

      // Step 2: Submit form
      const submitButton = document.getElementById("submit-btn");
      expect(submitButton).toBeInTheDocument();
      await user.click(submitButton);

      // Step 3: Should show delivery method selector
      await waitFor(() => {
        expect(
          screen.getByText(/Choose delivery method for the cover/)
        ).toBeInTheDocument();
      });

      // Step 4: Select download delivery
      const downloadButton = screen.getByLabelText(
        /Via browser download.*might take minutes/i
      );
      await user.click(downloadButton);

      // Step 5: Should start pipeline and show progress
      await waitFor(() => {
        expect(screen.getByText(/1\/6 Starting search/i)).toBeInTheDocument();
      });

      // Step 6: Should show progress updates
      await waitFor(
        () => {
          expect(
            screen.getByText(/2\/6 Creating your profile/i)
          ).toBeInTheDocument();
        },
        { timeout: 5000 }
      );

      // Step 7: Should show completion and download prompt
      await waitFor(
        () => {
          expect(screen.getByText(/All set! Generated/)).toBeInTheDocument();
        },
        { timeout: 10000 }
      );

      // Step 8: Download document
      const downloadPromptButton = screen.getByLabelText(
        /Download the cover letters/i
      );
      await user.click(downloadPromptButton);

      // Step 9: Should show thank you message after download
      await waitFor(
        () => {
          expect(
            screen.getByText(/Thank you very much for using JobsAI/i)
          ).toBeInTheDocument();
        },
        { timeout: 5000 }
      );

      // Step 10: Find Again button should be available
      expect(screen.getByText("Find Again")).toBeInTheDocument();
    });
  });

  describe("Complete email delivery flow", () => {
    it("should complete full email flow: form → email selection → submission → persistence", async () => {
      const user = userEvent.setup();

      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ job_id: "test-job-id" }),
      });

      render(<Search />);

      // Step 1: Fill form
      const fillButton = screen.getByText("Fill Form");
      await user.click(fillButton);

      // Step 2: Submit form
      const submitButton = document.getElementById("submit-btn");
      await user.click(submitButton);

      // Step 3: Select email delivery
      await waitFor(() => {
        const emailButton = screen.getByLabelText(/Via email when ready/i);
        expect(emailButton).toBeInTheDocument();
      });

      const emailButton = screen.getByLabelText(/Via email when ready/i);
      await user.click(emailButton);

      // Step 4: Enter email
      const emailInput = screen.getByLabelText(/Email address/i);
      await user.type(emailInput, "test@example.com");

      // Step 5: Submit email
      const continueButton = screen.getByLabelText(
        /Continue with email delivery/i
      );
      await user.click(continueButton);

      // Step 6: Should show thank you message immediately
      await waitFor(() => {
        expect(
          screen.getByText(/Thank you very much for using JobsAI/i)
        ).toBeInTheDocument();
      });

      // Step 7: Message should persist
      await waitFor(
        () => {
          expect(
            screen.getByText(/Thank you very much for using JobsAI/i)
          ).toBeInTheDocument();
        },
        { timeout: 5000 }
      );

      // Step 8: Find Again button should be available
      expect(screen.getByText("Find Again")).toBeInTheDocument();

      // Step 9: Should NOT poll for progress (email is fire-and-forget)
      await waitFor(
        () => {
          const progressCalls = fetchMock.mock.calls.filter((call) =>
            call[0]?.includes(API_ENDPOINTS.PROGRESS)
          );
          expect(progressCalls.length).toBe(0);
        },
        { timeout: 5000 }
      );
    });
  });

  describe("Error recovery flow", () => {
    it("should recover from network error and allow retry", async () => {
      const user = userEvent.setup();
      let attemptCount = 0;

      fetchMock.mockImplementation((url) => {
        if (url === API_ENDPOINTS.START) {
          attemptCount++;
          if (attemptCount === 1) {
            // First attempt fails
            return Promise.reject(new Error("Network error"));
          }
          // Second attempt succeeds
          return Promise.resolve({
            ok: true,
            json: async () => ({ job_id: "test-job-id" }),
          });
        }
        if (url.includes(API_ENDPOINTS.PROGRESS)) {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              status: "running",
              progress: { phase: "profiling" },
            }),
          });
        }
        return Promise.reject(new Error(`Unexpected URL: ${url}`));
      });

      render(<Search />);

      const fillButton = screen.getByText("Fill Form");
      await user.click(fillButton);

      const submitButton = document.getElementById("submit-btn");
      await user.click(submitButton);

      // Select download delivery
      await waitFor(() => {
        const downloadButton = screen.getByLabelText(
          /Via browser download.*might take minutes/i
        );
        expect(downloadButton).toBeInTheDocument();
      });

      const downloadButton = screen.getByLabelText(
        /Via browser download.*might take minutes/i
      );
      await user.click(downloadButton);

      // Should show error
      await waitFor(() => {
        expect(screen.getByTestId("error-message")).toBeInTheDocument();
      });

      // Retry submission
      const retryButton = document.getElementById("submit-btn");
      if (retryButton) {
        await user.click(retryButton);

        // Should show delivery method selector again
        await waitFor(() => {
          expect(
            screen.getByText(/Choose delivery method for the cover/)
          ).toBeInTheDocument();
        });

        // Select download again
        const downloadButton2 = screen.getByLabelText(
          /Via browser download.*might take minutes/i
        );
        await user.click(downloadButton2);

        // Should succeed on retry
        await waitFor(() => {
          expect(screen.getByText(/1\/6 Starting search/i)).toBeInTheDocument();
        });
      }
    });
  });

  describe("Rate limiting flow", () => {
    it("should handle rate limit and show appropriate message", async () => {
      const user = userEvent.setup();

      fetchMock.mockResolvedValueOnce({
        ok: false,
        status: 429,
      });

      render(<Search />);

      const fillButton = screen.getByText("Fill Form");
      await user.click(fillButton);

      const submitButton = document.getElementById("submit-btn");
      await user.click(submitButton);

      // Select download delivery
      await waitFor(() => {
        const downloadButton = screen.getByLabelText(
          /Via browser download.*might take minutes/i
        );
        expect(downloadButton).toBeInTheDocument();
      });

      const downloadButton = screen.getByLabelText(
        /Via browser download.*might take minutes/i
      );
      await user.click(downloadButton);

      // Should show rate limit message
      await waitFor(() => {
        expect(
          screen.getByText(/You've made too many searches lately/i)
        ).toBeInTheDocument();
      });

      // Should NOT show form or submit button
      expect(screen.queryByTestId("question-set-list")).not.toBeInTheDocument();
      expect(document.getElementById("submit-btn")).not.toBeInTheDocument();
    });
  });

  describe("Cancellation and Find Again flow", () => {
    it("should allow cancellation and then Find Again", async () => {
      const user = userEvent.setup();

      fetchMock.mockImplementation((url) => {
        if (url === API_ENDPOINTS.START) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ job_id: "test-job-id" }),
          });
        }
        if (url.includes(API_ENDPOINTS.PROGRESS)) {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              status: "running",
              progress: { phase: "profiling" },
            }),
          });
        }
        if (url.includes(API_ENDPOINTS.CANCEL)) {
          return Promise.resolve({ ok: true });
        }
        return Promise.reject(new Error(`Unexpected URL: ${url}`));
      });

      render(<Search />);

      const fillButton = screen.getByText("Fill Form");
      await user.click(fillButton);

      const submitButton = document.getElementById("submit-btn");
      await user.click(submitButton);

      // Select download delivery
      await waitFor(() => {
        const downloadButton = screen.getByLabelText(
          /Via browser download.*might take minutes/i
        );
        expect(downloadButton).toBeInTheDocument();
      });

      const downloadButton = screen.getByLabelText(
        /Via browser download.*might take minutes/i
      );
      await user.click(downloadButton);

      // Wait for cancel button
      await waitFor(() => {
        expect(screen.getByText("Cancel")).toBeInTheDocument();
      });

      // Cancel pipeline
      const cancelButton = screen.getByText("Cancel");
      await user.click(cancelButton);

      // Should show cancellation message
      await waitFor(() => {
        expect(
          screen.getByText(/You cancelled the job search/i)
        ).toBeInTheDocument();
      });

      // Find Again button should appear
      const findAgainButton = screen.getByText("Find Again");
      expect(findAgainButton).toBeInTheDocument();

      // Click Find Again
      await user.click(findAgainButton);

      // Should show form again
      await waitFor(() => {
        expect(screen.getByTestId("question-set-list")).toBeInTheDocument();
      });
    });
  });
});

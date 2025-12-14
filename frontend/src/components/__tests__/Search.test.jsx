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

vi.mock("../../components/messages/SuccessMessage", () => ({
  default: () => <div data-testid="success-message">Success!</div>,
}));

vi.mock("../../components/messages/ErrorMessage", () => ({
  default: ({ message }) => <div data-testid="error-message">{message}</div>,
}));

vi.mock("../../utils/fileDownload", () => ({
  downloadBlob: vi.fn(),
}));

describe("Search Component", () => {
  let fetchMock;

  beforeEach(() => {
    // Mock fetch globally
    window.fetch = vi.fn();
    fetchMock = window.fetch;

    // Mock window.scrollTo
    window.scrollTo = vi.fn();

    // Mock URL.createObjectURL and revokeObjectURL
    window.URL.createObjectURL = vi.fn(() => "blob:mock-url");
    window.URL.revokeObjectURL = vi.fn();
  });

  afterEach(() => {
    vi.clearAllMocks();
    vi.clearAllTimers();
  });

  describe("Form submission", () => {
    it("should show loading state when form is submitted", async () => {
      const user = userEvent.setup();
      fetchMock
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ job_id: "test-job-id" }),
        })
        .mockResolvedValue({
          ok: true,
          json: async () => ({
            status: "running",
            progress: { phase: "profiling" },
          }),
        });

      render(<Search />);

      // Fill form
      const fillButton = screen.getByText("Fill Form");
      await user.click(fillButton);

      // Submit form (use getElementById to avoid multiple text matches)
      const submitButton = document.getElementById("submit-btn");
      expect(submitButton).toBeInTheDocument();
      await user.click(submitButton);

      // Button should be hidden when submitting, so we check that it's not visible
      await waitFor(
        () => {
          const submitButton = document.getElementById("submit-btn");
          expect(submitButton).not.toBeInTheDocument();
          // Cancel button should appear immediately
          expect(screen.getByText("Cancel")).toBeInTheDocument();
        },
        { timeout: 3000 }
      );
    });

    it("should call API with correct data on submit", async () => {
      const user = userEvent.setup();
      fetchMock
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ job_id: "test-job-id" }),
        })
        .mockResolvedValue({
          ok: true,
          json: async () => ({
            status: "running",
            progress: { phase: "profiling" },
          }),
        });

      render(<Search />);

      const fillButton = screen.getByText("Fill Form");
      await user.click(fillButton);

      const submitButton = document.getElementById("submit-btn");
      expect(submitButton).toBeInTheDocument();
      await user.click(submitButton);

      await waitFor(
        () => {
          expect(fetchMock).toHaveBeenCalledWith(
            API_ENDPOINTS.START,
            expect.objectContaining({
              method: "POST",
              headers: {
                "Content-Type": "application/json",
              },
            })
          );
        },
        { timeout: 3000 }
      );
    });

    it("should display error when API call fails", async () => {
      const user = userEvent.setup();
      fetchMock.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ detail: "Server error" }),
      });

      render(<Search />);

      const fillButton = screen.getByText("Fill Form");
      await user.click(fillButton);

      const submitButton = document.getElementById("submit-btn");
      expect(submitButton).toBeInTheDocument();
      await user.click(submitButton);

      await waitFor(
        () => {
          expect(screen.getByTestId("error-message")).toBeInTheDocument();
        },
        { timeout: 3000 }
      );
    });

    it("should prevent double submission", async () => {
      const user = userEvent.setup();
      fetchMock.mockImplementation((url) => {
        if (url === API_ENDPOINTS.START) {
          return new Promise((resolve) => {
            setTimeout(
              () =>
                resolve({
                  ok: true,
                  json: async () => ({ job_id: "test-job-id" }),
                }),
              100
            );
          });
        }
        // Mock progress polling
        return Promise.resolve({
          ok: true,
          json: async () => ({
            status: "running",
            progress: { phase: "profiling" },
          }),
        });
      });

      render(<Search />);

      const fillButton = screen.getByText("Fill Form");
      await user.click(fillButton);

      const submitButton = document.getElementById("submit-btn");
      expect(submitButton).toBeInTheDocument();
      await user.click(submitButton);
      await user.click(submitButton); // Try to submit again

      // Should only call API once for START endpoint
      await waitFor(
        () => {
          const startCalls = fetchMock.mock.calls.filter(
            (call) => call[0] === API_ENDPOINTS.START
          );
          expect(startCalls.length).toBe(1);
        },
        { timeout: 3000 }
      );
    });
  });

  describe("Progress polling", () => {
    it("should poll progress endpoint after starting pipeline", async () => {
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
        return Promise.reject(new Error(`Unexpected URL: ${url}`));
      });

      render(<Search />);

      const fillButton = screen.getByText("Fill Form");
      await user.click(fillButton);

      const submitButton = document.getElementById("submit-btn");
      expect(submitButton).toBeInTheDocument();
      await user.click(submitButton);

      // Wait for progress polling to start (happens immediately after START)
      await waitFor(
        () => {
          const progressCalls = fetchMock.mock.calls.filter((call) =>
            call[0].includes(API_ENDPOINTS.PROGRESS)
          );
          expect(progressCalls.length).toBeGreaterThan(0);
        },
        { timeout: 10000 }
      );
    });

    it("should handle completion and download document", async () => {
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
              status: "complete",
              filename: "cover_letter.docx",
              download_url: "https://s3.amazonaws.com/test-url",
            }),
          });
        }
        if (url === `${API_ENDPOINTS.DOWNLOAD}/test-job-id`) {
          return Promise.resolve({
            ok: true,
            headers: new Headers({
              "content-type": "application/json",
            }),
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

      const fillButton = screen.getByText("Fill Form");
      await user.click(fillButton);

      const submitButton = document.getElementById("submit-btn");
      expect(submitButton).toBeInTheDocument();
      await user.click(submitButton);

      await waitFor(
        () => {
          expect(screen.getByTestId("success-message")).toBeInTheDocument();
        },
        { timeout: 10000 }
      );
    });

    it("should handle multiple document downloads", async () => {
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
              status: "complete",
              filenames: ["cover_letter_1.docx", "cover_letter_2.docx"],
            }),
          });
        }
        if (url === `${API_ENDPOINTS.DOWNLOAD}/test-job-id`) {
          return Promise.resolve({
            ok: true,
            headers: new Headers({
              "content-type": "application/json",
            }),
            json: async () => ({
              download_urls: [
                {
                  url: "https://s3.amazonaws.com/test-url-1",
                  filename: "cover_letter_1.docx",
                },
                {
                  url: "https://s3.amazonaws.com/test-url-2",
                  filename: "cover_letter_2.docx",
                },
              ],
            }),
          });
        }
        if (url.includes("s3.amazonaws.com")) {
          return Promise.resolve({
            ok: true,
            arrayBuffer: async () => new ArrayBuffer(8),
            headers: new Headers(),
          });
        }
        return Promise.reject(new Error(`Unexpected URL: ${url}`));
      });

      render(<Search />);

      const fillButton = screen.getByText("Fill Form");
      await user.click(fillButton);

      const submitButton = document.getElementById("submit-btn");
      expect(submitButton).toBeInTheDocument();
      await user.click(submitButton);

      // Wait for download to be triggered (after progress shows complete)
      await waitFor(
        () => {
          const s3Calls = fetchMock.mock.calls.filter((call) =>
            call[0].includes("s3.amazonaws.com")
          );
          expect(s3Calls.length).toBeGreaterThan(0);
        },
        { timeout: 10000 }
      );
    });
  });

  describe("Cancellation", () => {
    it("should show cancel button when pipeline is running", async () => {
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
        return Promise.reject(new Error(`Unexpected URL: ${url}`));
      });

      render(<Search />);

      const fillButton = screen.getByText("Fill Form");
      await user.click(fillButton);

      const submitButton = document.getElementById("submit-btn");
      expect(submitButton).toBeInTheDocument();
      await user.click(submitButton);

      await waitFor(
        () => {
          expect(screen.getByText("Cancel")).toBeInTheDocument();
        },
        { timeout: 10000 }
      );
    });

    it("should cancel pipeline when cancel button is clicked", async () => {
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
          return Promise.resolve({
            ok: true,
          });
        }
        return Promise.reject(new Error(`Unexpected URL: ${url}`));
      });

      render(<Search />);

      const fillButton = screen.getByText("Fill Form");
      await user.click(fillButton);

      const submitButton = document.getElementById("submit-btn");
      expect(submitButton).toBeInTheDocument();
      await user.click(submitButton);

      await waitFor(
        () => {
          expect(screen.getByText("Cancel")).toBeInTheDocument();
        },
        { timeout: 10000 }
      );

      const cancelButton = screen.getByText("Cancel");
      await user.click(cancelButton);

      await waitFor(
        () => {
          expect(fetchMock).toHaveBeenCalledWith(
            `${API_ENDPOINTS.CANCEL}/test-job-id`,
            expect.objectContaining({ method: "POST" })
          );
        },
        { timeout: 10000 }
      );
    });
  });

  describe("Validation", () => {
    it("should show validation errors for incomplete form", async () => {
      const user = userEvent.setup();
      render(<Search />);

      const submitButton = document.getElementById("submit-btn");
      expect(submitButton).toBeInTheDocument();
      await user.click(submitButton);

      await waitFor(
        () => {
          expect(screen.getByTestId("validation-errors")).toBeInTheDocument();
        },
        { timeout: 3000 }
      );
    });

    it("should not submit form when validation fails", async () => {
      const user = userEvent.setup();
      render(<Search />);

      const submitButton = document.getElementById("submit-btn");
      expect(submitButton).toBeInTheDocument();
      await user.click(submitButton);

      await waitFor(
        () => {
          // Should not call START endpoint when validation fails
          const startCalls = fetchMock.mock.calls.filter(
            (call) => call[0] === API_ENDPOINTS.START
          );
          expect(startCalls.length).toBe(0);
        },
        { timeout: 3000 }
      );
    });
  });

  describe("Find Again functionality", () => {
    it("should show Find Again button after successful submission", async () => {
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
              status: "complete",
              filename: "cover_letter.docx",
              download_url: "https://s3.amazonaws.com/test-url",
            }),
          });
        }
        if (url === `${API_ENDPOINTS.DOWNLOAD}/test-job-id`) {
          return Promise.resolve({
            ok: true,
            headers: new Headers({
              "content-type": "application/json",
            }),
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

      const fillButton = screen.getByText("Fill Form");
      await user.click(fillButton);

      const submitButton = document.getElementById("submit-btn");
      expect(submitButton).toBeInTheDocument();
      await user.click(submitButton);

      await waitFor(
        () => {
          expect(screen.getByText("Find Again")).toBeInTheDocument();
        },
        { timeout: 10000 }
      );
    });
  });
});

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
    global.fetch = vi.fn();
    fetchMock = global.fetch;

    // Mock window.scrollTo
    window.scrollTo = vi.fn();

    // Mock URL.createObjectURL and revokeObjectURL
    global.URL.createObjectURL = vi.fn(() => "blob:mock-url");
    global.URL.revokeObjectURL = vi.fn();
  });

  afterEach(() => {
    vi.clearAllMocks();
    vi.clearAllTimers();
  });

  describe("Form submission", () => {
    it("should show loading state when form is submitted", async () => {
      const user = userEvent.setup();
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ job_id: "test-job-id" }),
      });

      render(<Search />);

      // Fill form
      const fillButton = screen.getByText("Fill Form");
      await user.click(fillButton);

      // Submit form
      const submitButton = screen.getByText("Find Jobs");
      await user.click(submitButton);

      expect(screen.getByText(/Finding Jobs/i)).toBeInTheDocument();
    });

    it("should call API with correct data on submit", async () => {
      const user = userEvent.setup();
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ job_id: "test-job-id" }),
      });

      render(<Search />);

      const fillButton = screen.getByText("Fill Form");
      await user.click(fillButton);

      const submitButton = screen.getByText("Find Jobs");
      await user.click(submitButton);

      await waitFor(() => {
        expect(fetchMock).toHaveBeenCalledWith(
          API_ENDPOINTS.START,
          expect.objectContaining({
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
          })
        );
      });
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

      const submitButton = screen.getByText("Find Jobs");
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByTestId("error-message")).toBeInTheDocument();
      });
    });

    it("should prevent double submission", async () => {
      const user = userEvent.setup();
      fetchMock.mockImplementation(
        () =>
          new Promise((resolve) => {
            setTimeout(
              () =>
                resolve({
                  ok: true,
                  json: async () => ({ job_id: "test-job-id" }),
                }),
              100
            );
          })
      );

      render(<Search />);

      const fillButton = screen.getByText("Fill Form");
      await user.click(fillButton);

      const submitButton = screen.getByText("Find Jobs");
      await user.click(submitButton);
      await user.click(submitButton); // Try to submit again

      // Should only call API once
      await waitFor(() => {
        expect(fetchMock).toHaveBeenCalledTimes(1);
      });
    });
  });

  describe("Progress polling", () => {
    it("should poll progress endpoint after starting pipeline", async () => {
      const user = userEvent.setup();
      vi.useFakeTimers();

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

      const submitButton = screen.getByText("Find Jobs");
      await user.click(submitButton);

      await waitFor(() => {
        expect(fetchMock).toHaveBeenCalledWith(
          `${API_ENDPOINTS.PROGRESS}/test-job-id`
        );
      });

      // Advance timer to trigger polling
      vi.advanceTimersByTime(2000);

      await waitFor(() => {
        expect(fetchMock).toHaveBeenCalledTimes(2);
      });

      vi.useRealTimers();
    });

    it("should handle completion and download document", async () => {
      const user = userEvent.setup();
      const { downloadBlob } = await import("../../utils/fileDownload");

      fetchMock
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ job_id: "test-job-id" }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            status: "complete",
            filename: "cover_letter.docx",
            download_url: "https://s3.amazonaws.com/test-url",
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          headers: new Headers({
            "content-type": "application/json",
          }),
          json: async () => ({
            download_url: "https://s3.amazonaws.com/test-url",
            filename: "cover_letter.docx",
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          arrayBuffer: async () => new ArrayBuffer(8),
          headers: new Headers(),
        });

      render(<Search />);

      const fillButton = screen.getByText("Fill Form");
      await user.click(fillButton);

      const submitButton = screen.getByText("Find Jobs");
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByTestId("success-message")).toBeInTheDocument();
      });
    });

    it("should handle multiple document downloads", async () => {
      const user = userEvent.setup();
      const { downloadBlob } = await import("../../utils/fileDownload");

      fetchMock
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ job_id: "test-job-id" }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            status: "complete",
            filenames: ["cover_letter_1.docx", "cover_letter_2.docx"],
          }),
        })
        .mockResolvedValueOnce({
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
        })
        .mockResolvedValue({
          ok: true,
          arrayBuffer: async () => new ArrayBuffer(8),
          headers: new Headers(),
        });

      render(<Search />);

      const fillButton = screen.getByText("Fill Form");
      await user.click(fillButton);

      const submitButton = screen.getByText("Find Jobs");
      await user.click(submitButton);

      await waitFor(() => {
        expect(fetchMock).toHaveBeenCalledWith(
          "https://s3.amazonaws.com/test-url-1"
        );
      });
    });
  });

  describe("Cancellation", () => {
    it("should show cancel button when pipeline is running", async () => {
      const user = userEvent.setup();
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ job_id: "test-job-id" }),
      });

      render(<Search />);

      const fillButton = screen.getByText("Fill Form");
      await user.click(fillButton);

      const submitButton = screen.getByText("Find Jobs");
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText("Cancel")).toBeInTheDocument();
      });
    });

    it("should cancel pipeline when cancel button is clicked", async () => {
      const user = userEvent.setup();
      fetchMock
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ job_id: "test-job-id" }),
        })
        .mockResolvedValueOnce({
          ok: true,
        });

      render(<Search />);

      const fillButton = screen.getByText("Fill Form");
      await user.click(fillButton);

      const submitButton = screen.getByText("Find Jobs");
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText("Cancel")).toBeInTheDocument();
      });

      const cancelButton = screen.getByText("Cancel");
      await user.click(cancelButton);

      await waitFor(() => {
        expect(fetchMock).toHaveBeenCalledWith(
          `${API_ENDPOINTS.CANCEL}/test-job-id`,
          { method: "POST" }
        );
      });
    });
  });

  describe("Validation", () => {
    it("should show validation errors for incomplete form", async () => {
      const user = userEvent.setup();
      render(<Search />);

      const submitButton = screen.getByText("Find Jobs");
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByTestId("validation-errors")).toBeInTheDocument();
      });
    });

    it("should not submit form when validation fails", async () => {
      const user = userEvent.setup();
      render(<Search />);

      const submitButton = screen.getByText("Find Jobs");
      await user.click(submitButton);

      await waitFor(() => {
        expect(fetchMock).not.toHaveBeenCalled();
      });
    });
  });

  describe("Find Again functionality", () => {
    it("should show Find Again button after successful submission", async () => {
      const user = userEvent.setup();
      fetchMock
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ job_id: "test-job-id" }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            status: "complete",
            filename: "cover_letter.docx",
            download_url: "https://s3.amazonaws.com/test-url",
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          headers: new Headers({
            "content-type": "application/json",
          }),
          json: async () => ({
            download_url: "https://s3.amazonaws.com/test-url",
            filename: "cover_letter.docx",
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          arrayBuffer: async () => new ArrayBuffer(8),
          headers: new Headers(),
        });

      render(<Search />);

      const fillButton = screen.getByText("Fill Form");
      await user.click(fillButton);

      const submitButton = screen.getByText("Find Jobs");
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText("Find Again")).toBeInTheDocument();
      });
    });
  });
});

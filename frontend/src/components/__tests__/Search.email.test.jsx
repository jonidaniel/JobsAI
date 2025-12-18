/**
 * Email Delivery Flow Tests
 *
 * Tests the fire-and-forget email delivery flow:
 * - Email delivery method selection
 * - Email validation
 * - Fire-and-forget submission (no polling)
 * - UI persistence after email submission
 * - Error handling (silent failures except rate limits)
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Search from "../Search";
import { API_ENDPOINTS } from "../../config/api";

// Mock dependencies
vi.mock("../../components/QuestionSetList", () => ({
  default: ({ onFormDataChange }) => (
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
    </div>
  ),
}));

vi.mock("../../components/messages/ErrorMessage", () => ({
  default: ({ message }) => <div data-testid="error-message">{message}</div>,
}));

describe("Search Component - Email Delivery Flow", () => {
  let fetchMock;

  beforeEach(() => {
    window.fetch = vi.fn();
    fetchMock = window.fetch;
    window.scrollTo = vi.fn();
  });

  afterEach(() => {
    vi.clearAllMocks();
    vi.clearAllTimers();
  });

  describe("Email delivery method selection", () => {
    it("should show delivery method selector after form submission", async () => {
      const user = userEvent.setup();
      render(<Search />);

      // Fill and submit form
      const fillButton = screen.getByText("Fill Form");
      await user.click(fillButton);

      const submitButton = document.getElementById("submit-btn");
      await user.click(submitButton);

      // Should show delivery method selector
      await waitFor(() => {
        expect(
          screen.getByText(/Choose delivery method for the cover/)
        ).toBeInTheDocument();
      });
    });

    it("should show email input when email delivery is selected", async () => {
      const user = userEvent.setup();
      render(<Search />);

      // Fill and submit form
      const fillButton = screen.getByText("Fill Form");
      await user.click(fillButton);

      const submitButton = document.getElementById("submit-btn");
      await user.click(submitButton);

      // Select email delivery
      await waitFor(() => {
        const emailButton = screen.getByLabelText(/Via email when ready/i);
        expect(emailButton).toBeInTheDocument();
      });

      const emailButton = screen.getByLabelText(/Via email when ready/i);
      await user.click(emailButton);

      // Should show email input
      await waitFor(() => {
        expect(screen.getByLabelText(/Email address/i)).toBeInTheDocument();
      });
    });

    it("should validate email format", async () => {
      const user = userEvent.setup();
      render(<Search />);

      // Fill and submit form
      const fillButton = screen.getByText("Fill Form");
      await user.click(fillButton);

      const submitButton = document.getElementById("submit-btn");
      await user.click(submitButton);

      // Select email delivery
      await waitFor(() => {
        const emailButton = screen.getByLabelText(/Via email when ready/i);
        expect(emailButton).toBeInTheDocument();
      });

      const emailButton = screen.getByLabelText(/Via email when ready/i);
      await user.click(emailButton);

      // Enter invalid email
      const emailInput = screen.getByLabelText(/Email address/i);
      await user.type(emailInput, "invalid-email");

      const continueButton = screen.getByLabelText(
        /Continue with email delivery/i
      );
      await user.click(continueButton);

      // Should show validation error
      await waitFor(() => {
        expect(
          screen.getByText(/Please enter a valid email address/i)
        ).toBeInTheDocument();
      });
    });

    it("should require email address", async () => {
      const user = userEvent.setup();
      render(<Search />);

      // Fill and submit form
      const fillButton = screen.getByText("Fill Form");
      await user.click(fillButton);

      const submitButton = document.getElementById("submit-btn");
      await user.click(submitButton);

      // Select email delivery
      await waitFor(() => {
        const emailButton = screen.getByLabelText(/Via email when ready/i);
        expect(emailButton).toBeInTheDocument();
      });

      const emailButton = screen.getByLabelText(/Via email when ready/i);
      await user.click(emailButton);

      // Try to continue without email
      const continueButton = screen.getByLabelText(
        /Continue with email delivery/i
      );
      await user.click(continueButton);

      // Should show required error
      await waitFor(() => {
        expect(
          screen.getByText(/Email address is required/i)
        ).toBeInTheDocument();
      });
    });
  });

  describe("Email delivery submission", () => {
    it("should submit with email delivery method and not poll", async () => {
      const user = userEvent.setup();
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ job_id: "test-job-id" }),
      });

      render(<Search />);

      // Fill and submit form
      const fillButton = screen.getByText("Fill Form");
      await user.click(fillButton);

      const submitButton = document.getElementById("submit-btn");
      await user.click(submitButton);

      // Select email delivery
      await waitFor(() => {
        const emailButton = screen.getByLabelText(/Via email when ready/i);
        expect(emailButton).toBeInTheDocument();
      });

      const emailButton = screen.getByLabelText(/Via email when ready/i);
      await user.click(emailButton);

      // Enter valid email
      const emailInput = screen.getByLabelText(/Email address/i);
      await user.type(emailInput, "test@example.com");

      const continueButton = screen.getByLabelText(
        /Continue with email delivery/i
      );
      await user.click(continueButton);

      // Should call START endpoint with email delivery method
      await waitFor(() => {
        expect(fetchMock).toHaveBeenCalledWith(
          API_ENDPOINTS.START,
          expect.objectContaining({
            method: "POST",
            body: expect.stringContaining('"delivery_method":"email"'),
          })
        );
      });

      // Should show thank you message
      await waitFor(() => {
        expect(
          screen.getByText(/Thank you very much for using JobsAI/i)
        ).toBeInTheDocument();
      });

      // Should NOT poll for progress (email is fire-and-forget)
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

    it("should persist UI message after email submission", async () => {
      const user = userEvent.setup();
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ job_id: "test-job-id" }),
      });

      render(<Search />);

      // Fill and submit form
      const fillButton = screen.getByText("Fill Form");
      await user.click(fillButton);

      const submitButton = document.getElementById("submit-btn");
      await user.click(submitButton);

      // Select email delivery and submit
      await waitFor(() => {
        const emailButton = screen.getByLabelText(/Via email when ready/i);
        expect(emailButton).toBeInTheDocument();
      });

      const emailButton = screen.getByLabelText(/Via email when ready/i);
      await user.click(emailButton);

      const emailInput = screen.getByLabelText(/Email address/i);
      await user.type(emailInput, "test@example.com");

      const continueButton = screen.getByLabelText(
        /Continue with email delivery/i
      );
      await user.click(continueButton);

      // Wait for thank you message
      await waitFor(() => {
        expect(
          screen.getByText(/Thank you very much for using JobsAI/i)
        ).toBeInTheDocument();
      });

      // Message should persist (not disappear)
      await waitFor(
        () => {
          expect(
            screen.getByText(/Thank you very much for using JobsAI/i)
          ).toBeInTheDocument();
        },
        { timeout: 5000 }
      );

      // Find Again button should be visible
      expect(screen.getByText("Find Again")).toBeInTheDocument();
    });

    it("should handle rate limit errors for email delivery", async () => {
      const user = userEvent.setup();
      fetchMock.mockResolvedValueOnce({
        ok: false,
        status: 429,
      });

      render(<Search />);

      // Fill and submit form
      const fillButton = screen.getByText("Fill Form");
      await user.click(fillButton);

      const submitButton = document.getElementById("submit-btn");
      await user.click(submitButton);

      // Select email delivery and submit
      await waitFor(() => {
        const emailButton = screen.getByLabelText(/Via email when ready/i);
        expect(emailButton).toBeInTheDocument();
      });

      const emailButton = screen.getByLabelText(/Via email when ready/i);
      await user.click(emailButton);

      const emailInput = screen.getByLabelText(/Email address/i);
      await user.type(emailInput, "test@example.com");

      const continueButton = screen.getByLabelText(
        /Continue with email delivery/i
      );
      await user.click(continueButton);

      // Should show rate limit message (not thank you message)
      await waitFor(() => {
        expect(
          screen.getByText(/You've made too many searches lately/i)
        ).toBeInTheDocument();
      });
    });

    it("should silently handle other errors for email delivery", async () => {
      const user = userEvent.setup();
      fetchMock.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ detail: "Server error" }),
      });

      render(<Search />);

      // Fill and submit form
      const fillButton = screen.getByText("Fill Form");
      await user.click(fillButton);

      const submitButton = document.getElementById("submit-btn");
      await user.click(submitButton);

      // Select email delivery and submit
      await waitFor(() => {
        const emailButton = screen.getByLabelText(/Via email when ready/i);
        expect(emailButton).toBeInTheDocument();
      });

      const emailButton = screen.getByLabelText(/Via email when ready/i);
      await user.click(emailButton);

      const emailInput = screen.getByLabelText(/Email address/i);
      await user.type(emailInput, "test@example.com");

      const continueButton = screen.getByLabelText(
        /Continue with email delivery/i
      );
      await user.click(continueButton);

      // Should still show thank you message (silent failure)
      await waitFor(() => {
        expect(
          screen.getByText(/Thank you very much for using JobsAI/i)
        ).toBeInTheDocument();
      });

      // Should NOT show error message
      expect(screen.queryByTestId("error-message")).not.toBeInTheDocument();
    });
  });
});

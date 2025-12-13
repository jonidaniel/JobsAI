import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ErrorBoundary from "../ErrorBoundary";

// Component that throws an error
const ThrowError = ({ shouldThrow }) => {
  if (shouldThrow) {
    throw new Error("Test error");
  }
  return <div>No error</div>;
};

describe("ErrorBoundary", () => {
  // Suppress console.error for error boundary tests
  const originalError = console.error;
  beforeAll(() => {
    console.error = vi.fn();
  });

  afterAll(() => {
    console.error = originalError;
  });

  it("should render children when there is no error", () => {
    render(
      <ErrorBoundary>
        <div>Test content</div>
      </ErrorBoundary>
    );
    expect(screen.getByText("Test content")).toBeInTheDocument();
  });

  it("should render error UI when child component throws error", () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );
    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
    expect(
      screen.getByText(
        "We encountered an unexpected error. Please try refreshing the page."
      )
    ).toBeInTheDocument();
  });

  it("should show refresh button when error occurs", () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );
    expect(screen.getByText("Refresh Page")).toBeInTheDocument();
  });

  it("should call window.location.reload when refresh button is clicked", async () => {
    const user = userEvent.setup();
    const reloadMock = vi.fn();
    delete window.location;
    window.location = { reload: reloadMock };

    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    const refreshButton = screen.getByText("Refresh Page");
    await user.click(refreshButton);

    expect(reloadMock).toHaveBeenCalled();
  });
});

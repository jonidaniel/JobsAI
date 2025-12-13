import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import ErrorMessage from "../ErrorMessage";

describe("ErrorMessage", () => {
  it("should render error message", () => {
    render(<ErrorMessage message="Test error message" />);
    expect(screen.getByText("Test error message")).toBeInTheDocument();
  });

  it("should have alert role", () => {
    const { container } = render(<ErrorMessage message="Test error" />);
    const alert = container.querySelector('[role="alert"]');
    expect(alert).toBeInTheDocument();
  });

  it("should display Error heading", () => {
    render(<ErrorMessage message="Test error" />);
    expect(screen.getByText("Error")).toBeInTheDocument();
  });

  it("should have error styling classes", () => {
    const { container } = render(<ErrorMessage message="Test error" />);
    const alert = container.querySelector('[role="alert"]');
    expect(alert).toHaveClass("bg-red-900", "border-red-700", "text-red-100");
  });
});

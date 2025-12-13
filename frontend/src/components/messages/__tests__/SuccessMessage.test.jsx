import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import SuccessMessage from "../SuccessMessage";

describe("SuccessMessage", () => {
  it("should render success message", () => {
    render(<SuccessMessage />);
    expect(
      screen.getByText("Your document has been generated and downloaded.")
    ).toBeInTheDocument();
  });

  it("should have alert role", () => {
    const { container } = render(<SuccessMessage />);
    const alert = container.querySelector('[role="alert"]');
    expect(alert).toBeInTheDocument();
  });

  it("should display Success heading", () => {
    render(<SuccessMessage />);
    expect(screen.getByText("Success!")).toBeInTheDocument();
  });

  it("should have success styling classes", () => {
    const { container } = render(<SuccessMessage />);
    const alert = container.querySelector('[role="alert"]');
    expect(alert).toHaveClass(
      "bg-green-900",
      "border-green-700",
      "text-green-100"
    );
  });
});

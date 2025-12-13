import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import SingleChoice from "../SingleChoice";

describe("SingleChoice", () => {
  const defaultProps = {
    keyName: "test-question",
    label: "Test Question",
    options: ["Option 1", "Option 2", "Option 3"],
    value: "",
    onChange: vi.fn(),
  };

  it("should render label and all options", () => {
    render(<SingleChoice {...defaultProps} />);
    expect(screen.getByText("Test Question")).toBeInTheDocument();
    expect(screen.getByLabelText("Option 1")).toBeInTheDocument();
    expect(screen.getByLabelText("Option 2")).toBeInTheDocument();
    expect(screen.getByLabelText("Option 3")).toBeInTheDocument();
  });

  it("should call onChange when option is selected", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<SingleChoice {...defaultProps} onChange={onChange} />);

    const option1 = screen.getByLabelText("Option 1");
    await user.click(option1);

    expect(onChange).toHaveBeenCalledWith("test-question", "Option 1");
  });

  it("should show selected option as checked", () => {
    render(<SingleChoice {...defaultProps} value="Option 2" />);
    const option1 = screen.getByLabelText("Option 1");
    const option2 = screen.getByLabelText("Option 2");

    expect(option1).not.toBeChecked();
    expect(option2).toBeChecked();
  });

  it("should display error message when provided", () => {
    render(<SingleChoice {...defaultProps} error="This field is required" />);
    expect(screen.getByText("This field is required")).toBeInTheDocument();
    expect(screen.getByText("This field is required")).toHaveAttribute(
      "role",
      "alert"
    );
  });

  it("should render options in two columns when splitAt is provided", () => {
    const { container } = render(
      <SingleChoice {...defaultProps} splitAt={2} />
    );
    const flexContainer = container.querySelector(".flex.gap-8");
    expect(flexContainer).toBeInTheDocument();
  });

  it("should have correct data attributes", () => {
    const { container } = render(<SingleChoice {...defaultProps} />);
    const questionDiv = container.querySelector(
      '[data-question-key="test-question"]'
    );
    expect(questionDiv).toBeInTheDocument();

    const option1 = screen.getByLabelText("Option 1");
    expect(option1).toHaveAttribute("data-key", "test-question");
    expect(option1).toHaveAttribute("data-value", "Option 1");
  });

  it("should generate correct IDs for options", () => {
    render(<SingleChoice {...defaultProps} />);
    const option1 = screen.getByLabelText("Option 1");
    expect(option1).toHaveAttribute("id", "test-question-option-1");
  });
});

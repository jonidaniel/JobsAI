import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import MultipleChoice from "../MultipleChoice";

describe("MultipleChoice", () => {
  const defaultProps = {
    keyName: "test-question",
    label: "Test Question",
    options: ["Option 1", "Option 2", "Option 3", "Option 4"],
    value: [],
    onChange: vi.fn(),
  };

  it("should render label and all options", () => {
    render(<MultipleChoice {...defaultProps} />);
    expect(screen.getByText("Test Question")).toBeInTheDocument();
    expect(screen.getByLabelText("Option 1")).toBeInTheDocument();
    expect(screen.getByLabelText("Option 2")).toBeInTheDocument();
    expect(screen.getByLabelText("Option 3")).toBeInTheDocument();
    expect(screen.getByLabelText("Option 4")).toBeInTheDocument();
  });

  it("should call onChange when option is checked", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<MultipleChoice {...defaultProps} onChange={onChange} />);

    const option1 = screen.getByLabelText("Option 1");
    await user.click(option1);

    expect(onChange).toHaveBeenCalledWith("test-question", ["Option 1"]);
  });

  it("should call onChange when option is unchecked", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(
      <MultipleChoice
        {...defaultProps}
        value={["Option 1", "Option 2"]}
        onChange={onChange}
      />
    );

    const option1 = screen.getByLabelText("Option 1");
    await user.click(option1);

    expect(onChange).toHaveBeenCalledWith("test-question", ["Option 2"]);
  });

  it("should show selected options as checked", () => {
    render(
      <MultipleChoice {...defaultProps} value={["Option 2", "Option 3"]} />
    );
    const option1 = screen.getByLabelText("Option 1");
    const option2 = screen.getByLabelText("Option 2");
    const option3 = screen.getByLabelText("Option 3");

    expect(option1).not.toBeChecked();
    expect(option2).toBeChecked();
    expect(option3).toBeChecked();
  });

  it("should display error message when provided", () => {
    render(<MultipleChoice {...defaultProps} error="This field is required" />);
    expect(screen.getByText("This field is required")).toBeInTheDocument();
    expect(screen.getByText("This field is required")).toHaveAttribute(
      "role",
      "alert"
    );
  });

  it("should disable options when maxSelections is reached", () => {
    render(
      <MultipleChoice
        {...defaultProps}
        value={["Option 1", "Option 2"]}
        maxSelections={2}
      />
    );

    const option1 = screen.getByLabelText("Option 1");
    const option2 = screen.getByLabelText("Option 2");
    const option3 = screen.getByLabelText("Option 3");
    const option4 = screen.getByLabelText("Option 4");

    expect(option1).not.toBeDisabled();
    expect(option2).not.toBeDisabled();
    expect(option3).toBeDisabled();
    expect(option4).toBeDisabled();
  });

  it("should enforce adjacency requirement when requireAdjacent is true and maxSelections is 2", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(
      <MultipleChoice
        {...defaultProps}
        value={["Option 1"]}
        maxSelections={2}
        requireAdjacent={true}
        onChange={onChange}
      />
    );

    // Option 2 is adjacent to Option 1, should work
    const option2 = screen.getByLabelText("Option 2");
    await user.click(option2);
    expect(onChange).toHaveBeenCalledWith("test-question", [
      "Option 1",
      "Option 2",
    ]);

    // Reset and try non-adjacent
    onChange.mockClear();
    render(
      <MultipleChoice
        {...defaultProps}
        value={["Option 1"]}
        maxSelections={2}
        requireAdjacent={true}
        onChange={onChange}
      />
    );

    // Option 3 is not adjacent to Option 1, should not work
    const option3 = screen.getByLabelText("Option 3");
    await user.click(option3);
    expect(onChange).not.toHaveBeenCalled();
  });

  it("should disable non-adjacent options when requireAdjacent is true", () => {
    render(
      <MultipleChoice
        {...defaultProps}
        value={["Option 1"]}
        maxSelections={2}
        requireAdjacent={true}
      />
    );

    const option2 = screen.getByLabelText("Option 2");
    const option3 = screen.getByLabelText("Option 3");
    const option4 = screen.getByLabelText("Option 4");

    expect(option2).not.toBeDisabled(); // Adjacent
    expect(option3).toBeDisabled(); // Not adjacent
    expect(option4).toBeDisabled(); // Not adjacent
  });

  it("should have correct data attributes", () => {
    const { container } = render(<MultipleChoice {...defaultProps} />);
    const questionDiv = container.querySelector(
      '[data-question-key="test-question"]'
    );
    expect(questionDiv).toBeInTheDocument();

    const option1 = screen.getByLabelText("Option 1");
    expect(option1).toHaveAttribute("data-key", "test-question");
    expect(option1).toHaveAttribute("data-value", "Option 1");
  });
});

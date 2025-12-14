import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import TextField from "../TextField";
import { DEFAULT_TEXT_FIELD_MAX_LENGTH } from "../../../config/constants";

describe("TextField", () => {
  const defaultProps = {
    keyName: "test-field",
    label: "Test Field",
    value: "",
    onChange: vi.fn(),
  };

  it("should render label and input field", () => {
    render(<TextField {...defaultProps} />);
    expect(screen.getByText("Test Field")).toBeInTheDocument();
    expect(screen.getByLabelText("Test Field")).toBeInTheDocument();
  });

  it("should call onChange when text changes", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<TextField {...defaultProps} onChange={onChange} />);

    const input = screen.getByLabelText("Test Field");
    await user.type(input, "test value");

    expect(onChange).toHaveBeenCalled();
  });

  it("should display current value", () => {
    render(<TextField {...defaultProps} value="test value" />);
    const input = screen.getByLabelText("Test Field");
    expect(input).toHaveValue("test value");
  });

  it("should display error message when provided", () => {
    render(<TextField {...defaultProps} error="This field is required" />);
    expect(screen.getByText("This field is required")).toBeInTheDocument();
    expect(screen.getByText("This field is required")).toHaveAttribute(
      "role",
      "alert"
    );
  });

  it("should show required indicator when required is true", () => {
    render(<TextField {...defaultProps} required={true} />);
    expect(screen.getByText("*")).toBeInTheDocument();
  });

  it("should render textarea when height is provided", () => {
    render(<TextField {...defaultProps} height="75px" />);
    const textarea = screen.getByLabelText("Test Field");
    expect(textarea.tagName).toBe("TEXTAREA");
    expect(textarea).toHaveStyle({ height: "75px" });
  });

  it("should render input when height is not provided", () => {
    render(<TextField {...defaultProps} />);
    const input = screen.getByLabelText("Test Field");
    expect(input.tagName).toBe("INPUT");
  });

  it("should display character limit message", () => {
    render(<TextField {...defaultProps} />);
    expect(
      screen.getByText(`Max. ${DEFAULT_TEXT_FIELD_MAX_LENGTH} characters`)
    ).toBeInTheDocument();
  });

  it("should show validation warning when limit is exceeded and showValidation is true", async () => {
    const user = userEvent.setup();
    const longText = "a".repeat(DEFAULT_TEXT_FIELD_MAX_LENGTH + 10);
    let currentValue = "";
    const onChange = vi.fn((key, value) => {
      currentValue = value;
    });

    const { rerender } = render(
      <TextField
        {...defaultProps}
        showValidation={true}
        onChange={onChange}
        value={currentValue}
      />
    );

    const input = screen.getByLabelText("Test Field");
    await user.type(input, longText);

    // Update component with new value (simulating parent component update)
    rerender(
      <TextField
        {...defaultProps}
        showValidation={true}
        onChange={onChange}
        value={longText}
      />
    );

    await user.tab(); // Trigger blur

    // Wait for validation message to appear
    await waitFor(
      () => {
        expect(
          screen.getByText(
            `Character limit exceeded. Please reduce to ${DEFAULT_TEXT_FIELD_MAX_LENGTH} characters or less.`
          )
        ).toBeInTheDocument();
      },
      { timeout: 3000 }
    );
  });

  it("should not show validation warning when showValidation is false", async () => {
    const user = userEvent.setup();
    const longText = "a".repeat(DEFAULT_TEXT_FIELD_MAX_LENGTH + 10);
    render(<TextField {...defaultProps} showValidation={false} />);

    const input = screen.getByLabelText("Test Field");
    await user.type(input, longText);
    await user.tab(); // Trigger blur

    expect(
      screen.queryByText(/Character limit exceeded/)
    ).not.toBeInTheDocument();
  });

  it("should enforce maxLength when showValidation is false", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(
      <TextField
        {...defaultProps}
        showValidation={false}
        maxLength={10}
        onChange={onChange}
      />
    );

    const input = screen.getByLabelText("Test Field");
    await user.type(input, "this is a very long text");

    // Should only allow 10 characters
    const calls = onChange.mock.calls;
    const lastCall = calls[calls.length - 1];
    expect(lastCall[1].length).toBeLessThanOrEqual(10);
  });

  it("should display label2 when provided", () => {
    render(<TextField {...defaultProps} label2="Additional info" />);
    // label2 is rendered inside the label element, so use a flexible matcher
    expect(screen.getByText(/Additional info/)).toBeInTheDocument();
  });

  it("should have correct data attributes", () => {
    const { container } = render(<TextField {...defaultProps} />);
    const questionDiv = container.querySelector(
      '[data-question-key="test-field"]'
    );
    expect(questionDiv).toBeInTheDocument();

    const input = screen.getByLabelText("Test Field");
    expect(input).toHaveAttribute("data-key", "test-field");
  });
});

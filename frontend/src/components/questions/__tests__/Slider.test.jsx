import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Slider from "../Slider";
import { SLIDER_MIN, SLIDER_MAX } from "../../../config/sliders";

describe("Slider", () => {
  const defaultProps = {
    keyName: "test-slider",
    label: "Test Slider",
    value: 3,
    onChange: vi.fn(),
  };

  it("should render label and slider", () => {
    render(<Slider {...defaultProps} />);
    expect(screen.getByText("Test Slider")).toBeInTheDocument();
    expect(screen.getByLabelText("Test Slider")).toBeInTheDocument();
  });

  it("should call onChange when slider value changes", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<Slider {...defaultProps} onChange={onChange} />);

    const slider = screen.getByLabelText("Test Slider");
    await user.clear(slider);
    await user.type(slider, "5");

    expect(onChange).toHaveBeenCalled();
  });

  it("should have correct min and max values", () => {
    render(<Slider {...defaultProps} />);
    const slider = screen.getByLabelText("Test Slider");
    expect(slider).toHaveAttribute("min", String(SLIDER_MIN));
    expect(slider).toHaveAttribute("max", String(SLIDER_MAX));
  });

  it("should display current value", () => {
    render(<Slider {...defaultProps} value={5} />);
    const slider = screen.getByLabelText("Test Slider");
    expect(slider).toHaveValue("5");
  });

  it("should be disabled when disabled prop is true", () => {
    render(<Slider {...defaultProps} disabled={true} />);
    const slider = screen.getByLabelText("Test Slider");
    expect(slider).toBeDisabled();
  });

  it("should have correct aria attributes", () => {
    render(<Slider {...defaultProps} />);
    const slider = screen.getByLabelText("Test Slider");
    expect(slider).toHaveAttribute("aria-label", "Test Slider");
    expect(slider).toHaveAttribute("aria-valuemin", String(SLIDER_MIN));
    expect(slider).toHaveAttribute("aria-valuemax", String(SLIDER_MAX));
    expect(slider).toHaveAttribute("aria-valuenow", "3");
  });

  it("should render year indicators", () => {
    render(<Slider {...defaultProps} />);
    expect(screen.getByText("0 yrs")).toBeInTheDocument();
    expect(screen.getByText("< 0.5")).toBeInTheDocument();
    expect(screen.getByText("> 3.0")).toBeInTheDocument();
  });

  it("should not render label when label is not provided", () => {
    const { container } = render(
      <Slider keyName="test-slider" value={3} onChange={vi.fn()} />
    );
    const labels = container.querySelectorAll("label");
    expect(labels.length).toBe(0);
  });

  it("should have correct data-key attribute", () => {
    render(<Slider {...defaultProps} />);
    const slider = screen.getByLabelText("Test Slider");
    expect(slider).toHaveAttribute("data-key", "test-slider");
  });
});

import { SLIDER_MIN, SLIDER_MAX } from "../../config/sliders";

interface SliderProps {
  keyName: string;
  label: string;
  value: number;
  onChange: (keyName: string, value: number) => void;
  disabled?: boolean;
}

/**
 * Slider Component
 *
 * Renders a range input slider for experience level selection (0-7 years).
 * The slider includes visual notch labels showing years of experience ranges.
 */
export default function Slider({
  keyName,
  label,
  value,
  onChange,
  disabled = false,
}: SliderProps) {
  return (
    <div className="flex flex-col w-full">
      {label && (
        <label htmlFor={keyName} className="mb-1">
          {label}
        </label>
      )}
      <input
        id={keyName}
        className={`slider accent-blue-500 w-full ${
          disabled ? "opacity-60 cursor-not-allowed" : ""
        }`}
        type="range"
        min={SLIDER_MIN}
        max={SLIDER_MAX}
        value={value}
        onChange={(e) => onChange(keyName, Number(e.target.value))}
        disabled={disabled}
        data-key={keyName}
        aria-label={label}
        aria-valuemin={SLIDER_MIN}
        aria-valuemax={SLIDER_MAX}
        aria-valuenow={value}
      />
      {/* Year amount indicators - always visible, scale proportionally */}
      <div
        className="flex justify-between mt-1 text-gray-600 overflow-x-auto"
        style={{
          fontSize: "clamp(0.625rem, 1.5vw, 0.75rem)",
          gap: "clamp(0.125rem, 0.5vw, 0.5rem)",
        }}
      >
        <span className="truncate whitespace-nowrap">0 yrs</span>
        <span className="truncate whitespace-nowrap">&lt; 0.5</span>
        <span className="truncate whitespace-nowrap">&lt; 1.0</span>
        <span className="truncate whitespace-nowrap">&lt; 1.5</span>
        <span className="truncate whitespace-nowrap">&lt; 2.0</span>
        <span className="truncate whitespace-nowrap">&lt; 2.5</span>
        <span className="truncate whitespace-nowrap">&lt; 3.0</span>
        <span className="truncate whitespace-nowrap">&gt; 3.0</span>
      </div>
    </div>
  );
}

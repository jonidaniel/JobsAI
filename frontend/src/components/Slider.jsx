import { SLIDER_MIN, SLIDER_MAX } from "../config/constants";

/**
 * Slider Component
 *
 * Renders a range input slider for experience level selection (0-7 years).
 * The slider includes visual notch labels showing years of experience ranges.
 *
 * @param {string} keyName - Unique identifier for the slider (used as data-key)
 * @param {string} label - Display label for the slider
 * @param {number} value - Current slider value (0-7)
 * @param {function} onChange - Callback function called when slider value changes
 *                              Receives (keyName, newValue) as parameters
 */
export default function Slider({ keyName, label, value, onChange }) {
  return (
    <div className="flex flex-col w-full">
      <label htmlFor={keyName} className="mb-1">
        {label}
      </label>
      <input
        id={keyName}
        className="slider accent-blue-500 w-full"
        type="range"
        min={SLIDER_MIN}
        max={SLIDER_MAX}
        value={value}
        onChange={(e) => onChange(keyName, Number(e.target.value))}
        data-key={keyName}
        aria-label={label}
        aria-valuemin={SLIDER_MIN}
        aria-valuemax={SLIDER_MAX}
        aria-valuenow={value}
      />
      {/* Notch labels */}
      <div className="flex justify-between mt-1 text-gray-600 text-xs">
        <span>0 yrs</span>
        <span>&lt; 0.5 yrs</span>
        <span>&lt; 1.0 yrs</span>
        <span>&lt; 1.5 yrs</span>
        <span>&lt; 2.0 yrs</span>
        <span>&lt; 2.5 yrs</span>
        <span>&lt; 3.0 yrs</span>
        <span>&gt; 3.0 yrs</span>
      </div>
    </div>
  );
}

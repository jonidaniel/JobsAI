import { useState } from "react";
import { DEFAULT_TEXT_FIELD_MAX_LENGTH } from "../../config/constants";

/**
 * TextField Component
 *
 * Renders a controlled text input field for user text responses.
 *
 * @param {string} keyName - Unique identifier for the text field (used as data-key and id)
 * @param {string} label - Display label for the text field
 * @param {string} label2 - Second line of the label
 * @param {string} value - Current text field value (controlled component)
 * @param {function} onChange - Callback function called when text changes
 *                              Receives (keyName, newValue) as parameters
 * @param {string} error - Optional error message to display
 * @param {boolean} required - Whether this field is required (default: false)
 * @param {string|number} height - Optional height for the input field (e.g., "75px")
 * @param {number} maxLength - Maximum character length (default: 50 for text fields, 3000 for additional-info)
 * @param {boolean} showValidation - Whether to show validation warnings (default: true, false for tech experience fields)
 */
export default function TextField({
  keyName,
  label,
  label2,
  value,
  onChange,
  error,
  required = false,
  height,
  maxLength = DEFAULT_TEXT_FIELD_MAX_LENGTH,
  showValidation = true,
}) {
  const [hasInteracted, setHasInteracted] = useState(false);

  // Only calculate limit check if validation is enabled
  const exceedsLimit = showValidation
    ? (value || "").length > maxLength
    : false;

  const handleChange = (e) => {
    if (!hasInteracted && showValidation) {
      setHasInteracted(true);
    }
    // Enforce maxLength for tech fields (when showValidation is false)
    const newValue = showValidation
      ? e.target.value
      : e.target.value.slice(0, maxLength);
    onChange(keyName, newValue);
  };

  const handleBlur = () => {
    if (showValidation) {
      setHasInteracted(true);
    }
  };

  return (
    <div className="flex flex-col w-full" data-question-key={keyName}>
      {(label || required) && (
        <label htmlFor={keyName} className="mb-1">
          {label}
          {required && <span className="text-red-400 ml-1">*</span>}
          {label2}
        </label>
      )}
      {error && (
        <p className="text-red-500 text-sm mb-2" role="alert">
          {error}
        </p>
      )}
      <p className="text-gray-500 text-xs mb-1">Max. {maxLength} characters</p>
      {showValidation && hasInteracted && exceedsLimit && (
        <p className="text-red-500 text-sm mb-1" role="alert">
          Character limit exceeded. Please reduce to {maxLength} characters or
          less.
        </p>
      )}
      {height && (
        <p className="text-gray-500 text-xs mb-1">
          Grab the lower right corner to resize the text box
        </p>
      )}
      {height ? (
        <textarea
          id={keyName}
          className="text-field border border-gray-300 px-2 py-1 rounded w-full resize-y"
          value={value}
          onChange={handleChange}
          onBlur={handleBlur}
          data-key={keyName}
          aria-label={label}
          style={{ height }}
          rows={3}
          maxLength={showValidation ? undefined : maxLength}
        />
      ) : (
        <input
          id={keyName}
          className="text-field border border-gray-300 px-2 py-1 rounded w-full"
          type="text"
          value={value}
          onChange={handleChange}
          onBlur={handleBlur}
          data-key={keyName}
          aria-label={label}
          maxLength={showValidation ? undefined : maxLength}
        />
      )}
    </div>
  );
}

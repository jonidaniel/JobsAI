import { useState } from "react";
import { DEFAULT_TEXT_FIELD_MAX_LENGTH } from "../../config/constants";

interface TextFieldProps {
  keyName: string;
  label?: string;
  label2?: string;
  value: string;
  onChange: (keyName: string, value: string) => void;
  error?: string;
  required?: boolean;
  height?: string;
  maxLength?: number;
  showValidation?: boolean;
}

/**
 * TextField Component
 *
 * Renders a controlled text input field for user text responses.
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
}: TextFieldProps) {
  // Track if user has interacted with the field (for validation display)
  const [hasInteracted, setHasInteracted] = useState(false);

  // Only calculate limit check if validation is enabled
  // When showValidation is false, input is hard-limited via maxLength attribute
  const exceedsLimit = showValidation
    ? (value || "").length > maxLength
    : false;

  /**
   * Handles input change events
   * For tech fields (showValidation=false), enforces maxLength by slicing input
   */
  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ): void => {
    if (!hasInteracted && showValidation) {
      setHasInteracted(true);
    }
    // Enforce maxLength for tech fields (when showValidation is false)
    const newValue = showValidation
      ? e.target.value
      : e.target.value.slice(0, maxLength);
    onChange(keyName, newValue);
  };

  /**
   * Handles input blur events
   * Marks field as interacted for validation display
   */
  const handleBlur = (): void => {
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

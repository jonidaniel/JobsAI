import { renderLabel } from "../../utils/labelRenderer";

interface SingleChoiceProps {
  keyName: string;
  label: string;
  options: readonly string[];
  value: string;
  onChange: (keyName: string, value: string) => void;
  error?: string;
  required?: boolean;
  splitAt?: number;
}

/**
 * SingleChoice Component
 *
 * Renders a group of radio buttons allowing only one selection.
 * Used for questions that require a single answer.
 *
 * Features:
 * - Single selection enforced (radio button behavior)
 * - Supports option splitting (display options in multiple columns)
 * - Displays validation errors
 * - Supports rich label formatting (line breaks, italic, small text)
 *
 * Usage:
 * - Deep mode selection (Yes/No)
 * - Cover letter count selection (1-10)
 * - Cover letter style selection (Professional, Friendly, Confident)
 *
 * @param keyName - Form data key for this field
 * @param label - Question label (supports formatting via renderLabel)
 * @param options - Array of option strings to display
 * @param value - Current selected value (single string)
 * @param onChange - Callback when selection changes
 * @param error - Validation error message (optional)
 * @param required - Whether field is required
 * @param splitAt - Number of options before splitting into new row (optional)
 */
export default function SingleChoice({
  keyName,
  label,
  options,
  value,
  onChange,
  error,
  splitAt,
}: SingleChoiceProps) {
  /**
   * Renders a single radio button option
   */
  const renderRadioOption = (option: string) => {
    const optionKey = option.toLowerCase().replace(/\s+/g, "-");
    const isChecked = value === option;
    return (
      <div key={option} className="flex items-center mb-2">
        <input
          className="radio-field accent-blue-500"
          type="radio"
          name={keyName}
          checked={isChecked}
          onChange={() => onChange(keyName, option)}
          data-key={keyName}
          data-value={option}
          id={`${keyName}-${optionKey}`}
        />
        <label htmlFor={`${keyName}-${optionKey}`} className="ml-2">
          {option}
        </label>
      </div>
    );
  };

  return (
    <div className="flex flex-col w-full" data-question-key={keyName}>
      <label className="mb-1">{renderLabel(label)}</label>
      {error && (
        <p className="text-red-300 text-sm mb-2" role="alert">
          {error}
        </p>
      )}
      {splitAt !== undefined ? (
        // Two-column layout: split options at the specified index
        <div className="flex gap-8">
          <div className="flex-1">
            {options.slice(0, splitAt).map(renderRadioOption)}
          </div>
          <div className="flex-1">
            {options.slice(splitAt).map(renderRadioOption)}
          </div>
        </div>
      ) : (
        // Single-column layout (default)
        options.map(renderRadioOption)
      )}
    </div>
  );
}

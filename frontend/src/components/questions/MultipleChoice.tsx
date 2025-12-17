import { renderLabel } from "../../utils/labelRenderer";

interface MultipleChoiceProps {
  keyName: string;
  label: string;
  options: readonly string[];
  value: string[];
  onChange: (keyName: string, value: string[]) => void;
  error?: string;
  required?: boolean;
  maxSelections?: number;
  requireAdjacent?: boolean;
}

/**
 * MultipleChoice Component
 *
 * Renders a group of checkboxes allowing multiple selections.
 * Used for questions that allow selecting multiple options.
 *
 * Features:
 * - Supports max selections limit (e.g., max 2 for job level)
 * - Supports adjacent selection requirement (e.g., job level must be adjacent)
 * - Displays validation errors
 * - Supports rich label formatting (line breaks, italic, small text)
 *
 * Usage:
 * - Job level selection (max 2, must be adjacent)
 * - Job boards selection (multiple allowed)
 *
 * @param keyName - Form data key for this field
 * @param label - Question label (supports formatting via renderLabel)
 * @param options - Array of option strings to display
 * @param value - Current selected values (array of strings)
 * @param onChange - Callback when selection changes
 * @param error - Validation error message (optional)
 * @param required - Whether field is required
 * @param maxSelections - Maximum number of selections allowed
 * @param requireAdjacent - Whether selected options must be adjacent in options array
 */
export default function MultipleChoice({
  keyName,
  label,
  options,
  value,
  onChange,
  error,
  maxSelections,
  requireAdjacent = false,
}: MultipleChoiceProps) {
  /**
   * Checks if two selected options are adjacent in the options array
   */
  const areAdjacent = (option1: string, option2: string): boolean => {
    const index1 = options.indexOf(option1);
    const index2 = options.indexOf(option2);
    if (index1 === -1 || index2 === -1) return false;
    return Math.abs(index1 - index2) === 1;
  };

  /**
   * Handles checkbox change events
   * Adds option to array if checked, removes if unchecked
   * Respects maxSelections limit and adjacency requirement if provided
   */
  const handleCheckboxChange = (option: string, checked: boolean): void => {
    const currentValues = value || [];
    if (checked) {
      // Check if we've reached the maximum selections
      if (
        maxSelections !== undefined &&
        currentValues.length >= maxSelections
      ) {
        return; // Don't allow more selections
      }

      // If we have one selection and requireAdjacent, check if new option is adjacent
      if (
        requireAdjacent &&
        maxSelections === 2 &&
        currentValues.length === 1
      ) {
        if (!areAdjacent(currentValues[0]!, option)) {
          return; // Don't allow non-adjacent selection
        }
      }

      // Add option to selected values
      onChange(keyName, [...currentValues, option]);
    } else {
      // Remove option from selected values
      onChange(
        keyName,
        currentValues.filter((v) => v !== option)
      );
    }
  };

  return (
    <div className="flex flex-col w-full" data-question-key={keyName}>
      <label className="mb-1">{renderLabel(label)}</label>
      {error && (
        <p className="text-red-300 text-sm mb-2" role="alert">
          {error}
        </p>
      )}
      {options.map((option) => {
        const optionKey = option.toLowerCase().replace(/\s+/g, "-");
        const isChecked = value && value.includes(option);
        const currentValues = value || [];
        const isDisabled =
          maxSelections !== undefined &&
          !isChecked &&
          currentValues.length >= maxSelections;

        // If requireAdjacent and we have one selection, disable non-adjacent options
        const isNonAdjacentDisabled =
          requireAdjacent &&
          maxSelections === 2 &&
          currentValues.length === 1 &&
          !isChecked &&
          !areAdjacent(currentValues[0]!, option);

        const shouldDisable = isDisabled || isNonAdjacentDisabled;

        return (
          <div key={option} className="flex items-center mb-2">
            <input
              className="checkbox-field accent-blue-500"
              type="checkbox"
              checked={isChecked}
              disabled={shouldDisable}
              onChange={(e) => handleCheckboxChange(option, e.target.checked)}
              data-key={keyName}
              data-value={option}
              id={`${keyName}-${optionKey}`}
            />
            <label
              htmlFor={`${keyName}-${optionKey}`}
              className={`ml-2 ${
                shouldDisable ? "opacity-50 cursor-not-allowed" : ""
              }`}
            >
              {option}
            </label>
          </div>
        );
      })}
    </div>
  );
}

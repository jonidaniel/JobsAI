// import { useEffect } from "react";

/**
 * MultipleChoice Component
 *
 * Renders a group of checkboxes allowing multiple selections.
 * Used for questions that allow selecting multiple options, such as:
 * - Job level (Expert, Intermediate, Entry, Intern)
 * - Job boards (Duunitori, Jobly)
 *
 * @param {string} keyName - Unique identifier for the checkbox group
 * @param {string} label - Display label for the question
 * @param {string[]} options - Array of option strings to display as checkboxes
 * @param {string[]} value - Array of currently selected options
 * @param {function} onChange - Callback function called when checkbox state changes
 *                              Receives (keyName, newArray) as parameters
 * @param {string} error - Optional error message to display
 * @param {boolean} required - Whether this field is required (default: false)
 * @param {number} maxSelections - Maximum number of options that can be selected (default: unlimited)
 * @param {boolean} requireAdjacent - If true and maxSelections is 2, selected options must be adjacent (default: false)
 */
export default function MultipleChoice({
  keyName,
  label,
  options,
  value,
  onChange,
  error,
  required = false,
  maxSelections,
  requireAdjacent = false,
}) {
  /**
   * Checks if two selected options are adjacent in the options array
   */
  const areAdjacent = (option1, option2) => {
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
  const handleCheckboxChange = (option, checked) => {
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
        if (!areAdjacent(currentValues[0], option)) {
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

  /**
   * Renders label text with support for line breaks (\n) and italic text (*text*)
   */
  const renderLabel = (text) => {
    return text.split("\n").map((line, lineIndex, lineArray) => {
      // Split line by italic markers (*text*)
      const parts = line.split(/(\*[^*]+\*)/g);
      return (
        <span key={lineIndex}>
          {parts.map((part, partIndex) => {
            // Check if part is italic (starts and ends with *)
            if (part.startsWith("*") && part.endsWith("*") && part.length > 2) {
              return (
                <em key={partIndex} className="italic">
                  {part.slice(1, -1)}
                </em>
              );
            }
            return <span key={partIndex}>{part}</span>;
          })}
          {lineIndex < lineArray.length - 1 && <br />}
        </span>
      );
    });
  };

  return (
    <div className="flex flex-col w-full">
      <label className="mb-1">
        {renderLabel(label)}
        {required && <span className="text-red-400 ml-1">*</span>}
        {/* {renderLabel(label2)} */}
      </label>
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
          !areAdjacent(currentValues[0], option);

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

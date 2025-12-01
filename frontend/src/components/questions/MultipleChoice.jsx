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
 */
export default function MultipleChoice({
  keyName,
  label,
  options,
  value,
  onChange,
  error,
  required = false,
}) {
  /**
   * Handles checkbox change events
   * Adds option to array if checked, removes if unchecked
   */
  const handleCheckboxChange = (option, checked) => {
    const currentValues = value || [];
    if (checked) {
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
    <div className="flex flex-col w-full">
      <label className="mb-1">
        {label}
        {required && <span className="text-red-500 ml-1">*</span>}
      </label>
      {error && (
        <p className="text-red-500 text-sm mb-2" role="alert">
          {error}
        </p>
      )}
      {options.map((option) => {
        const optionKey = option.toLowerCase().replace(/\s+/g, "-");
        const isChecked = value && value.includes(option);
        return (
          <div key={option} className="flex items-center mb-2">
            <input
              className="checkbox-field accent-blue-500"
              type="checkbox"
              checked={isChecked}
              onChange={(e) => handleCheckboxChange(option, e.target.checked)}
              data-key={keyName}
              data-value={option}
              id={`${keyName}-${optionKey}`}
            />
            <label htmlFor={`${keyName}-${optionKey}`} className="ml-2">
              {option}
            </label>
          </div>
        );
      })}
    </div>
  );
}

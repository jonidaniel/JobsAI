/**
 * SingleChoice Component
 *
 * Renders a group of radio buttons allowing only one selection.
 * Used for questions that require a single answer.
 *
 * @param {string} keyName - Unique identifier for the radio button group
 * @param {string} label - Display label for the question
 * @param {string[]} options - Array of option strings to display as radio buttons
 * @param {string} value - Currently selected option (single value, not array)
 * @param {function} onChange - Callback function called when radio button state changes
 *                              Receives (keyName, selectedValue) as parameters
 */
export default function SingleChoice({
  keyName,
  label,
  options,
  value,
  onChange,
}) {
  return (
    <div className="flex flex-col w-full">
      <label className="mb-1">{label}</label>
      {options.map((option) => {
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
      })}
    </div>
  );
}

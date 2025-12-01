/**
 * TextField Component
 *
 * Renders a controlled text input field for user text responses.
 *
 * @param {string} keyName - Unique identifier for the text field (used as data-key and id)
 * @param {string} label - Display label for the text field
 * @param {string} value - Current text field value (controlled component)
 * @param {function} onChange - Callback function called when text changes
 *                              Receives (keyName, newValue) as parameters
 * @param {string} error - Optional error message to display
 * @param {boolean} required - Whether this field is required (default: false)
 */
export default function TextField({
  keyName,
  label,
  value,
  onChange,
  error,
  required = false,
}) {
  return (
    <div className="flex flex-col w-full">
      <label htmlFor={keyName} className="mb-1">
        {label}
        {required && <span className="text-red-500 ml-1">*</span>}
      </label>
      {error && (
        <p className="text-red-500 text-sm mb-2" role="alert">
          {error}
        </p>
      )}
      <input
        id={keyName}
        className="text-field border border-gray-300 px-2 py-1 rounded w-full"
        type="text"
        value={value}
        onChange={(e) => onChange(keyName, e.target.value)}
        data-key={keyName}
        aria-label={label}
      />
    </div>
  );
}

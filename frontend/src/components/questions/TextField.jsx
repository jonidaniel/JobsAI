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
}) {
  return (
    <div className="flex flex-col w-full">
      {(label || required) && (
        <label htmlFor={keyName} className="mb-1">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
          {label2}
        </label>
      )}
      {error && (
        <p className="text-red-500 text-sm mb-2" role="alert">
          {error}
        </p>
      )}
      {height ? (
        <textarea
          id={keyName}
          className="text-field border border-gray-300 px-2 py-1 rounded w-full resize-y"
          value={value}
          onChange={(e) => onChange(keyName, e.target.value)}
          data-key={keyName}
          aria-label={label}
          style={{ height }}
          rows={3}
        />
      ) : (
        <input
          id={keyName}
          className="text-field border border-gray-300 px-2 py-1 rounded w-full"
          type="text"
          value={value}
          onChange={(e) => onChange(keyName, e.target.value)}
          data-key={keyName}
          aria-label={label}
        />
      )}
    </div>
  );
}

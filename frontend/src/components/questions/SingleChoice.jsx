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
 * @param {string} error - Optional error message to display
 * @param {boolean} required - Whether this field is required (default: false)
 * @param {number} splitAt - Optional index to split options into two columns (left and right)
 */
export default function SingleChoice({
  keyName,
  label,
  options,
  value,
  onChange,
  error,
  splitAt,
}) {
  /**
   * Renders label text with support for line breaks (\n), italic text (*text*), red asterisk (* at end of line), and small text ({small}text{/small})
   */
  const renderLabel = (text) => {
    return text.split("\n").map((line, lineIndex, lineArray) => {
      // Check if line ends with " *" (standalone asterisk for required field)
      const hasRedAsterisk = line.endsWith(" *");
      const lineWithoutAsterisk = hasRedAsterisk ? line.slice(0, -2) : line;

      // Process small text markers first
      const processSmallText = (str) => {
        const parts = [];
        let remaining = str;
        let partIndex = 0;

        while (remaining.length > 0) {
          const smallStart = remaining.indexOf("{small}");
          const smallEnd = remaining.indexOf("{/small}");

          if (smallStart !== -1 && smallEnd !== -1 && smallEnd > smallStart) {
            // Add text before {small}
            if (smallStart > 0) {
              parts.push({
                type: "normal",
                text: remaining.slice(0, smallStart),
                index: partIndex++,
              });
            }
            // Add small text
            parts.push({
              type: "small",
              text: remaining.slice(smallStart + 7, smallEnd),
              index: partIndex++,
            });
            remaining = remaining.slice(smallEnd + 8);
          } else {
            // No more small markers, add remaining text
            parts.push({ type: "normal", text: remaining, index: partIndex++ });
            break;
          }
        }

        return parts;
      };

      const smallParts = processSmallText(lineWithoutAsterisk);

      return (
        <span key={lineIndex}>
          {smallParts.map(({ type, text, index }) => {
            if (type === "small") {
              // Render small text, but still process italics within it
              const italicParts = text.split(/(\*[^*]+\*)/g);
              return (
                <span key={index} className="text-sm">
                  {italicParts.map((part, partIndex) => {
                    if (
                      part.startsWith("*") &&
                      part.endsWith("*") &&
                      part.length > 2
                    ) {
                      return (
                        <em key={partIndex} className="italic">
                          {part.slice(1, -1)}
                        </em>
                      );
                    }
                    return <span key={partIndex}>{part}</span>;
                  })}
                </span>
              );
            } else {
              // Render normal text, process italics
              const italicParts = text.split(/(\*[^*]+\*)/g);
              return (
                <span key={index}>
                  {italicParts.map((part, partIndex) => {
                    if (
                      part.startsWith("*") &&
                      part.endsWith("*") &&
                      part.length > 2
                    ) {
                      return (
                        <em key={partIndex} className="italic">
                          {part.slice(1, -1)}
                        </em>
                      );
                    }
                    return <span key={partIndex}>{part}</span>;
                  })}
                </span>
              );
            }
          })}
          {hasRedAsterisk && <span className="text-red-400 ml-1">*</span>}
          {lineIndex < lineArray.length - 1 && <br />}
        </span>
      );
    });
  };

  return (
    <div className="flex flex-col w-full">
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
            {options.slice(0, splitAt).map((option) => {
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
          <div className="flex-1">
            {options.slice(splitAt).map((option) => {
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
        </div>
      ) : (
        // Single-column layout (default)
        options.map((option) => {
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
        })
      )}
    </div>
  );
}

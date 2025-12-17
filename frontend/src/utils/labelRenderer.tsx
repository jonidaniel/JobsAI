import type { ReactNode } from "react";

/**
 * Label Rendering Utility
 *
 * Shared utility for rendering labels with rich formatting support.
 * Used by MultipleChoice and SingleChoice components to display
 * question labels with various formatting options.
 *
 * Supported Formatting:
 * - **Line breaks**: `\n` creates line breaks
 * - **Italic text**: `*text*` renders as italic
 * - **Red asterisk**: ` *` at end of line renders as red asterisk (required field indicator)
 * - **Small text**: `{small}text{/small}` renders text in smaller font size
 *
 * Formatting can be combined (e.g., `*Italic*{small}small text{/small} *`)
 *
 * @module utils/labelRenderer
 */

interface SmallTextPart {
  type: "normal" | "small";
  text: string;
  index: number;
}

/**
 * Renders italic text parts by parsing *text* markers
 *
 * @param text - Text that may contain italic markers
 * @returns Array of span and em elements
 */
const renderItalicParts = (text: string): ReactNode[] => {
  const italicParts = text.split(/(\*[^*]+\*)/g);
  return italicParts.map((part, partIndex) => {
    if (part.startsWith("*") && part.endsWith("*") && part.length > 2) {
      return (
        <em key={partIndex} className="italic">
          {part.slice(1, -1)}
        </em>
      );
    }
    return <span key={partIndex}>{part}</span>;
  });
};

/**
 * Processes small text markers ({small}...{/small}) and returns parts array
 *
 * @param str - Text that may contain small text markers
 * @returns Array of objects with type ("normal" or "small"), text, and index
 */
const processSmallText = (str: string): SmallTextPart[] => {
  const parts: SmallTextPart[] = [];
  let remaining = str;
  let partIndex = 0;

  while (remaining.length > 0) {
    const smallStart = remaining.indexOf("{small}");
    const smallEnd = remaining.indexOf("{/small}");

    if (smallStart !== -1 && smallEnd !== -1 && smallEnd > smallStart) {
      if (smallStart > 0) {
        parts.push({
          type: "normal",
          text: remaining.slice(0, smallStart),
          index: partIndex++,
        });
      }
      parts.push({
        type: "small",
        text: remaining.slice(smallStart + 7, smallEnd),
        index: partIndex++,
      });
      remaining = remaining.slice(smallEnd + 8);
    } else {
      parts.push({ type: "normal", text: remaining, index: partIndex++ });
      break;
    }
  }

  return parts;
};

/**
 * Renders label text with support for line breaks, italic text, red asterisk, and small text
 *
 * @param text - The label text to render
 * @returns Array of span elements with formatted content
 */
export const renderLabel = (text: string): ReactNode[] => {
  return text.split("\n").map((line, lineIndex, lineArray) => {
    const hasRedAsterisk = line.endsWith(" *");
    const lineWithoutAsterisk = hasRedAsterisk ? line.slice(0, -2) : line;
    const smallParts = processSmallText(lineWithoutAsterisk);

    return (
      <span key={lineIndex}>
        {smallParts.map(({ type, text, index }) => {
          if (type === "small") {
            return (
              <span key={index} className="text-sm">
                {renderItalicParts(text)}
              </span>
            );
          } else {
            return <span key={index}>{renderItalicParts(text)}</span>;
          }
        })}
        {hasRedAsterisk && <span className="text-red-400 ml-1">*</span>}
        {lineIndex < lineArray.length - 1 && <br />}
      </span>
    );
  });
};

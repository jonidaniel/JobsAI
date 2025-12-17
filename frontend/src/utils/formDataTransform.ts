import { QUESTION_SET_NAMES } from "../config/questionSet";
import {
  GENERAL_QUESTION_KEYS,
  GENERAL_QUESTIONS_INDEX,
} from "../config/generalQuestions";
import { SLIDER_DATA } from "../config/sliders";
import type { FormData, GroupedFormData } from "../types";

/**
 * Transforms flat form data into grouped structure for backend API.
 *
 * Converts the flat key-value form data structure from the QuestionSets component
 * into the nested structure expected by the backend API. Filters out empty values
 * for optional fields while ensuring required fields are always included.
 *
 * Process:
 * 1. Filters out empty values (empty strings, 0 numbers, empty arrays) for optional fields
 * 2. Groups data by question set name (general, languages, databases, etc.)
 * 3. Converts each field to single-key object format: [{key: value}, ...]
 * 4. Handles special cases (cover-letter-num conversion, required fields)
 *
 * @param formData - Flat form data object from QuestionSets component.
 *   Keys are question field names (e.g., "job-level", "javascript", "text-field1").
 *   Values can be strings, numbers, or arrays depending on question type.
 *
 * @returns Grouped data structure by question set:
 *   {
 *     "general": [{key: value}, ...],  // Always 5 items (required)
 *     "languages": [{key: value}, ...],  // Only if has data
 *     "databases": [{key: value}, ...], // Only if has data
 *     ...
 *     "additional-info": [{key: value}] // Always 1 item (required)
 *   }
 *
 * @example
 * // Input
 * { "job-level": ["Expert"], "javascript": 5, "text-field1": "TypeScript" }
 *
 * // Output
 * {
 *   "general": [{"job-level": ["Expert"]}, ...],
 *   "languages": [{"javascript": 5}, {"text-field1": "TypeScript"}]
 * }
 */
export function transformFormData(formData: FormData): GroupedFormData {
  /**
   * Filters form data to only include non-empty values for optional fields
   * - Strings: Include if trimmed value is not empty
   * - Numbers: Include if value is not 0 (sliders default to 0)
   * - Arrays: Include if array has at least one element (checkboxes)
   *
   * Note: Required fields (general questions and additional-info) are always included
   * even if empty, as they are validated separately
   */
  const filtered = Object.fromEntries(
    Object.entries(formData)
      .filter(([, value]) => {
        if (typeof value === "string") return value.trim() !== "";
        if (typeof value === "number") return value !== 0;
        if (Array.isArray(value)) return value.length > 0;
        return false;
      })
      .map(([key, value]) => [
        key,
        typeof value === "string" ? value.trim() : value,
      ])
  ) as FormData;

  /**
   * Group filtered data by question set
   * Structure: { "general": [{key: value}, ...], "languages": [...], ... }
   */
  const result: GroupedFormData = {};

  // Group general questions (index 0)
  // Always include all 5 general questions (required by backend)
  // Use formData directly to ensure we have the values (validation ensures they're present)
  // Convert cover-letter-num to integer for backend
  const generalQuestions = GENERAL_QUESTION_KEYS.map((key) => {
    let value: FormDataValue = formData[key];

    // Convert cover-letter-num from string to integer
    // Radio buttons return strings, but backend expects integer
    if (key === "cover-letter-num") {
      const stringValue = typeof value === "string" ? value : String(value);
      const intValue = parseInt(stringValue, 10);
      // Validate conversion was successful
      if (isNaN(intValue) || intValue < 1 || intValue > 10) {
        console.warn(
          `Invalid cover-letter-num value: ${formData[key]}, defaulting to 5`
        );
        value = 5;
      } else {
        value = intValue;
      }
    }

    return { [key]: value };
  });
  // Backend requires exactly 5 items, so always include the array even if some values are empty
  result[QUESTION_SET_NAMES[GENERAL_QUESTIONS_INDEX]] = generalQuestions;

  // Group slider question sets (indices 1-8)
  // Each set includes default sliders and optional "Other" custom fields
  for (let i = 1; i < QUESTION_SET_NAMES.length - 1; i++) {
    const questionSetData = [
      // Include default sliders that have non-zero values
      ...Object.keys(SLIDER_DATA[i - 1] ?? {})
        .filter((key) => filtered[key] !== undefined)
        .map((key) => ({ [key]: filtered[key] })),
      // Include custom "Other" fields if they have values
      ...(filtered[`text-field${i}`] !== undefined
        ? [{ [`text-field${i}`]: filtered[`text-field${i}`] }]
        : []),
    ];

    // Only include question set if it has at least one field with data
    if (questionSetData.length > 0) {
      result[QUESTION_SET_NAMES[i]] = questionSetData;
    }
  }

  // Group text-only question set (index 9)
  // Always include additional-info (required by backend)
  // Use formData directly to ensure we have the value (validation ensures it's present)
  result[QUESTION_SET_NAMES[9]] = [
    { "additional-info": formData["additional-info"] || "" },
  ];

  return result;
}

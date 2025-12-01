import {
  QUESTION_SET_NAMES,
  GENERAL_QUESTIONS_INDEX,
} from "../config/constants";
import { GENERAL_QUESTION_KEYS } from "../config/generalQuestions";
import { SLIDER_DATA } from "../config/sliderData";

/**
 * Transforms flat form data into grouped structure for backend API
 *
 * Process:
 * 1. Filters out empty values (empty strings, 0 numbers, empty arrays)
 * 2. Groups data by question set
 * 3. Returns structured object matching backend expectations
 *
 * @param {Object} formData - Flat form data object from QuestionSets component
 * @returns {Object} Grouped data structure by question set
 *                   Format: { "general": [{key: value}, ...], "languages": [...], ... }
 */
export function transformFormData(formData) {
  /**
   * Filter form data to only include non-empty values
   * - Strings: Include if trimmed value is not empty
   * - Numbers: Include if value is not 0 (sliders default to 0)
   * - Arrays: Include if array has at least one element (checkboxes)
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
  );

  /**
   * Group filtered data by question set
   * Structure: { "general": [{key: value}, ...], "languages": [...], ... }
   */
  const result = {};

  // Group general questions (index 0)
  const generalQuestions = GENERAL_QUESTION_KEYS.filter(
    (key) => filtered[key] !== undefined
  ).map((key) => ({ [key]: filtered[key] }));
  if (generalQuestions.length > 0) {
    result[QUESTION_SET_NAMES[GENERAL_QUESTIONS_INDEX]] = generalQuestions;
  }

  // Group slider question sets (indices 1-8)
  for (let i = 1; i < QUESTION_SET_NAMES.length - 1; i++) {
    const questionSetData = [
      ...Object.keys(SLIDER_DATA[i - 1])
        .filter((key) => filtered[key] !== undefined)
        .map((key) => ({ [key]: filtered[key] })),
      ...(filtered[`text-field${i}`] !== undefined
        ? [{ [`text-field${i}`]: filtered[`text-field${i}`] }]
        : []),
    ];

    if (questionSetData.length > 0) {
      result[QUESTION_SET_NAMES[i]] = questionSetData;
    }
  }

  // Group text-only question set (index 9)
  if (filtered["additional-info"] !== undefined) {
    result[QUESTION_SET_NAMES[9]] = [
      { "additional-info": filtered["additional-info"] },
    ];
  }

  return result;
}

import {
  GENERAL_QUESTION_KEYS,
  NAME_OPTIONS,
} from "../config/generalQuestions";

/**
 * Validates that all mandatory questions are answered.
 *
 * Performs client-side validation of required form fields before submission.
 * Validates all 5 general questions and the personal description field.
 *
 * Validation Rules:
 * - Question 1 (job-level): At least one option, max 2, must be adjacent if 2
 * - Question 2 (job-boards): At least one job board selected
 * - Question 3 (deep-mode): Must select Yes or No
 * - Question 4 (cover-letter-num): Must select a number (1-10)
 * - Question 5 (cover-letter-style): At least one style, max 2 styles
 * - Question 10 (additional-info): Personal description cannot be empty
 *
 * @param {Object} formData - The form data object containing all question responses.
 *   Keys match GENERAL_QUESTION_KEYS and "additional-info".
 *
 * @returns {Object} Validation result object:
 *   - isValid {boolean}: True if all mandatory questions are valid
 *   - errors {Object<string, string>}: Map of field keys to error messages.
 *     Empty object if validation passes.
 *
 * @example
 * const result = validateGeneralQuestions(formData);
 * if (!result.isValid) {
 *   // Display errors: result.errors
 * }
 */
export function validateGeneralQuestions(formData) {
  const errors = {};

  // Question 1 (job-level): At least one option must be picked (array, max 2, must be adjacent if 2)
  const jobLevel = formData[GENERAL_QUESTION_KEYS[0]];
  if (!jobLevel || !Array.isArray(jobLevel) || jobLevel.length === 0) {
    errors[GENERAL_QUESTION_KEYS[0]] =
      "Please select at least one job level option.";
  } else if (jobLevel.length > 2) {
    errors[GENERAL_QUESTION_KEYS[0]] =
      "Please select at most two job level options.";
  } else if (jobLevel.length === 2) {
    // Check if the two selected options are adjacent in the options array
    const index1 = NAME_OPTIONS.indexOf(jobLevel[0]);
    const index2 = NAME_OPTIONS.indexOf(jobLevel[1]);
    if (index1 === -1 || index2 === -1 || Math.abs(index1 - index2) !== 1) {
      errors[GENERAL_QUESTION_KEYS[0]] =
        "If selecting two job levels, they must be adjacent (e.g., Expert-level + Intermediate, Intermediate + Entry, Entry + Intern).";
    }
  }

  // Question 2 (job-boards): At least one option must be picked (array)
  const jobBoards = formData[GENERAL_QUESTION_KEYS[1]];
  if (!jobBoards || !Array.isArray(jobBoards) || jobBoards.length === 0) {
    errors[GENERAL_QUESTION_KEYS[1]] = "Please select at least one job board.";
  }

  // Question 3 (deep-mode): A selection must be made (string)
  const deepMode = formData[GENERAL_QUESTION_KEYS[2]];
  if (!deepMode || deepMode.trim() === "") {
    errors[GENERAL_QUESTION_KEYS[2]] = "Please select an option.";
  }

  // Question 4 (cover-letter-num): A selection must be made (string)
  const coverLetterNum = formData[GENERAL_QUESTION_KEYS[3]];
  if (!coverLetterNum || coverLetterNum.trim() === "") {
    errors[GENERAL_QUESTION_KEYS[3]] = "Please select an option.";
  }

  // Question 5 (cover-letter-style): At least one option must be selected (array, max 2)
  const coverLetterStyle = formData[GENERAL_QUESTION_KEYS[4]];
  if (
    !coverLetterStyle ||
    !Array.isArray(coverLetterStyle) ||
    coverLetterStyle.length === 0
  ) {
    errors[GENERAL_QUESTION_KEYS[4]] = "Please select at least one option.";
  } else if (coverLetterStyle.length > 2) {
    errors[GENERAL_QUESTION_KEYS[4]] = "Please select at most two options.";
  }

  // Question 10 (additional-info): Personal description is mandatory (string)
  const additionalInfo = formData["additional-info"];
  if (!additionalInfo || additionalInfo.trim() === "") {
    errors["additional-info"] =
      "Please provide a personal description to help us find the most relevant jobs for you.";
  }

  return {
    isValid: Object.keys(errors).length === 0,
    errors,
  };
}

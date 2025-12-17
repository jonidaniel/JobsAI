/**
 * Application Constants
 *
 * Centralized constants used throughout the application.
 * These values define the structure and configuration of the questionnaire.
 *
 * Question Set Structure:
 * - 1 General Questions set (index 0): 5 multiple choice questions
 * - 8 Slider Question sets (indices 1-8): Multiple sliders + 1 "Other" text field each
 * - 1 Text-only Question set (index 9): Single text input field
 *
 * Total: 10 question sets
 */

/** Total number of question sets (0-9, inclusive) */
export const TOTAL_QUESTION_SETS = 10;

/**
 * Question Set Names
 *
 * Kebab-case names for each question set, used when grouping form data.
 * Index mapping:
 * 0: "general"
 * 1: "languages"
 * 2: "databases"
 * 3: "cloud-development"
 * 4: "web-frameworks"
 * 5: "dev-ides"
 * 6: "llms"
 * 7: "doc-and-collab"
 * 8: "operating-systems"
 * 9: "additional-info"
 */
export const QUESTION_SET_NAMES: readonly string[] = [
  "general",
  "languages",
  "databases",
  "cloud-development",
  "web-frameworks",
  "dev-ides",
  "llms",
  "doc-and-collab",
  "operating-systems",
  "additional-info",
] as const;

/**
 * Question Set Titles
 *
 * Display titles for each of the 10 question sets.
 * These titles are shown as headings above each question set.
 *
 * Index mapping:
 * 0: General Questions
 * 1: Programming, Scripting, and Markup Languages Experience
 * 2: Databases Experience
 * 3: Cloud Development Experience
 * 4: Web Frameworks and Technologies Experience
 * 5: Dev IDEs Experience
 * 6: Large Language Models Experience
 * 7: Code Documentation and Collaboration Experience
 * 8: Computer Operating Systems Experience
 * 9: Personal Description
 */
export const QUESTION_SET_TITLES: readonly string[] = [
  "General Questions",
  "Programming, Scripting, and Markup Languages Experience",
  "Databases Experience",
  "Cloud Development Experience",
  "Web Frameworks and Technologies Experience",
  "Dev IDEs Experience",
  "Large Language Models Experience",
  "Code Documentation and Collaboration Experience",
  "Computer Operating Systems Experience",
  "Personal Description",
] as const;

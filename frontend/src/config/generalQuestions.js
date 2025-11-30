/**
 * General Questions Configuration
 *
 * Configuration for the General Questions set (question set index 0).
 * This set contains 10 questions, with the first, second, third, fourth, and fifth questions being multiple choice
 * and the rest being text fields.
 */

/**
 * Labels for each question in the General Questions set
 *
 * Index mapping:
 * 0: Job level (multiple choice - see NAME_OPTIONS)
 * 1: Job boards (multiple choice - see JOB_BOARD_OPTIONS)
 * 2: Deep mode (multiple choice - see DEEP_MODE_OPTIONS)
 * 3: Cover letter style (multiple choice - see COVER_LETTER_STYLE_OPTIONS)
 * 4: Job count (multiple choice - see JOB_COUNT_OPTIONS)
 * 5: Background Summary
 * 6: Key Skills
 * 7: Previous Projects
 * 8: Education
 * 9: Additional Information
 */
export const GENERAL_QUESTION_LABELS = [
  "What level of job are you looking for?",
  "What job boards you want to scrape?",
  "Do you want to use deep mode for job scraping?",
  "What kind of style you want the cover letter to be?",
  "How many jobs you want to include in the job report?",
  "Are you currently employed somewhere related to software development?",
  "What is your education?",
  "How does your education show when you work?",
  "From what areas you would like to find jobs?",
  "Additional Information",
];

/**
 * Default values for specific general questions
 *
 * Key is the question index (0-9)
 * Value is the default text to pre-fill in the input field
 *
 * Only questions with defaults need to be specified here.
 * Questions without entries will default to empty string.
 * Note: Questions 0, 1, 2, 3, and 4 are multiple choice and don't use text defaults.
 */
export const GENERAL_QUESTION_DEFAULTS = {
  // Default values can be added here for text field questions (indices 5-9)
};

/**
 * Multiple choice options for the first question (Job level)
 *
 * Users can select multiple options (checkboxes).
 * These represent experience levels that can be combined.
 */
export const NAME_OPTIONS = ["Intern", "Entry", "Intermediate", "Expert"];

/**
 * Multiple choice options for the second question (Job boards)
 *
 * Users can select multiple options (checkboxes).
 * These represent job boards to scrape.
 */
export const JOB_BOARD_OPTIONS = ["Duunitori", "Jobly"];

/**
 * Multiple choice options for the third question (Deep mode)
 *
 * Users can select multiple options (checkboxes).
 * These represent whether to use deep mode for job scraping.
 */
export const DEEP_MODE_OPTIONS = ["Yes", "No"];

/**
 * Multiple choice options for the fourth question (Cover letter style)
 *
 * Users can select multiple options (checkboxes).
 * These represent the desired style for the cover letter.
 */
export const COVER_LETTER_STYLE_OPTIONS = [
  "Professional",
  "Friendly",
  "Confident",
];

/**
 * Multiple choice options for the fifth question (Job count)
 *
 * Users can select multiple options (checkboxes).
 * These represent the number of jobs to include in the job report.
 */
export const JOB_COUNT_OPTIONS = ["1", "2", "3", "4", "5", "10"];

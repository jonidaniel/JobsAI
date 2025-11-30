/**
 * General Questions Configuration
 *
 * Configuration for the General Questions set (question set index 0).
 * This set contains 10 questions, with the first question being a multiple choice
 * and the rest being text fields.
 */

/**
 * Labels for each question in the General Questions set
 *
 * Index mapping:
 * 0: Name (multiple choice - see NAME_OPTIONS)
 * 1: Years of Experience
 * 2: Background Summary
 * 3: Key Skills
 * 4: Previous Projects
 * 5: Education
 * 6: Certifications
 * 7: Languages
 * 8: Location
 * 9: Additional Information
 */
export const GENERAL_QUESTION_LABELS = [
  "What level of job are you looking for?",
  "Are you currently employed somewhere related to software development?",
  "Have you worked on any projects that are related to software development?",
  "What is your background summary?",
  "",
  "What is your education?",
  "How does your education show when you work?",
  "Languages",
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
 */
export const GENERAL_QUESTION_DEFAULTS = {
  2: "My name is Joni Potala. I have developed software since 2020. I have built and published multiple full-stack apps (frontend, backend, database, desktop, mobile). I have built multi-agent orchestrations with OpenAI Agents SDK for half a year. I have very good soft skills.",
};

/**
 * Multiple choice options for the first question (Name)
 *
 * Users can select multiple options (checkboxes).
 * These represent experience levels that can be combined.
 */
export const NAME_OPTIONS = ["Intern", "Entry", "Intermediate", "Expert"];

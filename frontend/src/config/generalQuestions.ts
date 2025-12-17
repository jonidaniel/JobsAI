/**
 * General Questions Configuration
 *
 * Configuration for the General Questions set (question set index 0).
 * This set contains 5 questions:
 * - Questions 0-1: Multiple choice (checkboxes)
 * - Questions 2-4: Single choice (radio buttons)
 */

/** Index of the General Questions set in the questionnaire */
export const GENERAL_QUESTIONS_INDEX = 0;

/** Number of questions in the General Questions set */
export const GENERAL_QUESTIONS_COUNT = 5;

/**
 * Labels for each question in the General Questions set
 *
 * Index mapping:
 * 0: Job level (multiple choice - see NAME_OPTIONS)
 * 1: Job boards (multiple choice - see JOB_BOARD_OPTIONS)
 * 2: Deep mode (single choice - see DEEP_MODE_OPTIONS)
 * 3: Job count (single choice - see JOB_COUNT_OPTIONS)
 * 4: Cover letter style (single choice - see COVER_LETTER_STYLE_OPTIONS)
 */
export const GENERAL_QUESTION_LABELS: readonly string[] = [
  "First things first.\nWhat's the *level of job* you're looking for? *\n{small}(you might select two adjacent levels){/small}",
  "{small}We'll scrape popular job boards with many keywords.{/small}\n*What boards* do you want us to include? *",
  "Do you want to use *deep search*? *\n{small}If yes, we'll open every job post and analyze them in detail. This will take a bit longer, but it'll find jobs with more relevance to you.{/small}",
  "{small}Once we've found jobs, we'll rank them, and then write cover letters for them.{/small}\n*How many top jobs* do you want cover letters for? *",
  "How about the *style* of the letters? *\n{small}Strictly professional or something else? A combination of two?{/small}",
] as const;

/**
 * Question keys for each question in the General Questions set
 * These keys are used to identify questions in form data and validation
 *
 * Index mapping:
 * 0: "job-level"
 * 1: "job-boards"
 * 2: "deep-mode"
 * 3: "cover-letter-num"
 * 4: "cover-letter-style"
 */
export const GENERAL_QUESTION_KEYS: readonly string[] = [
  "job-level",
  "job-boards",
  "deep-mode",
  "cover-letter-num",
  "cover-letter-style",
] as const;

/**
 * Multiple choice options for the first question (Job level)
 *
 * Users can select multiple options (checkboxes).
 * These represent experience levels that can be combined.
 */
export const NAME_OPTIONS: readonly string[] = [
  "Expert-level",
  "Intermediate",
  "Entry",
  "Intern",
] as const;

/**
 * Multiple choice options for the second question (Job boards)
 *
 * Users can select multiple options (checkboxes).
 * These represent job boards to scrape.
 */
export const JOB_BOARD_OPTIONS: readonly string[] = [
  "Duunitori",
  "Jobly",
] as const;

/**
 * Single choice options for the third question (Deep mode)
 *
 * Users can select only one option (radio buttons).
 * These represent whether to use deep mode for job scraping.
 */
export const DEEP_MODE_OPTIONS: readonly string[] = ["Yes", "No"] as const;

/**
 * Single choice options for the fourth question (Job count)
 *
 * Users can select only one option (radio buttons).
 * These represent the number of jobs to include in the job report.
 */
export const JOB_COUNT_OPTIONS: readonly string[] = [
  "1",
  "2",
  "3",
  "4",
  "5",
  "6",
  "7",
  "8",
  "9",
  "10",
] as const;

/**
 * Multiple choice options for the fifth question (Cover letter style)
 *
 * Users can select 1 or 2 options (checkboxes with max 2 selections).
 * These represent the desired style(s) for the cover letter.
 */
export const COVER_LETTER_STYLE_OPTIONS: readonly string[] = [
  "Professional",
  "Friendly",
  "Confident",
  "Funny",
] as const;

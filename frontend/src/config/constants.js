/**
 * Application Constants
 *
 * Centralized constants used throughout the application.
 * These values define the structure and configuration of the questionnaire.
 *
 * Question Set Structure:
 * - 1 General Questions set (index 0): 10 text fields (first is multiple choice)
 * - 8 Slider Question sets (indices 1-8): Multiple sliders + 1 "Other" text field each
 *
 * Total: 9 question sets
 */

/** Total number of question sets (0-8, inclusive) */
export const TOTAL_QUESTION_SETS = 9;

/** Number of questions in the General Questions set (index 0) */
export const GENERAL_QUESTIONS_COUNT = 10;

/** Number of slider-based question sets (indices 1-8) */
export const SLIDER_QUESTION_SETS_COUNT = 8;

/**
 * Slider Configuration
 *
 * Sliders represent years of experience ranges:
 * 0 = 0 yrs
 * 1 = < 0.5 yrs
 * 2 = < 1.0 yrs
 * 3 = < 1.5 yrs
 * 4 = < 2.0 yrs
 * 5 = < 2.5 yrs
 * 6 = < 3.0 yrs
 * 7 = > 3.0 yrs
 */
export const SLIDER_MIN = 0;
export const SLIDER_MAX = 7;
export const SLIDER_DEFAULT = 0;

/**
 * Question Set Indices
 *
 * Constants for identifying question set types by index
 */
export const GENERAL_QUESTIONS_INDEX = 0;
export const FIRST_SLIDER_INDEX = 1;
export const LAST_SLIDER_INDEX = 8;

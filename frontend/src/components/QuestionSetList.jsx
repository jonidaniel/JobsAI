import { useState, useEffect, useRef } from "react";

import QuestionSet from "./QuestionSet";

import { TOTAL_QUESTION_SETS } from "../config/questionSet";
import { GENERAL_QUESTION_KEYS } from "../config/generalQuestions";
import { SLIDER_DATA } from "../config/sliders";
import { SCROLL_OFFSET, SCROLL_DELAY } from "../config/constants";

/**
 * QuestionSets Component
 *
 * Main component for managing and displaying question sets.
 * Handles:
 * - Navigation between 10 question sets (prev/next buttons)
 * - Form state management for all inputs
 * - Synchronizing form data with parent component
 * - Smooth scrolling to active question set
 *
 * @param {function} onFormDataChange - Callback to notify parent when form data changes
 *                                      Receives the complete formData object
 * @param {object} validationErrors - Object mapping question keys to error messages
 * @param {number} activeIndex - Optional external control of active question set index
 * @param {function} onCurrentIndexChange - Optional callback to report current question set index
 * @param {boolean} skipInitialScroll - If true, skip scrolling to top on initial mount (used when remounting after submission)
 */
export default function QuestionSetList({
  onFormDataChange,
  validationErrors = {},
  activeIndex,
  onActiveIndexChange,
  onCurrentIndexChange,
  skipInitialScroll = false,
}) {
  // Current active question set index (0-9)
  // Use activeIndex prop if provided (external control), otherwise use internal state
  const [internalIndex, setInternalIndex] = useState(0);

  // Determine current index: use activeIndex if provided, otherwise use internal state
  // When activeIndex is set externally (e.g., for error navigation), it overrides internal state
  const currentIndex = activeIndex !== undefined ? activeIndex : internalIndex;

  /**
   * Reports current question set index to parent component
   * Allows Search component to track which question set is currently visible
   */
  useEffect(() => {
    if (onCurrentIndexChange) {
      onCurrentIndexChange(currentIndex);
    }
  }, [currentIndex, onCurrentIndexChange]);

  // Refs to DOM elements for each question set section (used for scrolling)
  const sectionRefs = useRef({});
  // Track if this is the initial mount (page refresh vs remount after submission)
  const isInitialMount = useRef(true);
  // Track if navigation was triggered by user action (arrow click vs external control)
  const isUserNavigation = useRef(false);

  /**
   * Initialize form data with default values
   * Runs once on component mount using lazy initialization
   *
   * Sets defaults for:
   * - All 5 mandatory general questions
   * - First 3 sliders in each technology set (sets 1-8)
   * - Additional info text field
   */
  const [formData, setFormData] = useState(() => {
    const initial = {};

    // Set default values for general questions (question set 0)
    // All 5 questions are mandatory and have default values
    initial[GENERAL_QUESTION_KEYS[0]] = ["Expert-level"]; // job-level
    initial[GENERAL_QUESTION_KEYS[1]] = ["Duunitori"]; // job-boards
    initial[GENERAL_QUESTION_KEYS[2]] = "Yes"; // deep-mode
    initial[GENERAL_QUESTION_KEYS[3]] = "1"; // cover-letter-num
    initial[GENERAL_QUESTION_KEYS[4]] = ["Professional"]; // cover-letter-style

    // Set default values for the first 3 sliders in each technology set (question sets 1-8)
    // SLIDER_DATA[0] = languages, SLIDER_DATA[1] = databases, etc.
    // Each set's first 3 sliders default to 0 (0 yrs)
    SLIDER_DATA.forEach((sliderSet) => {
      // Get first 3 technology keys from each set
      const technologyKeys = Object.keys(sliderSet).slice(0, 3);
      technologyKeys.forEach((key) => {
        initial[key] = 0; // Default slider value is 0 (0 yrs)
      });
    });

    // Set default values for "Other" text fields in slider question sets (question sets 1-8)
    for (let i = 1; i < TOTAL_QUESTION_SETS - 1; i++) {
      initial[`text-field${i}`] = "";
    }

    // Set default value for text-only question set (index 9)
    // No default value - user must provide their own description
    initial["additional-info"] = "";

    return initial;
  });

  /**
   * Notify parent component when form data changes
   * This allows Search component to collect form data for submission
   */
  useEffect(() => {
    if (onFormDataChange) {
      onFormDataChange(formData);
    }
  }, [formData, onFormDataChange]);

  /**
   * Handles form input changes
   * Updates formData state and triggers parent notification via useEffect
   *
   * @param {string} key - The form field key (e.g., "javascript", "job-level", "text-field1")
   * @param {string|number|string[]} value - The new value (string, number, or array for checkboxes)
   */
  const handleFormChange = (key, value) => {
    setFormData((prev) => ({ ...prev, [key]: value }));
  };

  /**
   * Scroll to active question set when navigation changes
   * - On page refresh: scroll to top of page
   * - On arrow click: scroll to top of question set
   * - On remount after submission: skip scrolling (preserve position)
   */
  useEffect(() => {
    if (isInitialMount.current) {
      // On initial mount (page refresh), scroll to top of page
      // But skip if this is a remount after submission
      isInitialMount.current = false;
      if (!skipInitialScroll) {
        window.scrollTo({ top: 0, behavior: "smooth" });
      } else {
        // If we're skipping scroll, ensure we don't scroll at all
        // This is a remount after submission, preserve position
        return;
      }
      return;
    }

    // Only scroll to question set if navigation was from user action
    if (isUserNavigation.current) {
      const section = sectionRefs.current[currentIndex];
      if (section) {
        // Small delay to ensure DOM is ready
        setTimeout(() => {
          // Calculate position with offset to show question set number clearly
          const rect = section.getBoundingClientRect();
          const targetPosition = window.scrollY + rect.top - SCROLL_OFFSET;

          window.scrollTo({
            top: targetPosition,
            behavior: "smooth",
          });
        }, SCROLL_DELAY);
      }
      // Reset the flag after scrolling
      isUserNavigation.current = false;
    }
  }, [currentIndex, skipInitialScroll]);

  /**
   * Navigates to previous question set
   * Wraps around to last question set if currently at first (0)
   */
  const handlePrevious = () => {
    const newIndex =
      currentIndex === 0 ? TOTAL_QUESTION_SETS - 1 : currentIndex - 1;
    isUserNavigation.current = true; // Mark as user navigation for scroll behavior
    setInternalIndex(newIndex);
    // Clear external control when user manually navigates
    if (onActiveIndexChange) {
      onActiveIndexChange(undefined);
    }
  };

  /**
   * Navigates to next question set
   * Wraps around to first question set (0) if currently at last
   */
  const handleNext = () => {
    const newIndex = (currentIndex + 1) % TOTAL_QUESTION_SETS;
    isUserNavigation.current = true; // Mark as user navigation for scroll behavior
    setInternalIndex(newIndex);
    // Clear external control when user manually navigates
    if (onActiveIndexChange) {
      onActiveIndexChange(undefined);
    }
  };

  // Shared arrow button container styles
  const arrowContainerStyle = {
    top: "clamp(450px, 20vh, 250px)",
    maxHeight: "calc(100vh - 100px)",
  };
  const arrowButtonStyle = {
    fontSize: "clamp(1rem, 3vw, 1.5rem)",
    padding: "clamp(0.5rem, 1.5vw, 0.75rem) clamp(0.75rem, 2vw, 1rem)",
  };

  return (
    <div
      id="question-set-wrapper"
      className="relative flex w-full"
      role="tablist"
      aria-label="Question sets navigation"
    >
      {/* Left arrow */}
      <div
        className="prev-btn-container sticky self-start h-0 flex items-center z-10"
        style={arrowContainerStyle}
      >
        <button
          className="prev-btn text-white rounded-lg transition-all hover:bg-gray-700"
          style={arrowButtonStyle}
          onClick={handlePrevious}
          aria-label="Previous question set"
          aria-controls="question-set-wrapper"
          tabIndex={0}
        >
          &larr;
        </button>
      </div>

      {/* TailwindCSS form */}
      <div className="bg-gray-800 p-4 sm:p-6 md:p-10 rounded-2xl shadow-lg flex-1">
        {/* Render all question sets, but only show the active one */}
        {Array.from({ length: TOTAL_QUESTION_SETS }).map((_, i) => (
          <QuestionSet
            key={i}
            index={i}
            isActive={i === currentIndex}
            sectionRef={(el) => {
              if (el) sectionRefs.current[i] = el;
            }}
            formData={formData}
            onFormChange={handleFormChange}
            validationErrors={validationErrors}
          />
        ))}
      </div>

      {/* Right arrow */}
      <div
        className="next-btn-container sticky self-start h-0 flex items-center z-10 ml-auto"
        style={arrowContainerStyle}
      >
        <button
          className="next-btn text-white rounded-lg transition-all hover:bg-gray-700"
          style={arrowButtonStyle}
          onClick={handleNext}
          aria-label="Next question set"
          aria-controls="question-set-wrapper"
          tabIndex={0}
        >
          &rarr;
        </button>
      </div>
    </div>
  );
}

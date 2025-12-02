import { useState, useEffect, useRef } from "react";

import QuestionSet from "./QuestionSet";

import { TOTAL_QUESTION_SETS } from "../config/questionSet";
import { GENERAL_QUESTION_KEYS } from "../config/generalQuestions";

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
 */
export default function QuestionSetList({
  onFormDataChange,
  validationErrors = {},
  activeIndex,
  onActiveIndexChange,
}) {
  // Current active question set index (0-9)
  // Use activeIndex prop if provided, otherwise use internal state
  const [internalIndex, setInternalIndex] = useState(0);

  // Determine current index: use activeIndex if provided, otherwise use internal state
  // When activeIndex is set externally, sync internal state for when it's cleared
  const currentIndex = activeIndex !== undefined ? activeIndex : internalIndex;

  // Refs to DOM elements for each question set section (for scrolling)
  const sectionRefs = useRef({});
  // Track if this is the initial mount (page refresh)
  const isInitialMount = useRef(true);
  // Track if navigation was triggered by user action (arrow click)
  const isUserNavigation = useRef(false);

  /**
   * Initialize form data with default values
   * Runs once on component mount using lazy initialization
   */
  const [formData, setFormData] = useState(() => {
    const initial = {};

    // Set default values for general questions (question set 0)
    GENERAL_QUESTION_KEYS.forEach((keyName, j) => {
      initial[keyName] = j < 2 ? [] : ""; // First 2 are arrays, rest are strings
    });

    // Set default values for slider question sets (question sets 1-8)
    // Sliders default to 0 (handled in Slider component)
    // Only need to initialize the "Other" text fields
    for (let i = 1; i < TOTAL_QUESTION_SETS - 1; i++) {
      initial[`text-field${i}`] = "";
    }

    // Set default value for text-only question set (index 9)
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
   */
  useEffect(() => {
    if (isInitialMount.current) {
      // On initial mount (page refresh), scroll to top of page
      isInitialMount.current = false;
      window.scrollTo({ top: 0, behavior: "smooth" });
      return;
    }

    // Only scroll to question set if navigation was from user action
    if (isUserNavigation.current) {
      const section = sectionRefs.current[currentIndex];
      if (section) {
        // Small delay to ensure DOM is ready
        setTimeout(() => {
          section.scrollIntoView({
            behavior: "smooth",
            block: "start",
          });
        }, 100);
      }
      // Reset the flag after scrolling
      isUserNavigation.current = false;
    }
  }, [currentIndex]);

  /**
   * Navigate to previous question set
   * Wraps around to last question set if currently at first (0)
   */
  const handlePrevious = () => {
    const newIndex =
      currentIndex === 0 ? TOTAL_QUESTION_SETS - 1 : currentIndex - 1;
    isUserNavigation.current = true; // Mark as user navigation
    setInternalIndex(newIndex);
    // Clear external control when user manually navigates
    if (onActiveIndexChange) {
      onActiveIndexChange(undefined);
    }
  };

  /**
   * Navigate to next question set
   * Wraps around to first question set (0) if currently at last
   */
  const handleNext = () => {
    const newIndex = (currentIndex + 1) % TOTAL_QUESTION_SETS;
    isUserNavigation.current = true; // Mark as user navigation
    setInternalIndex(newIndex);
    // Clear external control when user manually navigates
    if (onActiveIndexChange) {
      onActiveIndexChange(undefined);
    }
  };

  return (
    /*
     * Question set wrapper
     *
     * Only one question set is shown on the page at a time
     */
    <div
      id="question-set-wrapper"
      className="relative flex w-full"
      role="tablist"
      aria-label="Question sets navigation"
    >
      {/* Left arrow */}
      <div
        className="prev-btn-container sticky self-start h-0 flex items-center z-10"
        style={{
          top: "clamp(450px, 20vh, 250px)",
          maxHeight: "calc(100vh - 100px)",
        }}
      >
        <button
          className="prev-btn text-white rounded-lg transition-colors hover:bg-gray-700"
          style={{
            fontSize: "clamp(1rem, 3vw, 1.5rem)",
            padding: "clamp(0.5rem, 1.5vw, 0.75rem) clamp(0.75rem, 2vw, 1rem)",
          }}
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
        style={{
          top: "clamp(450px, 20vh, 250px)",
          maxHeight: "calc(100vh - 100px)",
        }}
      >
        <button
          className="next-btn text-white rounded-lg transition-colors hover:bg-gray-700"
          style={{
            fontSize: "clamp(1rem, 3vw, 1.5rem)",
            padding: "clamp(0.5rem, 1.5vw, 0.75rem) clamp(0.75rem, 2vw, 1rem)",
          }}
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

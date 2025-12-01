import { useState, useEffect, useRef } from "react";
import QuestionSet from "./QuestionSet";
import {
  TOTAL_QUESTION_SETS,
  GENERAL_QUESTIONS_COUNT,
} from "../config/constants";
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
 */
export default function QuestionSets({ onFormDataChange }) {
  // Current active question set index (0-9)
  const [currentIndex, setCurrentIndex] = useState(0);

  // Refs to DOM elements for each question set section (for scrolling)
  const sectionRefs = useRef({});

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
   * @param {string} key - The form field key (e.g., "javascript", "text-field-general-0")
   * @param {string|number|string[]} value - The new value (string, number, or array for checkboxes)
   */
  const handleFormChange = (key, value) => {
    setFormData((prev) => ({ ...prev, [key]: value }));
  };

  /**
   * Scroll to active question set when navigation changes
   * Uses smooth scrolling for better UX
   */
  useEffect(() => {
    const section = sectionRefs.current[currentIndex];
    if (section) {
      section.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }
  }, [currentIndex]);

  /**
   * Navigate to previous question set
   * Wraps around to last question set if currently at first (0)
   */
  const handlePrevious = () => {
    setCurrentIndex((prev) =>
      prev === 0 ? TOTAL_QUESTION_SETS - 1 : prev - 1
    );
  };

  /**
   * Navigate to next question set
   * Wraps around to first question set (0) if currently at last
   */
  const handleNext = () => {
    setCurrentIndex((prev) => (prev + 1) % TOTAL_QUESTION_SETS);
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
      <div className="prev-btn-container sticky top-1/2 -translate-y-1/2 self-start h-0 flex items-center z-10">
        <button
          className="prev-btn text-white text-2xl px-3 py-1 rounded-lg transition-colors"
          onClick={handlePrevious}
          aria-label="Previous question set"
          aria-controls="question-set-wrapper"
          tabIndex={0}
        >
          &larr;
        </button>
      </div>

      {/* TailwindCSS form */}
      <div className="bg-gray-800 p-10 rounded-2xl shadow-lg flex-1">
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
          />
        ))}
      </div>

      {/* Right arrow */}
      <div className="next-btn-container sticky top-1/2 -translate-y-1/2 self-start h-0 flex items-center z-10 ml-auto">
        <button
          className="next-btn text-white text-2xl px-3 py-1 rounded-lg transition-colors"
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

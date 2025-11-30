import { useState, useEffect, useRef } from "react";
import { SLIDER_DATA } from "../config/sliderData";
import {
  GENERAL_QUESTION_LABELS,
  GENERAL_QUESTION_DEFAULTS,
  NAME_OPTIONS,
  JOB_BOARD_OPTIONS,
  DEEP_MODE_OPTIONS,
  COVER_LETTER_STYLE_OPTIONS,
  JOB_COUNT_OPTIONS,
} from "../config/generalQuestions";
import { QUESTION_SET_TITLES } from "../config/questionSetTitles";
import {
  TOTAL_QUESTION_SETS,
  GENERAL_QUESTIONS_COUNT,
  SLIDER_MIN,
  SLIDER_MAX,
  SLIDER_DEFAULT,
  GENERAL_QUESTIONS_INDEX,
} from "../config/constants";

/**
 * Slider Component
 *
 * Renders a range input slider for experience level selection (0-7 years).
 * The slider includes visual notch labels showing years of experience ranges.
 *
 * @param {string} keyName - Unique identifier for the slider (used as data-key)
 * @param {string} label - Display label for the slider
 * @param {number} value - Current slider value (0-7)
 * @param {function} onChange - Callback function called when slider value changes
 *                              Receives (keyName, newValue) as parameters
 */
function Slider({ keyName, label, value, onChange }) {
  return (
    <div className="flex flex-col w-full">
      <label htmlFor={keyName} className="mb-1">
        {label}
      </label>
      <input
        id={keyName}
        className="slider accent-blue-500 w-full"
        type="range"
        min={SLIDER_MIN}
        max={SLIDER_MAX}
        value={value}
        onChange={(e) => onChange(keyName, Number(e.target.value))}
        data-key={keyName}
        aria-label={label}
        aria-valuemin={SLIDER_MIN}
        aria-valuemax={SLIDER_MAX}
        aria-valuenow={value}
      />
      {/* Notch labels */}
      <div className="flex justify-between mt-1 text-gray-600 text-xs">
        <span>0 yrs</span>
        <span>&lt; 0.5 yrs</span>
        <span>&lt; 1.0 yrs</span>
        <span>&lt; 1.5 yrs</span>
        <span>&lt; 2.0 yrs</span>
        <span>&lt; 2.5 yrs</span>
        <span>&lt; 3.0 yrs</span>
        <span>&gt; 3.0 yrs</span>
      </div>
    </div>
  );
}

/**
 * TextField Component
 *
 * Renders a controlled text input field for user text responses.
 *
 * @param {string} keyName - Unique identifier for the text field (used as data-key and id)
 * @param {string} label - Display label for the text field
 * @param {string} value - Current text field value (controlled component)
 * @param {function} onChange - Callback function called when text changes
 *                              Receives (keyName, newValue) as parameters
 */
function TextField({ keyName, label, value, onChange }) {
  return (
    <div className="flex flex-col w-full">
      <label htmlFor={keyName} className="mb-1">
        {label}
      </label>
      <input
        id={keyName}
        className="text-field border border-gray-300 px-2 py-1 rounded w-full"
        type="text"
        value={value}
        onChange={(e) => onChange(keyName, e.target.value)}
        data-key={keyName}
        aria-label={label}
      />
    </div>
  );
}

/**
 * MultipleChoice Component
 *
 * Renders a group of checkboxes allowing multiple selections.
 * Used for the "Name" question which allows selecting multiple experience levels
 * (Intern, Entry, Intermediate, Expert).
 *
 * @param {string} keyName - Unique identifier for the checkbox group
 * @param {string} label - Display label for the question
 * @param {string[]} options - Array of option strings to display as checkboxes
 * @param {string[]} value - Array of currently selected options
 * @param {function} onChange - Callback function called when checkbox state changes
 *                              Receives (keyName, newArray) as parameters
 */
function MultipleChoice({ keyName, label, options, value, onChange }) {
  /**
   * Handles checkbox change events
   * Adds option to array if checked, removes if unchecked
   */
  const handleCheckboxChange = (option, checked) => {
    const currentValues = value || [];
    if (checked) {
      // Add option to selected values
      onChange(keyName, [...currentValues, option]);
    } else {
      // Remove option from selected values
      onChange(
        keyName,
        currentValues.filter((v) => v !== option)
      );
    }
  };

  return (
    <div className="flex flex-col w-full">
      <label className="mb-1">{label}</label>
      {options.map((option) => {
        const optionKey = option.toLowerCase().replace(/\s+/g, "-");
        const isChecked = value && value.includes(option);
        return (
          <div key={option} className="flex items-center mb-2">
            <input
              className="checkbox-field accent-blue-500"
              type="checkbox"
              checked={isChecked}
              onChange={(e) => handleCheckboxChange(option, e.target.checked)}
              data-key={keyName}
              data-value={option}
              id={`${keyName}-${optionKey}`}
            />
            <label htmlFor={`${keyName}-${optionKey}`} className="ml-2">
              {option}
            </label>
          </div>
        );
      })}
    </div>
  );
}

/**
 * QuestionSet Component
 *
 * Renders a single question set (one of 9 total sets).
 * Only the active question set is visible; others are hidden via CSS.
 *
 * @param {number} index - Index of the question set (0-8)
 * @param {boolean} isActive - Whether this question set is currently visible
 * @param {object} sectionRef - React ref callback to store DOM reference for scrolling
 * @param {object} formData - Current form data state (all question values)
 * @param {function} onFormChange - Callback to update form data when inputs change
 */
function QuestionSet({ index, isActive, sectionRef, formData, onFormChange }) {
  return (
    <section
      ref={sectionRef}
      className={isActive ? "active" : ""}
      aria-hidden={!isActive}
      role="tabpanel"
      aria-labelledby={`question-set-${index}-title`}
    >
      <h3 className="text-3xl" id={`question-set-${index}-title`}>
        {index + 1}/{TOTAL_QUESTION_SETS}
      </h3>
      <h3 className="text-3xl">{QUESTION_SET_TITLES[index]}</h3>

      {/* Questions */}
      <div className="space-y-4">
        {index === GENERAL_QUESTIONS_INDEX ? (
          // General Questions (index 0): 10 questions, first, second, third, fourth, and fifth are multiple choice
          Array.from({ length: GENERAL_QUESTIONS_COUNT }).map((_, j) => {
            const keyName = `text-field-general-${j}`;
            if (j === 0) {
              // First question (Job level) is a multiple choice with checkboxes
              // Options: Intern, Entry, Intermediate, Expert
              return (
                <MultipleChoice
                  key={j}
                  keyName={keyName}
                  label={GENERAL_QUESTION_LABELS[j]}
                  options={NAME_OPTIONS}
                  value={formData[keyName] || []}
                  onChange={onFormChange}
                />
              );
            } else if (j === 1) {
              // Second question (Job boards) is a multiple choice with checkboxes
              // Options: Duunitori, Jobly
              return (
                <MultipleChoice
                  key={j}
                  keyName={keyName}
                  label={GENERAL_QUESTION_LABELS[j]}
                  options={JOB_BOARD_OPTIONS}
                  value={formData[keyName] || []}
                  onChange={onFormChange}
                />
              );
            } else if (j === 2) {
              // Third question (Deep mode) is a multiple choice with checkboxes
              // Options: Yes, No
              return (
                <MultipleChoice
                  key={j}
                  keyName={keyName}
                  label={GENERAL_QUESTION_LABELS[j]}
                  options={DEEP_MODE_OPTIONS}
                  value={formData[keyName] || []}
                  onChange={onFormChange}
                />
              );
            } else if (j === 3) {
              // Fourth question (Cover letter style) is a multiple choice with checkboxes
              // Options: Professional, Friendly, Confident
              return (
                <MultipleChoice
                  key={j}
                  keyName={keyName}
                  label={GENERAL_QUESTION_LABELS[j]}
                  options={COVER_LETTER_STYLE_OPTIONS}
                  value={formData[keyName] || []}
                  onChange={onFormChange}
                />
              );
            } else if (j === 4) {
              // Fifth question (Job count) is a multiple choice with checkboxes
              // Options: 1, 2, 3, 4, 5, 10
              return (
                <MultipleChoice
                  key={j}
                  keyName={keyName}
                  label={GENERAL_QUESTION_LABELS[j]}
                  options={JOB_COUNT_OPTIONS}
                  value={formData[keyName] || []}
                  onChange={onFormChange}
                />
              );
            } else {
              return (
                <TextField
                  key={j}
                  keyName={keyName}
                  label={GENERAL_QUESTION_LABELS[j]}
                  value={
                    formData[keyName] || GENERAL_QUESTION_DEFAULTS[j] || ""
                  }
                  onChange={onFormChange}
                />
              );
            }
          })
        ) : (
          // Slider question sets (indices 1-8): Multiple sliders + one "Other" text field
          <>
            {/* Render sliders for this question set */}
            {/* SLIDER_DATA[index - 1] contains the key-value pairs for this set */}
            {Object.entries(SLIDER_DATA[index - 1]).map(([key, label]) => (
              <Slider
                key={key}
                keyName={key}
                label={label}
                value={formData[key] || SLIDER_DEFAULT}
                onChange={onFormChange}
              />
            ))}
            {/* "Other" text field for additional input */}
            <TextField
              keyName={`text-field${index}`}
              label="Other"
              value={formData[`text-field${index}`] || ""}
              onChange={onFormChange}
            />
          </>
        )}
      </div>
    </section>
  );
}

/**
 * QuestionSets Component
 *
 * Main component for managing and displaying question sets.
 * Handles:
 * - Navigation between 9 question sets (prev/next buttons)
 * - Form state management for all inputs
 * - Synchronizing form data with parent component
 * - Smooth scrolling to active question set
 *
 * @param {function} onFormDataChange - Callback to notify parent when form data changes
 *                                      Receives the complete formData object
 */
export default function QuestionSets({ onFormDataChange }) {
  // Current active question set index (0-8)
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
    for (let j = 0; j < GENERAL_QUESTIONS_COUNT; j++) {
      const keyName = `text-field-general-${j}`;
      if (j === 0 || j === 1 || j === 2 || j === 3 || j === 4) {
        // First, second, third, fourth, and fifth questions are multiple choice - start with empty array
        initial[keyName] = [];
      } else {
        // Other general questions use default values from config
        initial[keyName] = GENERAL_QUESTION_DEFAULTS[j] || "";
      }
    }

    // Set default values for slider question sets (question sets 1-8)
    for (let i = 1; i < TOTAL_QUESTION_SETS; i++) {
      // Sliders default to 0 (handled in Slider component)
      // Only need to initialize the "Other" text field
      initial[`text-field${i}`] = "";
    }

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
    setFormData((prev) => {
      const updated = { ...prev, [key]: value };
      return updated;
    });
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
          className="prev-btn text-white text-2xl px-3 py-1 bg-gray-800 rounded-lg hover:bg-gray-700 transition-colors"
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
          className="next-btn text-white text-2xl px-3 py-1 bg-gray-800 rounded-lg hover:bg-gray-700 transition-colors"
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

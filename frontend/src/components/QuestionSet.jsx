import { SLIDER_DATA } from "../config/sliderData";
import {
  GENERAL_QUESTION_LABELS,
  GENERAL_QUESTION_KEYS,
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
 * SingleChoice Component
 *
 * Renders a group of radio buttons allowing only one selection.
 * Used for questions that require a single answer.
 *
 * @param {string} keyName - Unique identifier for the radio button group
 * @param {string} label - Display label for the question
 * @param {string[]} options - Array of option strings to display as radio buttons
 * @param {string} value - Currently selected option (single value, not array)
 * @param {function} onChange - Callback function called when radio button state changes
 *                              Receives (keyName, selectedValue) as parameters
 */
function SingleChoice({ keyName, label, options, value, onChange }) {
  return (
    <div className="flex flex-col w-full">
      <label className="mb-1">{label}</label>
      {options.map((option) => {
        const optionKey = option.toLowerCase().replace(/\s+/g, "-");
        const isChecked = value === option;
        return (
          <div key={option} className="flex items-center mb-2">
            <input
              className="radio-field accent-blue-500"
              type="radio"
              name={keyName}
              checked={isChecked}
              onChange={() => onChange(keyName, option)}
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
 * Renders a single question set (one of 10 total sets).
 * Only the active question set is visible; others are hidden via CSS.
 *
 * @param {number} index - Index of the question set (0-9)
 * @param {boolean} isActive - Whether this question set is currently visible
 * @param {object} sectionRef - React ref callback to store DOM reference for scrolling
 * @param {object} formData - Current form data state (all question values)
 * @param {function} onFormChange - Callback to update form data when inputs change
 */
export default function QuestionSet({
  index,
  isActive,
  sectionRef,
  formData,
  onFormChange,
}) {
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
        {index === 9 ? (
          // Text-only question set (index 9): Single text input field
          <TextField
            keyName="additional-info"
            label="Additional Information"
            value={formData["additional-info"] || ""}
            onChange={onFormChange}
          />
        ) : index === GENERAL_QUESTIONS_INDEX ? (
          // General Questions (index 0): 5 questions, all are multiple choice
          Array.from({ length: GENERAL_QUESTIONS_COUNT }).map((_, j) => {
            const keyName = GENERAL_QUESTION_KEYS[j];
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
              // Insert paragraph between questions 1 and 2
              return (
                <div key={`info-${j}`}>
                  <h3>We'll search popular job listing sites for you...</h3>
                  <br />
                  <MultipleChoice
                    key={j}
                    keyName={keyName}
                    label={GENERAL_QUESTION_LABELS[j]}
                    options={JOB_BOARD_OPTIONS}
                    value={formData[keyName] || []}
                    onChange={onFormChange}
                  />
                </div>
              );
            } else if (j === 2) {
              // Third question (Deep mode) is a single choice with radio buttons
              // Options: Yes, No
              return (
                <SingleChoice
                  key={j}
                  keyName={keyName}
                  label={GENERAL_QUESTION_LABELS[j]}
                  options={DEEP_MODE_OPTIONS}
                  value={formData[keyName] || ""}
                  onChange={onFormChange}
                />
              );
            } else if (j === 3) {
              // Insert paragraph between questions 3 and 4
              // Fourth question (Job count) is a single choice with radio buttons
              // Options: 1, 2, 3, 4, 5, 10
              return (
                <div key={`info-${j}`}>
                  <h3>...and then write cover letters for the top jobs</h3>
                  <br />
                  <SingleChoice
                    key={j}
                    keyName={keyName}
                    label={GENERAL_QUESTION_LABELS[j]}
                    options={JOB_COUNT_OPTIONS}
                    value={formData[keyName] || ""}
                    onChange={onFormChange}
                  />
                </div>
              );
            } else if (j === 4) {
              // Fifth question (Cover letter style) is a single choice with radio buttons
              // Options: Professional, Friendly, Confident
              return (
                <SingleChoice
                  key={j}
                  keyName={keyName}
                  label={GENERAL_QUESTION_LABELS[j]}
                  options={COVER_LETTER_STYLE_OPTIONS}
                  value={formData[keyName] || ""}
                  onChange={onFormChange}
                />
              );
            }
            // All general questions (0-4) are handled above
            return null;
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

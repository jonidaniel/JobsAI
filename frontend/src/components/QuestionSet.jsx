import { useState } from "react";
import Slider from "./questions/Slider";
import TextField from "./questions/TextField";
import MultipleChoice from "./questions/MultipleChoice";
import SingleChoice from "./questions/SingleChoice";

import {
  TOTAL_QUESTION_SETS,
  QUESTION_SET_TITLES,
} from "../config/questionSet";
import {
  GENERAL_QUESTION_LABELS,
  GENERAL_QUESTION_KEYS,
  GENERAL_QUESTIONS_COUNT,
  GENERAL_QUESTIONS_INDEX,
  NAME_OPTIONS,
  JOB_BOARD_OPTIONS,
  DEEP_MODE_OPTIONS,
  COVER_LETTER_STYLE_OPTIONS,
  JOB_COUNT_OPTIONS,
} from "../config/generalQuestions";
import { SLIDER_DATA, SLIDER_DEFAULT } from "../config/sliders";

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
 * @param {object} validationErrors - Object mapping question keys to error messages
 */
export default function QuestionSet({
  index,
  isActive,
  sectionRef,
  formData,
  onFormChange,
  validationErrors = {},
}) {
  // State to track how many "Other" field sets are shown for slider question sets (indices 1-8)
  // Always show at least one "Other" field set
  const baseOtherFieldKey = `text-field${index}`;
  // Count how many "other" fields have values, default to 1
  const countOtherFields = () => {
    let count = 1; // Always show at least one
    let i = 1;
    while (
      formData[`${baseOtherFieldKey}${i > 1 ? `-${i}` : ""}`] ||
      formData[`${baseOtherFieldKey}${i > 1 ? `-${i}` : ""}-slider`]
    ) {
      i++;
      count = i;
    }
    return count;
  };
  const [otherFieldCount, setOtherFieldCount] = useState(countOtherFields);
  const [addMoreClicked, setAddMoreClicked] = useState(false);

  const label = <p>The last question.</p>;
  const label2 = (
    <p>
      <br />
      <br />
      Give us a depiction of <i>what kind of person you are.</i> What are your
      interests and aspirations? Here's where you should bring up your
      personality.
      <br />
      <br />
      What do you look for in a job?
      <br />
      What is the one big thing you bring to the table?
      <br />
      And what separates you from others?
      <br />
      <br />
      Consider this answer as <i>the engine</i> of the job search.
      <br />
      <br />
      Don't worry too much about grammar. We'll find the best words for you.
      <br />
      There's no need to repeat any of the information here that you've already
      given in earlier steps. Don't enter any personally identifiable
      information.
      <br />
      <br />
    </p>
  );

  return (
    <section
      ref={sectionRef}
      className={isActive ? "active" : ""}
      aria-hidden={!isActive}
      role="tabpanel"
      aria-labelledby={`question-set-${index}-title`}
      data-index={index}
    >
      <h3
        className="text-3xl"
        style={{ fontSize: "clamp(1.25rem, 4vw, 1.875rem)" }}
        id={`question-set-${index}-title`}
      >
        {index + 1}/{TOTAL_QUESTION_SETS}
      </h3>
      <h3
        className="text-3xl"
        style={{ fontSize: "clamp(1.25rem, 4vw, 1.875rem)" }}
      >
        {QUESTION_SET_TITLES[index]}
      </h3>

      {/* Questions */}
      <div className="space-y-4">
        {index === 9 ? (
          // Text-only question set (index 9): Single text input field
          <TextField
            keyName="additional-info"
            label={label}
            label2={label2}
            value={formData["additional-info"] || ""}
            onChange={onFormChange}
            error={validationErrors["additional-info"]}
            required={true}
            height="150px"
          />
        ) : index === GENERAL_QUESTIONS_INDEX ? (
          // Create 'General Questions' set (index 0)
          // 5 questions, all are multiple choice
          Array.from({ length: GENERAL_QUESTIONS_COUNT }).map((_, j) => {
            const keyName = GENERAL_QUESTION_KEYS[j];
            if (j === 0) {
              // First question (Job level) is a multiple choice with checkboxes
              // Options: Expert-level, Intermediate, Entry, Intern
              // Users can select 1 or 2 options, but if 2, they must be adjacent
              return (
                <MultipleChoice
                  key={j}
                  keyName={keyName}
                  label={GENERAL_QUESTION_LABELS[j]}
                  options={NAME_OPTIONS}
                  value={formData[keyName] || []}
                  onChange={onFormChange}
                  error={validationErrors[keyName]}
                  required={true}
                  maxSelections={2}
                  requireAdjacent={true}
                />
              );
            } else if (j === 1) {
              // Insert paragraph between questions 1 and 2
              return (
                <div key={`info-${j}`}>
                  <MultipleChoice
                    key={j}
                    keyName={keyName}
                    label={GENERAL_QUESTION_LABELS[j]}
                    options={JOB_BOARD_OPTIONS}
                    value={formData[keyName] || []}
                    onChange={onFormChange}
                    error={validationErrors[keyName]}
                    required={true}
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
                  error={validationErrors[keyName]}
                  required={true}
                />
              );
            } else if (j === 3) {
              // Insert paragraph between questions 3 and 4
              // Fourth question (Job count) is a single choice with radio buttons
              // Options: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
              // Split at index 5: options 1-5 on left, 6-10 on right
              return (
                <div key={`info-${j}`}>
                  <SingleChoice
                    key={j}
                    keyName={keyName}
                    label={GENERAL_QUESTION_LABELS[j]}
                    options={JOB_COUNT_OPTIONS}
                    value={formData[keyName] || ""}
                    onChange={onFormChange}
                    error={validationErrors[keyName]}
                    required={true}
                    splitAt={5}
                  />
                </div>
              );
            } else if (j === 4) {
              // Fifth question (Cover letter style) is a multiple choice with checkboxes
              // Users can select 1 or 2 options
              // Options: Professional, Friendly, Confident, Funny
              return (
                <MultipleChoice
                  key={j}
                  keyName={keyName}
                  label={GENERAL_QUESTION_LABELS[j]}
                  options={COVER_LETTER_STYLE_OPTIONS}
                  value={formData[keyName] || []}
                  onChange={onFormChange}
                  error={validationErrors[keyName]}
                  required={true}
                  maxSelections={2}
                />
              );
            }
            // All general questions (0-4) are handled above
            return null;
          })
        ) : (
          // Slider question sets (indices 1-8)
          // Multiple sliders + one "Other" text field each
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
            {/* "Other" text fields and sliders - always show at least one, can add more */}
            {Array.from({ length: otherFieldCount }).map((_, i) => {
              const fieldIndex = i + 1;
              const fieldKey =
                fieldIndex === 1
                  ? baseOtherFieldKey
                  : `${baseOtherFieldKey}-${fieldIndex}`;
              const sliderKey = `${fieldKey}-slider`;

              const isFirst = fieldIndex === 1;

              return (
                <div key={fieldKey} className="mt-4">
                  <TextField
                    keyName={fieldKey}
                    label={
                      isFirst
                        ? "Type a new experience and choose amount of years"
                        : ""
                    }
                    value={formData[fieldKey] || ""}
                    onChange={onFormChange}
                  />
                  <Slider
                    keyName={sliderKey}
                    label=""
                    value={formData[sliderKey] || SLIDER_DEFAULT}
                    onChange={onFormChange}
                  />
                </div>
              );
            })}
            {/* Button to add another "Other" field set */}
            {(() => {
              // Get the last/most recently added field key
              const lastFieldKey =
                otherFieldCount === 1
                  ? baseOtherFieldKey
                  : `${baseOtherFieldKey}-${otherFieldCount}`;
              const lastSliderKey = `${lastFieldKey}-slider`;

              const lastFieldValue = formData[lastFieldKey] || "";
              const lastSliderValue = formData[lastSliderKey] ?? SLIDER_DEFAULT;
              // Both must be filled: field must not be empty AND slider must not be 0
              const isFieldEmpty = !lastFieldValue.trim();
              const isSliderZero = lastSliderValue === 0;
              const shouldShowWarning = isFieldEmpty || isSliderZero;

              // Reset the clicked state if conditions are no longer met
              if (!shouldShowWarning && addMoreClicked) {
                setAddMoreClicked(false);
              }

              const handleAddMore = () => {
                if (shouldShowWarning) {
                  setAddMoreClicked(true);
                } else {
                  setOtherFieldCount(otherFieldCount + 1);
                  setAddMoreClicked(false);
                }
              };

              return (
                <div className="flex flex-col items-start">
                  <button
                    type="button"
                    onClick={handleAddMore}
                    className="mt-4 px-4 py-2 text-sm border border-gray-400 rounded hover:bg-gray-800 transition-colors"
                    style={{ backgroundColor: "#0e0e0e" }}
                  >
                    Add more
                  </button>
                  {shouldShowWarning && addMoreClicked && (
                    <p className="text-red-500 text-sm mt-2" role="alert">
                      Please fill in the experience field and set the years
                      before adding more.
                    </p>
                  )}
                </div>
              );
            })()}
          </>
        )}
      </div>
    </section>
  );
}

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
import { PERSONAL_DESCRIPTION_MAX_LENGTH } from "../config/constants";

/**
 * Shared button component for "Add more"
 * Declared outside component to avoid recreation on each render
 */
const AddMoreButton = ({ onClick, warningMessage }) => (
  <div className="flex flex-col items-start">
    <button
      type="button"
      onClick={onClick}
      className="mt-4 px-4 py-2 text-sm border border-gray-400 rounded hover:bg-gray-800 transition-colors"
      style={{ backgroundColor: "#0e0e0e" }}
    >
      Add more
    </button>
    {warningMessage && (
      <p className="text-red-500 text-sm mt-2" role="alert">
        {warningMessage}
      </p>
    )}
  </div>
);

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
  // Start with 0 fields, show first field only after clicking "Add more"
  const baseOtherFieldKey = `text-field${index}`;

  // Count how many "other" fields have values, default to 0
  // Use lazy initialization to only calculate once on mount
  const [otherFieldCount, setOtherFieldCount] = useState(() => {
    let count = 0;
    let i = 1;
    while (
      formData[`${baseOtherFieldKey}${i > 1 ? `-${i}` : ""}`] ||
      formData[`${baseOtherFieldKey}${i > 1 ? `-${i}` : ""}-slider`]
    ) {
      i++;
      count = i - 1;
    }
    return count;
  });
  const [addMoreClicked, setAddMoreClicked] = useState(false);

  // Helper to generate field key for a given index
  const getFieldKey = (fieldIndex) =>
    fieldIndex === 1 ? baseOtherFieldKey : `${baseOtherFieldKey}-${fieldIndex}`;

  /**
   * Renders the "Add more" button with validation logic for existing fields
   * Validates that the last field is filled, slider is not zero, and no duplicates exist
   */
  const renderAddMoreButtonWithValidation = () => {
    const lastFieldKey = getFieldKey(otherFieldCount);
    const lastFieldValue = formData[lastFieldKey] || "";
    const lastSliderValue =
      formData[`${lastFieldKey}-slider`] ?? SLIDER_DEFAULT;

    const isFieldEmpty = !lastFieldValue.trim();
    const isSliderZero = lastSliderValue === 0;

    // Check for duplicate experiences
    const defaultLabels = Object.values(SLIDER_DATA[index - 1] || {});
    const addedExperiences = Array.from(
      { length: otherFieldCount - 1 },
      (_, j) => {
        return formData[getFieldKey(j + 1)]?.trim() || "";
      }
    ).filter(Boolean);

    const normalizedCurrentValue = lastFieldValue.trim().toLowerCase();
    const isDuplicate =
      defaultLabels.some(
        (label) => label.toLowerCase() === normalizedCurrentValue
      ) ||
      addedExperiences.some(
        (exp) => exp.toLowerCase() === normalizedCurrentValue
      );

    const shouldShowWarning = isFieldEmpty || isSliderZero || isDuplicate;

    // Reset the clicked state if conditions are no longer met
    if (!shouldShowWarning && addMoreClicked) {
      setAddMoreClicked(false);
    }

    return (
      <AddMoreButton
        onClick={() => {
          if (shouldShowWarning) {
            setAddMoreClicked(true);
          } else {
            setOtherFieldCount(otherFieldCount + 1);
            setAddMoreClicked(false);
          }
        }}
        warningMessage={
          shouldShowWarning && addMoreClicked
            ? isDuplicate
              ? "This experience already exists. Please enter a different one."
              : "Please fill in the experience field and set the years before adding more."
            : null
        }
      />
    );
  };

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
            maxLength={PERSONAL_DESCRIPTION_MAX_LENGTH}
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
              return (
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
              );
            } else if (j === 2) {
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
              return (
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
            {/* "Other" text fields and sliders - shown only after clicking "Add more" */}
            {Array.from({ length: otherFieldCount }).map((_, i) => {
              const fieldIndex = i + 1;
              const fieldKey = getFieldKey(fieldIndex);
              const sliderKey = `${fieldKey}-slider`;

              // Check if this is the last (currently editable) field
              const isLastField = i === otherFieldCount - 1;
              const fieldValue = formData[fieldKey] || "";

              return (
                <div key={fieldKey} className="mt-4">
                  {isLastField ? (
                    // Last field: editable
                    <>
                      <TextField
                        keyName={fieldKey}
                        label=""
                        value={fieldValue}
                        onChange={onFormChange}
                        showValidation={false}
                      />
                      <Slider
                        keyName={sliderKey}
                        label=""
                        value={formData[sliderKey] || SLIDER_DEFAULT}
                        onChange={onFormChange}
                      />
                    </>
                  ) : (
                    // Previous fields: read-only, styled like default sliders
                    <>
                      {fieldValue && (
                        <Slider
                          keyName={sliderKey}
                          label={fieldValue}
                          value={formData[sliderKey] || SLIDER_DEFAULT}
                          onChange={() => {}} // No-op, field is read-only
                          disabled={true}
                        />
                      )}
                    </>
                  )}
                </div>
              );
            })}
            {/* Button to add another "Other" field set */}
            {otherFieldCount === 0 ? (
              <AddMoreButton
                onClick={() => {
                  setOtherFieldCount(1);
                  setAddMoreClicked(false);
                }}
              />
            ) : (
              renderAddMoreButtonWithValidation()
            )}
          </>
        )}
      </div>
    </section>
  );
}

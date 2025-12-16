import { useState, useMemo } from "react";
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
      className="mt-4 px-4 py-2 text-sm border border-gray-400 rounded hover:bg-gray-800 transition-all"
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
  // Base key for "Other" field sets in slider question sets (indices 1-8)
  // Format: "text-field1", "text-field2", etc.
  const baseOtherFieldKey = `text-field${index}`;

  // State to track how many "Other" field sets are shown
  // Start with 0 fields, show first field only after clicking "Add more"
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

  /**
   * Generates field key for a given index
   * First field uses base key, subsequent fields append index (e.g., "text-field1-2")
   *
   * @param {number} fieldIndex - The field index (1-based)
   * @returns {string} The field key
   */
  const getFieldKey = (fieldIndex) =>
    fieldIndex === 1 ? baseOtherFieldKey : `${baseOtherFieldKey}-${fieldIndex}`;

  /**
   * Renders a general question based on its index
   * Uses configuration array to determine component type and props
   *
   * @param {number} j - Question index (0-4)
   * @returns {JSX.Element|null} The rendered question component or null
   */
  const renderGeneralQuestion = (j) => {
    const keyName = GENERAL_QUESTION_KEYS[j];
    const commonProps = {
      keyName,
      label: GENERAL_QUESTION_LABELS[j],
      value: formData[keyName] || (j < 2 ? [] : ""),
      onChange: onFormChange,
      error: validationErrors[keyName],
      required: true,
    };

    // Configuration for each question
    const questionConfig = [
      {
        // Question 0: Job level - MultipleChoice with adjacency requirement
        component: MultipleChoice,
        props: {
          ...commonProps,
          options: NAME_OPTIONS,
          maxSelections: 2,
          requireAdjacent: true,
        },
      },
      {
        // Question 1: Job boards - MultipleChoice
        component: MultipleChoice,
        props: {
          ...commonProps,
          options: JOB_BOARD_OPTIONS,
        },
      },
      {
        // Question 2: Deep mode - SingleChoice
        component: SingleChoice,
        props: {
          ...commonProps,
          options: DEEP_MODE_OPTIONS,
        },
      },
      {
        // Question 3: Job count - SingleChoice with split layout
        component: SingleChoice,
        props: {
          ...commonProps,
          options: JOB_COUNT_OPTIONS,
          splitAt: 5,
        },
      },
      {
        // Question 4: Cover letter style - MultipleChoice with max selections
        component: MultipleChoice,
        props: {
          ...commonProps,
          options: COVER_LETTER_STYLE_OPTIONS,
          maxSelections: 2,
        },
      },
    ];

    if (j >= 0 && j < questionConfig.length) {
      const { component: Component, props } = questionConfig[j];
      return <Component key={j} {...props} />;
    }

    return null;
  };

  /**
   * Memoized validation check for duplicate experiences
   * Only recalculates when relevant dependencies change
   *
   * @returns {Object} Validation result with isFieldEmpty, isSliderZero, isDuplicate, and shouldShowWarning
   */
  const validationResult = useMemo(() => {
    // Only calculate if we have fields to validate
    if (otherFieldCount === 0) {
      return {
        isFieldEmpty: false,
        isSliderZero: false,
        isDuplicate: false,
        shouldShowWarning: false,
      };
    }

    // Inline field key generation to avoid dependency on getFieldKey function
    // baseOtherFieldKey is `text-field${index}`, so we inline it here
    const baseKey = `text-field${index}`;
    const lastFieldKey =
      otherFieldCount === 1 ? baseKey : `${baseKey}-${otherFieldCount}`;
    const lastFieldValue = formData[lastFieldKey] || "";
    const lastSliderValue =
      formData[`${lastFieldKey}-slider`] ?? SLIDER_DEFAULT;

    // Validation checks
    const isFieldEmpty = !lastFieldValue.trim();
    const isSliderZero = lastSliderValue === 0;

    // Only check for duplicates if field has a value
    let isDuplicate = false;
    if (!isFieldEmpty) {
      // Check for duplicate experiences (case-insensitive)
      const defaultLabels = Object.values(SLIDER_DATA[index - 1] || {});
      const addedExperiences = Array.from(
        { length: otherFieldCount - 1 },
        (_, j) => {
          const fieldIndex = j + 1;
          const fieldKey =
            fieldIndex === 1 ? baseKey : `${baseKey}-${fieldIndex}`;
          return formData[fieldKey]?.trim() || "";
        }
      ).filter(Boolean);

      const normalizedCurrentValue = lastFieldValue.trim().toLowerCase();
      isDuplicate =
        defaultLabels.some(
          (label) => label.toLowerCase() === normalizedCurrentValue
        ) ||
        addedExperiences.some(
          (exp) => exp.toLowerCase() === normalizedCurrentValue
        );
    }

    const shouldShowWarning = isFieldEmpty || isSliderZero || isDuplicate;

    return {
      isFieldEmpty,
      isSliderZero,
      isDuplicate,
      shouldShowWarning,
    };
  }, [otherFieldCount, formData, index]);

  /**
   * Renders the "Add more" button with validation logic for existing fields
   * Validates that:
   * - The last field is filled (not empty)
   * - The slider is not zero
   * - No duplicate experiences exist (case-insensitive)
   *
   * @returns {JSX.Element} The AddMoreButton component with appropriate props
   */
  const renderAddMoreButtonWithValidation = () => {
    const { isDuplicate, shouldShowWarning } = validationResult;

    // Reset the clicked state if validation conditions are no longer met
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

      {/* Questions section - renders different question types based on index */}
      <div className="space-y-4">
        {index === 9 ? (
          // Text-only question set (index 9): Personal description textarea
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
          // General Questions set (index 0): 5 questions rendered using configuration-based approach
          Array.from({ length: GENERAL_QUESTIONS_COUNT }).map((_, j) =>
            renderGeneralQuestion(j)
          )
        ) : (
          // Slider question sets (indices 1-8): Multiple sliders + optional "Other" text fields
          <>
            {/* Render default sliders for this question set */}
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
            {/* Custom "Other" text fields and sliders - shown only after clicking "Add more" */}
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
                    // Last field: editable text input and slider
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
            {/* Button to add another custom "Other" field set */}
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

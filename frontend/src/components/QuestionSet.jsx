import Slider from "./questions/Slider";
import TextField from "./questions/TextField";
import MultipleChoice from "./questions/MultipleChoice";
import SingleChoice from "./questions/SingleChoice";

import {
  TOTAL_QUESTION_SETS,
  GENERAL_QUESTIONS_COUNT,
  SLIDER_DEFAULT,
  GENERAL_QUESTIONS_INDEX,
} from "../config/constants";
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
import { SLIDER_DATA } from "../config/sliderData";

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

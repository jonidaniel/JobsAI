import { useEffect, useRef } from "react";
import { SLIDER_DATA } from "../config/sliderData";
import {
  GENERAL_QUESTION_LABELS,
  GENERAL_QUESTION_DEFAULTS,
  NAME_OPTIONS,
} from "../config/generalQuestions";
import { QUESTION_SET_TITLES } from "../config/questionSetTitles";

// React Components
function Slider({ keyName, label }) {
  return (
    <div className="flex flex-col w-full">
      <label className="mb-1">{label}</label>
      <input
        className="slider accent-blue-500 w-full"
        type="range"
        min="0"
        max="7"
        value="0"
        data-key={keyName}
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

function TextField({ keyName, label, defaultValue = "" }) {
  return (
    <div className="flex flex-col w-full">
      <label className="mb-1">{label}</label>
      <input
        className="text-field border border-gray-300 px-2 py-1 rounded w-full"
        type="text"
        data-key={keyName}
        defaultValue={defaultValue}
      />
    </div>
  );
}

function MultipleChoice({ keyName, label, options }) {
  return (
    <div className="flex flex-col w-full">
      <label className="mb-1">{label}</label>
      {options.map((option) => {
        const optionKey = option.toLowerCase().replace(/\s+/g, "-");
        return (
          <div key={option} className="flex items-center mb-2">
            <input
              className="checkbox-field accent-blue-500"
              type="checkbox"
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

export default function QuestionSets() {
  const initialized = useRef(false);
  const currentIndexRef = useRef(0);
  const questionSetsRef = useRef([]);

  useEffect(() => {
    // Prevent double initialization of navigator in StrictMode
    if (initialized.current) {
      return;
    }
    initialized.current = true;

    // Set up navigator
    const questionSets = Array.from(
      document.querySelectorAll("#question-set-wrapper section")
    );

    function showQuestionSet(index, shouldScroll = false) {
      questionSets.forEach((questionSet, questionSetIndex) => {
        questionSet.classList.toggle("active", questionSetIndex === index);
      });
      if (shouldScroll && questionSets[index]) {
        questionSets[index].scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
      }
    }

    questionSetsRef.current = questionSets;
    showQuestionSet(currentIndexRef.current, false);
  }, []);

  // Parse slider data
  const sliderData = SLIDER_DATA.map((jsonStr) => JSON.parse(jsonStr));

  return (
    /*
     * Question set wrapper
     *
     * There are 9 question sets in total:
     *     1/9 'General Questions'
     *     2/9 'Programming, Scripting, and Markup Languages',
     *     3/9 'Databases',
     *     4/9 'Cloud Development',
     *     5/9 'Web Frameworks and Technologies',
     *     6/9 'Dev IDEs',
     *     7/9 'Large Language Models',
     *     8/9 'Code Documentation and Collaboration',
     *     9/9 'Computer Operating Systems'
     *
     * Only one question set is shown on the page at a time
     */
    <div id="question-set-wrapper" className="relative flex w-full">
      {/* Left arrow */}
      <div className="prev-btn-container sticky top-1/2 -translate-y-1/2 self-start h-0 flex items-center z-10">
        <button
          className="prev-btn text-white text-2xl px-3 py-1 bg-gray-800 rounded-lg hover:bg-gray-700 transition-colors"
          onClick={() => {
            const questionSets = questionSetsRef.current;
            currentIndexRef.current =
              currentIndexRef.current === 0
                ? questionSets.length - 1
                : currentIndexRef.current - 1;
            questionSets.forEach((questionSet, questionSetIndex) => {
              questionSet.classList.toggle(
                "active",
                questionSetIndex === currentIndexRef.current
              );
            });
            if (questionSets[currentIndexRef.current]) {
              questionSets[currentIndexRef.current].scrollIntoView({
                behavior: "smooth",
                block: "start",
              });
            }
          }}
        >
          &larr;
        </button>
      </div>

      {/* TailwindCSS form */}
      <div className="bg-gray-800 p-10 rounded-2xl shadow-lg flex-1">
        {/* Create an array of 9 question sets */}
        {Array.from({ length: 9 }).map((_, i) => (
          /* Question set */
          <section key={i}>
            <h3 className="text-3xl">{i + 1}/9</h3>
            <h3 className="text-3xl">{getTitle(i)}</h3>

            {/* Questions */}
            <div className="space-y-4">
              {i === 0 ? (
                // 'General Questions'
                Array.from({ length: 10 }).map((_, j) => {
                  if (j === 0) {
                    // First question (Name) is a multiple choice with checkboxes
                    return (
                      <MultipleChoice
                        key={j}
                        keyName={`text-field-general-${j}`}
                        label={GENERAL_QUESTION_LABELS[j]}
                        options={NAME_OPTIONS}
                      />
                    );
                  } else {
                    return (
                      <TextField
                        key={j}
                        keyName={`text-field-general-${j}`}
                        label={GENERAL_QUESTION_LABELS[j]}
                        defaultValue={GENERAL_QUESTION_DEFAULTS[j] || ""}
                      />
                    );
                  }
                })
              ) : (
                // Other question sets (1-8)
                <>
                  {/* Sliders */}
                  {Object.entries(sliderData[i - 1]).map(([key, label]) => (
                    <Slider key={key} keyName={key} label={label} />
                  ))}
                  {/* Text field */}
                  <TextField keyName={`text-field${i}`} label="Other" />
                </>
              )}
            </div>
          </section>
        ))}
      </div>

      {/* Right arrow */}
      <div className="next-btn-container sticky top-1/2 -translate-y-1/2 self-start h-0 flex items-center z-10 ml-auto">
        <button
          className="next-btn text-white text-2xl px-3 py-1 bg-gray-800 rounded-lg hover:bg-gray-700 transition-colors"
          onClick={() => {
            const questionSets = questionSetsRef.current;
            currentIndexRef.current =
              (currentIndexRef.current + 1) % questionSets.length;
            questionSets.forEach((questionSet, questionSetIndex) => {
              questionSet.classList.toggle(
                "active",
                questionSetIndex === currentIndexRef.current
              );
            });
            if (questionSets[currentIndexRef.current]) {
              questionSets[currentIndexRef.current].scrollIntoView({
                behavior: "smooth",
                block: "start",
              });
            }
          }}
        >
          &rarr;
        </button>
      </div>
    </div>
  );
}

function getTitle(i) {
  return QUESTION_SET_TITLES[i];
}

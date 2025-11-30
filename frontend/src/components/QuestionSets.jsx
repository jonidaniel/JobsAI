import { useEffect, useRef } from "react";
import builder from "../scripts/builder";

export default function QuestionSets() {
  const initialized = useRef(false);
  const currentIndexRef = useRef(0);
  const questionSetsRef = useRef([]);

  useEffect(() => {
    // Prevent double initialization of builder/navigator in StrictMode
    if (initialized.current) {
      return;
    }
    initialized.current = true;

    builder();

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
                Array.from({ length: 10 }).map((_, j) => (
                  <div key={j} id={`text-field-general-${j}`}></div>
                ))
              ) : (
                // Other question sets
                <>
                  <div id={`sliders${i}`}></div>
                  <div id={`text-field${i}`}></div>
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
  return [
    "General Questions",
    "Programming, Scripting, and Markup Languages Experience",
    "Databases Experience",
    "Cloud Development Experience",
    "Web Frameworks and Technologies Experience",
    "Dev IDEs Experience",
    "Large Language Models Experience",
    "Code Documentation and Collaboration Experience",
    "Computer Operating Systems Experience",
  ][i];
}

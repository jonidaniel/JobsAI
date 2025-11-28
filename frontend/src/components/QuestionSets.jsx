import { useEffect } from "react";
import builder from "../scripts/builder";
import navigatorScript from "../scripts/navigator";
import submitter from "../scripts/submitter";

export default function QuestionSets() {
  useEffect(() => {
    builder();
    navigatorScript();
    submitter();
  }, []);

  return (
    <div id="question-set-wrapper" className="relative">
      <div className="bg-gray-800 p-10 rounded-2xl shadow-lg w-full max-w-2xl space-y-10">
        <h1 className="text-3xl font-semibold text-white">
          Fill in your experience levels in each category and we will search
          jobs relevant to you
        </h1>

        {/** EXACT COPY of all 8 <section> blocks, but JSX instead of HTML */}
        {Array.from({ length: 8 }).map((_, i) => (
          <section key={i}>
            <div className="flex justify-between items-center mb-6">
              <button className="prev-btn text-white text-2xl px-3 py-1">
                &larr;
              </button>
              <h3 className="text-xl font-semibold text-white mb-4">
                {getTitle(i)} ({i + 1}/8)
              </h3>
              <button className="next-btn text-white text-2xl px-3 py-1">
                &rarr;
              </button>
            </div>

            <div className="space-y-4">
              <div id={`sliders${i + 1}`}></div>
              <div id={`text-field${i + 1}`}></div>
            </div>

            <div className="bottom-arrows flex justify-between items-center mb-6">
              <button className="prev-btn text-white text-2xl px-3 py-1">
                &larr;
              </button>
              <h3 className="text-xl font-semibold text-white mb-4">
                {getTitle(i)} ({i + 1}/8)
              </h3>
              <button className="next-btn text-white text-2xl px-3 py-1">
                &rarr;
              </button>
            </div>
          </section>
        ))}

        <div className="flex justify-center">
          <button
            id="submit-btn"
            className="mt-6 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg shadow"
          >
            Submit
          </button>
        </div>
      </div>
    </div>
  );
}

function getTitle(i) {
  return [
    "Programming, Scripting, and Markup Languages",
    "Databases",
    "Cloud Development",
    "Web Frameworks and Technologies",
    "Dev IDEs",
    "Large Language Models",
    "Code Documentation and Collaboration",
    "Computer Operating Systems",
  ][i];
}

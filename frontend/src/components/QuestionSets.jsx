import { useEffect, useRef } from "react";
import builder from "../scripts/builder";

export default function QuestionSets() {
  const initialized = useRef(false);
  const isSubmitting = useRef(false);
  const currentIndexRef = useRef(0);
  const questionSetsRef = useRef([]);

  useEffect(() => {
    // Set up submit button handler (always runs, even after cleanup)
    let submitBtnRef = null;
    let submitTimeoutId = null;
    let submitAttempts = 0;
    const maxSubmitAttempts = 50;
    let submitHandler = null; // Store handler reference for proper cleanup

    const handleSubmit = (e) => {
      if (e) {
        e.preventDefault();
        e.stopPropagation();
      }
      // Prevent double submission
      if (isSubmitting.current) {
        return;
      }
      isSubmitting.current = true;

      // The result will be stored as key-value pairs in this object
      const result = {};

      // Iterate over all slider questions
      document.querySelectorAll(".slider").forEach((slider) => {
        if (slider.value != 0) {
          // Grab the slider's unique key (e.g. "javascript")
          const key = slider.dataset.key;
          // Create a new key to the result object and store the slider's value (e.g. 3) under it
          result[key] = Number(slider.value);
        }
      });

      // Iterate over all text field questions
      document.querySelectorAll(".text-field").forEach((textField) => {
        if (textField.value != "") {
          // Grab the text field's unique key (e.g. "text-field1")
          const key = textField.dataset.key;
          // Create a new key to the result object and store the text field's value (e.g. "React Native") under it
          result[key] = textField.value.trim();
        }
      });

      async function downloadDocx(payload) {
        try {
          const response = await fetch("http://localhost:8000/api/endpoint", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify(payload),
          });

          if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
          }

          // Get the response as a blob (binary)
          const blob = await response.blob();

          // Get the filename from Content-Disposition header if available
          const contentDisposition = response.headers.get(
            "Content-Disposition"
          );
          let filename = "document.docx"; // default fallback
          if (contentDisposition) {
            const match = contentDisposition.match(/filename="?(.+)"?/);
            if (match && match[1]) filename = match[1];
          }

          // Create a temporary URL for the blob
          const url = window.URL.createObjectURL(blob);

          // Create a temporary link element to trigger download
          const a = document.createElement("a");
          a.href = url;
          a.download = filename;
          document.body.appendChild(a);
          a.click();
          a.remove();

          // Clean up the blob URL
          window.URL.revokeObjectURL(url);
        } catch (error) {
          console.error("Download failed:", error);
        } finally {
          // Reset submission flag after request completes
          isSubmitting.current = false;
        }
      }

      // Send to backend
      downloadDocx(result);
    };

    const setupSubmitter = () => {
      const submitBtn = document.getElementById("submit-btn");
      if (!submitBtn) {
        submitAttempts++;
        if (submitAttempts < maxSubmitAttempts) {
          submitTimeoutId = setTimeout(setupSubmitter, 100);
        } else {
          console.error("Submit button not found after maximum attempts!");
        }
        return;
      }

      submitBtnRef = submitBtn;
      // Remove any existing listener first (if we have a stored reference)
      if (submitHandler) {
        submitBtn.removeEventListener("click", submitHandler);
      }
      // Create and store the handler reference
      submitHandler = (e) => handleSubmit(e);
      submitBtn.addEventListener("click", submitHandler);
    };

    // Always set up submit button (runs every time useEffect runs)
    setupSubmitter();

    // Prevent double initialization of builder/navigator in StrictMode
    if (initialized.current) {
      // But still return cleanup for submit button
      return () => {
        if (submitTimeoutId) {
          clearTimeout(submitTimeoutId);
        }
        if (submitBtnRef && submitHandler) {
          submitBtnRef.removeEventListener("click", submitHandler);
          submitHandler = null; // Clear reference
        }
      };
    }
    initialized.current = true;

    builder();

    // Set up navigator with cleanup
    const questionSets = Array.from(
      document.querySelectorAll("#question-set-wrapper section")
    );

    function showQuestionSet(index, refreshing = true) {
      questionSets.forEach((questionSet, questionSetIndex) => {
        questionSet.classList.toggle("active", questionSetIndex === index);
      });
      if (refreshing && questionSets[index]) {
        questionSets[index].scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
      }
    }

    questionSetsRef.current = questionSets;
    showQuestionSet(currentIndexRef.current, false);

    // Cleanup function to remove all event listeners
    return () => {
      // Clear any pending timeout
      if (submitTimeoutId) {
        clearTimeout(submitTimeoutId);
      }
      if (submitBtnRef && submitHandler) {
        submitBtnRef.removeEventListener("click", submitHandler);
        submitHandler = null; // Clear reference
      }
      // Don't reset initialized.current - we want it to stay true even after cleanup
      // This prevents re-initialization in StrictMode
    };
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

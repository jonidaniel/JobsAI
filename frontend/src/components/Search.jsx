import QuestionSets from "./QuestionSets";

import "../styles/search.css";

export default function Search() {
  return (
    <section id="search">
      <h2>Search</h2>
      <h3 className="text-3xl font-semibold text-white text-center">
        Fill in questions in each category and we will find jobs relevant to you
      </h3>
      <QuestionSets />
      {/* Submit button */}
      <div className="flex justify-center">
        <button
          id="submit-btn"
          className="mt-6 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg shadow"
        >
          Find Jobs
        </button>
      </div>
    </section>
  );
}

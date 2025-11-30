export default function navigator() {
  // Toggles which question set (1–9) is visible
  function showQuestionSet(currentIndex, refreshing = true) {
    // Iterate over all question sets
    questionSets.forEach((questionSet, questionSetIndex) => {
      // Make the question set visible if its index matches currentIndex
      questionSet.classList.toggle("active", questionSetIndex === currentIndex);
    });
    // If coming from a page refresh (i.e. not loading the page for the first time)
    if (refreshing) {
      // Scroll browser view to top of question set
      questionSets[currentIndex].scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }
  }

  // Store all question sets in an array
  const questionSets = Array.from(
    document.querySelectorAll("#question-set-wrapper section")
  );

  // Makes question set 1/9 be the one that shows up on page load
  let currentIndex = 0;

  // Get the left arrow (prev-btn) - now outside the container
  const prevBtn = document.querySelector(".prev-btn");
  // Get the right arrow (next-btn) - now outside the container
  const nextBtn = document.querySelector(".next-btn");

  // Add click listener to the left arrow
  if (prevBtn) {
    prevBtn.addEventListener("click", () => {
      // If currently at index 0, go to the last question set
      // Otherwise, go to the previous question set
      currentIndex =
        currentIndex === 0 ? questionSets.length - 1 : currentIndex - 1;
      // Show the previous question set
      showQuestionSet(currentIndex, true);
    });
  }

  // Add click listener to the right arrow
  if (nextBtn) {
    nextBtn.addEventListener("click", () => {
      // Move to the next question set (wraps around to 0 after the last one)
      currentIndex = (currentIndex + 1) % questionSets.length;
      // Show the next question set
      showQuestionSet(currentIndex, true);
    });
  }

  showQuestionSet(currentIndex, false); // false indicates that the page is being loaded for the first time
}

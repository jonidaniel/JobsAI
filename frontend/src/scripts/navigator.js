export default function navigator() {
  // Toggles which question set (1–8) is visible
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

  // Makes question set 1/8 be the one that shows up on page load
  let currentIndex = 0;

  // Attach on click listeners to all 32 arrows
  questionSets.forEach((questionSet, questionSetIndex) => {
    // Grab both left arrows of a question set (top and bottom)
    const leftArrows = questionSet.querySelectorAll(".prev-btn");
    // Grab both right arrows of a question set (top and bottom)
    const rightArrows = questionSet.querySelectorAll(".next-btn");

    // Add listeners to both left arrows
    for (let arrow of leftArrows) {
      // Left arrow is clicked
      arrow.addEventListener("click", () => {
        // If questionSetIndex is 0 (i.e. if currently showing question set 1/8),
        // then set currentIndex as 7 (i.e. show set 8/8)
        // If questionSetIndex is anything else,
        // then subtract it by one (i.e. show previous set)
        currentIndex =
          questionSetIndex === 0
            ? questionSets.length - 1
            : questionSetIndex - 1;
        // Go make previous question set visible
        showQuestionSet(currentIndex, true); // // true indicates that the page is being refreshed
      });
    }

    // Add listeners to both right arrows
    for (let arrow of rightArrows) {
      // Right arrow is clicked
      arrow.addEventListener("click", () => {
        // Set currentIndex as ????????????????????????????????????????????????????
        currentIndex = (questionSetIndex + 1) % questionSets.length;
        // Go make next question set visible
        showQuestionSet(currentIndex, true); // true indicates that the page is being refreshed
      });
    }
  });

  showQuestionSet(currentIndex, false); // false indicates that the page is being loaded for the first time
}

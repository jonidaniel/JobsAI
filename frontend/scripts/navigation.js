// Gather all experience-category-container div's child sections (experience categories) to an array when the DOM content is loaded
document.addEventListener("DOMContentLoaded", () => {
  const experienceCategories = Array.from(
    document.querySelectorAll("#experience-categories-container section")
  );
  let currentIndex = 0;

  // Toggle a section's (an experience category's) state
  function showSection(index) {
    experienceCategories.forEach((category, i) => {
      category.classList.toggle("active", i === index);
    });
  }

  // On click listener for left arrow
  document.getElementById("prevBtn").onclick = () => {
    currentIndex =
      currentIndex === 0 ? experienceCategories.length - 1 : currentIndex - 1;
    showSection(currentIndex);
  };

  // On click listener for right arrow
  document.getElementById("nextBtn").onclick = () => {
    currentIndex = (currentIndex + 1) % experienceCategories.length;
    showSection(currentIndex);
  };

  // Show the first section
  showSection(currentIndex);
});

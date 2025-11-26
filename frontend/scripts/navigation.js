// Gather all section tags (i.e. experience categories: languages, databases...)
// under experience-category-container div to an array
document.addEventListener("DOMContentLoaded", () => {
  const experienceCategories = Array.from(
    document.querySelectorAll("#experience-categories-container section")
  );

  let currentIndex = 0;

  // Toggle which experience category to show (index 0–7), only one at a time
  // (affects also the arrows because they are inside the categories)
  function showCategory(index) {
    experienceCategories.forEach((category, i) => {
      category.classList.toggle("active", i === index);
    });
    // Make arrow clicks scroll to top of category
    experienceCategories[index].scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  }

  // Attach listeners to arrows inside each experience category
  // (there are 2 arrows inside each category, 16 total)
  experienceCategories.forEach((category, index) => {
    const prevArrow = category.querySelectorAll(".prev-btn");
    const nextArrow = category.querySelectorAll(".next-btn");

    // On click listener for upper left arrow
    prevArrow[0].addEventListener("click", (event) => {
      event.preventDefault();
      currentIndex = index === 0 ? experienceCategories.length - 1 : index - 1;
      // Go change to previous category
      showCategory(currentIndex);
    });

    // On click listener for upper right arrow
    nextArrow[0].addEventListener("click", (event) => {
      event.preventDefault();
      currentIndex = (index + 1) % experienceCategories.length;
      // Go change to next category
      showCategory(currentIndex);
    });

    // On click listener for lower left arrow
    prevArrow[1].addEventListener("click", (event) => {
      event.preventDefault();
      currentIndex = index === 0 ? experienceCategories.length - 1 : index - 1;
      // Go change to previous category
      showCategory(currentIndex);
    });

    // On click listener for lower right arrow
    nextArrow[1].addEventListener("click", (event) => {
      event.preventDefault();
      currentIndex = (index + 1) % experienceCategories.length;
      // Go change to next category
      showCategory(currentIndex);
    });
  });

  // Show first section on load
  showCategory(currentIndex);
});

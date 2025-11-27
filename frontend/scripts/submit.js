/*
 JobsAI/frontend/scripts/submit.js

 Handles submit button clicks.
*/

function main() {
  // Grab the submit button
  const submitBtn = document.getElementById("submit-btn");

  // On submit button click
  submitBtn.addEventListener("click", () => {
    const result = {};

    // Gather all slider inputs
    document.querySelectorAll(".slider").forEach((slider) => {
      // Get the slider's unique key (e.g. JavaScript)
      const key = slider.dataset.key;
      // Save value under unique key
      result[key] = Number(slider.value);
    });

    // Gather all text inputs
    document.querySelectorAll(".input-field").forEach((input) => {
      // Get the text input's unique key (e.g. Other1)
      const key = input.dataset.key;
      // Save value under unique key
      result[key] = input.value.trim();
    });

    // { JavaScript: 1, HTML/CSS: 2, ... }
    console.log(result);
    // console.log(result.JavaScript);

    // Send to backend
    // fetch("/api/submit", { method: "POST", body: JSON.stringify(result) });
  });
}

document.addEventListener("DOMContentLoaded", main);

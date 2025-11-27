/*
 JobsAI/frontend/scripts/submitter.js

 Handles submit button clicks.
*/

function main() {
  const submitBtn = document.getElementById("submit-btn");

  // Submit button is clicked
  submitBtn.addEventListener("click", () => {
    // The result will be stored as key-value pairs in this object
    // {
    //   javascript: 3,
    //   html-css: 2,
    //   ...
    //   text-field4: "React Native",
    //   ...
    // }
    const result = {};

    // Iterate over all slider questions
    document.querySelectorAll(".slider").forEach((slider) => {
      // Grab the slider's unique key (e.g. "javascript")
      const key = slider.dataset.key;
      // Create a new key to the result object and store the slider's value (e.g. 3) under it
      result[key] = Number(slider.value);
    });

    // Iterate over all text field questions
    document.querySelectorAll(".text-field").forEach((textField) => {
      // Grab the text field's unique key (e.g. "text-field1")
      const key = textField.dataset.key;
      // Create a new key to the result object and store the text field's value (e.g. "React Native") under it
      result[key] = textField.value.trim();
    });

    console.log(result);

    async function myFunc(answers) {
      const response = await fetch("http://localhost:8000/api/endpoint", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(answers),
      });
      //console.log(response.body);
      return response;
    }
    // Send to backend
    const response = myFunc(result);
    response.then((asd) => {
      console.log(asd);
    });
  });
}

document.addEventListener("DOMContentLoaded", main);

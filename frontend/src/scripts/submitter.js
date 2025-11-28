export default function submitter() {
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
        const contentDisposition = response.headers.get("Content-Disposition");
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
      }
    }

    // Send to backend
    downloadDocx(result);
  });
}

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";

import "./styles/index.css";
import "./styles/font.css";

/**
 * Application Entry Point
 *
 * Initializes the React application and mounts it to the DOM.
 * Uses React 19's createRoot API for concurrent rendering.
 *
 * Features:
 * - StrictMode: Enables additional development checks and warnings
 * - Error handling: Throws error if root element not found
 * - Global styles: Imports Tailwind CSS and custom font styles
 */
const rootElement = document.getElementById("root");
if (!rootElement) {
  throw new Error("Root element not found");
}

createRoot(rootElement).render(
  <StrictMode>
    <App />
  </StrictMode>
);

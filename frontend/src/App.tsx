import ErrorBoundary from "./components/ErrorBoundary";
import NavBar from "./components/NavBar";
import Hero from "./components/Hero";
import Search from "./components/Search";
import Contact from "./components/Contact";

import "./styles/App.css";

/**
 * App Component - Root Application Component
 *
 * This is the root component of the JobsAI application. It orchestrates
 * all page sections and provides error boundary protection.
 *
 * Structure:
 * - ErrorBoundary (outer): Catches errors in NavBar, Hero, Contact, or inner ErrorBoundary
 * - NavBar: Fixed navigation bar
 * - Hero: Landing section with title
 * - ErrorBoundary (inner): Isolates Search component errors to prevent full app crash
 * - Search: Main questionnaire and pipeline interface
 * - Contact: Contact information section
 *
 * Error Handling:
 * - Outer ErrorBoundary protects the entire app
 * - Inner ErrorBoundary isolates Search component errors (most complex component)
 * - This prevents Search component errors from crashing the entire application
 */
export default function App() {
  return (
    <ErrorBoundary>
      <NavBar />
      <Hero />
      <ErrorBoundary>
        <Search />
      </ErrorBoundary>
      <Contact />
    </ErrorBoundary>
  );
}

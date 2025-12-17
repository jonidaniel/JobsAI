import ErrorBoundary from "./components/ErrorBoundary";
import NavBar from "./components/NavBar";
import Hero from "./components/Hero";
import Search from "./components/Search";
import Contact from "./components/Contact";

import "./styles/App.css";

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

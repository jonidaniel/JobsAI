import { useEffect } from "react";
import "../styles/nav.css";

/**
 * NavBar Component
 *
 * Renders the main navigation bar with links to different sections.
 * Provides smooth scrolling navigation to Hero, Search, and Contact sections.
 */
export default function NavBar() {
  useEffect(() => {
    // Handle smooth scrolling for navigation links
    const handleNavClick = (e) => {
      const href = e.currentTarget.getAttribute("href");
      if (href && href.startsWith("#")) {
        e.preventDefault();
        const targetId = href.substring(1);
        const targetElement = document.getElementById(targetId);
        if (targetElement) {
          targetElement.scrollIntoView({
            behavior: "smooth",
            block: "start",
          });
        }
      }
    };

    // Attach click handlers to all nav links
    const navLinks = document.querySelectorAll("nav a");
    navLinks.forEach((link) => {
      link.addEventListener("click", handleNavClick);
    });

    // Cleanup
    return () => {
      navLinks.forEach((link) => {
        link.removeEventListener("click", handleNavClick);
      });
    };
  }, []);

  return (
    <nav>
      <a href="#hero">Home</a>
      <a href="#search">Search</a>
      <a href="#contact">Contact</a>
    </nav>
  );
}

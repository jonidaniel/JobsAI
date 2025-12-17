import "../styles/contact.css";

/**
 * Contact Component
 *
 * Renders the contact section with contact information and links.
 * Displays phone number, email, and links to GitHub and LinkedIn.
 */
export default function Contact() {
  return (
    <section id="contact">
      <h2>Contact</h2>
      <h3 className="text-base sm:text-xl md:text-2xl lg:text-3xl font-semibold text-white text-center">
        Feel free to contact us on any channel
      </h3>
      <div className="bg-gray-800 p-4 sm:p-6 md:p-10 rounded-2xl shadow-lg space-y-4 w-full max-w-2xl mx-auto">
        <div className="text-center">
          <a
            href="https://github.com/jonidaniel/jobsai"
            target="_blank"
            rel="noopener noreferrer"
          >
            JobsAI on GitHub
          </a>
        </div>
        <p>+358405882001</p>
        <p>joni-makinen@live.fi</p>

        <div className="text-center">
          <a
            href="https://www.linkedin.com/in/joni-daniel-makinen/"
            target="_blank"
            rel="noopener noreferrer"
          >
            LinkedIn
          </a>
        </div>
      </div>
    </section>
  );
}

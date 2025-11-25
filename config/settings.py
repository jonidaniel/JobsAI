# ---------- SETTINGS ----------

# The job boards to scrape for job listings
JOB_BOARDS = ["Duunitori"]  # Choose from "Duunitori" and "Jobly"
# Deep mode allows deeper scraping of job listings
# If True, the listings are opened individually, i.e., each one is crawled for full job description
DEEP_MODE = True  # Choose from True or False
# The size of the job report
REPORT_SIZE = 10
# The style or tone of the cover letters
LETTER_STYLE = "professional"  # Choose from "professional", "friendly", or "confident"

# The candidate's contact information for the cover letters
CONTACT_INFORMATION = {
    "website": "jonimakinen.com",
    "linkedin": "linkedin.com/in/joni-daniel-makinen",
    "github": "github.com/jonidaniel",
    "email": "joni-makinen@live.fi",
    "phone": "+358405882001",
}

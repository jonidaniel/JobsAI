# ---------- SETTINGS ----------

# The job boards to scrape for job listings
job_boards = ["Duunitori"]  # Choose from "Duunitori" and "Jobly"
# Deep mode allows deeper scraping of job listings
# If True, the listings are opened individually, i.e., each one is crawled for full job description
deep_mode = True  # Choose from True or False
# The size of the job report
report_size = 1
# The style or tone of the cover letters
letter_style = "professional"  # Choose from "professional", "friendly", or "confident"

# The candidate's contact information for the cover letters
contact_information = {
    "website": "jonimakinen.com",
    "linkedin": "linkedin.com/in/joni-daniel-makinen",
    "github": "github.com/jonidaniel",
    "email": "joni-makinen@live.fi",
    "phone": "+358405882001",
}

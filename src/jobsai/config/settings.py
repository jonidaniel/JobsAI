"""
JobsAI Configuration Settings

This module contains all user-configurable settings for the JobsAI system.
Modify these values to customize the behavior of the agent pipeline.
"""

# ---------- SETTINGS ----------

# Job Boards Configuration
# List of job boards to scrape for job listings
# Available options: "Duunitori", "Jobly"
# Add multiple boards to search across multiple platforms
job_boards = ["Duunitori"]  # Choose from "Duunitori" and "Jobly"

# Deep Mode Configuration
# If True: Fetches full job descriptions by visiting each job's detail page
#          More accurate scoring but slower and uses more resources
# If False: Only uses job titles and snippets from search results
#           Faster but less accurate scoring
deep_mode = True  # Choose from True or False

# Report Size Configuration
# Number of top-scoring jobs to include in the job report
# Higher values generate more cover letter instructions but take longer
report_size = 1

# Cover Letter Style Configuration
# Tone/style of generated cover letters
# Options:
#   - "professional": Clear, respectful, concise (default)
#   - "friendly": Warm, positive but still professional
#   - "confident": Confident, proactive without being arrogant
letter_style = "professional"  # Choose from "professional", "friendly", or "confident"

# Contact Information Configuration
# Candidate's contact details to include in cover letters
# These appear at the top-right of the generated document
contact_information = {
    "website": "jonimakinen.com",
    "linkedin": "linkedin.com/in/joni-daniel-makinen",
    "github": "github.com/jonidaniel",
    "email": "joni-makinen@live.fi",
    "phone": "+358405882001",
}

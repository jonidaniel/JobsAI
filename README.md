# JobsAI (0.1.0)

## Description

### An agentic AI system for end-to-end automated job searching and job application document generation: enter your skills and preferences to the system once and get job recommendations and cover letters continuously. Checks input resources consistently and updates search queries autonomously.

## Operating Logic / Workflow

- ### 1. Assesses a candidate's skills and saves them as a _skill profile_

- ### 2. Forms job search keywords based on the profile

- ### 2. Finds relevant job listings by doing web searches

- ### 3. Prioritizes the listings based on relevancy

- ### 4. Writes a report on the findings, with explanations and justifications

- ### 5. Generates résumé and cover letter suggestions based on your skill profile and job requirements

## Project Structure

`/agents/` This is where agents are located

`/data/` This is where outputted data, like job listings and cover letter recommendations, are stored

`/memory/vector_db/` This is where the candidate's skill profile is stored

`/tests/` This is where tests, like HTML files simulating job listing sites, are located

`/utils/` This is where utilities, like normalization functions and scraper scripts, are stored

## Technologies

JobsAI is built using [Python](), [LangChain]()

JobsAI requires minimum Python3.12 for it to work.

## Setup

JobAI was developed with `uv` package manager and we strongly recommend using it for running the system

Download `uv` and go to the project's root directory and run `uv sync` to install dependencies

Then run `uv run main.py` to run JobAI

## Agent Architecture

### Entails 7 agents arranged in a _prompt chaining architecture_, each agent with predefined purposes and responsibilities:

1. Skill Assessment agent `/agents/skill_assessor.py`

   - Assesses a candidate's skillset

2. Searcher agent `/agents/searcher.py`

   - Searches relevant job listing based on the assessment

3. Scorer agent `/agents/scorer.py`

   - Scorer the job listings based on relevancy

4. Planner agent `/agents/planner.py`

   - Plans...

5. Reporter agent `/agents/reporter.py`

   - Writes a report...

6. Generator agent `/agents/generator.py`

   - Generates suggestions for résumés and cover letters

7. Notifier agent `/agents/notifier.py`

   - Notifies the candidate of new job opportunities

## Author

© 2025 Joni Mäkinen

# Development Diary

### 2025/11/18

- Initiated the project
- Fed the initial project idea of an autonomous job seeker system to a chat model and started refining it
- Carved out an implementation roadmap with about a dozen phases
- Defined the projects' scope and goals, its tech stack, and the agents' roles
- Initiated a remote repo for the project and started making commits
- Initiated a uv project and defined a directory structure
- Defined the Skill Assessment agent
- Started building the agent and related modules
- Did integration tests on the agent
- Initiated the Development Diary

### 2025/11/19

- Added docstrings to SkillAssessor functions
- Did more integration tests on Skill Assessment agent
- Finished the agent
- Defined the Searcher agent
- Started to develop the agent
- Developed a query builder (/utils/query_builder.py)
- Did integration tests on the query builder
- Developed first job listing site scraper (Duunitori)
- Wrote a handful of sections to the project's main README file
- Tested the Duunitori scraper
- Did more tests on the query builder
- Started to develop the Scorer agent

### 2025/11/20

- Finished the scorer agent
- Started to develop the Reporter agent
- Optimized/refactored the current workflow

### 2025/11/21

- Continued optimizing/refactoring the workflow
- Made big refactors to /config/
- Refined logging
- Refined class and function documentation
- Started creating the reporter agent

### 2025/11/22

- Made the reporter agent work
- Continued optimizing/refactoring the workflow
- Refined logging
- Refined class and function documentation

### 2025/11/23

- Started creating the generator agent
- Continued optimizing/refactoring the workflow
- Refined logging
- Refined class and function documentation

### 2025/11/24

- Continued working with the generator agent
- Made huge refactors to /utils/
- Refined class and function documentation

### 2025/11/25

- Made the generator agent somewhat work
- Implemented versioned skill profile, raw jobs, scored jobs, and job report saving
- Implemented dated file storing throughout the whole workflow

### 2025/11/26

- Refined reporter agent, now it builds honed cover letter writing instructions for generator agent
- Made a massive refactor, now the project structure looks really good
- Built the project UI up until the point where a clean result object is retrieved after submit button click

### 2025/11/27

- Made the frontend concise and intuitive
- Implemented a FastAPI HTTP server
- Integrated frontend to backend server, now when frontend submit button is clicked, request travels to FastAPI server, server initiates backend agent logic, then response is sent back to frontend

### 2025/11/28

- Converted old plain HTML frontend to identical React frontend
- Refined the UI so that a more higher quality and more appropriate JSON string is sent to the backend
- Made the backend pipeline return a real Document object (.docx) back to Fast API server
- Made the server endpoint respond to frontend with a Response object (.docx), now everything starting from doing selections and clicking 'submit' in the UI and ending to the browser receiving a pre-written and downloadable Word document cover letter works fast and pretty accurately

### 2025/11/29

- Improved the question sets and the arrows

### 2025/11/30

- Designed the first nice look for the UI, picked two different fonts and applied them to the the page. Worked on the frontend payload structuring and sending

### 2025/12/1

- Improved the frontend payload structuring and sending

### 2025/12/2

- Honed form value validations in the frontend and Pydantic validation model in the backend.

### 2025/12/3

- Made the transition from clicking 'Find Jobs' to showing 'Again' button, also clicking 'Again' and then ending up on a new form
- Changed the way of passing data between agents to _in-memory_, instead of saving data in files and then loading it in the next agent
- Designed and partly implemented changes to agent's responsibilities
- Started planning removing 'skill_profile' and making agents communicate with strings instead of SkillProfiles.

### 2025/12/4

- Finished the transformation of using LLM-generated candidate profile text instead of SkillProfiles as profile
- Finished the transformation of creating search keywords with an LLM instead of doing it deterministically.

### 2025/12/5

- Implemented Server-Sent Events (SSE) with separate POST endpoint to allow users to see pipeline progress and to cancel it, if necessary

### 2025/12/6–10

- Gained understanding on transferring the frontend to an AWS S3 bucket and backend to AWS Lambda, and how GitHub Actions would automate my development workflow

### 2025/12/11

- Transferred the frontend and backend to AWS
- Set up GitHub Actions to automatically update S3 frontend and Lambda backend on pushes to main branch

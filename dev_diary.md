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

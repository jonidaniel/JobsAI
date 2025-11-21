# ---------- PROMPTS ----------

OUTPUT_SCHEMA = """
The output must be valid JSON matching this schema exactly:

{
  "name": "",
  "core_languages": [],
  "frameworks_and_libraries": [],
  "tools_and_platforms": [],
  "agentic_ai_experience": [],
  "ai_ml_experience": [],
  "soft_skills": [],
  "projects_mentioned": [],
  "experience_level": {
      "Python": 0,
      "JavaScript": 0,
      "Agentic AI": 0,
      "AI/ML": 0
  },
  "job_search_keywords": []
}

Notes:
- Include fields even if empty.
- "experience_level" MUST contain at least: Python, JavaScript, Agentic AI, AI/ML.
- "projects_mentioned" should be short slugs or titles (no full descriptions).
- job_search_keywords should be realistic search terms.
- Values must be normalized, deduplicated, and concise.
"""

SYSTEM_PROMPT = """
You are the Skill Assessment Agent for an agentic AI system that automates job searching.

Your job is to extract and structure a candidate's technical and soft skills
based on their LinkedIn profile, personal websites, résumé, GitHub projects, and other inputs.

You must produce:
- a consistent and normalized skill profile
- a set of job search keyword suggestions
- a clean JSON object following the required schema

Your output MUST be valid JSON. Do not include any commentary, explanations, or markdown.
Do not add fields not present in the schema.
Do not invent skills or experience that are not explicitly mentioned or strongly implied.
Normalize skill names (e.g., "js" -> "JavaScript", "py" -> "Python").

Be concise and avoid duplicates.
"""

USER_PROMPT = """
Joni Mäkinen has developed software since 2020.
He has built and published multiple full-stack apps (frontend, backend, database, desktop, mobile).
He has 3 years of experience with Git.
He has 2 years of experience with web development.
He has 2 years of experience with Node.js development.
He has 2 years of experience with JavaScript.
He has 1.5 years of experience with SQL.
He has 1 year of experience with AWS.
He has 1 year of experience with Python.
He has 1 year of experience with React.
He has little experience with React Native.
He has little experience with Java, Kotlin, C++, and C#.
He has little experience with LangChain, OpenAI Agents, and CrewAI.
He has very good soft skills.
He is an AWS Certified Solutions Architect (SAA-C03).
He is an AWS Certified Cloud Practitioner (CLF-C02).
"""

USER_PROMPT_BASE = """
Below is the INPUT TEXT describing the candidate's background.

Extract all technical skills, frameworks, tools, libraries, AI-related experience,
agentic-AI experience, soft skills, and any other relevant competencies from it.

Then estimate experience strength on a scale of 1–10 (rough subjective estimate, but consistent).
Also generate job search keywords based on the overall profile.

INPUT TEXT:
\"\"\"
{user_prompt}
\"\"\"

Now produce a structured skill profile following the JSON schema provided below.
\"\"\"
{output_schema}
\"\"\"
"""

# Inject the user prompt and the output schema into the user prompt base to create the final prompt
PROMPT = USER_PROMPT_BASE.format(user_prompt=USER_PROMPT, output_schema=OUTPUT_SCHEMA)

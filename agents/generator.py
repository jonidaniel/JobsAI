# ---------- GENERATOR AGENT ----------

# ✔ Accepts both the merged SkillProfile and the report text
# ✔ Calls the LLM to produce a tailored job-application email, cover letter, or motivation letter
# ✔ Can be later extended to generate CV sections, project summaries, etc.
# ✔ Uses the same internal structure and design conventions as your other agents
# ✔ Returns the generated text to main.py, where NotifierAgent or others can use it

import logging
from typing import Optional

from utils import call_llm  # BUILD THIS !!!
from utils import normalize_text # BUILD THIS !!!

from config.schemas import SkillProfile

logger = logging.getLogger(__name__)

class GeneratorAgent:
    """
    Generates human-quality output based on:
    - the skill profile
    - the job analysis report
    - optional job-specific context (e.g., job title or employer)

    Typical generation targets:
    - job application email
    - cover letter
    - motivation/explanation of fit
    """

    def __init__(self, model: str = "gpt-4.1"):
        self.model = model

    # ------------------------------
    # Public interface
    # ------------------------------
    def generate_application(
        self,
        skill_profile: SkillProfile,
        job_report: str,
        employer: Optional[str] = None,
        job_title: Optional[str] = None,
        style: str = "professional"
        ) -> str:
        """
        Produce a tailored job-application message based on
        the candidate's skills and the job report.

        Returns:
            output: the generated text
        """

        system_prompt = self._build_system_prompt(style)
        user_prompt = self._build_user_prompt(skill_profile, job_report, employer, job_title)

        logger.info(" Generating application text...")

        raw = call_llm(user_prompt, system_prompt, model=self.model)

        output = normalize_text(raw)

        logger.info(" Application text generated.\n")

        return output

    # ------------------------------
    # Internal functions
    # ------------------------------

    def _build_system_prompt(self, style: str) -> str:
        """
        System prompt defines *how* the assistant writes.
        """

        tone_instructions = {
            "professional": (
                "Write in a clear, respectful, concise, professional tone. "
                "Use well-structured paragraphs. Avoid exaggerations."
                ),
                "friendly": (
                    "Write in a warm, positive tone but keep it professional."
                    ),
                    "confident": (
                        "Write with a confident, proactive tone without sounding arrogant."
                        ),
                        }

        base_style = tone_instructions.get(style, tone_instructions["professional"])

        return (
            "You are a professional job-application generator. "
            "Your goal is to produce polished text suitable for real-world job applications.\n"
            "Follow this style:\n"
            f"{base_style}\n"
            )

    def _build_user_prompt(
        self,
        skill_profile: SkillProfile,
        job_report: str,
        employer: Optional[str],
        job_title: Optional[str]
        ) -> str:
        """
        Constructs the full user prompt including:
        - candidate skills
        - job analysis report
        - optional job title / employer info

        Args:
            skill_profile: 
            job_report: 
            employer: 
            job_title: 

        Returns:
            "
            Generate a tailored job-application message.

            Candidate Skill Profile (JSON):
            {skill_profile.model_dump_json(indent=2)}

            Job Match Analysis:
            {job_report}

            {employer_text}{title_text}

            Instructions:
            - Produce a compelling but concise job-application message.
            - Highlight the candidate's relevant skills based on the report.
            - If employer or job title are given, tailor the message to them.
            - Keep it truthful, specific, and readable.
            "
        """

        employer_text = f"Employer: {employer}\n" if employer else ""
        title_text = f"Target job title: {job_title}\n" if job_title else ""

        return f"""
            Generate a tailored job-application message.

            Candidate Skill Profile (JSON):
            {skill_profile.model_dump_json(indent=2)}

            Job Match Analysis:
            {job_report}

            {employer_text}{title_text}

            Instructions:
            - Produce a compelling but concise job-application message.
            - Highlight the candidate’s relevant skills based on the report.
            - If employer or job title are given, tailor the message to them.
            - Keep it truthful, specific, and readable.
            """

# ---------- GENERATOR AGENT ----------

# generate_letters
# _build_system_prompt
# _build_system_prompt

import logging
from typing import Optional

from utils.llms import call_llm
from utils.normalization import normalize_text

from config.schemas import SkillProfile

logger = logging.getLogger(__name__)


class GeneratorAgent:
    """
    Generate cover letter.
    """

    def __init__(self):
        """
        Construct the GeneratorAgent class.
        """

    # ------------------------------
    # Public interface
    # ------------------------------
    def generate_letters(
        self,
        skill_profile: SkillProfile,
        job_report: str,
        employer: Optional[str] = None,
        job_title: Optional[str] = None,
        style: str = "professional",
    ) -> str:
        """
        Produce a tailored job-application message based on
        the candidate's skills and the job report.

        Args:
            skill_profile:
            job_report:
            employer:
            job_title:
            style:

        Returns:
            output: the generated text
        """

        system_prompt = self._build_system_prompt(style)
        user_prompt = self._build_user_prompt(
            skill_profile, job_report, employer, job_title
        )

        logger.info(" GENERATING APPLICATION TEXT...")

        raw = call_llm(system_prompt, user_prompt)

        output = normalize_text(raw)

        logger.info(" APPLICATION TEXT GENERATION COMPLETED\n")

        return output

    # ------------------------------
    # Internal functions
    # ------------------------------

    def _build_system_prompt(self, style: str) -> str:
        """
        Build system prompt.

        Args:
            style:
        """

        tone_instructions = {
            "professional": (
                "Write in a clear, respectful, concise, professional tone. "
                "Use well-structured paragraphs. Avoid exaggerations."
            ),
            "friendly": ("Write in a warm, positive tone but keep it professional."),
            "confident": (
                "Write with a confident, proactive tone without sounding arrogant."
            ),
        }

        base_style = tone_instructions.get(style, tone_instructions["professional"])

        return (
            "You are a professional cover letter writer. "
            "Your goal is to produce polished text suitable for real-world job applications.\n"
            "Follow this style:\n"
            f"{base_style}\n"
        )

    def _build_user_prompt(
        self,
        skill_profile: SkillProfile,
        job_report: str,
        employer: Optional[str],
        job_title: Optional[str],
    ) -> str:
        """
        Build user prompt.

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

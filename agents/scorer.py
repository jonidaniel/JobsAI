import logging
from typing import List, Dict
from utils.normalization import normalize_list
from agents.skill_assessor import SkillProfile

# Logging configuration
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ScorerAgent:
    def __init__(self, weight_agentic_ai: float = 2.0):
        """
        Initialize the ScorerAgent.

        Args:
            weight_agentic_ai: Multiplier for agentic AI / LLM skills to prioritize them.
        """
        self.weight_agentic_ai = weight_agentic_ai

    def score_jobs(self, job_listings: List[Dict], skill_profile: SkillProfile) -> List[Dict]:
        """
        Score and rank job listings based on the candidate's skills.

        Args:
            job_listings: List of job dicts from Searcher.
            skill_profile: SkillProfile object from SkillAssessor.

        Returns:
            List of job dicts with added fields:
                - score
                - matched_skills
                - missing_skills
        """
        scored_jobs = []
        # Gather all keywords from the skill profile
        profile_keywords = set(
            normalize_list(skill_profile.core_languages)
            + normalize_list(skill_profile.agentic_ai_experience)
            + normalize_list(skill_profile.ai_ml_experience)
            + normalize_list(skill_profile.job_search_keywords)
        )

        for job in job_listings:
            # Normalize job text
            text = " ".join([
                job.get("title", ""),
                job.get("description_snippet", ""),
                job.get("full_description", "")
            ]).lower()

            # Match keywords
            matched = [kw for kw in profile_keywords if kw.lower() in text]
            missing = [kw for kw in profile_keywords if kw.lower() not in text]

            # Base score
            if profile_keywords:
                score = len(matched) / len(profile_keywords) * 100
            else:
                score = 0

            # Weight agentic AI / LLM skills
            agentic_keywords = normalize_list(skill_profile.agentic_ai_experience)
            agentic_matches = sum(1 for kw in agentic_keywords if kw.lower() in text)
            if agentic_keywords:
                score += (agentic_matches / len(agentic_keywords)) * 100 * (self.weight_agentic_ai - 1)

            # Experience level adjustment (simple heuristic)
            title = job.get("title", "").lower()
            if "junior" in title or "entry level" in title:
                score *= 1.1  # boost junior-friendly jobs
            if "senior" in title or "lead" in title:
                score *= 0.9  # penalize senior roles

            # Cap score to 100
            score = min(100, round(score, 2))

            # Enrich job dict
            job_copy = job.copy()
            job_copy.update({
                "score": score,
                "matched_skills": matched,
                "missing_skills": missing
            })
            scored_jobs.append(job_copy)

        # Sort descending by score
        scored_jobs.sort(key=lambda x: x["score"], reverse=True)
        logger.info("Scored %d jobs", len(scored_jobs))
        return scored_jobs

    def save_scored_jobs(self, scored_jobs: List[Dict], path: str):
        """
        Save scored jobs to JSON file.

        Args:
            scored_jobs: List of scored job dicts.
            path: File path to save.
        """
        import json
        import os

        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(scored_jobs, f, ensure_ascii=False, indent=2)
        logger.info("Saved %d scored jobs to %s", len(scored_jobs), path)


# ---------- SIMPLE CLI USAGE ----------
if __name__ == "__main__":
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Score job listings based on skills.")
    parser.add_argument("job_json", help="Path to raw job listings JSON")
    parser.add_argument("profile_json", help="Path to SkillProfile JSON")
    parser.add_argument("--output", default="data/job_listings/scored_jobs.json", help="Path to save scored jobs")
    args = parser.parse_args()

    import json

    jobs = json.loads(Path(args.job_json).read_text(encoding="utf-8"))
    profile_data = json.loads(Path(args.profile_json).read_text(encoding="utf-8"))

    from agents.skill_assessor import SkillProfile
    profile = SkillProfile(**profile_data)

    scorer = ScorerAgent()
    scored = scorer.score_jobs(jobs, profile)
    scorer.save_scored_jobs(scored, args.output)

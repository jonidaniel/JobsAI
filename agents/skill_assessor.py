class SkillAssessor:
    def __init__(self, llm_client, memory_path):
        self.llm = llm_client
        self.memory_path = memory_path

    def assess(self, text_input: str) -> dict:
        """Call the LLM to parse skills and return structured profile."""
        print("In assess")

    def save(self, profile: dict):
        """Save profile to memory (JSON)."""
        print("In save")

    def load_existing(self) -> dict | None:
        """Load profile if it exists."""
        print("In load_existing")

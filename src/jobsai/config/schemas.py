# ---------- SCHEMAS ----------

from typing import List, Dict, Any, Union
from enum import Enum

from pydantic import BaseModel, Field, model_validator, field_validator, ConfigDict

# ----- MAPPING -----

# For mapping experience strings to numeric values (frontend payload has numeric values)
EXPERIENCE_ALIAS_MAP = {
    1: "less than half a year",
    2: "less than a year",
    3: "less than 1.5 years",
    4: "less than 2 years",
    5: "less than 2.5 years",
    6: "less than 3 years",
    7: "over 3 years",
}

SKILL_ALIAS_MAP = {
    "py": "Python",
    "python3": "Python",
    "python": "Python",
    "js": "JavaScript",
    "node": "Node.js",
    "nodejs": "Node.js",
    "reactjs": "React",
    "fastapi": "FastAPI",
    "flask": "Flask",
    "postgres": "PostgreSQL",
    "sql": "SQL",
}

# For mapping frontend payload keys to proper terms
SUBMIT_ALIAS_MAP = {
    "javascript": "JavaScript",
    "html-css": "HTML/CSS",
    "sql": "SQL",
    "python": "Python",
    "bash-shell": "Bash/Shell",
    "typescript": "TypeScript",
    "csharp": "C#",
    "java": "Java",
    "powershell": "PowerShell",
    "cplusplus": "C++",
    "c": "C",
    "php": "PHP",
    "go": "Go",
    "rust": "Rust",
    "kotlin": "Kotlin",
    "lua": "Lua",
    "ruby": "Ruby",
    "dart": "Dart",
    "assembly": "Assembly",
    "swift": "Swift",
    "groovy": "Groovy",
    "visual-basic-dotnet": "Visual Basic (.Net)",
    "perl": "Perl",
    "r": "R",
    "vba": "VBA",
    "gdscript": "GDScript",
    "scala": "Scala",
    "elixir": "Elixir",
    "matlab": "MATLAB",
    "delphi": "Delphi",
    "lisp": "Lisp",
    "zig": "Zig",
    "micropython": "MicroPython",
    "erlang": "Erlang",
    "fsharp": "F#",
    "ada": "Ada",
    "gleam": "Gleam",
    "fortran": "Fortran",
    "ocaml": "OCaml",
    "prolog": "Prolog",
    "cobol": "COBOL",
    "mojo": "Mojo",
    "postgresql": "PostgreSQL",
    "mysql": "MySQL",
    "sqlite": "SQLite",
    "microsoft-sql-server": "Microsoft SQL Server",
    "redis": "Redis",
    "mongodb": "MongoDB",
    "mariadb": "MariaDB",
    "elasticsearch": "Elasticsearch",
    "dynamodb": "Dynamodb",
    "oracle": "Oracle",
    "bigquery": "BigQuery",
    "supabase1": "Supabase",
    "cloud-firestore": "Cloud Firestore",
    "h2": "H2",
    "cosmos-db": "Cosmos DB",
    "firebase-realtime-database": "Firebase Realtime Database",
    "snowflake": "Snowflake",
    "microsoft-access": "Microsoft Access",
    "influxdb": "InfluxDB",
    "duckdb": "DuckDB",
    "databricks-sql": "Databricks SQL",
    "cassandra": "Cassandra",
    "neo4j": "Neo4J",
    "clickhouse": "Clickhouse",
    "valkey": "Valkey",
    "amazon-redshift": "Amazon Redshift",
    "ibm-db2": "IBM DB2",
    "cockroachdb": "Cockroachdb",
    "pocketbase": "Pocketbase",
    "datomic": "Datomic",
    "docker": "Docker",
    "npm": "npm",
    "amazon-web-services-aws": "Amazon Web Services (AWS)",
    "pip": "Pip",
    "kubernetes": "Kubernetes",
    "microsoft-azure": "Microsoft Azure",
    "vite": "Vite",
    "homebrew": "Homebrew",
    "google-cloud": "Google Cloud",
    "yarn": "Yarn",
    "make": "Make",
    "nuget": "NuGet",
    "webpack": "Webpack",
    "cloudflare": "Cloudflare",
    "terraform": "Terraform",
    "apt": "APT",
    "maven-build-tool": "Maven (build tool)",
    "gradle": "Gradle",
    "pnpm": "pnpm",
    "cargo": "Cargo",
    "firebase": "Firebase",
    "prometheus": "Prometheus",
    "msbuild": "MSBuild",
    "composer": "Composer",
    "ansible": "Ansible",
    "digital-ocean": "Digital Ocean",
    "podman": "Podman",
    "chocolatey": "Chocolatey",
    "vercel": "Vercel",
    "datadog": "Datadog",
    "poetry": "Poetry",
    "pacman": "Pacman",
    "netlify": "Netlify",
    "heroku": "Heroku",
    "bun": "Bun",
    "supabase2": "Supabase",
    "ninja": "Ninja",
    "splunk": "Splunk",
    "new-relic": "New Relic",
    "railway": "Railway",
    "ibm-cloud": "IBM Cloud",
    "yandex-cloud": "Yandex Cloud",
    "nodejs": "Node.js",
    "react": "React",
    "jquery": "jQuery",
    "nextjs": "Next.js",
    "aspdotnet-core": "ASP.NET Core",
    "express": "Express",
    "angular": "Angular",
    "vuejs": "Vue.js",
    "spring-boot": "Spring Boot",
    "fastapi": "FastAPI",
    "aspdotnet": "ASP.NET",
    "flask": "Flask",
    "wordpress": "WordPress",
    "django": "Django",
    "laravel": "Laravel",
    "blazor": "Blazor",
    "angularjs": "AngularJS",
    "nestjs": "NestJS",
    "svelte": "Svelte",
    "ruby-on-rails": "Ruby on Rails",
    "astro": "Astro",
    "symfony": "Symfony",
    "nuxtjs": "Nuxt.js",
    "deno": "Deno",
    "fastify": "Fastify",
    "axum": "Axum",
    "phoenix": "Phoenix",
    "drupal": "Drupal",
    "visual-studio-code": "Visual Studio Code",
    "visual-studio": "Visual Studio",
    "intellij-idea": "IntelliJ IDEA",
    "notepadplusplus": "Notepad++",
    "vim": "Vim",
    "cursor": "Cursor",
    "android-studio": "Android Studio",
    "pycharm": "PyCharm",
    "neovim": "Neovim",
    "jupyter-nb-jupyterlab": "Jupyter Nb/JupyterLab",
    "nano": "Nano",
    "xcode": "Xcode",
    "sublime-text": "Sublime Text",
    "claude-code": "Claude Code",
    "webstorm": "WebStorm",
    "rider": "Rider",
    "zed": "Zed",
    "eclipse": "Eclipse",
    "phpstorm": "PhpStorm",
    "vscodium": "VSCodium",
    "windsurf": "Windsurf",
    "rustrover": "RustRover",
    "lovabledotdev": "Lovable.dev",
    "bolt": "Bolt",
    "cline-and-or-roo": "Cline and/or Roo",
    "aider": "Aider",
    "trae": "Trae",
    "openai-gpt": "OpenAI GPT",
    "claude-sonnet": "Claude Sonnet",
    "gemini-flash": "Gemini Flash",
    "openai-reasoning": "OpenAI Reasoning",
    "openai-image": "OpenAI Image",
    "gemini-reasoning": "Gemini Reasoning",
    "deepseek-reasoning": "DeepSeek Reasoning",
    "meta-llama": "Meta Llama",
    "deepseek-general": "DeepSeek General",
    "x-grok": "X Grok",
    "mistral": "Mistral",
    "perplexity-sonar": "Perplexity Sonar",
    "alibaba-qwen": "Alibaba Qwen",
    "microsoft-phi-4-models": "Microsoft Phi-4 models",
    "amazon-titan-models": "Amazon Titan models",
    "cohere-command-a": "Cohere: Command A",
    "reka-flash3-or-other-reka-models": "Reka (Flash 3 or other Reka models)",
    "github": "GitHub",
    "jira": "Jira",
    "gitlab": "GitLab",
    "confluence": "Confluence",
    "markdown-file": "Markdown File",
    "azure-devops": "Azure Devops",
    "notion": "Notion",
    "obsidian": "Obsidian",
    "miro": "Miro",
    "google-workspace": "Google Workspace",
    "trello": "Trello",
    "wikis": "Wikis",
    "lucid-includes-lucidchart": "Lucid (includes Lucidchart)",
    "google-colab": "Google Colab",
    "asana": "Asana",
    "doxygen": "Doxygen",
    "clickup": "Clickup",
    "linear": "Linear",
    "redmine": "Redmine",
    "mondaydotcom": "Monday.com",
    "youtrack": "YouTrack",
    "airtable": "Airtable",
    "stack-overflow-for-teams": "Stack Overflow for Teams",
    "microsoft-planner": "Microsoft Planner",
    "coda": "Coda",
    "windows": "Windows",
    "macos": "MacOS",
    "android": "Android",
    "ubuntu": "Ubuntu",
    "ios": "iOS",
    "linux-non-wsl": "Linux (non-WSL)",
    "windows-subsystem-for-linux-wsl": "Windows Subsystem for Linux (WSL)",
    "debian": "Debian",
    "arch": "Arch",
    "ipados": "iPadOS",
    "fedora": "Fedora",
    "red-hat": "Red Hat",
    "nixos": "NixOS",
    "pop-os": "Pop!_OS",
    "chromeos": "ChromeOS",
}

# ----- PROMPTING -----

OUTPUT_SCHEMA = """{
  "name": STRING VALUE,
  "core_languages": [STRING VALUE(S)],
  "frameworks_and_libraries": [STRING VALUE(S)],
  "tools_and_platforms": [STRING VALUE(S)],
  "agentic_ai_experience": [STRING VALUE(S)],
  "ai_ml_experience": [STRING VALUE(S)],
  "soft_skills": [STRING VALUE(S)],
  "projects_mentioned": [STRING VALUE(S)],
  "experience_level": {
      "Python": INTEGER VALUE,
      "JavaScript": INTEGER VALUE,
      "Agentic AI": INTEGER VALUE,
      "AI/ML": INTEGER VALUE
  },
  "job_search_keywords": [STRING VALUE(S)]
}"""

# ----- PYDANTIC -----


class ExperienceLevels(BaseModel):
    """
    Experience level ratings for key technology areas.

    Values represent years of experience on a scale:
    - 0: No experience
    - 1: Less than half a year
    - 2: Less than a year
    - 3: Less than 1.5 years
    - 4: Less than 2 years
    - 5: Less than 2.5 years
    - 6: Less than 3 years
    - 7: Over 3 years

    Fields use aliases to support both Python naming conventions and
    display-friendly names (e.g., "Agentic AI" contains a space).
    """

    Python: int = 0
    JavaScript: int = 0
    Agentic_Ai: int = Field(0, alias="Agentic AI")
    AI_ML: int = Field(0, alias="AI/ML")

    class Config:
        """
        Pydantic model configuration.

        validate_by_name: Allows access by both field name and alias
        json_schema_extra: Example values for API documentation
        """

        validate_by_name = True
        json_schema_extra = {
            "example": {"Python": 7, "JavaScript": 6, "Agentic AI": 5, "AI/ML": 4}
        }


class SkillProfile(BaseModel):
    """
    A candidate's comprehensive skill profile.

    This is the central data structure that represents a candidate's skills,
    experience, and qualifications. It's created by the ProfilerAgent from
    form submissions and used throughout the pipeline for:
    - Generating job search queries
    - Scoring job relevancy
    - Writing personalized cover letters

    All list fields are automatically deduplicated and normalized during processing.
    """

    name: str = ""  # Candidate's name (optional)
    core_languages: List[str] = []  # Programming languages (Python, JavaScript, etc.)
    frameworks_and_libraries: List[str] = (
        []
    )  # Frameworks and libraries (React, FastAPI, etc.)
    tools_and_platforms: List[str] = []  # Tools and platforms (Docker, AWS, etc.)
    agentic_ai_experience: List[str] = []  # Agentic AI tools/technologies
    ai_ml_experience: List[str] = []  # AI/ML technologies and tools
    soft_skills: List[str] = []  # Soft skills (communication, teamwork, etc.)
    projects_mentioned: List[str] = []  # Project names/titles mentioned
    experience_level: ExperienceLevels = Field(
        default_factory=ExperienceLevels
    )  # Experience ratings
    job_search_keywords: List[str] = []  # Additional keywords for job searching

    class Config:
        """
        Pydantic model configuration.

        validate_by_name: Allows access by both field name and alias
        """

        validate_by_name = True


# ----- FRONTEND PAYLOAD VALIDATION -----

# Valid question set names (kebab-case)
VALID_QUESTION_SETS = {
    "general",
    "languages",
    "databases",
    "cloud-development",
    "web-frameworks",
    "dev-ides",
    "llms",
    "doc-and-collab",
    "operating-systems",
    "additional-info",
}

# Valid general question keys
VALID_GENERAL_KEYS = {
    "job-level",
    "job-boards",
    "deep-mode",
    "cover-letter-num",
    "cover-letter-style",
}

# Valid job level options
VALID_JOB_LEVELS = {"Expert-level", "Expert", "Intermediate", "Entry", "Intern"}

# Valid job board options
VALID_JOB_BOARDS = {"Duunitori", "Jobly"}

# Valid deep mode options
VALID_DEEP_MODE = {"Yes", "No"}

# Valid cover letter count options
VALID_COVER_LETTER_NUM = {"1", "2", "3", "4", "5", "6", "7", "8", "9", "10"}

# Valid cover letter style options
VALID_COVER_LETTER_STYLE = {"Professional", "Friendly", "Confident", "Funny"}


class GeneralQuestionItem(BaseModel):
    """
    Validates a single general question item (single-key dictionary).

    Examples:
        {"job-level": ["Expert", "Intermediate"]}
        {"deep-mode": "Yes"}
    """

    @model_validator(mode="before")
    @classmethod
    def validate_single_key_dict(cls, data: Any) -> Dict[str, Any]:
        """Ensure the item is a single-key dictionary."""
        if not isinstance(data, dict):
            raise ValueError("General question item must be a dictionary")
        if len(data) != 1:
            raise ValueError(
                "General question item must contain exactly one key-value pair"
            )
        return data

    @field_validator("*", mode="before")
    @classmethod
    def validate_value_type(cls, v: Any, info) -> Any:
        """Validate the value type based on the key."""
        key = list(info.data.keys())[0] if isinstance(info.data, dict) else None

        if key == "job-level":
            if not isinstance(v, list) or len(v) == 0:
                raise ValueError(
                    "job-level must be a non-empty array with at least one option"
                )
            if len(v) > 2:
                raise ValueError("job-level must contain at most 2 options")
            invalid = [x for x in v if x not in VALID_JOB_LEVELS]
            if invalid:
                raise ValueError(
                    f"Invalid job-level options: {invalid}. Valid options: {VALID_JOB_LEVELS}"
                )
            # If 2 options selected, they must be adjacent
            if len(v) == 2:
                valid_pairs = [
                    {"Expert-level", "Intermediate"},
                    {
                        "Expert",
                        "Intermediate",
                    },  # Also accept "Expert" for backward compatibility
                    {"Intermediate", "Entry"},
                    {"Entry", "Intern"},
                ]
                option_set = set(v)
                if not any(option_set == pair for pair in valid_pairs):
                    raise ValueError(
                        "If selecting two job levels, they must be adjacent "
                        "(Expert-level + Intermediate, Intermediate + Entry, or Entry + Intern)"
                    )
        elif key == "job-boards":
            if not isinstance(v, list) or len(v) == 0:
                raise ValueError(
                    "job-boards must be a non-empty array with at least one option"
                )
            invalid = [x for x in v if x not in VALID_JOB_BOARDS]
            if invalid:
                raise ValueError(
                    f"Invalid job-board options: {invalid}. Valid options: {VALID_JOB_BOARDS}"
                )
        elif key == "deep-mode":
            if not isinstance(v, str) or v not in VALID_DEEP_MODE:
                raise ValueError(f"deep-mode must be one of: {VALID_DEEP_MODE}")
        elif key == "cover-letter-num":
            if not isinstance(v, str) or v not in VALID_COVER_LETTER_NUM:
                raise ValueError(
                    f"cover-letter-num must be one of: {VALID_COVER_LETTER_NUM}"
                )
        elif key == "cover-letter-style":
            if not isinstance(v, list) or len(v) == 0:
                raise ValueError(
                    "cover-letter-style must be a non-empty array with at least one option"
                )
            if len(v) > 2:
                raise ValueError("cover-letter-style must contain at most 2 options")
            invalid = [x for x in v if x not in VALID_COVER_LETTER_STYLE]
            if invalid:
                raise ValueError(
                    f"Invalid cover-letter-style options: {invalid}. Valid options: {VALID_COVER_LETTER_STYLE}"
                )
        else:
            raise ValueError(
                f"Invalid general question key: {key}. Valid keys: {VALID_GENERAL_KEYS}"
            )

        return v

    model_config = ConfigDict(
        extra="allow"
    )  # Allow dynamic keys since we validate structure in model_validator


class TechnologySetItem(BaseModel):
    """
    Validates a single technology set item (single-key dictionary).

    Examples:
        {"javascript": 5}  # Slider value (0-7)
        {"text-field1": "Additional languages..."}  # Text field (string)
    """

    @model_validator(mode="before")
    @classmethod
    def validate_single_key_dict(cls, data: Any) -> Dict[str, Any]:
        """Ensure the item is a single-key dictionary."""
        if not isinstance(data, dict):
            raise ValueError("Technology set item must be a dictionary")
        if len(data) != 1:
            raise ValueError(
                "Technology set item must contain exactly one key-value pair"
            )
        return data

    @field_validator("*", mode="before")
    @classmethod
    def validate_value_type(cls, v: Any, info) -> Any:
        """Validate the value type based on the key."""
        key = list(info.data.keys())[0] if isinstance(info.data, dict) else None

        if key and key.startswith("text-field"):
            # Text field: must be a string (can be empty for optional fields)
            if not isinstance(v, str):
                raise ValueError(f"Text field '{key}' must be a string")
            # Validate length: max 50 characters
            if len(v) > 50:
                raise ValueError(
                    f"Text field '{key}' must be at most 50 characters, got {len(v)}"
                )
        else:
            # Slider value: must be an integer 0-7
            if not isinstance(v, int) or v < 0 or v > 7:
                raise ValueError(
                    f"Slider value for '{key}' must be an integer between 0 and 7, got: {v}"
                )

        return v

    model_config = ConfigDict(
        extra="allow"
    )  # Allow dynamic keys since we validate structure in model_validator


class AdditionalInfoItem(BaseModel):
    """
    Validates the additional-info question set item.

    Example:
        {"additional-info": "Personal description..."}
    """

    @model_validator(mode="before")
    @classmethod
    def validate_single_key_dict(cls, data: Any) -> Dict[str, Any]:
        """Ensure the item is a single-key dictionary with 'additional-info' key and non-empty value."""
        if not isinstance(data, dict):
            raise ValueError("Additional info item must be a dictionary")
        if len(data) != 1:
            raise ValueError(
                "Additional info item must contain exactly one key-value pair"
            )
        if "additional-info" not in data:
            raise ValueError("Additional info item must have key 'additional-info'")

        # Validate the value is a non-empty string
        value = data["additional-info"]
        if not isinstance(value, str):
            raise ValueError("additional-info must be a string")
        if value.strip() == "":
            raise ValueError("additional-info cannot be empty")
        # Validate length: max 3000 characters
        if len(value) > 3000:
            raise ValueError(
                f"additional-info must be at most 3000 characters, got {len(value)}"
            )

        return data

    model_config = ConfigDict(
        extra="allow"
    )  # Allow dynamic keys since we validate structure in model_validator


class FrontendPayload(BaseModel):
    """
    Validates the complete frontend payload structure.

    The payload is grouped by question set, where each question set contains
    an array of single-key objects representing individual form fields.

    Structure:
        {
            "general": [GeneralQuestionItem, ...],  # 5 required items
            "languages": [TechnologySetItem, ...],  # Optional
            "databases": [TechnologySetItem, ...],  # Optional
            ...
            "additional-info": [AdditionalInfoItem]  # 1 required item
        }
    """

    general: List[GeneralQuestionItem] = Field(
        ..., min_length=5, max_length=5, description="General questions (5 required)"
    )
    languages: List[TechnologySetItem] = Field(
        default_factory=list,
        max_length=42,
        description="Programming languages experience (max 42 items)",
    )
    databases: List[TechnologySetItem] = Field(
        default_factory=list,
        max_length=30,
        description="Databases experience (max 30 items)",
    )
    cloud_development: List[TechnologySetItem] = Field(
        default_factory=list,
        max_length=42,
        alias="cloud-development",
        description="Cloud development experience (max 42 items)",
    )
    web_frameworks: List[TechnologySetItem] = Field(
        default_factory=list,
        max_length=28,
        alias="web-frameworks",
        description="Web frameworks experience (max 28 items)",
    )
    dev_ides: List[TechnologySetItem] = Field(
        default_factory=list,
        max_length=27,
        alias="dev-ides",
        description="Dev IDEs experience (max 27 items)",
    )
    llms: List[TechnologySetItem] = Field(
        default_factory=list,
        max_length=17,
        description="Large language models experience (max 17 items)",
    )
    doc_and_collab: List[TechnologySetItem] = Field(
        default_factory=list,
        max_length=25,
        alias="doc-and-collab",
        description="Documentation and collaboration experience (max 25 items)",
    )
    operating_systems: List[TechnologySetItem] = Field(
        default_factory=list,
        max_length=15,
        alias="operating-systems",
        description="Operating systems experience (max 15 items)",
    )
    additional_info: List[AdditionalInfoItem] = Field(
        ...,
        min_length=1,
        max_length=1,
        alias="additional-info",
        description="Personal description (required)",
    )

    @model_validator(mode="after")
    def validate_general_questions(self) -> "FrontendPayload":
        """Validate that all 5 general questions are present with correct keys."""
        general_keys = set()
        for item in self.general:
            # Each item is a dict with one key
            item_dict = item.model_dump()
            key = list(item_dict.keys())[0]
            general_keys.add(key)

        required_keys = VALID_GENERAL_KEYS
        missing = required_keys - general_keys
        if missing:
            raise ValueError(
                f"Missing required general questions: {missing}. "
                f"All 5 questions are required: {required_keys}"
            )

        # Check for duplicates
        if len(general_keys) < len(self.general):
            raise ValueError("Duplicate general question keys found")

        return self

    @model_validator(mode="after")
    def validate_additional_info(self) -> "FrontendPayload":
        """Validate that additional-info is present and non-empty."""
        if not self.additional_info or len(self.additional_info) == 0:
            raise ValueError("additional-info is required and cannot be empty")

        # Extract the value from the single-key dict
        info_item = self.additional_info[0]
        info_dict = info_item.model_dump()
        if "additional-info" not in info_dict:
            raise ValueError("additional-info item must have key 'additional-info'")

        info_value = info_dict["additional-info"]
        if (
            not info_value
            or not isinstance(info_value, str)
            or info_value.strip() == ""
        ):
            raise ValueError("additional-info cannot be empty")

        return self

    model_config = ConfigDict(
        extra="forbid",  # Reject unknown question sets
        populate_by_name=True,  # Allow both kebab-case and snake_case
    )

# ---------- SCHEMAS ----------

from typing import List

from pydantic import BaseModel, Field

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

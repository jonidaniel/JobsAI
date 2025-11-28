# ---------- SCHEMAS ----------

from typing import List

from pydantic import BaseModel, Field

# ----- MAPPING -----

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

SKILL_ALIAS_MAP2 = {
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

# ----- PYDANTIC -----


class ExperienceLevels(BaseModel):
    """
    asd

    Args:
        BaseModel:
    """

    Python: int = 0
    JavaScript: int = 0
    Agentic_Ai: int = Field(0, alias="Agentic AI")
    AI_ML: int = Field(0, alias="AI/ML")

    class Config:
        """
        asd
        """

        validate_by_name = True
        json_schema_extra = {
            "example": {"Python": 7, "JavaScript": 6, "Agentic AI": 5, "AI/ML": 4}
        }


class SkillProfile(BaseModel):
    """
    A candidate's skill profile.

    Args:
        BaseModel:
    """

    name: str = ""
    core_languages: List[str] = []
    frameworks_and_libraries: List[str] = []
    tools_and_platforms: List[str] = []
    agentic_ai_experience: List[str] = []
    ai_ml_experience: List[str] = []
    soft_skills: List[str] = []
    projects_mentioned: List[str] = []
    experience_level: ExperienceLevels = Field(default_factory=ExperienceLevels)
    job_search_keywords: List[str] = []

    class Config:
        """
        asd
        """

        validate_by_name = True

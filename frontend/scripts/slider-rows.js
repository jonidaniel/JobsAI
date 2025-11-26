// Create slider row
function createSliderRow(key) {
  return `
    <div class="flex flex-col w-full">
      <label class="mb-1">${key}</label>
      <input
        type="range"
        min="0"
        max="7"
        value="0"
        class="slider w-full accent-blue-500"
        data-key=${key}
      />
      <!-- Notch labels -->
      <div class="flex justify-between text-xs text-gray-600 mt-1">
        <span>0 yrs</span>
        <span>< 0.5 yrs</span>
        <span>< 1.0 yrs</span>
        <span>< 1.5 yrs</span>
        <span>< 2.0 yrs</span>
        <span>< 2.5 yrs</span>
        <span>< 3.0 yrs</span>
        <span>> 3.0 yrs</span>
      </div>
    </div>
  `;
}

// Inject HTML into containers

// Programming, scripting, and markup languages
document.getElementById("javascript").innerHTML = createSliderRow("JavaScript");
document.getElementById("html-css").innerHTML = createSliderRow("HTML/CSS");
document.getElementById("sql").innerHTML = createSliderRow("SQL");
document.getElementById("python").innerHTML = createSliderRow("Python");
document.getElementById("bash-shell").innerHTML = createSliderRow("Bash/Shell");
document.getElementById("typescript").innerHTML = createSliderRow("TypeScript");
document.getElementById("csharp").innerHTML = createSliderRow("C#");
document.getElementById("java").innerHTML = createSliderRow("Java");
document.getElementById("powershell").innerHTML = createSliderRow("PowerShell");
document.getElementById("cplusplus").innerHTML = createSliderRow("C++");
document.getElementById("c").innerHTML = createSliderRow("C");
document.getElementById("php").innerHTML = createSliderRow("PHP");
document.getElementById("go").innerHTML = createSliderRow("Go");
document.getElementById("rust").innerHTML = createSliderRow("Rust");
document.getElementById("kotlin").innerHTML = createSliderRow("Kotlin");
document.getElementById("lua").innerHTML = createSliderRow("Lua");
document.getElementById("ruby").innerHTML = createSliderRow("Ruby");
document.getElementById("dart").innerHTML = createSliderRow("Dart");
document.getElementById("assembly").innerHTML = createSliderRow("Assembly");
document.getElementById("swift").innerHTML = createSliderRow("Swift");
document.getElementById("groovy").innerHTML = createSliderRow("Groovy");
document.getElementById("visual-basic-dotnet").innerHTML = createSliderRow(
  "Visual Basic (.Net)"
);
document.getElementById("perl").innerHTML = createSliderRow("Perl");
document.getElementById("r").innerHTML = createSliderRow("R");
document.getElementById("vba").innerHTML = createSliderRow("VBA");
document.getElementById("gdscript").innerHTML = createSliderRow("GDScript");
document.getElementById("scala").innerHTML = createSliderRow("Scala");
document.getElementById("elixir").innerHTML = createSliderRow("Elixir");
document.getElementById("matlab").innerHTML = createSliderRow("MATLAB");
document.getElementById("delphi").innerHTML = createSliderRow("Delphi");
document.getElementById("lisp").innerHTML = createSliderRow("Lisp");
document.getElementById("zig").innerHTML = createSliderRow("Zig");
document.getElementById("micropython").innerHTML =
  createSliderRow("MicroPython");
document.getElementById("erlang").innerHTML = createSliderRow("Erlang");
document.getElementById("fsharp").innerHTML = createSliderRow("F#");
document.getElementById("ada").innerHTML = createSliderRow("Ada");
document.getElementById("gleam").innerHTML = createSliderRow("Gleam");
document.getElementById("fortran").innerHTML = createSliderRow("Fortran");
document.getElementById("ocaml").innerHTML = createSliderRow("OCaml");
document.getElementById("prolog").innerHTML = createSliderRow("Prolog");
document.getElementById("cobol").innerHTML = createSliderRow("COBOL");
document.getElementById("mojo").innerHTML = createSliderRow("Mojo");

// Databases
document.getElementById("postgresql").innerHTML = createSliderRow("PostgreSQL");
document.getElementById("mysql").innerHTML = createSliderRow("MySQL");
document.getElementById("sqlite").innerHTML = createSliderRow("SQLite");
document.getElementById("microsoft-sql-server").innerHTML = createSliderRow(
  "Microsoft SQL Server"
);
document.getElementById("redis").innerHTML = createSliderRow("Redis");
document.getElementById("mongodb").innerHTML = createSliderRow("MongoDB");
document.getElementById("mariadb").innerHTML = createSliderRow("MariaDB");
document.getElementById("elasticsearch").innerHTML =
  createSliderRow("Elasticsearch");
document.getElementById("dynamodb").innerHTML = createSliderRow("Dynamodb");
document.getElementById("oracle").innerHTML = createSliderRow("Oracle");
document.getElementById("bigquery").innerHTML = createSliderRow("BigQuery");
document.getElementById("supabase1").innerHTML = createSliderRow("Supabase");
document.getElementById("cloud-firestore").innerHTML =
  createSliderRow("Cloud Firestore");
document.getElementById("h2").innerHTML = createSliderRow("H2");
document.getElementById("cosmos-db").innerHTML = createSliderRow("Cosmos DB");
document.getElementById("firebase-realtime-database").innerHTML =
  createSliderRow("Firebase Realtime Database");
document.getElementById("snowflake").innerHTML = createSliderRow("Snowflake");
document.getElementById("microsoft-access").innerHTML =
  createSliderRow("Microsoft Access");
document.getElementById("influxdb").innerHTML = createSliderRow("InfluxDB");
document.getElementById("duckdb").innerHTML = createSliderRow("DuckDB");
document.getElementById("databricks-sql").innerHTML =
  createSliderRow("Databricks SQL");
document.getElementById("cassandra").innerHTML = createSliderRow("Cassandra");
document.getElementById("neo4j").innerHTML = createSliderRow("Neo4J");
document.getElementById("clickhouse").innerHTML = createSliderRow("Clickhouse");
document.getElementById("valkey").innerHTML = createSliderRow("Valkey");
document.getElementById("amazon-redshift").innerHTML =
  createSliderRow("Amazon Redshift");
document.getElementById("ibm-db2").innerHTML = createSliderRow("IBM DB2");
document.getElementById("cockroachdb").innerHTML =
  createSliderRow("Cockroachdb");
document.getElementById("pocketbase").innerHTML = createSliderRow("Pocketbase");
document.getElementById("datomic").innerHTML = createSliderRow("Datomic");

// Cloud development
document.getElementById("docker").innerHTML = createSliderRow("Docker");
document.getElementById("npm").innerHTML = createSliderRow("npm");
document.getElementById("amazon-web-services-aws").innerHTML = createSliderRow(
  "Amazon Web Services (AWS)"
);
document.getElementById("pip").innerHTML = createSliderRow("Pip");
document.getElementById("kubernetes").innerHTML = createSliderRow("Kubernetes");
document.getElementById("microsoft-azure").innerHTML =
  createSliderRow("Microsoft Azure");
document.getElementById("vite").innerHTML = createSliderRow("Vite");
document.getElementById("homebrew").innerHTML = createSliderRow("Homebrew");
document.getElementById("google-cloud").innerHTML =
  createSliderRow("Google Cloud");
document.getElementById("yarn").innerHTML = createSliderRow("Yarn");
document.getElementById("make").innerHTML = createSliderRow("Make");
document.getElementById("nuget").innerHTML = createSliderRow("NuGet");
document.getElementById("webpack").innerHTML = createSliderRow("Webpack");
document.getElementById("cloudflare").innerHTML = createSliderRow("Cloudflare");
document.getElementById("terraform").innerHTML = createSliderRow("Terraform");
document.getElementById("apt").innerHTML = createSliderRow("APT");
document.getElementById("maven-build-tool").innerHTML =
  createSliderRow("Maven (build tool)");
document.getElementById("gradle").innerHTML = createSliderRow("Gradle");
document.getElementById("pnpm").innerHTML = createSliderRow("pnpm");
document.getElementById("cargo").innerHTML = createSliderRow("Cargo");
document.getElementById("firebase").innerHTML = createSliderRow("Firebase");
document.getElementById("prometheus").innerHTML = createSliderRow("Prometheus");
document.getElementById("msbuild").innerHTML = createSliderRow("MSBuild");
document.getElementById("composer").innerHTML = createSliderRow("Composer");
document.getElementById("ansible").innerHTML = createSliderRow("Ansible");
document.getElementById("digital-ocean").innerHTML =
  createSliderRow("Digital Ocean");
document.getElementById("podman").innerHTML = createSliderRow("Podman");
document.getElementById("chocolatey").innerHTML = createSliderRow("Chocolatey");
document.getElementById("vercel").innerHTML = createSliderRow("Vercel");
document.getElementById("datadog").innerHTML = createSliderRow("Datadog");
document.getElementById("poetry").innerHTML = createSliderRow("Poetry");
document.getElementById("pacman").innerHTML = createSliderRow("Pacman");
document.getElementById("netlify").innerHTML = createSliderRow("Netlify");
document.getElementById("heroku").innerHTML = createSliderRow("Heroku");
document.getElementById("bun").innerHTML = createSliderRow("Bun");
document.getElementById("supabase2").innerHTML = createSliderRow("Supabase");
document.getElementById("ninja").innerHTML = createSliderRow("Ninja");
document.getElementById("splunk").innerHTML = createSliderRow("Splunk");
document.getElementById("new-relic").innerHTML = createSliderRow("New Relic");
document.getElementById("railway").innerHTML = createSliderRow("Railway");
document.getElementById("ibm-cloud").innerHTML = createSliderRow("IBM Cloud");
document.getElementById("yandex-cloud").innerHTML =
  createSliderRow("Yandex Cloud");

// Web frameworks and technologies
document.getElementById("nodejs").innerHTML = createSliderRow("Node.js");
document.getElementById("react").innerHTML = createSliderRow("React");
document.getElementById("jquery").innerHTML = createSliderRow("jQuery");
document.getElementById("nextjs").innerHTML = createSliderRow("Next.js");
document.getElementById("aspdotnet-core").innerHTML =
  createSliderRow("ASP.NET Core");
document.getElementById("express").innerHTML = createSliderRow("Express");
document.getElementById("angular").innerHTML = createSliderRow("Angular");
document.getElementById("vuejs").innerHTML = createSliderRow("Vue.js");
document.getElementById("spring-boot").innerHTML =
  createSliderRow("Spring Boot");
document.getElementById("fastapi").innerHTML = createSliderRow("FastAPI");
document.getElementById("aspdotnet").innerHTML = createSliderRow("ASP.NET");
document.getElementById("flask").innerHTML = createSliderRow("Flask");
document.getElementById("wordpress").innerHTML = createSliderRow("WordPress");
document.getElementById("django").innerHTML = createSliderRow("Django");
document.getElementById("laravel").innerHTML = createSliderRow("Laravel");
document.getElementById("blazor").innerHTML = createSliderRow("Blazor");
document.getElementById("angularjs").innerHTML = createSliderRow("AngularJS");
document.getElementById("nestjs").innerHTML = createSliderRow("NestJS");
document.getElementById("svelte").innerHTML = createSliderRow("Svelte");
document.getElementById("ruby-on-rails").innerHTML =
  createSliderRow("Ruby on Rails");
document.getElementById("astro").innerHTML = createSliderRow("Astro");
document.getElementById("symfony").innerHTML = createSliderRow("Symfony");
document.getElementById("nuxtjs").innerHTML = createSliderRow("Nuxt.js");
document.getElementById("deno").innerHTML = createSliderRow("Deno");
document.getElementById("fastify").innerHTML = createSliderRow("Fastify");
document.getElementById("axum").innerHTML = createSliderRow("Axum");
document.getElementById("phoenix").innerHTML = createSliderRow("Phoenix");
document.getElementById("drupal").innerHTML = createSliderRow("Drupal");

// Dev IDEs
document.getElementById("visual-studio-code").innerHTML =
  createSliderRow("Visual Studio Code");
document.getElementById("visual-studio").innerHTML =
  createSliderRow("Visual Studio");
document.getElementById("intellij-idea").innerHTML =
  createSliderRow("IntelliJ IDEA");
document.getElementById("notepadplusplus").innerHTML =
  createSliderRow("Notepad++");
document.getElementById("vim").innerHTML = createSliderRow("Vim");
document.getElementById("cursor").innerHTML = createSliderRow("Cursor");
document.getElementById("android-studio").innerHTML =
  createSliderRow("Android Studio");
document.getElementById("pycharm").innerHTML = createSliderRow("PyCharm");
document.getElementById("neovim").innerHTML = createSliderRow("Neovim");
document.getElementById("jupyter-nb-jupyterlab").innerHTML = createSliderRow(
  "Jupyter Nb/JupyterLab"
);
document.getElementById("nano").innerHTML = createSliderRow("Nano");
document.getElementById("xcode").innerHTML = createSliderRow("Xcode");
document.getElementById("sublime-text").innerHTML =
  createSliderRow("Sublime Text");
document.getElementById("claude-code").innerHTML =
  createSliderRow("Claude Code");
document.getElementById("webstorm").innerHTML = createSliderRow("WebStorm");
document.getElementById("rider").innerHTML = createSliderRow("Rider");
document.getElementById("zed").innerHTML = createSliderRow("Zed");
document.getElementById("eclipse").innerHTML = createSliderRow("Eclipse");
document.getElementById("phpstorm").innerHTML = createSliderRow("PhpStorm");
document.getElementById("vscodium").innerHTML = createSliderRow("VSCodium");
document.getElementById("windsurf").innerHTML = createSliderRow("Windsurf");
document.getElementById("rustrover").innerHTML = createSliderRow("RustRover");
document.getElementById("lovabledotdev").innerHTML =
  createSliderRow("Lovable.dev");
document.getElementById("bolt").innerHTML = createSliderRow("Bolt");
document.getElementById("cline-and-or-roo").innerHTML =
  createSliderRow("Cline and/or Roo");
document.getElementById("aider").innerHTML = createSliderRow("Aider");
document.getElementById("trae").innerHTML = createSliderRow("Trae");

// Large language models
document.getElementById("openai-gpt").innerHTML = createSliderRow("OpenAI GPT");
document.getElementById("claude-sonnet").innerHTML =
  createSliderRow("Claude Sonnet");
document.getElementById("gemini-flash").innerHTML =
  createSliderRow("Gemini Flash");
document.getElementById("openai-reasoning").innerHTML =
  createSliderRow("OpenAI Reasoning");
document.getElementById("openai-image").innerHTML =
  createSliderRow("OpenAI Image");
document.getElementById("gemini-reasoning").innerHTML =
  createSliderRow("Gemini Reasoning");
document.getElementById("deepseek-reasoning").innerHTML =
  createSliderRow("DeepSeek Reasoning");
document.getElementById("meta-llama").innerHTML = createSliderRow("Meta Llama");
document.getElementById("deepseek-general").innerHTML =
  createSliderRow("DeepSeek General");
document.getElementById("x-grok").innerHTML = createSliderRow("X Grok");
document.getElementById("mistral").innerHTML = createSliderRow("Mistral");
document.getElementById("perplexity-sonar").innerHTML =
  createSliderRow("Perplexity Sonar");
document.getElementById("alibaba-qwen").innerHTML =
  createSliderRow("Alibaba Qwen");
document.getElementById("microsoft-phi-4-models").innerHTML = createSliderRow(
  "Microsoft Phi-4 models"
);
document.getElementById("amazon-titan-models").innerHTML = createSliderRow(
  "Amazon Titan models"
);
document.getElementById("cohere-command-a").innerHTML =
  createSliderRow("Cohere: Command A");
document.getElementById("reka-flash3-or-other-reka-models").innerHTML =
  createSliderRow("Reka (Flash 3 or other Reka models)");

// Code documentation and collaboration tools
document.getElementById("github").innerHTML = createSliderRow("GitHub");
document.getElementById("jira").innerHTML = createSliderRow("Jira");
document.getElementById("gitlab").innerHTML = createSliderRow("GitLab");
document.getElementById("confluence").innerHTML = createSliderRow("Confluence");
document.getElementById("markdown-file").innerHTML =
  createSliderRow("Markdown File");
document.getElementById("azure-devops").innerHTML =
  createSliderRow("Azure Devops");
document.getElementById("notion").innerHTML = createSliderRow("Notion");
document.getElementById("obsidian").innerHTML = createSliderRow("Obsidian");
document.getElementById("miro").innerHTML = createSliderRow("Miro");
document.getElementById("google-workspace").innerHTML =
  createSliderRow("Google Workspace");
document.getElementById("trello").innerHTML = createSliderRow("Trello");
document.getElementById("wikis").innerHTML = createSliderRow("Wikis");
document.getElementById("lucid-includes-lucidchart").innerHTML =
  createSliderRow("Lucid (includes Lucidchart)");
document.getElementById("google-colab").innerHTML =
  createSliderRow("Google Colab");
document.getElementById("asana").innerHTML = createSliderRow("Asana");
document.getElementById("doxygen").innerHTML = createSliderRow("Doxygen");
document.getElementById("clickup").innerHTML = createSliderRow("Clickup");
document.getElementById("linear").innerHTML = createSliderRow("Linear");
document.getElementById("redmine").innerHTML = createSliderRow("Redmine");
document.getElementById("mondaydotcom").innerHTML =
  createSliderRow("Monday.com");
document.getElementById("youtrack").innerHTML = createSliderRow("YouTrack");
document.getElementById("airtable").innerHTML = createSliderRow("Airtable");
document.getElementById("stack-overflow-for-teams").innerHTML = createSliderRow(
  "Stack Overflow for Teams"
);
document.getElementById("microsoft-planner").innerHTML =
  createSliderRow("Microsoft Planner");
document.getElementById("coda").innerHTML = createSliderRow("Coda");

// Computer operating systems
document.getElementById("windows").innerHTML = createSliderRow("Windows");
document.getElementById("macos").innerHTML = createSliderRow("MacOS");
document.getElementById("android").innerHTML = createSliderRow("Android");
document.getElementById("ubuntu").innerHTML = createSliderRow("Ubuntu");
document.getElementById("ios").innerHTML = createSliderRow("iOS");
document.getElementById("linux-non-wsl").innerHTML =
  createSliderRow("Linux (non-WSL)");
document.getElementById("windows-subsystem-for-linux-wsl").innerHTML =
  createSliderRow("Windows Subsystem for Linux (WSL)");
document.getElementById("debian").innerHTML = createSliderRow("Debian");
document.getElementById("arch").innerHTML = createSliderRow("Arch");
document.getElementById("ipados").innerHTML = createSliderRow("iPadOS");
document.getElementById("fedora").innerHTML = createSliderRow("Fedora");
document.getElementById("red-hat").innerHTML = createSliderRow("Red Hat");
document.getElementById("nixos").innerHTML = createSliderRow("NixOS");
document.getElementById("pop-os").innerHTML = createSliderRow("Pop!_OS");
document.getElementById("chromeos").innerHTML = createSliderRow("ChromeOS");

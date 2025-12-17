/**
 * Slider Question Data Configuration
 *
 * Contains the slider questions for question sets 1-8.
 * Each question set has multiple sliders representing experience levels
 * for different technologies/tools.
 *
 * Data Structure:
 * - Each array element is a JSON string representing one question set
 * - Each JSON object maps technology keys to display labels
 * - Keys are kebab-case identifiers (e.g., "javascript", "postgresql")
 * - Values are human-readable labels (e.g., "JavaScript", "PostgreSQL")
 *
 * Question Set Mapping:
 * 0: General Questions (not in this file)
 * 1: Programming, Scripting, and Markup Languages Experience
 * 2: Databases Experience
 * 3: Cloud Development Experience
 * 4: Web Frameworks and Technologies Experience
 * 5: Dev IDEs Experience
 * 6: Large Language Models Experience
 * 7: Code Documentation and Collaboration Experience
 * 8: Computer Operating Systems Experience
 */

/**
 * Slider Configuration
 *
 * Sliders represent years of experience ranges:
 * 0 = 0 yrs
 * 1 = < 0.5 yrs
 * 2 = < 1.0 yrs
 * 3 = < 1.5 yrs
 * 4 = < 2.0 yrs
 * 5 = < 2.5 yrs
 * 6 = < 3.0 yrs
 * 7 = > 3.0 yrs
 */
export const SLIDER_MIN = 0;
export const SLIDER_MAX = 7;
export const SLIDER_DEFAULT = 0;

/**
 * Type for slider data - maps technology keys to display labels
 */
export type SliderData = Record<string, string>;

/**
 * Raw JSON strings for slider data
 * Stored as strings for easier editing and version control
 * Parsed once at module load time for performance
 */
const SLIDER_DATA_RAW: readonly string[] = [
  '{"javascript":"JavaScript","html-css":"HTML/CSS","sql":"SQL","python":"Python","bash-shell":"Bash/Shell","typescript":"TypeScript","csharp":"C#","java":"Java","powershell":"PowerShell","cplusplus":"C++","c":"C","php":"PHP","go":"Go","rust":"Rust","kotlin":"Kotlin","lua":"Lua","ruby":"Ruby","dart":"Dart","assembly":"Assembly","swift":"Swift","groovy":"Groovy","visual-basic-dotnet":"Visual Basic (.Net)","perl":"Perl","r":"R","vba":"VBA","gdscript":"GDScript","scala":"Scala","elixir":"Elixir","matlab":"MATLAB","delphi":"Delphi","lisp":"Lisp","zig":"Zig","micropython":"MicroPython","erlang":"Erlang","fsharp":"F#","ada":"Ada","gleam":"Gleam","fortran":"Fortran","ocaml":"OCaml","prolog":"Prolog","cobol":"COBOL","mojo":"Mojo"}',
  '{"postgresql":"PostgreSQL","mysql":"MySQL","sqlite":"SQLite","microsoft-sql-server":"Microsoft SQL Server","redis":"Redis","mongodb":"MongoDB","mariadb":"MariaDB","elasticsearch":"Elasticsearch","dynamodb":"Dynamodb","oracle":"Oracle","bigquery":"BigQuery","supabase1":"Supabase","cloud-firestore":"Cloud Firestore","h2":"H2","cosmos-db":"Cosmos DB","firebase-realtime-database":"Firebase Realtime Database","snowflake":"Snowflake","microsoft-access":"Microsoft Access","influxdb":"InfluxDB","duckdb":"DuckDB","databricks-sql":"Databricks SQL","cassandra":"Cassandra","neo4j":"Neo4J","clickhouse":"Clickhouse","valkey":"Valkey","amazon-redshift":"Amazon Redshift","ibm-db2":"IBM DB2","cockroachdb":"Cockroachdb","pocketbase":"Pocketbase","datomic":"Datomic"}',
  '{"docker":"Docker","npm":"npm","amazon-web-services-aws":"Amazon Web Services (AWS)","pip":"Pip","kubernetes":"Kubernetes","microsoft-azure":"Microsoft Azure","vite":"Vite","homebrew":"Homebrew","google-cloud":"Google Cloud","yarn":"Yarn","make":"Make","nuget":"NuGet","webpack":"Webpack","cloudflare":"Cloudflare","terraform":"Terraform","apt":"APT","maven-build-tool":"Maven (build tool)","gradle":"Gradle","pnpm":"pnpm","cargo":"Cargo","firebase":"Firebase","prometheus":"Prometheus","msbuild":"MSBuild","composer":"Composer","ansible":"Ansible","digital-ocean":"Digital Ocean","podman":"Podman","chocolatey":"Chocolatey","vercel":"Vercel","datadog":"Datadog","poetry":"Poetry","pacman":"Pacman","netlify":"Netlify","heroku":"Heroku","bun":"Bun","supabase2":"Supabase","ninja":"Ninja","splunk":"Splunk","new-relic":"New Relic","railway":"Railway","ibm-cloud":"IBM Cloud","yandex-cloud":"Yandex Cloud"}',
  '{"nodejs":"Node.js","react":"React","jquery":"jQuery","nextjs":"Next.js","aspdotnet-core":"ASP.NET Core","express":"Express","angular":"Angular","vuejs":"Vue.js","spring-boot":"Spring Boot","fastapi":"FastAPI","aspdotnet":"ASP.NET","flask":"Flask","wordpress":"WordPress","django":"Django","laravel":"Laravel","blazor":"Blazor","angularjs":"AngularJS","nestjs":"NestJS","svelte":"Svelte","ruby-on-rails":"Ruby on Rails","astro":"Astro","symfony":"Symfony","nuxtjs":"Nuxt.js","deno":"Deno","fastify":"Fastify","axum":"Axum","phoenix":"Phoenix","drupal":"Drupal"}',
  '{"visual-studio-code":"Visual Studio Code","visual-studio":"Visual Studio","intellij-idea":"IntelliJ IDEA","notepadplusplus":"Notepad++","vim":"Vim","cursor":"Cursor","android-studio":"Android Studio","pycharm":"PyCharm","neovim":"Neovim","jupyter-nb-jupyterlab":"Jupyter Nb/JupyterLab","nano":"Nano","xcode":"Xcode","sublime-text":"Sublime Text","claude-code":"Claude Code","webstorm":"WebStorm","rider":"Rider","zed":"Zed","eclipse":"Eclipse","phpstorm":"PhpStorm","vscodium":"VSCodium","windsurf":"Windsurf","rustrover":"RustRover","lovabledotdev":"Lovable.dev","bolt":"Bolt","cline-and-or-roo":"Cline and/or Roo","aider":"Aider","trae":"Trae"}',
  '{"openai-gpt":"OpenAI GPT","claude-sonnet":"Claude Sonnet","gemini-flash":"Gemini Flash","openai-reasoning":"OpenAI Reasoning","openai-image":"OpenAI Image","gemini-reasoning":"Gemini Reasoning","deepseek-reasoning":"DeepSeek Reasoning","meta-llama":"Meta Llama","deepseek-general":"DeepSeek General","x-grok":"X Grok","mistral":"Mistral","perplexity-sonar":"Perplexity Sonar","alibaba-qwen":"Alibaba Qwen","microsoft-phi-4-models":"Microsoft Phi-4 models","amazon-titan-models":"Amazon Titan models","cohere-command-a":"Cohere: Command A","reka-flash3-or-other-reka-models":"Reka (Flash 3 or other Reka models)"}',
  '{"github":"GitHub","jira":"Jira","gitlab":"GitLab","confluence":"Confluence","markdown-file":"Markdown File","azure-devops":"Azure Devops","notion":"Notion","obsidian":"Obsidian","miro":"Miro","google-workspace":"Google Workspace","trello":"Trello","wikis":"Wikis","lucid-includes-lucidchart":"Lucid (includes Lucidchart)","google-colab":"Google Colab","asana":"Asana","doxygen":"Doxygen","clickup":"Clickup","linear":"Linear","redmine":"Redmine","mondaydotcom":"Monday.com","youtrack":"YouTrack","airtable":"Airtable","stack-overflow-for-teams":"Stack Overflow for Teams","microsoft-planner":"Microsoft Planner","coda":"Coda"}',
  '{"windows":"Windows","macos":"MacOS","android":"Android","ubuntu":"Ubuntu","ios":"iOS","linux-non-wsl":"Linux (non-WSL)","windows-subsystem-for-linux-wsl":"Windows Subsystem for Linux (WSL)","debian":"Debian","arch":"Arch","ipados":"iPadOS","fedora":"Fedora","red-hat":"Red Hat","nixos":"NixOS","pop-os":"Pop!_OS","chromeos":"ChromeOS"}',
] as const;

/**
 * Parsed slider data
 *
 * JSON strings are parsed once at module load time.
 * This is more efficient than parsing on every component render.
 *
 * Structure: Array of 8 objects, each containing key-value pairs
 * where keys are technology identifiers and values are display labels.
 *
 * Usage: SLIDER_DATA[index - 1] gives the data for question set at index
 * (e.g., SLIDER_DATA[0] is for question set 1)
 */
export const SLIDER_DATA: readonly SliderData[] = SLIDER_DATA_RAW.map(
  (jsonStr) => JSON.parse(jsonStr) as SliderData
);

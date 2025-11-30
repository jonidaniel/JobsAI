import { useEffect, useRef } from "react";

// Question data constants
const SLIDER_DATA = [
  '{"javascript":"JavaScript","html-css":"HTML/CSS","sql":"SQL","python":"Python","bash-shell":"Bash/Shell","typescript":"TypeScript","csharp":"C#","java":"Java","powershell":"PowerShell","cplusplus":"C++","c":"C","php":"PHP","go":"Go","rust":"Rust","kotlin":"Kotlin","lua":"Lua","ruby":"Ruby","dart":"Dart","assembly":"Assembly","swift":"Swift","groovy":"Groovy","visual-basic-dotnet":"Visual Basic (.Net)","perl":"Perl","r":"R","vba":"VBA","gdscript":"GDScript","scala":"Scala","elixir":"Elixir","matlab":"MATLAB","delphi":"Delphi","lisp":"Lisp","zig":"Zig","micropython":"MicroPython","erlang":"Erlang","fsharp":"F#","ada":"Ada","gleam":"Gleam","fortran":"Fortran","ocaml":"OCaml","prolog":"Prolog","cobol":"COBOL","mojo":"Mojo"}',
  '{"postgresql":"PostgreSQL","mysql":"MySQL","sqlite":"SQLite","microsoft-sql-server":"Microsoft SQL Server","redis":"Redis","mongodb":"MongoDB","mariadb":"MariaDB","elasticsearch":"Elasticsearch","dynamodb":"Dynamodb","oracle":"Oracle","bigquery":"BigQuery","supabase1":"Supabase","cloud-firestore":"Cloud Firestore","h2":"H2","cosmos-db":"Cosmos DB","firebase-realtime-database":"Firebase Realtime Database","snowflake":"Snowflake","microsoft-access":"Microsoft Access","influxdb":"InfluxDB","duckdb":"DuckDB","databricks-sql":"Databricks SQL","cassandra":"Cassandra","neo4j":"Neo4J","clickhouse":"Clickhouse","valkey":"Valkey","amazon-redshift":"Amazon Redshift","ibm-db2":"IBM DB2","cockroachdb":"Cockroachdb","pocketbase":"Pocketbase","datomic":"Datomic"}',
  '{"docker":"Docker","npm":"npm","amazon-web-services-aws":"Amazon Web Services (AWS)","pip":"Pip","kubernetes":"Kubernetes","microsoft-azure":"Microsoft Azure","vite":"Vite","homebrew":"Homebrew","google-cloud":"Google Cloud","yarn":"Yarn","make":"Make","nuget":"NuGet","webpack":"Webpack","cloudflare":"Cloudflare","terraform":"Terraform","apt":"APT","maven-build-tool":"Maven (build tool)","gradle":"Gradle","pnpm":"pnpm","cargo":"Cargo","firebase":"Firebase","prometheus":"Prometheus","msbuild":"MSBuild","composer":"Composer","ansible":"Ansible","digital-ocean":"Digital Ocean","podman":"Podman","chocolatey":"Chocolatey","vercel":"Vercel","datadog":"Datadog","poetry":"Poetry","pacman":"Pacman","netlify":"Netlify","heroku":"Heroku","bun":"Bun","supabase2":"Supabase","ninja":"Ninja","splunk":"Splunk","new-relic":"New Relic","railway":"Railway","ibm-cloud":"IBM Cloud","yandex-cloud":"Yandex Cloud"}',
  '{"nodejs":"Node.js","react":"React","jquery":"jQuery","nextjs":"Next.js","aspdotnet-core":"ASP.NET Core","express":"Express","angular":"Angular","vuejs":"Vue.js","spring-boot":"Spring Boot","fastapi":"FastAPI","aspdotnet":"ASP.NET","flask":"Flask","wordpress":"WordPress","django":"Django","laravel":"Laravel","blazor":"Blazor","angularjs":"AngularJS","nestjs":"NestJS","svelte":"Svelte","ruby-on-rails":"Ruby on Rails","astro":"Astro","symfony":"Symfony","nuxtjs":"Nuxt.js","deno":"Deno","fastify":"Fastify","axum":"Axum","phoenix":"Phoenix","drupal":"Drupal"}',
  '{"visual-studio-code":"Visual Studio Code","visual-studio":"Visual Studio","intellij-idea":"IntelliJ IDEA","notepadplusplus":"Notepad++","vim":"Vim","cursor":"Cursor","android-studio":"Android Studio","pycharm":"PyCharm","neovim":"Neovim","jupyter-nb-jupyterlab":"Jupyter Nb/JupyterLab","nano":"Nano","xcode":"Xcode","sublime-text":"Sublime Text","claude-code":"Claude Code","webstorm":"WebStorm","rider":"Rider","zed":"Zed","eclipse":"Eclipse","phpstorm":"PhpStorm","vscodium":"VSCodium","windsurf":"Windsurf","rustrover":"RustRover","lovabledotdev":"Lovable.dev","bolt":"Bolt","cline-and-or-roo":"Cline and/or Roo","aider":"Aider","trae":"Trae"}',
  '{"openai-gpt":"OpenAI GPT","claude-sonnet":"Claude Sonnet","gemini-flash":"Gemini Flash","openai-reasoning":"OpenAI Reasoning","openai-image":"OpenAI Image","gemini-reasoning":"Gemini Reasoning","deepseek-reasoning":"DeepSeek Reasoning","meta-llama":"Meta Llama","deepseek-general":"DeepSeek General","x-grok":"X Grok","mistral":"Mistral","perplexity-sonar":"Perplexity Sonar","alibaba-qwen":"Alibaba Qwen","microsoft-phi-4-models":"Microsoft Phi-4 models","amazon-titan-models":"Amazon Titan models","cohere-command-a":"Cohere: Command A","reka-flash3-or-other-reka-models":"Reka (Flash 3 or other Reka models)"}',
  '{"github":"GitHub","jira":"Jira","gitlab":"GitLab","confluence":"Confluence","markdown-file":"Markdown File","azure-devops":"Azure Devops","notion":"Notion","obsidian":"Obsidian","miro":"Miro","google-workspace":"Google Workspace","trello":"Trello","wikis":"Wikis","lucid-includes-lucidchart":"Lucid (includes Lucidchart)","google-colab":"Google Colab","asana":"Asana","doxygen":"Doxygen","clickup":"Clickup","linear":"Linear","redmine":"Redmine","mondaydotcom":"Monday.com","youtrack":"YouTrack","airtable":"Airtable","stack-overflow-for-teams":"Stack Overflow for Teams","microsoft-planner":"Microsoft Planner","coda":"Coda"}',
  '{"windows":"Windows","macos":"MacOS","android":"Android","ubuntu":"Ubuntu","ios":"iOS","linux-non-wsl":"Linux (non-WSL)","windows-subsystem-for-linux-wsl":"Windows Subsystem for Linux (WSL)","debian":"Debian","arch":"Arch","ipados":"iPadOS","fedora":"Fedora","red-hat":"Red Hat","nixos":"NixOS","pop-os":"Pop!_OS","chromeos":"ChromeOS"}',
];

const GENERAL_QUESTION_LABELS = [
  "Name",
  "Years of Experience",
  "Background Summary",
  "Key Skills",
  "Previous Projects",
  "Education",
  "Certifications",
  "Languages",
  "Location",
  "Additional Information",
];

const GENERAL_QUESTION_DEFAULTS = {
  2: "My name is Joni Potala. I have developed software since 2020. I have built and published multiple full-stack apps (frontend, backend, database, desktop, mobile). I have built multi-agent orchestrations with OpenAI Agents SDK for half a year. I have very good soft skills.",
};

// React Components
function Slider({ keyName, label }) {
  return (
    <div className="flex flex-col w-full">
      <label className="mb-1">{label}</label>
      <input
        className="slider accent-blue-500 w-full"
        type="range"
        min="0"
        max="7"
        value="0"
        data-key={keyName}
      />
      {/* Notch labels */}
      <div className="flex justify-between mt-1 text-gray-600 text-xs">
        <span>0 yrs</span>
        <span>&lt; 0.5 yrs</span>
        <span>&lt; 1.0 yrs</span>
        <span>&lt; 1.5 yrs</span>
        <span>&lt; 2.0 yrs</span>
        <span>&lt; 2.5 yrs</span>
        <span>&lt; 3.0 yrs</span>
        <span>&gt; 3.0 yrs</span>
      </div>
    </div>
  );
}

function TextField({ keyName, label, defaultValue = "" }) {
  return (
    <div className="flex flex-col w-full">
      <label className="mb-1">{label}</label>
      <input
        className="text-field border border-gray-300 px-2 py-1 rounded w-full"
        type="text"
        data-key={keyName}
        defaultValue={defaultValue}
      />
    </div>
  );
}

function MultipleChoice({ keyName, label, options }) {
  return (
    <div className="flex flex-col w-full">
      <label className="mb-1">{label}</label>
      {options.map((option) => {
        const optionKey = option.toLowerCase().replace(/\s+/g, "-");
        return (
          <div key={option} className="flex items-center mb-2">
            <input
              className="checkbox-field accent-blue-500"
              type="checkbox"
              data-key={keyName}
              data-value={option}
              id={`${keyName}-${optionKey}`}
            />
            <label htmlFor={`${keyName}-${optionKey}`} className="ml-2">
              {option}
            </label>
          </div>
        );
      })}
    </div>
  );
}

export default function QuestionSets() {
  const initialized = useRef(false);
  const currentIndexRef = useRef(0);
  const questionSetsRef = useRef([]);

  useEffect(() => {
    // Prevent double initialization of navigator in StrictMode
    if (initialized.current) {
      return;
    }
    initialized.current = true;

    // Set up navigator
    const questionSets = Array.from(
      document.querySelectorAll("#question-set-wrapper section")
    );

    function showQuestionSet(index, shouldScroll = false) {
      questionSets.forEach((questionSet, questionSetIndex) => {
        questionSet.classList.toggle("active", questionSetIndex === index);
      });
      if (shouldScroll && questionSets[index]) {
        questionSets[index].scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
      }
    }

    questionSetsRef.current = questionSets;
    showQuestionSet(currentIndexRef.current, false);
  }, []);

  // Parse slider data
  const sliderData = SLIDER_DATA.map((jsonStr) => JSON.parse(jsonStr));

  return (
    /*
     * Question set wrapper
     *
     * There are 9 question sets in total:
     *     1/9 'General Questions'
     *     2/9 'Programming, Scripting, and Markup Languages',
     *     3/9 'Databases',
     *     4/9 'Cloud Development',
     *     5/9 'Web Frameworks and Technologies',
     *     6/9 'Dev IDEs',
     *     7/9 'Large Language Models',
     *     8/9 'Code Documentation and Collaboration',
     *     9/9 'Computer Operating Systems'
     *
     * Only one question set is shown on the page at a time
     */
    <div id="question-set-wrapper" className="relative flex w-full">
      {/* Left arrow */}
      <div className="prev-btn-container sticky top-1/2 -translate-y-1/2 self-start h-0 flex items-center z-10">
        <button
          className="prev-btn text-white text-2xl px-3 py-1 bg-gray-800 rounded-lg hover:bg-gray-700 transition-colors"
          onClick={() => {
            const questionSets = questionSetsRef.current;
            currentIndexRef.current =
              currentIndexRef.current === 0
                ? questionSets.length - 1
                : currentIndexRef.current - 1;
            questionSets.forEach((questionSet, questionSetIndex) => {
              questionSet.classList.toggle(
                "active",
                questionSetIndex === currentIndexRef.current
              );
            });
            if (questionSets[currentIndexRef.current]) {
              questionSets[currentIndexRef.current].scrollIntoView({
                behavior: "smooth",
                block: "start",
              });
            }
          }}
        >
          &larr;
        </button>
      </div>

      {/* TailwindCSS form */}
      <div className="bg-gray-800 p-10 rounded-2xl shadow-lg flex-1">
        {/* Create an array of 9 question sets */}
        {Array.from({ length: 9 }).map((_, i) => (
          /* Question set */
          <section key={i}>
            <h3 className="text-3xl">{i + 1}/9</h3>
            <h3 className="text-3xl">{getTitle(i)}</h3>

            {/* Questions */}
            <div className="space-y-4">
              {i === 0 ? (
                // 'General Questions'
                Array.from({ length: 10 }).map((_, j) => {
                  if (j === 0) {
                    // First question (Name) is a multiple choice with checkboxes
                    return (
                      <MultipleChoice
                        key={j}
                        keyName={`text-field-general-${j}`}
                        label={GENERAL_QUESTION_LABELS[j]}
                        options={["Intern", "Entry", "Intermediate", "Expert"]}
                      />
                    );
                  } else {
                    return (
                      <TextField
                        key={j}
                        keyName={`text-field-general-${j}`}
                        label={GENERAL_QUESTION_LABELS[j]}
                        defaultValue={GENERAL_QUESTION_DEFAULTS[j] || ""}
                      />
                    );
                  }
                })
              ) : (
                // Other question sets (1-8)
                <>
                  {/* Sliders */}
                  {Object.entries(sliderData[i - 1]).map(([key, label]) => (
                    <Slider key={key} keyName={key} label={label} />
                  ))}
                  {/* Text field */}
                  <TextField keyName={`text-field${i}`} label="Other" />
                </>
              )}
            </div>
          </section>
        ))}
      </div>

      {/* Right arrow */}
      <div className="next-btn-container sticky top-1/2 -translate-y-1/2 self-start h-0 flex items-center z-10 ml-auto">
        <button
          className="next-btn text-white text-2xl px-3 py-1 bg-gray-800 rounded-lg hover:bg-gray-700 transition-colors"
          onClick={() => {
            const questionSets = questionSetsRef.current;
            currentIndexRef.current =
              (currentIndexRef.current + 1) % questionSets.length;
            questionSets.forEach((questionSet, questionSetIndex) => {
              questionSet.classList.toggle(
                "active",
                questionSetIndex === currentIndexRef.current
              );
            });
            if (questionSets[currentIndexRef.current]) {
              questionSets[currentIndexRef.current].scrollIntoView({
                behavior: "smooth",
                block: "start",
              });
            }
          }}
        >
          &rarr;
        </button>
      </div>
    </div>
  );
}

function getTitle(i) {
  return [
    "General Questions",
    "Programming, Scripting, and Markup Languages Experience",
    "Databases Experience",
    "Cloud Development Experience",
    "Web Frameworks and Technologies Experience",
    "Dev IDEs Experience",
    "Large Language Models Experience",
    "Code Documentation and Collaboration Experience",
    "Computer Operating Systems Experience",
  ][i];
}

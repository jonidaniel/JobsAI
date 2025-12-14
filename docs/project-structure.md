```
.
├── asd.md
├── asd.txt
├── dev_diary.md
├── docs
├── frontend
│   ├── assets
│   │   ├── icons
│   │   │   └── favicon.ico
│   │   └── imgs
│   │       └── face.png
│   ├── index.html
│   ├── scripts
│   │   ├── builder.js
│   │   ├── navigation.js
│   │   └── submit.js
│   └── styles
│       └── stylesheet.css
├── LICENSE
├── pyproject.toml
├── pytest.ini
├── README.md
├── src
│   └── jobsai
│       ├── agents
│       │   ├── __init__.py
│       │   ├── __pycache__
│       │   │   ├── __init__.cpython-312.pyc
│       │   │   ├── generator.cpython-312.pyc
│       │   │   ├── profiler.cpython-312.pyc
│       │   │   ├── reporter.cpython-312.pyc
│       │   │   ├── scorer.cpython-312.pyc
│       │   │   └── searcher.cpython-312.pyc
│       │   ├── generator.py
│       │   ├── notifier.py
│       │   ├── planner.py
│       │   ├── profiler.py
│       │   ├── reporter.py
│       │   ├── scorer.py
│       │   └── searcher.py
│       ├── config
│       │   ├── __pycache__
│       │   │   ├── headers.cpython-312.pyc
│       │   │   ├── paths.cpython-312.pyc
│       │   │   ├── prompts.cpython-312.pyc
│       │   │   ├── schemas.cpython-312.pyc
│       │   │   └── settings.cpython-312.pyc
│       │   ├── headers.py
│       │   ├── paths.py
│       │   ├── prompts.py
│       │   ├── schemas.py
│       │   └── settings.py
│       ├── data
│       │   ├── cover_letters
│       │   │   ├── 20251126_030736_cover_letter.docx
│       │   │   ├── 20251126_031625_cover_letter.docx
│       │   │   └── 20251126_032404_cover_letter.docx
│       │   ├── job_listings
│       │   │   ├── raw
│       │   │   │   ├── 20251126_030736_duunitori_agentic_ai.json
│       │   │   │   ├── 20251126_030736_duunitori_ai_engineer.json
│       │   │   │   ├── 20251126_030736_duunitori_c#_developer.json
│       │   │   │   ├── 20251126_030736_duunitori_c#_engineer.json
│       │   │   │   ├── 20251126_030736_duunitori_c++_developer.json
│       │   │   │   ├── 20251126_030736_duunitori_c++_engineer.json
│       │   │   │   ├── 20251126_030736_duunitori_java_engineer.json
│       │   │   │   ├── 20251126_030736_duunitori_javascript_developer.json
│       │   │   │   ├── 20251126_030736_duunitori_junior_c#_developer.json
│       │   │   │   ├── 20251126_030736_duunitori_junior_c++_developer.json
│       │   │   │   ├── 20251126_030736_duunitori_kotlin_engineer.json
│       │   │   │   ├── 20251126_030736_duunitori_llm_engineer.json
│       │   │   │   ├── 20251126_030736_duunitori_machine_learning_engineer.json
│       │   │   │   ├── 20251126_030736_duunitori_ml_engineer.json
│       │   │   │   ├── 20251126_030736_duunitori_python_developer.json
│       │   │   │   ├── 20251126_030736_duunitori_python_engineer.json
│       │   │   │   ├── 20251126_030736_duunitori_sql_engineer.json
│       │   │   │   ├── 20251126_031625_duunitori_agentic_ai.json
│       │   │   │   ├── 20251126_031625_duunitori_ai_engineer.json
│       │   │   │   ├── 20251126_031625_duunitori_c#_developer.json
│       │   │   │   ├── 20251126_031625_duunitori_c#_engineer.json
│       │   │   │   ├── 20251126_031625_duunitori_c++_developer.json
│       │   │   │   ├── 20251126_031625_duunitori_c++_engineer.json
│       │   │   │   ├── 20251126_031625_duunitori_java_engineer.json
│       │   │   │   ├── 20251126_031625_duunitori_javascript_developer.json
│       │   │   │   ├── 20251126_031625_duunitori_junior_c#_developer.json
│       │   │   │   ├── 20251126_031625_duunitori_junior_c++_developer.json
│       │   │   │   ├── 20251126_031625_duunitori_kotlin_engineer.json
│       │   │   │   ├── 20251126_031625_duunitori_llm_engineer.json
│       │   │   │   ├── 20251126_031625_duunitori_machine_learning_engineer.json
│       │   │   │   ├── 20251126_031625_duunitori_ml_engineer.json
│       │   │   │   ├── 20251126_031625_duunitori_python_developer.json
│       │   │   │   ├── 20251126_031625_duunitori_python_engineer.json
│       │   │   │   ├── 20251126_031625_duunitori_sql_engineer.json
│       │   │   │   ├── 20251126_032404_duunitori_agentic_ai.json
│       │   │   │   ├── 20251126_032404_duunitori_ai_engineer.json
│       │   │   │   ├── 20251126_032404_duunitori_c#_developer.json
│       │   │   │   ├── 20251126_032404_duunitori_c#_engineer.json
│       │   │   │   ├── 20251126_032404_duunitori_c++_developer.json
│       │   │   │   ├── 20251126_032404_duunitori_c++_engineer.json
│       │   │   │   ├── 20251126_032404_duunitori_java_engineer.json
│       │   │   │   ├── 20251126_032404_duunitori_javascript_developer.json
│       │   │   │   ├── 20251126_032404_duunitori_junior_c#_developer.json
│       │   │   │   ├── 20251126_032404_duunitori_junior_c++_developer.json
│       │   │   │   ├── 20251126_032404_duunitori_kotlin_engineer.json
│       │   │   │   ├── 20251126_032404_duunitori_llm_engineer.json
│       │   │   │   ├── 20251126_032404_duunitori_machine_learning_engineer.json
│       │   │   │   ├── 20251126_032404_duunitori_ml_engineer.json
│       │   │   │   ├── 20251126_032404_duunitori_python_developer.json
│       │   │   │   ├── 20251126_032404_duunitori_python_engineer.json
│       │   │   │   └── 20251126_032404_duunitori_sql_engineer.json
│       │   │   └── scored
│       │   │       ├── 20251126_030736_scored_jobs.json
│       │   │       ├── 20251126_031625_scored_jobs.json
│       │   │       └── 20251126_032404_scored_jobs.json
│       │   └── reports
│       │       ├── 20251126_030736_job_report.txt
│       │       ├── 20251126_031625_job_report.txt
│       │       └── 20251126_032404_job_report.txt
│       ├── main.py
│       └── utils
│           ├── __init__.py
│           ├── __pycache__
│           │   ├── __init__.cpython-312.pyc
│           │   ├── llms.cpython-312.pyc
│           │   ├── normalization.cpython-312.pyc
│           │   └── queries.cpython-312.pyc
│           ├── llms.py
│           ├── normalization.py
│           ├── queries.py
│           └── scrapers
│               ├── __pycache__
│               │   ├── duunitori.cpython-312.pyc
│               │   └── jobly.cpython-312.pyc
│               ├── duunitori.py
│               └── jobly.py
├── tests
│   ├── fixtures
│   │   ├── duunitori_detail.html
│   │   ├── duunitori_page_1.html
│   │   └── duunitori_page_empty.html
│   ├── test_build_queries.py
│   ├── test_scorer_agent.py
│   ├── test_scraper_duunitori.py
│   └── test_searcher_agent.py
├── uv.lock
└── uv.toml

28 directories, 123 files
```

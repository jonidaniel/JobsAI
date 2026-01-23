# Project Structure

This document describes the complete directory structure and organization of the JobsAI project.

## Root Directory

```
JobsAI/
├── .github/                    # GitHub configuration
│   └── workflows/
│       └── deploy.yml          # CI/CD deployment workflow
├── docs/                       # Project documentation
│   ├── architecture.md         # System architecture overview
│   ├── changelog.md            # Version history
│   ├── configuration.md        # Configuration guide
│   ├── deployment.md           # AWS deployment guide
│   ├── dev_diary.md            # Development diary
│   ├── frontend.md             # Frontend documentation
│   ├── project-structure.md    # This file
│   └── rate-limiting.md        # Rate limiting documentation
├── frontend/                   # React frontend application
│   ├── src/                    # Source code
│   ├── public/                 # Static assets
│   ├── dist/                   # Production build output
│   ├── node_modules/           # Dependencies
│   ├── .gitignore              # Frontend-specific gitignore
│   ├── eslint.config.js        # ESLint configuration
│   ├── index.html              # HTML template
│   ├── package.json            # Dependencies and scripts
│   ├── package-lock.json       # Lock file
│   ├── postcss.config.js       # PostCSS configuration
│   ├── tailwind.config.js      # Tailwind CSS configuration
│   ├── tsconfig.json           # TypeScript configuration
│   ├── tsconfig.node.json      # TypeScript node config
│   ├── vite.config.ts          # Vite configuration
│   └── vitest.config.ts        # Vitest test configuration
├── src/                        # Python backend source code
│   └── jobsai/                 # Main package
│       ├── agents/             # Agent and service classes
│       ├── api/                # FastAPI server and routes
│       ├── config/             # Configuration and schemas
│       ├── utils/              # Utility functions
│       └── main.py             # Pipeline orchestration
├── tests/                      # Backend test suite
│   ├── fixtures/               # Test fixtures (HTML files)
│   └── test_*.py               # Test files
├── lambda_handler.py           # Lambda entry point (API Gateway)
├── lambda_worker.py            # Lambda worker (async pipeline)
├── .gitignore                  # Git ignore rules
├── .python-version             # Python version specification
├── LICENSE                     # License file
├── pyproject.toml              # Python project configuration
├── pytest.ini                  # Pytest configuration
├── README.md                   # Main project README
├── uv.lock                     # UV lock file
└── uv.toml                     # UV configuration
```

## Frontend Structure

```
frontend/src/
├── assets/                     # Static assets
│   ├── icons/
│   │   └── favicon.ico         # Favicon
│   └── imgs/
│       └── face.png            # Images
├── components/                 # React components
│   ├── __tests__/              # Component tests
│   │   ├── ErrorBoundary.test.jsx
│   │   ├── Search.test.jsx
│   │   ├── Search.email.test.jsx
│   │   ├── Search.integration.test.jsx
│   │   └── Search.scroll.test.jsx
│   ├── actions/                # Action components
│   │   └── ActionButtons.tsx   # Submit/Cancel buttons
│   ├── delivery/               # Delivery method components
│   │   ├── DeliveryMethodSelector.tsx
│   │   └── types.ts
│   ├── download/               # Download components
│   │   └── DownloadPrompt.tsx
│   ├── messages/               # Message components
│   │   ├── __tests__/
│   │   │   └── ErrorMessage.test.jsx
│   │   └── ErrorMessage.tsx
│   ├── progress/               # Progress components
│   │   └── ProgressTracker.tsx
│   ├── questions/               # Question input components
│   │   ├── __tests__/
│   │   │   ├── MultipleChoice.test.jsx
│   │   │   ├── SingleChoice.test.jsx
│   │   │   ├── Slider.test.jsx
│   │   │   └── TextField.test.jsx
│   │   ├── MultipleChoice.tsx  # Checkbox group
│   │   ├── SingleChoice.tsx   # Radio button group
│   │   ├── Slider.tsx          # Range slider
│   │   └── TextField.tsx       # Text input/textarea
│   ├── status/                 # Status components
│   │   └── StatusMessages.tsx
│   ├── Contact.tsx             # Contact section
│   ├── ErrorBoundary.tsx       # Error boundary
│   ├── Hero.tsx                # Landing section
│   ├── NavBar.tsx              # Navigation bar
│   ├── QuestionSet.tsx         # Single question set renderer
│   ├── QuestionSetList.tsx     # Question set manager
│   └── Search.tsx              # Main search/questionnaire component
├── config/                     # Configuration files
│   ├── api.ts                  # API endpoint configuration
│   ├── constants.ts            # Application constants
│   ├── generalQuestions.ts     # General questions configuration
│   ├── questionSet.ts          # Question set names and titles
│   └── sliders.ts              # Slider configuration
├── hooks/                      # Custom React hooks
│   ├── useDownload.ts          # Document download hook
│   ├── useFormSubmission.ts    # Form submission hook
│   └── usePipelinePolling.ts   # Pipeline progress polling hook
├── styles/                     # CSS stylesheets
│   ├── App.css                 # App-level styles
│   ├── contact.css             # Contact section styles
│   ├── font.css                # Font definitions
│   ├── hero.css                # Hero section styles
│   ├── index.css               # Global styles (Tailwind imports)
│   ├── nav.css                 # Navigation styles
│   └── search.css              # Search component styles
├── test/                       # Test configuration
│   ├── COVERAGE.md             # Test coverage documentation
│   ├── README.md               # Test documentation
│   └── setup.js                # Test setup file
├── types/                      # TypeScript type definitions
│   └── index.ts                # All type definitions
├── utils/                      # Utility functions
│   ├── __tests__/
│   │   ├── fileDownload.test.js
│   │   └── validation.test.js
│   ├── errorMessages.ts        # Error message utilities
│   ├── fileDownload.ts         # File download utilities
│   ├── formDataTransform.ts    # Form data transformation
│   ├── labelRenderer.tsx       # Label rendering utilities
│   └── validation.ts           # Form validation logic
├── App.tsx                     # Root component
├── main.tsx                    # Application entry point
└── vite-env.d.ts               # Vite type definitions
```

## Backend Structure

```
src/jobsai/
├── agents/                     # Agent and service classes
│   ├── __init__.py             # Agent exports
│   ├── analyzer.py             # AnalyzerAgent - job analysis
│   ├── generator.py            # GeneratorAgent - cover letter generation
│   ├── profiler.py             # ProfilerAgent - profile creation
│   ├── query_builder.py        # QueryBuilderAgent - keyword generation
│   ├── scorer.py               # ScorerService - job scoring
│   └── searcher.py             # SearcherService - job searching
├── api/                        # FastAPI server and routes
│   ├── __init__.py
│   ├── server.py               # FastAPI application setup
│   ├── handlers/               # Request handlers
│   │   ├── __init__.py
│   │   ├── exceptions.py       # Exception handlers
│   │   └── lambda_invocation.py # Lambda invocation utilities
│   ├── middleware/             # Middleware
│   │   ├── __init__.py
│   │   ├── logging.py          # Request logging middleware
│   │   └── rate_limiting.py    # Rate limiting middleware
│   ├── routes/                 # API routes
│   │   ├── __init__.py
│   │   ├── download.py         # Download endpoint
│   │   └── pipeline.py         # Pipeline endpoints (start, progress, cancel)
│   └── utils/                  # API utilities
│       ├── __init__.py
│       └── state_helpers.py    # State management helpers
├── config/                     # Configuration and schemas
│   ├── __init__.py             # Config exports
│   ├── aliases.py              # Skill alias mappings
│   ├── headers.py              # HTTP headers configuration
│   ├── paths.py                # File system paths
│   ├── profile_schemas.py       # Profile data schemas
│   ├── prompts.py              # LLM prompts
│   ├── request_schemas.py      # Request validation schemas
│   ├── schemas.py              # Legacy schemas (deprecated, re-exports)
│   └── validation_constants.py  # Validation constants
├── utils/                      # Utility functions
│   ├── __init__.py
│   ├── dynamodb_manager.py     # DynamoDB operations
│   ├── email_service.py        # AWS SES email service
│   ├── exceptions.py           # Custom exceptions
│   ├── form_data.py            # Form data extraction
│   ├── llms.py                 # OpenAI API integration
│   ├── logger.py               # Structured logging
│   ├── normalization.py        # Text/data normalization
│   ├── presigned_urls.py      # S3 presigned URL generation
│   ├── rate_limiter.py         # Rate limiting utilities
│   ├── s3_manager.py           # S3 operations
│   ├── scrapers/               # Job board scrapers
│   │   ├── base.py             # Base scraper class
│   │   ├── configs.py           # Scraper configurations
│   │   ├── duunitori.py         # Duunitori scraper
│   │   └── jobly.py             # Jobly scraper
│   └── state_manager.py        # State management (DynamoDB/S3)
└── main.py                     # Pipeline orchestration
```

## Test Structure

```
tests/
├── fixtures/                   # Test fixtures
│   ├── duunitori_detail.html   # Duunitori job detail page HTML
│   ├── duunitori_page_1.html   # Duunitori search results HTML
│   └── duunitori_page_empty.html # Empty results HTML
├── test_analyzer_agent.py      # AnalyzerAgent tests
├── test_api_integration.py     # API integration tests
├── test_form_data.py           # Form data extraction tests
├── test_generator_agent.py     # GeneratorAgent tests
├── test_integration_pipeline.py # Complete pipeline integration tests
├── test_main.py                # Main pipeline tests
├── test_profiler_agent.py      # ProfilerAgent tests
├── test_query_builder_agent.py # QueryBuilderAgent tests
├── test_scorer_service.py      # ScorerService tests
├── test_scraper_duunitori.py   # Duunitori scraper tests
├── test_searcher_service.py    # SearcherService tests
├── test_selector_configs.py    # Scraper selector tests
├── test_server.py              # API server tests
└── test_state_manager.py       # State manager tests
```

## Key Files

### Entry Points

- **`lambda_handler.py`**: AWS Lambda handler for API Gateway requests
- **`lambda_worker.py`**: AWS Lambda handler for async pipeline execution
- **`frontend/src/main.tsx`**: Frontend application entry point
- **`src/jobsai/main.py`**: Backend pipeline orchestration

### Configuration Files

- **`pyproject.toml`**: Python project configuration (dependencies, build settings)
- **`frontend/package.json`**: Frontend dependencies and scripts
- **`pytest.ini`**: Pytest configuration
- **`uv.toml`**: UV package manager configuration

### Documentation

- **`README.md`**: Main project documentation
- **`docs/`**: Comprehensive documentation directory
  - `architecture.md`: System architecture
  - `frontend.md`: Frontend documentation
  - `configuration.md`: Configuration guide
  - `deployment.md`: AWS deployment guide
  - `rate-limiting.md`: Rate limiting documentation

## Directory Conventions

### Naming

- **Python files**: `snake_case.py`
- **TypeScript/React files**: `PascalCase.tsx` (components), `camelCase.ts` (utilities)
- **Directories**: `kebab-case` or `snake_case`
- **Test files**: `test_*.py` (backend), `*.test.jsx` (frontend)

### Organization

- **Components**: Grouped by feature/domain
- **Utilities**: Shared utilities in `utils/` directories
- **Configuration**: Centralized in `config/` directories
- **Tests**: Co-located with source or in `__tests__/` directories

## Build Artifacts

The following directories are generated and should not be committed:

- `frontend/dist/` - Production build output
- `frontend/node_modules/` - Node.js dependencies
- `__pycache__/` - Python bytecode cache
- `.pytest_cache/` - Pytest cache
- `*.pyc` - Compiled Python files

These are excluded via `.gitignore`.

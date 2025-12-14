# JobsAI

An agentic AI system for end-to-end automated job finding and cover letter generation. Enter your skills and preferences once, and get personalized job recommendations with AI-generated cover letters tailored to each position.

## Overview

JobsAI automates the job search process through a 6-step pipeline:

1. **Profiling** - Creates a comprehensive candidate profile from questionnaire responses
2. **Keyword Generation** - Extracts search keywords from the profile
3. **Searching** - Searches multiple job boards (Duunitori, Jobly) for relevant positions
4. **Scoring** - Scores job listings based on profile match and technology alignment
5. **Analyzing** - Analyzes top-scoring jobs and generates personalized cover letter instructions
6. **Generating** - Creates professional Word documents with personalized cover letters

## Architecture

The system uses a **serverless architecture** deployed on AWS:

- **Frontend**: React application hosted on AWS S3 (with CloudFront CDN)
- **Backend**: FastAPI application running on AWS Lambda
- **State Management**: DynamoDB for job state persistence
- **Document Storage**: S3 for generated cover letter documents
- **CI/CD**: GitHub Actions for automated deployment

### Pipeline Components

#### Agents (LLM-Powered)

1. **ProfilerAgent** (`src/jobsai/agents/profiler.py`)

   - Uses LLM to extract and structure candidate skills from form submissions
   - Creates a comprehensive text profile describing skills, experience, and professional characteristics

2. **QueryBuilderAgent** (`src/jobsai/agents/query_builder.py`)

   - Generates search keywords from the candidate profile
   - Creates optimized queries for job board searches

3. **AnalyzerAgent** (`src/jobsai/agents/analyzer.py`)

   - Analyzes top-scoring job listings
   - Generates personalized cover letter writing instructions for each position

4. **GeneratorAgent** (`src/jobsai/agents/generator.py`)
   - Creates personalized cover letter documents in Word format
   - Supports multiple writing styles (Professional, Friendly, Confident, Funny)
   - Formats documents as standard business letters

#### Services (Deterministic)

5. **SearcherService** (`src/jobsai/agents/searcher.py`)

   - Scrapes job boards (Duunitori, Jobly) for relevant positions
   - Supports "deep mode" for fetching full job descriptions
   - Deduplicates jobs across queries and boards

6. **ScorerService** (`src/jobsai/agents/scorer.py`)
   - Scores job listings based on skill profile match
   - Computes relevancy scores using keyword matching and experience alignment
   - Ranks jobs by match quality

## Technology Stack

### Backend

- **Python 3.12+** - Core language
- **FastAPI** - REST API framework
- **Mangum** - ASGI adapter for AWS Lambda
- **Pydantic** - Data validation and serialization
- **OpenAI API** - LLM-powered agents (GPT-4, GPT-3.5-turbo)
- **BeautifulSoup** - Web scraping for job boards
- **python-docx** - Word document generation
- **boto3** - AWS SDK for DynamoDB and S3
- **uv** - Fast Python package manager

### Frontend

- **React 19** - UI framework
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **Modern JavaScript (ES6+)** - Language features

### Infrastructure

- **AWS Lambda** - Serverless compute for backend
- **AWS S3** - Static hosting for frontend and document storage
- **AWS DynamoDB** - NoSQL database for job state
- **AWS API Gateway** - HTTP API for Lambda
- **GitHub Actions** - CI/CD pipeline

## Project Structure

```
JobsAI/
├── frontend/                    # React frontend application
│   ├── src/
│   │   ├── components/         # React components
│   │   │   ├── questions/      # Question components (Slider, MultipleChoice, etc.)
│   │   │   ├── messages/       # Success/Error message components
│   │   │   └── Search.jsx      # Main search/questionnaire component
│   │   ├── config/             # Configuration files (API endpoints, questions)
│   │   ├── styles/             # CSS files
│   │   └── utils/               # Utility functions (validation, file download)
│   ├── public/                 # Static assets
│   └── package.json
├── src/
│   └── jobsai/                 # Python backend
│       ├── agents/             # Agent and service classes
│       │   ├── profiler.py     # Profile generation agent
│       │   ├── query_builder.py # Keyword generation agent
│       │   ├── searcher.py     # Job search service
│       │   ├── scorer.py       # Job scoring service
│       │   ├── analyzer.py     # Job analysis agent
│       │   └── generator.py    # Cover letter generation agent
│       ├── api/                # FastAPI server
│       │   └── server.py      # API endpoints and middleware
│       ├── config/             # Configuration and schemas
│       │   ├── schemas.py      # Pydantic models for validation
│       │   ├── prompts.py     # LLM prompts
│       │   └── paths.py        # File system paths
│       ├── utils/              # Utility functions
│       │   ├── llms.py         # OpenAI API integration
│       │   ├── state_manager.py # DynamoDB/S3 state management
│       │   ├── form_data.py    # Form data extraction
│       │   └── scrapers/       # Job board scrapers
│       └── main.py             # Pipeline orchestration
├── lambda_handler.py            # Lambda entry point (API Gateway)
├── lambda_worker.py            # Lambda worker (async pipeline execution)
├── .github/
│   └── workflows/
│       └── deploy.yml          # GitHub Actions deployment workflow
├── docs/                       # Project documentation
├── tests/                      # Test files
└── README.md                   # This file
```

## Setup

### Prerequisites

- **Python 3.12+**
- **Node.js 20.x+** (for frontend)
- **uv** package manager (recommended for Python)
- **AWS Account** (for deployment)
- **OpenAI API Key** (for LLM operations)

### Local Development Setup

#### Backend Setup

1. **Install dependencies using uv:**

   ```bash
   uv sync
   ```

2. **Set up environment variables:**
   Create a `.env` file in the project root:

   ```
   OPENAI_API_KEY=your_api_key_here
   OPENAI_MODEL=gpt-4  # or gpt-3.5-turbo
   ```

3. **Run the FastAPI server:**

   ```bash
   uv run python -m uvicorn jobsai.api.server:app --reload --app-dir src
   ```

   The API will be available at `http://localhost:8000`

#### Frontend Setup

1. **Navigate to frontend directory:**

   ```bash
   cd frontend
   ```

2. **Install dependencies:**

   ```bash
   npm install
   ```

3. **Start development server:**

   ```bash
   npm run dev
   ```

   The frontend will be available at `http://localhost:3000`

### AWS Deployment

The project includes automated deployment via GitHub Actions. See the deployment workflow in `.github/workflows/deploy.yml`.

**Required AWS Resources:**

- Lambda function for backend API
- S3 bucket for frontend hosting
- S3 bucket for document storage
- DynamoDB table for job state
- API Gateway or Lambda Function URL

**Required GitHub Secrets:**

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`
- `LAMBDA_FUNCTION_NAME`
- `S3_BUCKET_NAME` (for frontend)
- `VITE_API_BASE_URL` (API Gateway/Function URL)
- `CLOUDFRONT_DISTRIBUTION_ID` (optional, for CDN)

**Lambda Environment Variables (for rate limiting):**

- `RATE_LIMIT_REQUESTS` (optional, default: 5) - Max requests per window
- `RATE_LIMIT_WINDOW_SECONDS` (optional, default: 3600) - Time window in seconds
- `RATE_LIMIT_ENABLED` (optional, default: true) - Enable/disable rate limiting

For detailed deployment instructions, see the documentation in `docs/`.

## Usage

### Local Development

1. **Start both servers** (backend and frontend)
2. **Open the frontend** in your browser (`http://localhost:3000`)
3. **Fill out the questionnaire:**
   - General questions (job level, job boards, deep mode, cover letter preferences)
   - Technology experience levels (8 sets: languages, databases, cloud, frameworks, etc.)
   - Personal description
4. **Click "Find Jobs"** to trigger the pipeline
5. **Monitor progress** via the progress messages
6. **Download** the generated cover letter document (.docx) when complete

### Production (Deployed)

The deployed application works the same way, but:

- Pipeline runs asynchronously in a separate Lambda invocation
- Progress is tracked via DynamoDB (persistent across containers)
- Documents are stored in S3 and downloaded via presigned URLs
- Frontend polls the API every 2 seconds for progress updates

## API Endpoints

### Async Pipeline (Recommended)

- `POST /api/start` - Start pipeline, returns `job_id`
- `GET /api/progress/{job_id}` - Poll for progress updates
- `GET /api/download/{job_id}` - Get presigned S3 URL for document download
- `POST /api/cancel/{job_id}` - Cancel a running pipeline

### Legacy Synchronous Endpoint

- `POST /api/endpoint` - Run pipeline synchronously (returns document directly)

## Documentation

Comprehensive documentation is available in the `docs/` directory:

- **API**: `docs/api.md` - API endpoint documentation
- **Architecture**: `docs/architecture.md` - System architecture overview
- **Configuration**: `docs/configuration.md` - Environment variables and settings
- **Deployment**: `docs/deployment.md` - AWS deployment guide
- **Rate Limiting**: `docs/rate-limiting.md` - Rate limiting configuration and usage
- **Frontend**: `docs/frontend.md` - Frontend architecture and components
- **User Guide**: `docs/user-guide.md` - End-user instructions
- **How-To**: `docs/how-to.md` - Development and setup guides
- **Project Structure**: `docs/project-structure.md` - Detailed file organization

## Development

### Running Tests

```bash
uv run pytest
```

### Code Style

- **Python**: Follow PEP 8 conventions, Google-style docstrings
- **JavaScript**: ESLint configuration included
- **Frontend**: Uses Tailwind CSS for styling

### Key Design Decisions

- **Serverless Architecture**: Lambda + S3 + DynamoDB for scalability and cost efficiency
- **Async Pipeline Execution**: Worker Lambda pattern for long-running tasks
- **State Persistence**: DynamoDB ensures state survives across Lambda containers
- **Presigned S3 URLs**: Direct downloads bypass API Gateway binary encoding issues
- **Polling over SSE**: More reliable with API Gateway's 29-second timeout limit

## License

© 2025 Joni Mäkinen

## Version

1.0.0

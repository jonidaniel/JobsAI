# JobsAI Architecture

## Overview

JobsAI is a serverless, agentic AI system that automates job searching and cover letter generation. The architecture is designed for scalability, cost efficiency, and reliability using AWS serverless services.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Browser                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ HTTPS
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CloudFront CDN (Optional)                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ HTTPS
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    S3 Bucket (Frontend)                         │
│              Static React Application                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ API Calls
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API Gateway / Function URL                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ HTTP Events
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Lambda Function (API Handler)                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  FastAPI Application (via Mangum)                       │  │
│  │  - /api/start: Start pipeline, return job_id             │  │
│  │  - /api/progress/{job_id}: Poll for progress            │  │
│  │  - /api/download/{job_id}: Get presigned S3 URL          │  │
│  │  - /api/cancel/{job_id}: Cancel pipeline                │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Async Invocation
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Lambda Function (Worker)                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Pipeline Execution                                       │  │
│  │  1. ProfilerAgent: Create candidate profile              │  │
│  │  2. QueryBuilderAgent: Generate search keywords          │  │
│  │  3. SearcherService: Scrape job boards                   │  │
│  │  4. ScorerService: Score job listings                    │  │
│  │  5. AnalyzerAgent: Generate cover letter instructions    │  │
│  │  6. GeneratorAgent: Create Word documents               │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────┬───────────────────────────────┬────────────────────┘
             │                               │
             │                               │
             ▼                               ▼
┌──────────────────────────┐    ┌──────────────────────────┐
│      DynamoDB            │    │      S3 Bucket           │
│  - Job state             │    │  - Generated documents   │
│  - Progress updates      │    │  - Presigned URLs       │
│  - Rate limiting data    │    │                          │
└──────────────────────────┘    └──────────────────────────┘
```

## Component Details

### Frontend Layer

**Technology**: React 19, Vite, Tailwind CSS

**Hosting**: AWS S3 (static website hosting)

**CDN**: CloudFront (optional, for global distribution)

**Responsibilities**:

- User interface for questionnaire
- Form validation
- API communication
- Progress polling
- Document download

**Key Components**:

- `Search.jsx`: Main questionnaire and submission component
- `QuestionSetList.jsx`: Manages multiple question sets
- `QuestionSet.jsx`: Individual question set container
- Question components: `Slider`, `MultipleChoice`, `SingleChoice`, `TextField`

### API Layer

**Technology**: FastAPI, Mangum (ASGI adapter for Lambda)

**Hosting**: AWS Lambda (via API Gateway or Function URL)

**Responsibilities**:

- Request validation (Pydantic schemas)
- Rate limiting (IP-based, DynamoDB-backed)
- CORS handling
- Job state management
- Async Lambda invocation

**Endpoints**:

- `POST /api/start`: Start pipeline, returns `job_id`
- `GET /api/progress/{job_id}`: Poll for progress updates
- `GET /api/download/{job_id}`: Get presigned S3 URL for document download
- `POST /api/cancel/{job_id}`: Cancel a running pipeline

**Middleware**:

- Request logging
- Rate limiting (applied to `/api/start` only)
- CORS (configurable origins)

### Worker Layer

**Technology**: Python 3.12, AWS Lambda

**Hosting**: AWS Lambda (async invocation)

**Responsibilities**:

- Execute complete pipeline (6 steps)
- Update progress in DynamoDB
- Store documents in S3
- Handle cancellation requests

**Pipeline Steps**:

1. **Profiling**: LLM extracts candidate skills from form data
2. **Keyword Generation**: LLM creates search keywords from profile
3. **Searching**: Scrapes job boards (Duunitori, Jobly) for positions
4. **Scoring**: Scores jobs based on profile match and technology alignment
5. **Analyzing**: LLM generates personalized cover letter instructions
6. **Generating**: LLM creates cover letter content, formats as Word document

### Data Layer

#### DynamoDB

**Table**: `jobsai-pipeline-states` (configurable)

**Schema**:

- **Primary Key**: `job_id` (String, UUID)
- **Attributes**:
  - `status` (String): `running`, `complete`, `error`, `cancelled`
  - `progress` (String, JSON): Current phase and message
  - `result` (String, JSON): Document metadata (S3 keys, filenames)
  - `error` (String): Error message if failed
  - `created_at` (String, ISO format): Job creation timestamp
  - `ttl` (Number): Unix timestamp for automatic cleanup (1 hour)

**Usage**:

- Job state persistence across Lambda containers
- Progress updates during pipeline execution
- Rate limiting counters (optional separate table)
- Cancellation flags

**TTL**: Automatic cleanup after 1 hour

#### S3

**Buckets**:

1. **Frontend Bucket**: Static website hosting for React app
2. **Documents Bucket**: Storage for generated cover letters

**Document Storage**:

- **Path**: `documents/{job_id}/{filename}`
- **Format**: `.docx` (Word documents)
- **Access**: Presigned URLs (1-hour expiration)
- **Content-Type**: `application/vnd.openxmlformats-officedocument.wordprocessingml.document`

## Data Flow

### 1. Job Submission Flow

```
User → Frontend → API Gateway → Lambda (API Handler)
                                      │
                                      ├─→ Rate Limit Check (DynamoDB)
                                      ├─→ Validate Payload (Pydantic)
                                      ├─→ Create Job State (DynamoDB)
                                      └─→ Invoke Worker Lambda (Async)
                                          │
                                          └─→ Lambda (Worker)
                                              │
                                              ├─→ Update Progress (DynamoDB)
                                              ├─→ Execute Pipeline
                                              ├─→ Store Documents (S3)
                                              └─→ Update Status (DynamoDB)
```

### 2. Progress Polling Flow

```
User → Frontend → API Gateway → Lambda (API Handler)
                                      │
                                      └─→ Read Job State (DynamoDB)
                                          │
                                          └─→ Return Progress JSON
```

### 3. Document Download Flow

```
User → Frontend → API Gateway → Lambda (API Handler)
                                      │
                                      ├─→ Read Job State (DynamoDB)
                                      ├─→ Generate Presigned URL (S3)
                                      └─→ Return URL to Frontend
                                          │
                                          └─→ Frontend → S3 (Direct Download)
```

## Design Patterns

### 1. Serverless Architecture

- **No servers to manage**: All compute is serverless (Lambda)
- **Auto-scaling**: Lambda scales automatically with demand
- **Pay-per-use**: Costs scale with actual usage
- **High availability**: AWS manages infrastructure redundancy

### 2. Async Pipeline Execution

- **Worker Lambda Pattern**: Long-running tasks in separate Lambda invocation
- **Non-blocking API**: API responds immediately with `job_id`
- **State-based communication**: Progress via DynamoDB, not direct responses
- **Timeout handling**: Worker can run up to 15 minutes (Lambda max)

### 3. State Persistence

- **DynamoDB for state**: Survives Lambda container lifecycle
- **S3 for documents**: Binary data storage with presigned URLs
- **TTL for cleanup**: Automatic removal of old data

### 4. Rate Limiting

- **IP-based tracking**: Prevents abuse from single source
- **DynamoDB-backed**: Persistent across Lambda invocations
- **Fail-open**: Service continues if rate limiting fails
- **Configurable limits**: Environment variable control

### 5. Presigned S3 URLs

- **Direct downloads**: Bypass API Gateway binary encoding issues
- **Time-limited access**: URLs expire after 1 hour
- **No API overhead**: Reduces Lambda execution time and costs
- **Secure**: Signed URLs prevent unauthorized access

## Scalability Considerations

### Horizontal Scaling

- **Lambda**: Automatically scales to handle concurrent requests
- **DynamoDB**: Handles high read/write throughput
- **S3**: Unlimited storage and bandwidth

### Bottlenecks

1. **OpenAI API Rate Limits**: LLM calls may be rate-limited
   - **Mitigation**: Retry logic with exponential backoff
2. **Job Board Scraping**: Sequential scraping may be slow
   - **Mitigation**: Parallel requests where possible, deep mode optional
3. **DynamoDB Hot Partitions**: Rate limiting may create hot partitions
   - **Mitigation**: Optional separate table for rate limiting

### Cost Optimization

- **Lambda Reserved Concurrency**: Limit concurrent executions (recommended)
- **DynamoDB On-Demand**: Pay only for what you use
- **S3 Lifecycle Policies**: Archive old documents to Glacier (optional)
- **CloudFront Caching**: Reduce S3 requests for frontend

## Security

### Network Security

- **HTTPS Only**: All traffic encrypted in transit
- **CORS**: Configurable allowed origins
- **API Gateway**: AWS-managed DDoS protection

### Access Control

- **IAM Roles**: Lambda execution roles with least privilege
- **S3 Bucket Policies**: Private buckets, presigned URLs for access
- **DynamoDB IAM**: Table-level access control

### Data Protection

- **No PII Storage**: Only job state and documents (no personal info)
- **TTL Cleanup**: Automatic deletion of old data
- **Presigned URLs**: Time-limited document access

## Monitoring & Observability

### Logging

- **CloudWatch Logs**: All Lambda logs automatically captured
- **Structured Logging**: Consistent log format across components
- **Request Logging**: All API requests logged

### Metrics (Recommended)

- Lambda invocations, errors, duration
- DynamoDB read/write capacity, throttling
- S3 request counts, data transfer
- API Gateway request counts, latency

### Alerts (Recommended)

- Lambda error rate > threshold
- DynamoDB throttling
- Rate limit hits
- Pipeline failure rate

## Deployment

### CI/CD

- **GitHub Actions**: Automated deployment on push to `main`
- **Two-stage deployment**: Frontend first, then backend
- **Zero-downtime**: Lambda updates are atomic

### Infrastructure

- **Manual Setup**: AWS resources created manually (see `docs/deployment.md`)
- **No IaC**: Currently no Terraform/CloudFormation (future improvement)

## Future Improvements

1. **Infrastructure as Code**: Terraform/CloudFormation for reproducible deployments
2. **Monitoring**: CloudWatch dashboards and alarms
3. **User Authentication**: Per-user rate limits and usage tracking
4. **Queue System**: SQS for better backpressure handling
5. **Caching**: Redis/ElastiCache for frequently accessed data
6. **Multi-region**: Global distribution for lower latency

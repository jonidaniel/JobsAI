# CloudWatch Logging Guide

## Overview

JobsAI uses structured JSON logging optimized for CloudWatch Logs Insights. All logs are formatted as JSON with consistent fields for easy querying, filtering, and analysis.

## Log Format

All logs are structured as JSON with the following base fields:

```json
{
  "timestamp": "2025-01-15 10:30:45",
  "level": "INFO",
  "logger": "jobsai.api.server",
  "message": "Pipeline started",
  "aws_request_id": "abc-123-def",
  "function_name": "jobsai-api",
  "function_version": "$LATEST",
  "memory_limit_mb": 1024,
  "request_id": "req-123",
  "job_id": "job-456",
  "duration_ms": 1234.56,
  "http_method": "POST",
  "http_path": "/api/start",
  "http_status_code": 200,
  "client_ip": "1.2.3.4"
}
```

## Correlation IDs

Correlation IDs enable tracing requests across Lambda invocations:

- **`request_id`**: Unique identifier for API requests (from API Gateway or Lambda context)
- **`job_id`**: Unique identifier for pipeline jobs (UUID)

These IDs are automatically added to all log records when set, allowing you to trace a single request or job through multiple Lambda invocations.

## Log Levels

Log levels are controlled via the `LOG_LEVEL` environment variable:

- **DEBUG**: Detailed diagnostic information (development only)
- **INFO**: General informational messages (default)
- **WARNING**: Warning messages for potential issues
- **ERROR**: Error messages for failures
- **CRITICAL**: Critical errors requiring immediate attention

**Default**: `INFO` (set `LOG_LEVEL=DEBUG` for development)

## CloudWatch Logs Insights Queries

### Find All Errors

```sql
fields @timestamp, level, message, error, job_id, request_id
| filter level = "ERROR"
| sort @timestamp desc
| limit 100
```

### Trace a Specific Job

```sql
fields @timestamp, level, message, operation, duration_ms
| filter job_id = "your-job-id-here"
| sort @timestamp asc
```

### Find Slow Operations

```sql
fields @timestamp, operation, duration_ms, job_id
| filter duration_ms > 5000
| sort duration_ms desc
| limit 50
```

### API Request Statistics

```sql
fields @timestamp, http_method, http_path, http_status_code, duration_ms
| filter ispresent(http_method)
| stats count() as requests, avg(duration_ms) as avg_duration, max(duration_ms) as max_duration by http_path, http_status_code
```

### Pipeline Success Rate

```sql
fields @timestamp, job_id, status
| filter ispresent(job_id) and (status = "success" or status = "error")
| stats count() as total, sum(status = "success") as successes, sum(status = "error") as errors by bin(5m)
```

### Rate Limit Hits

```sql
fields @timestamp, client_ip, http_path, message
| filter message like /rate limit exceeded/i
| stats count() as hits by client_ip
| sort hits desc
```

### LLM Call Performance

```sql
fields @timestamp, operation, duration_ms, model
| filter operation = "llm_call"
| stats avg(duration_ms) as avg_ms, max(duration_ms) as max_ms, count() as calls by model
```

### Error Trends

```sql
fields @timestamp, level, exception_type, job_id
| filter level = "ERROR"
| stats count() as error_count by exception_type, bin(1h)
| sort error_count desc
```

## Usage Examples

### Basic Logging

```python
from jobsai.utils.logger import get_logger

logger = get_logger(__name__)
logger.info("Pipeline started", extra={"extra_fields": {"job_id": "123", "phase": "profiling"}})
```

### Performance Logging

```python
from jobsai.utils.logger import log_performance

with log_performance("llm_call", model="gpt-4", tokens=500):
    result = call_llm(...)
```

### Request Logging (FastAPI)

```python
from jobsai.utils.logger import log_request

@app.post("/api/start")
@log_request
async def start_pipeline(payload: FrontendPayload):
    ...
```

### Lambda Handler Logging

```python
from jobsai.utils.logger import log_request, configure_logging

@log_request
def handler(event, context):
    configure_logging(context)
    ...
```

## Best Practices

### 1. Use Structured Fields

Always include relevant context in log records:

```python
# Good
logger.info("Job completed", extra={"extra_fields": {"job_id": job_id, "documents": len(docs)}})

# Bad
logger.info(f"Job {job_id} completed with {len(docs)} documents")
```

### 2. Set Correlation IDs Early

Set correlation IDs at the start of request processing:

```python
from jobsai.utils.logger import set_correlation_id

# In Lambda handler
set_correlation_id(request_id=context.aws_request_id, job_id=event.get("job_id"))
```

### 3. Log Performance for Expensive Operations

Use `log_performance` for operations that might be slow:

```python
with log_performance("job_search", board="Duunitori", queries=len(keywords)):
    jobs = searcher.search_jobs(keywords, ...)
```

### 4. Include Error Context

Always include relevant context when logging errors:

```python
try:
    result = risky_operation()
except Exception as e:
    logger.error(
        "Operation failed",
        extra={"extra_fields": {"job_id": job_id, "operation": "scoring", "error": str(e)}},
        exc_info=True,
    )
```

### 5. Avoid Logging Sensitive Data

Never log:

- API keys or secrets
- Personal information (PII)
- Full request/response bodies (log summaries instead)

## Log Retention

CloudWatch Logs retention is configured at the log group level:

- **Default**: Never expire (manual cleanup required)
- **Recommended**: 7-30 days for production
- **Cost consideration**: Longer retention = higher costs

Configure retention:

```bash
aws logs put-retention-policy \
  --log-group-name /aws/lambda/jobsai-api \
  --retention-in-days 30
```

## Monitoring and Alerts

### Create CloudWatch Alarms

Monitor error rates:

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name jobsai-error-rate \
  --alarm-description "Alert on high error rate" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1 \
  --alarm-actions arn:aws:sns:us-east-1:ACCOUNT:jobsai-alerts
```

### Log-Based Metrics

Create custom metrics from log patterns:

```bash
aws logs put-metric-filter \
  --log-group-name /aws/lambda/jobsai-api \
  --filter-name pipeline-errors \
  --filter-pattern '[timestamp, level=ERROR, ...]' \
  --metric-transformations \
    metricName=PipelineErrors,metricNamespace=JobsAI,metricValue=1
```

## Troubleshooting

### Logs Not Appearing

1. Check Lambda execution role has `logs:CreateLogGroup` and `logs:CreateLogStream` permissions
2. Verify log group exists: `/aws/lambda/jobsai-api`
3. Check log level is not too restrictive (e.g., ERROR when logging INFO)

### Logs Not in JSON Format

1. Verify `configure_logging()` is called in Lambda handler
2. Check that `CloudWatchJSONFormatter` is being used
3. Ensure no other logging configuration is overriding the formatter

### Correlation IDs Missing

1. Verify `set_correlation_id()` is called early in request processing
2. Check that correlation IDs are set before logging
3. Ensure context is passed to `configure_logging(context)`

## Related Documentation

- **Architecture**: See `docs/architecture.md` for system design
- **Configuration**: See `docs/configuration.md` for environment variables
- **Deployment**: See `docs/deployment.md` for AWS setup

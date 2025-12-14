# Rate Limiting Configuration

## Overview

JobsAI implements IP-based rate limiting to prevent abuse and control Lambda execution costs. Rate limiting is applied to the `/api/start` endpoint, which triggers expensive pipeline executions.

## How It Works

- **IP-based tracking**: Each client IP address is tracked separately
- **Sliding window**: Requests are counted within a configurable time window
- **DynamoDB storage**: Rate limit counters are stored in DynamoDB with automatic TTL cleanup
- **Fail-open**: If DynamoDB is unavailable, requests are allowed (but logged) to prevent service disruption

## Configuration

Rate limiting is controlled via environment variables:

### Required Variables

None - rate limiting uses sensible defaults if not configured.

### Optional Variables

| Variable                    | Default               | Description                                                |
| --------------------------- | --------------------- | ---------------------------------------------------------- |
| `RATE_LIMIT_REQUESTS`       | `5`                   | Maximum number of requests per IP per time window          |
| `RATE_LIMIT_WINDOW_SECONDS` | `3600`                | Time window in seconds (default: 1 hour)                   |
| `RATE_LIMIT_ENABLED`        | `true`                | Enable/disable rate limiting (`true` or `false`)           |
| `RATE_LIMIT_TABLE_NAME`     | `DYNAMODB_TABLE_NAME` | DynamoDB table name (defaults to same table as job states) |

### Example Configuration

```bash
# Allow 10 requests per hour
RATE_LIMIT_REQUESTS=10
RATE_LIMIT_WINDOW_SECONDS=3600

# Allow 3 requests per 30 minutes
RATE_LIMIT_REQUESTS=3
RATE_LIMIT_WINDOW_SECONDS=1800

# Disable rate limiting (not recommended for production)
RATE_LIMIT_ENABLED=false
```

## Response Headers

When rate limiting is active, the API includes the following headers in responses:

- `X-RateLimit-Limit`: Maximum requests allowed per window
- `X-RateLimit-Remaining`: Number of requests remaining in current window
- `X-RateLimit-Reset`: Unix timestamp when the rate limit resets

## Rate Limit Exceeded

When a client exceeds the rate limit, they receive:

- **Status Code**: `429 Too Many Requests`
- **Response Body**:
  ```json
  {
    "detail": "Rate limit exceeded. Please try again later.",
    "error": "too_many_requests",
    "reset_at": 1234567890
  }
  ```
- **Headers**:
  - `Retry-After`: Seconds until the rate limit resets

## Implementation Details

### DynamoDB Schema

Rate limit records are stored in DynamoDB with the following structure:

- **Primary Key**: `job_id` (String) - Format: `rate_limit:{ip_address}`
- **Attributes**:
  - `count` (Number): Current request count in the window
  - `window_start` (Number): Unix timestamp of window start
  - `ttl` (Number): Unix timestamp for automatic cleanup (window_end + 5 minutes)

### IP Address Detection

The system detects client IP addresses in the following order:

1. `X-Forwarded-For` header (used by API Gateway, CloudFront, proxies)
2. `X-Real-IP` header (used by some proxies)
3. Direct client host from request

This ensures accurate IP detection even when behind load balancers or CDNs.

## Best Practices

1. **Set appropriate limits**: Balance user experience with cost control

   - Too low: Legitimate users may be blocked
   - Too high: Vulnerable to abuse

2. **Monitor rate limit hits**: Check CloudWatch logs for `Rate limit exceeded` messages

   - High frequency may indicate abuse or legitimate high usage
   - Consider adjusting limits based on usage patterns

3. **Use separate table (optional)**: For high-traffic scenarios, consider using a separate DynamoDB table for rate limiting:

   ```bash
   RATE_LIMIT_TABLE_NAME=jobsai-rate-limits
   ```

   This prevents hot partition issues if rate limiting data grows large.

4. **Enable in production**: Always enable rate limiting in production environments:
   ```bash
   RATE_LIMIT_ENABLED=true
   ```

## Troubleshooting

### Rate limiting not working

1. Check that `RATE_LIMIT_ENABLED=true` (default)
2. Verify DynamoDB table exists and Lambda has permissions
3. Check CloudWatch logs for DynamoDB errors
4. Verify environment variables are set in Lambda configuration

### Too many false positives

- Increase `RATE_LIMIT_REQUESTS` or `RATE_LIMIT_WINDOW_SECONDS`
- Check if multiple users share the same IP (corporate networks, NAT)
- Consider implementing user-based rate limiting instead of IP-based

### DynamoDB errors

- Verify Lambda execution role has `dynamodb:GetItem`, `dynamodb:PutItem`, `dynamodb:UpdateItem` permissions
- Check table exists and is in the same region as Lambda
- Verify table has TTL enabled on `ttl` attribute

## Security Considerations

- **IP spoofing**: Rate limiting can be bypassed by changing IP addresses
- **Distributed attacks**: Multiple IPs can still overwhelm the system
- **Fail-open behavior**: If DynamoDB fails, requests are allowed (prevents service disruption but reduces protection)

For stronger protection, consider:

- API Gateway throttling (additional layer)
- AWS WAF rules
- User authentication with per-user rate limits
- CAPTCHA for suspicious patterns

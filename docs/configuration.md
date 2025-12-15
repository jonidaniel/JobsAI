# Configuration Guide

This document describes all configuration options, environment variables, and settings for the JobsAI system.

## Overview

JobsAI uses environment variables for configuration, allowing different settings for development, staging, and production environments. Configuration is read at runtime, with sensible defaults where appropriate.

## Environment Variables

### Required Variables

These variables must be set for the application to function:

#### Backend (Lambda)

| Variable                      | Description                           | Example                    |
| ----------------------------- | ------------------------------------- | -------------------------- |
| `OPENAI_API_KEY`              | OpenAI API key for LLM operations     | `sk-...`                   |
| `OPENAI_MODEL`                | OpenAI model to use                   | `gpt-4` or `gpt-3.5-turbo` |
| `DYNAMODB_TABLE_NAME`         | DynamoDB table for job state          | `jobsai-pipeline-states`   |
| `S3_DOCUMENTS_BUCKET`         | S3 bucket name for document storage   | `jobsai-documents`         |
| `WORKER_LAMBDA_FUNCTION_NAME` | Lambda function name for async worker | `jobsai-worker`            |

#### Frontend (Build Time)

| Variable            | Description              | Example                   |
| ------------------- | ------------------------ | ------------------------- |
| `VITE_API_BASE_URL` | Base URL for backend API | `https://api.example.com` |

### Optional Variables

#### Backend (Lambda)

| Variable                    | Default               | Description                                                     |
| --------------------------- | --------------------- | --------------------------------------------------------------- |
| `FRONTEND_URL`              | `""`                  | Frontend domain for CORS (comma-separated for multiple)         |
| `LAMBDA_FUNCTION_NAME`      | `""`                  | Lambda function name (fallback for worker)                      |
| `RATE_LIMIT_REQUESTS`       | `5`                   | Maximum requests per IP per time window                         |
| `RATE_LIMIT_WINDOW_SECONDS` | `3600`                | Rate limit time window in seconds (default: 1 hour)             |
| `RATE_LIMIT_ENABLED`        | `true`                | Enable/disable rate limiting (`true` or `false`)                |
| `RATE_LIMIT_TABLE_NAME`     | `DYNAMODB_TABLE_NAME` | DynamoDB table for rate limiting (defaults to job states table) |
| `SES_REGION`                | `eu-north-1`          | AWS region for SES (must match Lambda region)                   |
| `SES_FROM_EMAIL`            | `""`                  | Verified sender email address for SES                           |
| `EMAIL_ENABLED`             | `false`               | Enable/disable email delivery (`true` or `false`)               |

#### Frontend (Build Time)

| Variable            | Default                       | Description          |
| ------------------- | ----------------------------- | -------------------- |
| `VITE_API_BASE_URL` | `http://localhost:8000` (dev) | Backend API base URL |

## Configuration by Component

### Lambda Function Configuration

#### Runtime Settings

- **Runtime**: Python 3.12
- **Handler**: `lambda_handler.handler`
- **Timeout**:
  - API requests: 29 seconds (API Gateway limit)
  - Worker invocations: 15 minutes (for long-running pipelines)
- **Memory**: 1024 MB minimum (recommended for LLM operations)
- **Architecture**: x86_64

#### Environment Variables

Set in Lambda console → Configuration → Environment variables:

```bash
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4
DYNAMODB_TABLE_NAME=jobsai-pipeline-states
S3_DOCUMENTS_BUCKET=jobsai-documents
WORKER_LAMBDA_FUNCTION_NAME=jobsai-api
FRONTEND_URL=https://www.jonimakinen.com
RATE_LIMIT_REQUESTS=5
RATE_LIMIT_WINDOW_SECONDS=3600
RATE_LIMIT_ENABLED=true
SES_REGION=eu-north-1
SES_FROM_EMAIL=noreply@yourdomain.com
EMAIL_ENABLED=true
```

#### IAM Permissions

Lambda execution role needs:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:Query"
      ],
      "Resource": "arn:aws:dynamodb:*:*:table/jobsai-pipeline-states"
    },
    {
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:GetObject", "s3:GeneratePresignedUrl"],
      "Resource": "arn:aws:s3:::jobsai-documents/*"
    },
    {
      "Effect": "Allow",
      "Action": ["lambda:InvokeFunction"],
      "Resource": "arn:aws:lambda:*:*:function:jobsai-api"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    },
    {
      "Effect": "Allow",
      "Action": ["ses:SendEmail", "ses:SendRawEmail"],
      "Resource": "*"
    }
  ]
}
```

### DynamoDB Table Configuration

#### Table Settings

- **Table Name**: `jobsai-pipeline-states` (configurable)
- **Partition Key**: `job_id` (String)
- **Billing Mode**: On-Demand (recommended) or Provisioned
- **TTL Attribute**: `ttl` (Number, Unix timestamp)

#### TTL Configuration

Enable TTL on the `ttl` attribute:

- Items are automatically deleted after TTL expires
- Default TTL: 1 hour from creation
- Rate limit records: Window duration + 5 minutes

### S3 Bucket Configuration

#### Documents Bucket

- **Bucket Name**: `jobsai-documents` (configurable)
- **Region**: Same as Lambda function (recommended)
- **Access**: Private (only Lambda can write, presigned URLs for read)
- **Versioning**: Optional (recommended for production)
- **Lifecycle Policies**: Optional (archive to Glacier after 90 days)

#### Frontend Bucket

- **Bucket Name**: `jobsai-frontend` (configurable)
- **Static Website Hosting**: Enabled
- **Index Document**: `index.html`
- **Error Document**: `index.html` (for SPA routing)
- **Public Access**: Read-only for CloudFront or public

### API Gateway Configuration

#### Settings

- **API Type**: HTTP API (recommended) or REST API
- **CORS**: Configured in FastAPI (see `FRONTEND_URL`)
- **Throttling**: Optional (additional layer beyond rate limiting)
- **Timeout**: 29 seconds (API Gateway limit)

#### Integration

- **Integration Type**: Lambda Function
- **Integration Method**: POST (for all methods)
- **Timeout**: 29 seconds

### CloudFront Configuration (Optional)

#### Distribution Settings

- **Origin**: S3 bucket (frontend)
- **Viewer Protocol Policy**: Redirect HTTP to HTTPS
- **Allowed HTTP Methods**: GET, HEAD, OPTIONS
- **Cache Policy**: CachingOptimized (or custom)
- **Price Class**: Use All Edge Locations (or cheaper option)

#### Cache Invalidation

- **Manual**: Via GitHub Actions (on deployment)
- **Automatic**: Via CloudFront cache behaviors

## Local Development Configuration

### Backend (.env file)

Create `.env` in project root:

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4

# AWS Configuration (optional for local dev)
DYNAMODB_TABLE_NAME=jobsai-pipeline-states
S3_DOCUMENTS_BUCKET=jobsai-documents

# Rate Limiting (optional)
RATE_LIMIT_ENABLED=false  # Disable for local development

# Email Configuration (optional for local dev)
SES_REGION=eu-north-1
SES_FROM_EMAIL=noreply@yourdomain.com
EMAIL_ENABLED=false  # Disable for local development (unless testing SES)
```

### Frontend (.env file)

Create `.env` in `frontend/` directory:

```bash
# API Configuration
VITE_API_BASE_URL=http://localhost:8000
```

## Configuration Validation

### Backend

Environment variables are validated at import time:

- **OpenAI**: `OPENAI_API_KEY` and `OPENAI_MODEL` must be set
- **AWS**: DynamoDB and S3 clients fail gracefully if not configured (for local dev)

### Frontend

- **API URL**: Falls back to `http://localhost:8000` in development
- **Production**: Throws error if `VITE_API_BASE_URL` is missing

## Configuration Best Practices

### 1. Use Environment-Specific Values

- **Development**: Lower rate limits, local endpoints
- **Staging**: Production-like settings, test data
- **Production**: Optimized limits, real endpoints

### 2. Secure Secrets

- **Never commit**: `.env` files should be in `.gitignore`
- **Use AWS Secrets Manager**: For production secrets (future improvement)
- **Rotate keys**: Regularly rotate OpenAI API keys

### 3. Monitor Configuration

- **CloudWatch**: Monitor environment variable usage
- **Alerts**: Set up alerts for missing required variables
- **Documentation**: Keep this file updated with changes

### 4. Rate Limiting Tuning

- **Start conservative**: Begin with default limits (5/hour)
- **Monitor usage**: Check CloudWatch logs for rate limit hits
- **Adjust based on usage**: Increase if legitimate users are blocked
- **Consider user-based limits**: For authenticated users (future)

## Troubleshooting

### Missing Environment Variables

**Symptom**: Lambda fails to start or returns errors

**Solution**:

1. Check Lambda console → Configuration → Environment variables
2. Verify all required variables are set
3. Check variable names (case-sensitive)
4. Verify no extra spaces or quotes

### CORS Errors

**Symptom**: Frontend cannot call API

**Solution**:

1. Set `FRONTEND_URL` in Lambda environment variables
2. Include protocol (`https://`) in URL
3. For multiple origins, use comma-separated list
4. Check API Gateway CORS settings (if using REST API)

### Rate Limiting Not Working

**Symptom**: Rate limits not enforced

**Solution**:

1. Verify `RATE_LIMIT_ENABLED=true`
2. Check DynamoDB table exists and Lambda has permissions
3. Verify `RATE_LIMIT_TABLE_NAME` is correct
4. Check CloudWatch logs for DynamoDB errors

### DynamoDB Access Denied

**Symptom**: Lambda cannot read/write DynamoDB

**Solution**:

1. Check Lambda execution role IAM permissions
2. Verify table name matches `DYNAMODB_TABLE_NAME`
3. Ensure table is in same region as Lambda
4. Check table exists and is active

### S3 Access Denied

**Symptom**: Documents not stored or presigned URLs fail

**Solution**:

1. Check Lambda execution role has S3 permissions
2. Verify bucket name matches `S3_DOCUMENTS_BUCKET`
3. Check bucket policy allows Lambda role
4. Verify bucket exists and is in same region

### Email Not Sending

**Symptom**: Cover letters not received via email

**Solution**:

1. Verify `EMAIL_ENABLED=true` is set in Lambda environment variables
2. Check `SES_FROM_EMAIL` matches verified email/domain in SES
3. Verify `SES_REGION` matches the region where SES is configured
4. Ensure sender email/domain is verified in SES Console
5. Check Lambda execution role has SES permissions (`ses:SendEmail`, `ses:SendRawEmail`)
6. Review CloudWatch logs for email sending errors
7. If in SES Sandbox, verify recipient email addresses or request production access
8. Check SES account dashboard for bounce/complaint rates (may suspend sending if too high)

## Configuration Examples

### Production Configuration

```bash
# Lambda Environment Variables
OPENAI_API_KEY=sk-prod-key-here
OPENAI_MODEL=gpt-4
DYNAMODB_TABLE_NAME=jobsai-pipeline-states-prod
S3_DOCUMENTS_BUCKET=jobsai-documents-prod
WORKER_LAMBDA_FUNCTION_NAME=jobsai-api-prod
FRONTEND_URL=https://www.jonimakinen.com
RATE_LIMIT_REQUESTS=10
RATE_LIMIT_WINDOW_SECONDS=3600
RATE_LIMIT_ENABLED=true
SES_REGION=eu-north-1
SES_FROM_EMAIL=noreply@yourdomain.com
EMAIL_ENABLED=true
```

### Development Configuration

```bash
# Lambda Environment Variables (or .env for local)
OPENAI_API_KEY=sk-dev-key-here
OPENAI_MODEL=gpt-3.5-turbo
DYNAMODB_TABLE_NAME=jobsai-pipeline-states-dev
S3_DOCUMENTS_BUCKET=jobsai-documents-dev
WORKER_LAMBDA_FUNCTION_NAME=jobsai-api-dev
FRONTEND_URL=http://localhost:3000
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=3600
RATE_LIMIT_ENABLED=false
```

### High-Traffic Configuration

```bash
# Lambda Environment Variables
RATE_LIMIT_REQUESTS=20
RATE_LIMIT_WINDOW_SECONDS=3600
RATE_LIMIT_TABLE_NAME=jobsai-rate-limits  # Separate table
# Consider Lambda reserved concurrency: 10-20
```

## AWS SES Configuration

### Step 1: Verify Sender Email/Domain in SES

#### Option A: Verify a Single Email Address (Easier for Testing)

1. **Go to AWS SES Console**:

   - Navigate to: https://console.aws.amazon.com/ses/
   - Select your region (e.g., `eu-north-1`)

2. **Verify Email Address**:

   - Click "Verified identities" in the left sidebar
   - Click "Create identity"
   - Select "Email address"
   - Enter your email (e.g., `noreply@yourdomain.com`)
   - Click "Create identity"

3. **Check Your Email**:
   - AWS will send a verification email
   - Click the verification link in the email
   - Status will change to "Verified"

#### Option B: Verify a Domain (Recommended for Production)

1. **Create Identity**:

   - In SES Console → "Verified identities" → "Create identity"
   - Select "Domain"
   - Enter your domain (e.g., `yourdomain.com`)
   - Click "Create identity"

2. **Add DNS Records**:

   - AWS will provide DNS records (CNAME records)
   - Add these to your domain's DNS settings:
     - Go to your domain registrar (e.g., Route 53, Namecheap)
     - Add the provided CNAME records
   - Wait for DNS propagation (usually 5-30 minutes)

3. **Verify Domain**:
   - Once DNS records are added, AWS will automatically verify
   - Status will change to "Verified"

### Step 2: Move Out of SES Sandbox (If Needed)

**SES Sandbox Limitations**:

- Can only send to verified email addresses
- Limited to 200 emails per day
- 1 email per second sending rate

**To Move Out of Sandbox**:

1. **Request Production Access**:

   - In SES Console, go to "Account dashboard"
   - Click "Request production access"
   - Fill out the form:
     - **Mail Type**: Transactional
     - **Website URL**: Your website URL
     - **Use case description**:
       ```
       We send personalized cover letters to users who request them via email.
       Users explicitly opt-in by selecting "Via email" option in our application.
       This is a transactional service, not marketing emails.
       ```
     - **Expected sending volume**: Estimate your monthly volume
     - **How you handle bounces/complaints**:
       ```
       We monitor bounce and complaint rates via CloudWatch.
       We will remove bounced addresses from our system.
       ```

2. **Wait for Approval**:

   - Usually takes 24-48 hours
   - AWS will email you when approved
   - Check "Account dashboard" for status

3. **After Approval**:
   - Can send to any email address
   - Higher sending limits (based on your request)
   - Still must send from verified email/domain

### Step 3: Set Environment Variables

#### In Lambda Console

1. **Navigate to Lambda Function**:

   - Go to AWS Lambda Console
   - Select your function (e.g., `jobsai-api`)

2. **Add Environment Variables**:

   - Go to "Configuration" → "Environment variables"
   - Click "Edit"
   - Add the following variables:

   ```bash
   SES_REGION=eu-north-1
   SES_FROM_EMAIL=noreply@yourdomain.com
   EMAIL_ENABLED=true
   ```

   **Important Notes**:

   - `SES_REGION`: Must match the region where you verified your email/domain
   - `SES_FROM_EMAIL`: Must be a verified email address or from a verified domain
   - `EMAIL_ENABLED`: Set to `true` to enable email delivery

3. **Save Changes**:
   - Click "Save"
   - Lambda will automatically update

#### Via AWS CLI

```bash
aws lambda update-function-configuration \
  --function-name jobsai-api \
  --environment Variables="{
    SES_REGION=eu-north-1,
    SES_FROM_EMAIL=noreply@yourdomain.com,
    EMAIL_ENABLED=true
  }"
```

#### Via Infrastructure as Code (Terraform/CloudFormation)

If using IaC, add to your Lambda function configuration:

```hcl
# Terraform example
resource "aws_lambda_function" "jobsai_api" {
  # ... other configuration ...

  environment {
    variables = {
      SES_REGION     = "eu-north-1"
      SES_FROM_EMAIL = "noreply@yourdomain.com"
      EMAIL_ENABLED  = "true"
    }
  }
}
```

### Step 4: Verify IAM Permissions

Ensure your Lambda execution role has SES permissions:

1. **Check IAM Role**:

   - Go to Lambda function → "Configuration" → "Permissions"
   - Click on the execution role name

2. **Add SES Policy** (if not already added):

   - Click "Add permissions" → "Create inline policy"
   - Use JSON editor:

   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": ["ses:SendEmail", "ses:SendRawEmail"],
         "Resource": "*"
       }
     ]
   }
   ```

   - Name: `SESEmailSendingPolicy`
   - Click "Create policy"

### Step 5: Test Email Delivery

#### Test via AWS Console

1. **Send Test Email**:
   - Go to SES Console → "Verified identities"
   - Select your verified email
   - Click "Send test email"
   - Enter recipient email
   - Send test email

#### Test via Application

1. **Use Your Application**:

   - Submit a job search with "Via email" option
   - Enter a test email address
   - Wait for pipeline to complete
   - Check email inbox for cover letters

2. **Check CloudWatch Logs**:
   ```bash
   aws logs tail /aws/lambda/jobsai-api --follow
   ```
   - Look for "Email sent successfully" messages
   - Check for any errors

### Troubleshooting SES

#### Email Not Sending

**Check**:

1. `EMAIL_ENABLED=true` is set
2. `SES_FROM_EMAIL` matches verified email/domain
3. `SES_REGION` matches SES region
4. Lambda role has SES permissions
5. Sender email/domain is verified in SES

**Common Errors**:

- `Email address not verified`: Verify sender email in SES
- `MessageRejected`: Check bounce/complaint rates
- `AccessDenied`: Check IAM permissions

#### Still in Sandbox

**Symptoms**:

- Can only send to verified emails
- Getting "Email address not verified" errors for recipients

**Solution**:

- Request production access (see Step 2)
- Or verify recipient emails in SES (for testing only)

#### High Bounce/Complaint Rates

**Monitor**:

- SES Console → "Account dashboard"
- Check bounce and complaint rates
- Keep bounce rate < 5%
- Keep complaint rate < 0.1%

**If Rates Too High**:

- AWS may suspend sending
- Review email content
- Remove invalid email addresses
- Request review from AWS support

## Related Documentation

- **Rate Limiting**: See `docs/rate-limiting.md` for detailed rate limiting configuration
- **Deployment**: See `docs/deployment.md` for AWS resource setup
- **Architecture**: See `docs/architecture.md` for system design

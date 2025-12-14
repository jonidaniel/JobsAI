# AWS Deployment Guide

This guide walks you through deploying JobsAI to AWS. It covers manual setup of all required AWS resources.

## Prerequisites

- AWS Account with appropriate permissions
- AWS CLI installed and configured
- GitHub repository with GitHub Actions enabled
- OpenAI API key

## Overview

JobsAI requires the following AWS resources:

1. **Lambda Function**: Backend API and worker
2. **DynamoDB Table**: Job state storage
3. **S3 Buckets**: Frontend hosting and document storage
4. **API Gateway** (or Lambda Function URL): HTTP API endpoint
5. **CloudFront Distribution** (optional): CDN for frontend
6. **IAM Roles**: Lambda execution permissions

## Step-by-Step Deployment

### 1. Create S3 Buckets

#### Frontend Bucket

```bash
# Create bucket
aws s3 mb s3://jobsai-frontend --region us-east-1

# Enable static website hosting
aws s3 website s3://jobsai-frontend \
  --index-document index.html \
  --error-document index.html

# Set bucket policy for public read (if not using CloudFront)
cat > bucket-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::jobsai-frontend/*"
    }
  ]
}
EOF
aws s3api put-bucket-policy --bucket jobsai-frontend --policy file://bucket-policy.json
```

#### Documents Bucket

```bash
# Create bucket
aws s3 mb s3://jobsai-documents --region us-east-1

# Keep bucket private (no public access)
# Documents accessed via presigned URLs only
```

### 2. Create DynamoDB Table

```bash
aws dynamodb create-table \
  --table-name jobsai-pipeline-states \
  --attribute-definitions AttributeName=job_id,AttributeType=S \
  --key-schema AttributeName=job_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1

# Enable TTL
aws dynamodb update-time-to-live \
  --table-name jobsai-pipeline-states \
  --time-to-live-specification Enabled=true,AttributeName=ttl \
  --region us-east-1
```

**Table Configuration**:

- **Partition Key**: `job_id` (String)
- **Billing Mode**: On-Demand (or Provisioned with auto-scaling)
- **TTL**: Enabled on `ttl` attribute

### 3. Create IAM Role for Lambda

#### Create Trust Policy

```bash
cat > trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
```

#### Create Role

```bash
aws iam create-role \
  --role-name jobsai-lambda-role \
  --assume-role-policy-document file://trust-policy.json
```

#### Attach Policies

```bash
# Basic Lambda execution
aws iam attach-role-policy \
  --role-name jobsai-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# Create custom policy for DynamoDB, S3, and Lambda invoke
cat > lambda-policy.json <<EOF
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
      "Action": [
        "s3:PutObject",
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::jobsai-documents/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "lambda:InvokeFunction"
      ],
      "Resource": "arn:aws:lambda:*:*:function:jobsai-api"
    }
  ]
}
EOF

aws iam put-role-policy \
  --role-name jobsai-lambda-role \
  --policy-name jobsai-lambda-policy \
  --policy-document file://lambda-policy.json
```

### 4. Create Lambda Function

#### Package Lambda Code

First, create the deployment package locally (or let GitHub Actions handle it):

```bash
# Create package directory
mkdir -p lambda-package

# Copy source code
cp -r src/jobsai lambda-package/
cp lambda_handler.py lambda-package/
cp lambda_worker.py lambda-package/

# Install dependencies
pip install -r requirements.txt -t lambda-package/

# Create zip file
cd lambda-package
zip -r ../lambda.zip .
cd ..
```

#### Create Function

```bash
aws lambda create-function \
  --function-name jobsai-api \
  --runtime python3.12 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/jobsai-lambda-role \
  --handler lambda_handler.handler \
  --zip-file fileb://lambda.zip \
  --timeout 900 \
  --memory-size 1024 \
  --environment Variables="{
    OPENAI_API_KEY=sk-your-key-here,
    OPENAI_MODEL=gpt-4,
    DYNAMODB_TABLE_NAME=jobsai-pipeline-states,
    S3_DOCUMENTS_BUCKET=jobsai-documents,
    WORKER_LAMBDA_FUNCTION_NAME=jobsai-api,
    FRONTEND_URL=https://www.jonimakinen.com,
    RATE_LIMIT_REQUESTS=5,
    RATE_LIMIT_WINDOW_SECONDS=3600,
    RATE_LIMIT_ENABLED=true
  }" \
  --region us-east-1
```

**Note**: Replace `YOUR_ACCOUNT_ID` with your AWS account ID.

#### Update Function Code (for updates)

```bash
aws lambda update-function-code \
  --function-name jobsai-api \
  --zip-file fileb://lambda.zip \
  --region us-east-1
```

### 5. Create API Gateway (HTTP API)

#### Create API

```bash
aws apigatewayv2 create-api \
  --name jobsai-api \
  --protocol-type HTTP \
  --cors-configuration AllowOrigins="*",AllowMethods="GET,POST,OPTIONS",AllowHeaders="*" \
  --region us-east-1
```

**Note**: Save the API ID from the response.

#### Create Integration

```bash
aws apigatewayv2 create-integration \
  --api-id YOUR_API_ID \
  --integration-type AWS_PROXY \
  --integration-uri arn:aws:lambda:us-east-1:YOUR_ACCOUNT_ID:function:jobsai-api \
  --payload-format-version "2.0" \
  --region us-east-1
```

**Note**: Replace `YOUR_API_ID` and `YOUR_ACCOUNT_ID`.

#### Create Route

```bash
aws apigatewayv2 create-route \
  --api-id YOUR_API_ID \
  --route-key "$default" \
  --target integrations/YOUR_INTEGRATION_ID \
  --region us-east-1
```

#### Create Stage

```bash
aws apigatewayv2 create-stage \
  --api-id YOUR_API_ID \
  --stage-name prod \
  --auto-deploy \
  --region us-east-1
```

#### Get API Endpoint

```bash
aws apigatewayv2 get-api \
  --api-id YOUR_API_ID \
  --region us-east-1
```

**Note**: The `ApiEndpoint` in the response is your API base URL.

### Alternative: Lambda Function URL

Instead of API Gateway, you can use Lambda Function URL:

```bash
aws lambda create-function-url-config \
  --function-name jobsai-api \
  --auth-type NONE \
  --cors '{
    "AllowOrigins": ["*"],
    "AllowMethods": ["GET", "POST", "OPTIONS"],
    "AllowHeaders": ["*"]
  }' \
  --region us-east-1
```

Get the Function URL:

```bash
aws lambda get-function-url-config \
  --function-name jobsai-api \
  --region us-east-1
```

### 6. Create CloudFront Distribution (Optional)

#### Create Distribution

```bash
aws cloudfront create-distribution \
  --distribution-config '{
    "CallerReference": "jobsai-frontend-'$(date +%s)'",
    "Comment": "JobsAI Frontend CDN",
    "DefaultCacheBehavior": {
      "TargetOriginId": "S3-jobsai-frontend",
      "ViewerProtocolPolicy": "redirect-to-https",
      "AllowedMethods": {
        "Quantity": 2,
        "Items": ["GET", "HEAD"]
      },
      "ForwardedValues": {
        "QueryString": false,
        "Cookies": {"Forward": "none"}
      },
      "MinTTL": 0,
      "DefaultTTL": 86400,
      "MaxTTL": 31536000,
      "Compress": true
    },
    "Origins": {
      "Quantity": 1,
      "Items": [{
        "Id": "S3-jobsai-frontend",
        "DomainName": "jobsai-frontend.s3.amazonaws.com",
        "S3OriginConfig": {
          "OriginAccessIdentity": ""
        }
      }]
    },
    "Enabled": true,
    "PriceClass": "PriceClass_100"
  }'
```

**Note**: Save the Distribution ID from the response.

### 7. Configure GitHub Secrets

In your GitHub repository, go to Settings → Secrets and variables → Actions, and add:

- `AWS_ACCESS_KEY_ID`: AWS access key
- `AWS_SECRET_ACCESS_KEY`: AWS secret key
- `AWS_REGION`: AWS region (e.g., `us-east-1`)
- `LAMBDA_FUNCTION_NAME`: `jobsai-api`
- `S3_BUCKET_NAME`: `jobsai-frontend`
- `VITE_API_BASE_URL`: Your API Gateway or Function URL
- `CLOUDFRONT_DISTRIBUTION_ID`: CloudFront distribution ID (optional)

### 8. Deploy via GitHub Actions

Push to `main` branch to trigger deployment:

```bash
git add .
git commit -m "Initial deployment"
git push origin main
```

GitHub Actions will:

1. Build frontend
2. Deploy to S3
3. Invalidate CloudFront (if configured)
4. Package Lambda code
5. Update Lambda function

## Post-Deployment

### 1. Verify Deployment

#### Test API Endpoint

```bash
curl https://YOUR_API_URL/api/start \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"general_questions": {}, "tech_stack": {}, "multiple_choice": {}}'
```

#### Test Frontend

Visit your CloudFront URL or S3 website endpoint:

- CloudFront: `https://YOUR_DISTRIBUTION_ID.cloudfront.net`
- S3: `http://jobsai-frontend.s3-website-us-east-1.amazonaws.com`

### 2. Monitor Logs

```bash
# View Lambda logs
aws logs tail /aws/lambda/jobsai-api --follow

# View recent errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/jobsai-api \
  --filter-pattern "ERROR" \
  --max-items 10
```

### 3. Set Up Alarms (Recommended)

```bash
# Create SNS topic for alerts
aws sns create-topic --name jobsai-alerts

# Create CloudWatch alarm for Lambda errors
aws cloudwatch put-metric-alarm \
  --alarm-name jobsai-lambda-errors \
  --alarm-description "Alert on Lambda errors" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1 \
  --alarm-actions arn:aws:sns:us-east-1:YOUR_ACCOUNT_ID:jobsai-alerts
```

## Cost Optimization

### 1. Lambda Reserved Concurrency

Limit concurrent executions to control costs:

```bash
aws lambda put-function-concurrency \
  --function-name jobsai-api \
  --reserved-concurrent-executions 10
```

### 2. DynamoDB On-Demand

Use On-Demand billing (already configured) for unpredictable traffic.

### 3. S3 Lifecycle Policies

Archive old documents to Glacier:

```bash
aws s3api put-bucket-lifecycle-configuration \
  --bucket jobsai-documents \
  --lifecycle-configuration '{
    "Rules": [{
      "Id": "ArchiveOldDocuments",
      "Status": "Enabled",
      "Prefix": "documents/",
      "Transitions": [{
        "Days": 90,
        "StorageClass": "GLACIER"
      }]
    }]
  }'
```

## Troubleshooting

### Lambda Function Not Invoking

1. Check IAM role permissions
2. Verify API Gateway integration
3. Check Lambda logs for errors
4. Verify environment variables are set

### CORS Errors

1. Check `FRONTEND_URL` in Lambda environment variables
2. Verify API Gateway CORS configuration
3. Check browser console for specific error

### DynamoDB Access Denied

1. Verify IAM role has DynamoDB permissions
2. Check table name matches `DYNAMODB_TABLE_NAME`
3. Ensure table is in same region as Lambda

### S3 Access Denied

1. Verify IAM role has S3 permissions
2. Check bucket name matches `S3_DOCUMENTS_BUCKET`
3. Verify bucket policy allows Lambda role

## Cleanup

To remove all resources:

```bash
# Delete Lambda function
aws lambda delete-function --function-name jobsai-api

# Delete DynamoDB table
aws dynamodb delete-table --table-name jobsai-pipeline-states

# Delete S3 buckets (must be empty first)
aws s3 rm s3://jobsai-frontend --recursive
aws s3 rb s3://jobsai-frontend
aws s3 rm s3://jobsai-documents --recursive
aws s3 rb s3://jobsai-documents

# Delete API Gateway
aws apigatewayv2 delete-api --api-id YOUR_API_ID

# Delete CloudFront distribution (disable first)
aws cloudfront get-distribution-config --id YOUR_DISTRIBUTION_ID
# Then delete after disabled

# Delete IAM role
aws iam delete-role-policy --role-name jobsai-lambda-role --policy-name jobsai-lambda-policy
aws iam delete-role --role-name jobsai-lambda-role
```

## Next Steps

- Set up monitoring and alerts (CloudWatch)
- Configure custom domain (Route 53 + API Gateway)
- Implement Infrastructure as Code (Terraform/CloudFormation)
- Set up staging environment
- Configure backup and disaster recovery

## Related Documentation

- **Architecture**: See `docs/architecture.md` for system design
- **Configuration**: See `docs/configuration.md` for environment variables
- **Rate Limiting**: See `docs/rate-limiting.md` for rate limit configuration

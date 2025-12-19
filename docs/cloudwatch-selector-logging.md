# CloudWatch Selector Logging

This document explains the CloudWatch logging added for debugging scraper selectors.

## Overview

All selector values extracted from job cards are now logged to CloudWatch with structured JSON format. This allows you to:

- See what values are being extracted for each field
- Debug why selectors might not be working
- Monitor selector performance across different job boards
- Identify when selectors fail to match

## Logged Information

### 1. Job Card Parsing (`_parse_job_card`)

For each job card parsed, the following is logged at `INFO` level:

```json
{
  "message": "Parsed job card",
  "level": "INFO",
  "extra_fields": {
    "job_board": "duunitori",
    "title": "Senior Python Developer",
    "company": "Tech Corp",
    "location": "Helsinki",
    "url": "https://duunitori.fi/tyopaikat/123456",
    "published_date": "2025-01-15",
    "description_snippet": null,
    "title_length": 23,
    "company_length": 8,
    "location_length": 8,
    "snippet_length": 0
  }
}
```

**Fields:**

- `job_board`: Which job board (duunitori, jobly, indeed)
- `title`, `company`, `location`, `url`, `published_date`, `description_snippet`: Extracted values
- `*_length`: Character count for each field (helps identify empty fields)

### 2. Selector Mismatches (`DEBUG` level)

When a selector doesn't match, a debug log is emitted:

```json
{
  "message": "Company selector did not match",
  "level": "DEBUG",
  "extra_fields": {
    "job_board": "duunitori",
    "selector": ".job-box__hover.gtm-search-result"
  }
}
```

This helps identify which selectors are failing for specific job boards.

### 3. Full Description Extraction

When fetching full descriptions from detail pages:

**Success:**

```json
{
  "message": "Full description extracted",
  "level": "INFO",
  "extra_fields": {
    "job_board": "duunitori",
    "job_url": "https://duunitori.fi/tyopaikat/123456",
    "selector_index": 0,
    "selector": ".gtm-apply-clicks.description.description--jobentry",
    "description_length": 2543,
    "description_preview": "We are looking for a Senior Python Developer..."
  }
}
```

**Failure (no selectors matched):**

```json
{
  "message": "No full description found",
  "level": "WARNING",
  "extra_fields": {
    "job_board": "duunitori",
    "job_url": "https://duunitori.fi/tyopaikat/123456",
    "selectors_tried": 1,
    "selectors": [".gtm-apply-clicks.description.description--jobentry"]
  }
}
```

### 4. Job Card Processing Complete

After processing each job card (including full description fetch):

```json
{
  "message": "Job card processing complete",
  "level": "INFO",
  "extra_fields": {
    "job_board": "duunitori",
    "job_url": "https://duunitori.fi/tyopaikat/123456",
    "has_full_description": true,
    "full_description_length": 2543
  }
}
```

## CloudWatch Logs Insights Queries

### Find all parsed job cards for a specific board

```
fields @timestamp, message, extra_fields.job_board, extra_fields.title, extra_fields.company, extra_fields.location
| filter extra_fields.job_board = "duunitori"
| sort @timestamp desc
```

### Find job cards with empty fields

```
fields @timestamp, extra_fields.job_board, extra_fields.title, extra_fields.company, extra_fields.location
| filter extra_fields.title_length = 0 or extra_fields.company_length = 0 or extra_fields.location_length = 0
| sort @timestamp desc
```

### Find failed full description extractions

```
fields @timestamp, extra_fields.job_board, extra_fields.job_url, extra_fields.selectors
| filter message = "No full description found"
| sort @timestamp desc
```

### Count selector failures by field

```
fields extra_fields.job_board, extra_fields.selector
| filter message like /selector did not match/
| stats count() by extra_fields.job_board, extra_fields.selector
```

### Find successful full description extractions

```
fields @timestamp, extra_fields.job_board, extra_fields.selector, extra_fields.description_length
| filter message = "Full description extracted"
| sort @timestamp desc
```

### Average description length by job board

```
fields extra_fields.job_board, extra_fields.description_length
| filter message = "Full description extracted"
| stats avg(extra_fields.description_length) as avg_length by extra_fields.job_board
```

## Debugging Workflow

1. **Check if selectors are matching:**

   - Query for "Parsed job card" logs
   - Check `*_length` fields - if they're 0, the selector didn't match

2. **Find which selectors are failing:**

   - Query for "selector did not match" (DEBUG level)
   - Group by `job_board` and `selector` to see patterns

3. **Debug full description extraction:**

   - Query for "No full description found" warnings
   - Check which selectors were tried
   - Verify the selectors work on detail pages

4. **Monitor selector performance:**
   - Track average description lengths
   - Identify job boards with low success rates
   - Find patterns in failed extractions

## Log Levels

- **INFO**: Normal operation (parsed values, successful extractions)
- **DEBUG**: Selector mismatches (only visible if LOG_LEVEL=DEBUG)
- **WARNING**: Failed extractions, errors

## Enabling DEBUG Logs

To see selector mismatch logs, set the environment variable:

```bash
export LOG_LEVEL=DEBUG
```

Or in Lambda environment variables:

```
LOG_LEVEL=DEBUG
```

## Example: Debugging Duunitori Company Selector

If you see many job cards with `company_length: 0`:

1. Query for Duunitori company selector failures:

   ```
   fields @timestamp, extra_fields.selector
   | filter message = "Company selector did not match" and extra_fields.job_board = "duunitori"
   ```

2. Check the selector being used: `.job-box__hover.gtm-search-result`

3. Inspect a real Duunitori page to verify the selector still works

4. Update the selector in `configs.py` if needed

## Notes

- All logs use structured JSON format for easy querying
- Logs include correlation IDs (`job_id`, `request_id`) when available
- Empty fields are logged with length 0, not as empty strings
- Full description previews are limited to 200 characters to avoid log bloat

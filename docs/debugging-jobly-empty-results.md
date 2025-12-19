# Debugging Jobly Empty Results

## Problem

When searching with only Jobly selected, you get "No job listings found to score."

## Root Cause Analysis

The error occurs when `raw_jobs` is empty, meaning the Jobly scraper returned 0 jobs.

## Possible Causes

### 1. Job Card Selector Not Matching

The selector `.job__content.clearfix` might not match Jobly's current HTML structure.

**Check CloudWatch logs for:**

```
"No job cards found on page 1 for query '...' — stopping pagination"
```

If you see this, the selector isn't finding any job cards.

### 2. Scraper Error

The scraper might be failing silently.

**Check CloudWatch logs for:**

```
"Error scraping Jobly for query '...': ..."
```

If you see this, there's an exception being caught.

### 3. Successful Scraping but 0 Results

**Check CloudWatch logs for:**

```
"Completed scraping Jobly for query '...': 0 jobs found"
```

This means the scraper ran successfully but found no jobs.

## Debugging Steps

### Step 1: Check CloudWatch Logs

Look for these log messages in the worker Lambda log stream:

1. **Job card selector issue:**

   ```
   "No job cards found on page 1 for query '...' — stopping pagination"
   ```

2. **Scraper error:**

   ```
   "Error scraping Jobly for query '...': ..."
   ```

3. **Successful but empty:**
   ```
   "Completed scraping Jobly for query '...': 0 jobs found"
   ```

### Step 2: Test Jobly Selectors

Use the test script to verify selectors work:

```bash
# Save a Jobly search page
curl -H "User-Agent: Mozilla/5.0..." \
     "https://www.jobly.fi/en/jobs?search=python&page=1" \
     > jobly_test.html

# Test selectors
python scripts/test_selectors.py --file jobly_test.html --config jobly --show-all
```

### Step 3: Check for Selector Mismatches

If you see warnings in CloudWatch:

```
"Parsed job card with missing fields"
```

This indicates selectors are partially working but some fields are missing.

## Most Likely Issue

Based on the configuration, the most likely issue is:

**Job card selector `.job__content.clearfix` is not matching**

Jobly's HTML structure may have changed. The selector needs to match the container element that wraps each job listing.

## Solution

1. **Inspect Jobly HTML:**

   - Visit https://www.jobly.fi/en/jobs?search=python
   - Open DevTools (F12)
   - Inspect a job listing
   - Find the container element's class

2. **Update the selector in `configs.py`:**

   ```python
   job_card_selector=".new-selector-here",  # Update this
   ```

3. **Test the new selector:**

   ```bash
   python scripts/test_selectors.py --file jobly_test.html --config jobly
   ```

4. **Verify it works:**
   - Run a search with only Jobly
   - Check CloudWatch for "Completed scraping Jobly: X jobs found" where X > 0

## Quick Fix

If you need to test immediately, try these alternative selectors:

```python
# Option 1: More generic
job_card_selector=".job__content"

# Option 2: Different structure
job_card_selector="article.job, .job-item, [class*='job']"

# Option 3: Check if it's a different class
job_card_selector=".node--type-job"
```

## Additional Checks

1. **Check if Jobly is blocking requests:**

   - Look for 403/429 status codes in logs
   - Check if headers are correct

2. **Check if query encoding is correct:**

   - The query encoder might be producing invalid URLs
   - Check the actual URL being fetched in logs: "Fetching Jobly search page: ..."

3. **Check if deep mode is causing issues:**
   - Try with `deep_mode=False` to see if that's the problem
   - Deep mode failures shouldn't prevent jobs from being found, but worth checking

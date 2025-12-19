# How to Check Jobly Scraping Logs

## Your Current Log

You're seeing:

```
"No job listings found to score."
```

This means the scraper returned 0 jobs. Now we need to find out why.

## Check These Logs (in chronological order)

### 1. Search Start

Look for:

```
"Searching Jobly for query '...'"
```

This confirms Jobly scraping started.

### 2. Page Fetching

Look for:

```
"Fetching Jobly search page: https://www.jobly.fi/en/jobs?search=..."
```

This shows the URL being fetched. Check if it's correct.

### 3. Job Cards Found (or NOT found)

Look for one of these:

**If selector doesn't match:**

```
"No job cards found on page 1 for query '...' — stopping pagination"
```

**If scraping succeeded:**

```
"Completed scraping Jobly for query '...': 0 jobs found"
```

**If there was an error:**

```
"Error scraping Jobly for query '...': ..."
```

### 4. Final Result

Look for:

```
"Fetched 0 listings for query '...'"
```

## What to Look For

### Scenario A: Selector Not Matching

If you see:

```
"No job cards found on page 1 for query '...' — stopping pagination"
```

**Problem:** The job card selector `.job__content.clearfix` isn't matching Jobly's HTML.

**Solution:** Update the selector in `configs.py` line 108.

### Scenario B: Scraper Error

If you see:

```
"Error scraping Jobly for query '...': [error message]"
```

**Problem:** An exception occurred during scraping.

**Solution:** Fix the error (could be network, parsing, etc.).

### Scenario C: Successful but Empty

If you see:

```
"Completed scraping Jobly for query '...': 0 jobs found"
```

**Problem:** Scraper ran but found no jobs (unlikely unless Jobly has no results).

**Solution:** Check if the query/search terms are valid.

## Quick CloudWatch Query

Use this CloudWatch Logs Insights query to find all Jobly-related logs:

```
fields @timestamp, message, extra_fields
| filter message like /Jobly/ or message like /jobly/
| sort @timestamp asc
```

This will show all logs related to Jobly scraping in chronological order.

## Most Likely Issue

Based on the error, **Scenario A** is most likely: the job card selector isn't matching.

The selector `.job__content.clearfix` might need to be updated if Jobly changed their HTML structure.

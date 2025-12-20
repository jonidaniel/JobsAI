# Debugging Indeed Empty Results

## Problem

Indeed scraper returns 0 jobs - "No job listings found to score."

## Current Configuration

**Job Card Selector:**

```python
job_card_selector=".resultContent.css-1o6lhys.eu4oa1w0"
```

## Most Likely Issue

Indeed uses CSS-in-JS class names that change frequently. The selector `.resultContent.css-1o6lhys.eu4oa1w0` is likely outdated.

## Debugging Steps

### Step 1: Check CloudWatch Logs

Look for these messages in the worker Lambda log stream:

**If selector doesn't match:**

```
"No job cards found on page 1 for query '...' — stopping pagination"
```

**If there was an error:**

```
"Error scraping Indeed for query '...': [error details]"
```

**If scraping succeeded but empty:**

```
"Completed scraping Indeed for query '...': 0 jobs found"
```

### Step 2: Test Indeed Selectors

1. **Save a real Indeed search page:**

   ```bash
   curl -H "User-Agent: Mozilla/5.0..." \
        "https://www.indeed.com/jobs?q=python&start=0" \
        > indeed_test.html
   ```

2. **Test the current selector:**

   ```bash
   python scripts/test_selectors.py --file indeed_test.html --config indeed --show-all
   ```

3. **If it shows 0 job cards, the selector is broken.**

### Step 3: Find the Correct Selector

**Option A: Use browser DevTools**

1. Visit https://www.indeed.com/jobs?q=python
2. Open DevTools (F12)
3. Inspect a job listing
4. Find the container element's class
5. Look for stable selectors (data attributes, semantic classes)

**Option B: Use the find_detail_selectors script**

```bash
python scripts/find_detail_selectors.py --url "https://www.indeed.com/jobs?q=python&start=0"
```

**Option C: Try more stable selectors**

Indeed often uses:

- `[data-jk]` - Job ID attribute (most stable)
- `.job_seen_beacon` - Older selector (may still work)
- `[data-testid]` attributes - More stable than CSS classes

## Recommended Fix

### Option 1: Use data-jk attribute (most stable)

```python
job_card_selector="[data-jk]"
```

This is the most reliable selector as Indeed uses `data-jk` to identify job listings.

### Option 2: Try multiple selectors

```python
job_card_selector="[data-jk], .job_seen_beacon, .resultContent"
```

The base scraper's `select()` method will find all matching elements.

### Option 3: Use semantic selectors

Look for:

- `article[data-jk]`
- `div[data-jk]`
- `[role="article"][data-jk]`

## Testing After Fix

1. Update the selector in `configs.py`
2. Test locally:
   ```bash
   python scripts/test_selectors.py --file indeed_test.html --config indeed
   ```
3. Verify it finds job cards (should show > 0)
4. Deploy and test in production
5. Check CloudWatch for "Completed scraping Indeed: X jobs found" where X > 0

## Common Indeed Selector Issues

1. **CSS-in-JS classes change frequently** - Avoid selectors like `.css-1ac2h1w.eu4oa1w0`
2. **Use data attributes** - `[data-jk]` is the most stable
3. **Test with real pages** - Indeed's HTML structure varies by region/search type

## Quick Fix to Try

Update `configs.py` line 131:

```python
# Try this first (most stable)
job_card_selector="[data-jk]"

# Or try this (fallback)
job_card_selector="[data-jk], .job_seen_beacon"
```

The `[data-jk]` attribute is Indeed's way of identifying job listings and is much more stable than CSS classes.

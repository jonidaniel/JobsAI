# Deep Dive: Debugging Indeed Scraper Issues

## Problem

Indeed scraper returns 0 jobs despite trying multiple selectors. This suggests the issue is **not** the selector itself.

## Possible Root Causes

### 1. JavaScript-Rendered Content ⚠️ MOST LIKELY

Indeed may load job listings via JavaScript after the initial page load. BeautifulSoup only sees the initial HTML, not JavaScript-rendered content.

**Symptoms:**

- HTML response is received (status 200)
- HTML contains basic page structure but no job listings
- Selectors don't match because content isn't in the HTML yet

**Solution:**

- Use Selenium/Playwright to render JavaScript
- Or use Indeed's API (if available)
- Or check if Indeed has a non-JS fallback URL

### 2. Bot Detection / Blocking

Indeed may be detecting the scraper and returning a blocking page.

**Symptoms:**

- Status 200 but HTML contains "captcha", "blocked", "verify you are human"
- Different HTML structure than expected
- Cloudflare challenge page

**Check CloudWatch logs for:**

```
"Possible blocking detected"
"blocking_indicators": ["captcha", "blocked"]
```

**Solution:**

- Improve headers (add more browser-like headers)
- Use rotating User-Agents
- Add delays between requests
- Use proxy rotation

### 3. Geographic Restrictions

Indeed may serve different content based on IP location.

**Symptoms:**

- Different HTML structure
- Empty results page
- Redirect to different domain

**Solution:**

- Check if Lambda's IP is in a restricted region
- Use VPN/proxy if needed

### 4. Rate Limiting / Throttling

Indeed may be silently throttling requests.

**Symptoms:**

- Status 200 but empty/minimal HTML
- No error messages
- Works sometimes, fails other times

**Solution:**

- Add longer delays between requests
- Reduce request frequency

### 5. Cookie/Session Requirements

Indeed may require cookies or session state.

**Symptoms:**

- First request works, subsequent fail
- Need to visit homepage first

**Solution:**

- Visit homepage first to get cookies
- Maintain session across requests

## Diagnostic Steps

### Step 1: Check What HTML is Actually Received

Look in CloudWatch logs for:

```
"No job cards found on page 1 for query '...'"
```

Check the `extra_fields`:

- `html_length`: How much HTML was received?
- `html_preview`: First 500 chars of HTML
- `has_blocking_indicators`: True if blocking detected
- `blocking_indicators`: List of blocking keywords found

### Step 2: Check HTTP Status Codes

Look for:

```
"Non-200 status (403) for ..."
"Non-200 status (429) for ..."
```

403 = Forbidden (blocked)
429 = Too Many Requests (rate limited)

### Step 3: Check for JavaScript Requirements

If HTML preview shows:

- Basic page structure
- "Please enable JavaScript" message
- Empty `<div id="results">` or similar

Then content is likely JavaScript-rendered.

### Step 4: Test with curl/requests directly

```bash
curl -H "User-Agent: Mozilla/5.0..." \
     "https://www.indeed.com/jobs?q=python&start=0" \
     > indeed_raw.html

# Check if it contains job listings
grep -i "data-jk\|job_seen\|resultContent" indeed_raw.html
```

If grep finds nothing, the content is likely JavaScript-rendered.

## Solutions

### Option 1: Use Selenium/Playwright (JavaScript Rendering)

This requires significant changes:

1. Install Selenium/Playwright in Lambda
2. Use headless browser to render JavaScript
3. Extract HTML after rendering
4. Then parse with BeautifulSoup

**Pros:** Works with JavaScript-rendered content
**Cons:** Much slower, more complex, higher Lambda costs

### Option 2: Improve Bot Detection Evasion

1. **Better headers:**

   ```python
   HEADERS_INDEED = {
       "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...",
       "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
       "Accept-Language": "en-US,en;q=0.9",
       "Accept-Encoding": "gzip, deflate, br",
       "Connection": "keep-alive",
       "Upgrade-Insecure-Requests": "1",
       "Sec-Fetch-Dest": "document",
       "Sec-Fetch-Mode": "navigate",
       "Sec-Fetch-Site": "none",
       "Cache-Control": "max-age=0",
   }
   ```

2. **Visit homepage first:**

   ```python
   # Before scraping, visit homepage to get cookies
   session.get("https://www.indeed.com/")
   ```

3. **Add delays:**
   ```python
   time.sleep(2)  # Wait between requests
   ```

### Option 3: Check if Indeed Has API

Indeed may have an official API that doesn't require scraping.

### Option 4: Use Alternative Approach

If Indeed is too difficult to scrape reliably:

- Focus on Duunitori and Jobly (which work)
- Add other job boards that are easier to scrape
- Consider using third-party job aggregator APIs

## Quick Test

Run a search with Indeed and check CloudWatch logs for:

1. **HTML preview** - Does it contain job listings or blocking messages?
2. **Blocking indicators** - Are there captcha/blocking keywords?
3. **HTML length** - Is it suspiciously short (suggests blocking/error page)?

This will tell us exactly what's happening.

# Testing Scraper Selectors

This guide explains how to test the CSS selectors in `configs.py` to ensure they work correctly.

## Quick Testing Script

The easiest way to test selectors is using the `test_selectors.py` script:

```bash
# Test against a saved HTML file
python scripts/test_selectors.py --file path/to/page.html --config duunitori

# Test against a live URL (requires requests library)
python scripts/test_selectors.py --url https://duunitori.fi/tyopaikat/haku/python --config duunitori

# Test all configs against fixtures
python scripts/test_selectors.py --all

# Show detailed previews of matched content
python scripts/test_selectors.py --file page.html --config duunitori --show-all
```

## Manual Testing Steps

### 1. Save HTML from a Job Board

**Option A: Browser DevTools**

1. Open the job board search page in your browser
2. Open DevTools (F12)
3. Right-click on the page → "Save as" → Save as HTML
4. Or copy HTML from Elements tab

**Option B: Using curl/wget**

```bash
curl -H "User-Agent: Mozilla/5.0..." https://duunitori.fi/tyopaikat/haku/python > test_page.html
```

**Option C: Python script**

```python
import requests
from jobsai.config.headers import HEADERS_DUUNITORI

response = requests.get("https://duunitori.fi/tyopaikat/haku/python", headers=HEADERS_DUUNITORI)
with open("test_page.html", "w") as f:
    f.write(response.text)
```

### 2. Test Selectors

```bash
python scripts/test_selectors.py --file test_page.html --config duunitori --show-all
```

### 3. Check Results

The script will show:

- ✓ or ✗ for each selector
- Number of matches found
- Preview text (if `--show-all` is used)
- Any errors

## Unit Testing

For automated testing, use the test module:

```python
from tests.test_selector_configs import test_all_selectors_on_fixture, print_test_results
from jobsai.utils.scrapers.configs import DUUNITORI_CONFIG

# Test against a fixture
results = test_all_selectors_on_fixture("duunitori_page_1.html", DUUNITORI_CONFIG)
print_test_results(results)
```

## Creating Test Fixtures

1. Save HTML from a job board search page
2. Place it in `tests/fixtures/`
3. Name it: `{board}_page_1.html` (e.g., `jobly_page_1.html`, `indeed_page_1.html`)

## Testing Checklist

For each scraper config, verify:

- [ ] **Job card selector** finds job listings
- [ ] **Title selector** extracts job titles
- [ ] **Company selector** extracts company names
- [ ] **Location selector** extracts locations
- [ ] **URL selector** extracts job URLs
- [ ] **Published date selector** extracts dates (if applicable)
- [ ] **Description snippet selector** extracts snippets (if applicable)
- [ ] **Full description selectors** work on job detail pages

## Common Issues

### Selector returns 0 matches

- Check if the HTML structure changed
- Verify the selector syntax is correct
- Try a more generic selector first, then narrow down

### Selector matches too many elements

- Make the selector more specific
- Add additional class names or attributes
- Use parent-child relationships

### Selector works in browser but not in script

- Check if content is loaded via JavaScript (scraper won't see it)
- Verify headers are correct (some sites block non-browser requests)
- Check if site requires cookies/session

## Example: Testing Indeed Selectors

```bash
# 1. Save Indeed search page
curl -H "User-Agent: Mozilla/5.0..." "https://www.indeed.com/jobs?q=python&start=0" > indeed_test.html

# 2. Test selectors
python scripts/test_selectors.py --file indeed_test.html --config indeed --show-all

# 3. If selectors fail, inspect HTML and update configs.py
```

## Tips

- **Test with multiple pages**: HTML structure can vary between pages
- **Test edge cases**: Empty results, single result, many results
- **Keep fixtures updated**: Re-save fixtures periodically as sites change
- **Use browser DevTools**: Inspect elements to find better selectors
- **Check for data attributes**: Often more stable than CSS classes

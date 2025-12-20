"""
Test selector configurations for all scrapers.

This module provides utilities to test selectors against HTML fixtures
or live pages to verify they work correctly.
"""

import os
from bs4 import BeautifulSoup
from typing import Dict, List, Optional

from jobsai.utils.scrapers.configs import (
    DUUNITORI_CONFIG,
    JOBLY_CONFIG,
)


def load_fixture(path: str) -> str:
    """Load HTML fixture as text."""
    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", path)
    with open(fixture_path, "r", encoding="utf-8") as f:
        return f.read()


def test_selector_on_html(
    html: str, selector: str, config_name: str, field_name: str
) -> Dict[str, any]:
    """
    Test a single selector on HTML and return results.

    Args:
        html: HTML content to test against
        selector: CSS selector to test
        config_name: Name of the config (for reporting)
        field_name: Name of the field being tested (for reporting)

    Returns:
        Dict with test results
    """
    soup = BeautifulSoup(html, "html.parser")
    results = {
        "config": config_name,
        "field": field_name,
        "selector": selector,
        "matches": [],
        "match_count": 0,
        "success": False,
    }

    if not selector:
        results["error"] = "Selector is None or empty"
        return results

    try:
        # Try select_one first (for single matches)
        single_match = soup.select_one(selector)
        if single_match:
            results["matches"].append(
                {
                    "type": "single",
                    "text": single_match.get_text(strip=True)[:200],  # First 200 chars
                    "html": str(single_match)[:500],  # First 500 chars
                }
            )
            results["success"] = True

        # Also try select (for multiple matches)
        all_matches = soup.select(selector)
        results["match_count"] = len(all_matches)

        if len(all_matches) > 1:
            results["matches"].append(
                {
                    "type": "multiple",
                    "count": len(all_matches),
                    "first_text": all_matches[0].get_text(strip=True)[:200],
                }
            )

    except Exception as e:
        results["error"] = str(e)

    return results


def test_job_card_selector(html: str, config) -> Dict[str, any]:
    """Test if job_card_selector finds job cards."""
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select(config.job_card_selector)

    return {
        "selector": config.job_card_selector,
        "cards_found": len(cards),
        "success": len(cards) > 0,
        "sample_card_html": str(cards[0])[:500] if cards else None,
    }


def test_all_selectors_on_fixture(fixture_path: str, config) -> Dict[str, any]:
    """
    Test all selectors from a config against a fixture HTML file.

    Args:
        fixture_path: Path to HTML fixture file
        config: ScraperConfig to test

    Returns:
        Dict with test results for all selectors
    """
    html = load_fixture(fixture_path)
    results = {
        "config_name": config.name,
        "fixture": fixture_path,
        "job_cards": test_job_card_selector(html, config),
        "selectors": {},
    }

    # Test each selector
    selectors_to_test = {
        "title": config.title_selector,
        "company": config.company_selector,
        "location": config.location_selector,
        "url": config.url_selector,
        "published_date": config.published_date_selector,
        "description_snippet": config.description_snippet_selector,
    }

    for field_name, selector in selectors_to_test.items():
        if selector:  # Skip None selectors
            results["selectors"][field_name] = test_selector_on_html(
                html, selector, config.name, field_name
            )

    # Test full_description_selectors (list)
    results["selectors"]["full_description"] = []
    for i, selector in enumerate(config.full_description_selectors):
        result = test_selector_on_html(
            html, selector, config.name, f"full_description[{i}]"
        )
        results["selectors"]["full_description"].append(result)

    return results


def print_test_results(results: Dict):
    """Pretty print test results."""
    print(f"\n{'='*60}")
    print(f"Testing: {results['config_name']}")
    print(f"Fixture: {results['fixture']}")
    print(f"{'='*60}")

    # Job cards
    cards = results["job_cards"]
    status = "✓" if cards["success"] else "✗"
    print(f"\n{status} Job Cards: {cards['cards_found']} found")
    print(f"   Selector: {cards['selector']}")

    # Individual selectors
    print(f"\nSelectors:")
    for field_name, result in results["selectors"].items():
        if isinstance(result, list):
            # Full description selectors (list)
            print(f"\n  {field_name}:")
            for i, r in enumerate(result):
                status = "✓" if r.get("success") else "✗"
                count = r.get("match_count", 0)
                print(f"    [{i}] {status} {r['selector']} ({count} matches)")
                if r.get("error"):
                    print(f"        ERROR: {r['error']}")
        else:
            # Single selector
            status = "✓" if result.get("success") else "✗"
            count = result.get("match_count", 0)
            print(f"  {status} {field_name}: {count} matches")
            print(f"    Selector: {result['selector']}")
            if result.get("error"):
                print(f"    ERROR: {result['error']}")
            elif result.get("matches"):
                match = result["matches"][0]
                if "text" in match:
                    preview = match["text"][:100]
                    print(f"    Preview: {preview}...")


# Example test functions
def test_duunitori_selectors():
    """Test Duunitori selectors against fixture."""
    results = test_all_selectors_on_fixture("duunitori_page_1.html", DUUNITORI_CONFIG)
    print_test_results(results)
    return results


def test_jobly_selectors():
    """Test Jobly selectors - requires fixture file."""
    # Note: You'll need to create a jobly_page_1.html fixture
    # results = test_all_selectors_on_fixture("jobly_page_1.html", JOBLY_CONFIG)
    # print_test_results(results)
    print("Jobly fixture not found. Create tests/fixtures/jobly_page_1.html first.")
    return None


if __name__ == "__main__":
    # Run tests
    print("Testing Duunitori selectors...")
    test_duunitori_selectors()

    print("\n\nTesting Jobly selectors...")
    test_jobly_selectors()

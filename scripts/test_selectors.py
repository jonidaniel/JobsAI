#!/usr/bin/env python3
"""
Quick selector testing script.

Usage:
    # Test selectors against a saved HTML file
    python scripts/test_selectors.py --file path/to/html.html --config duunitori

    # Test selectors against a live URL (requires requests)
    python scripts/test_selectors.py --url https://duunitori.fi/tyopaikat/haku/python --config duunitori

    # Test all configs against fixtures
    python scripts/test_selectors.py --all
"""

import argparse
import sys
from pathlib import Path
from bs4 import BeautifulSoup

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from jobsai.utils.scrapers.configs import DUUNITORI_CONFIG, JOBLY_CONFIG, INDEED_CONFIG


def load_html_from_file(file_path: str) -> str:
    """Load HTML from file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def load_html_from_url(url: str) -> str:
    """Load HTML from URL."""
    try:
        import requests
        from jobsai.config.headers import (
            HEADERS_DUUNITORI,
            HEADERS_JOBLY,
            HEADERS_INDEED,
        )

        # Use appropriate headers
        if "duunitori" in url.lower():
            headers = HEADERS_DUUNITORI
        elif "jobly" in url.lower():
            headers = HEADERS_JOBLY
        elif "indeed" in url.lower():
            headers = HEADERS_INDEED
        else:
            headers = HEADERS_DUUNITORI  # Default

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except ImportError:
        print(
            "ERROR: requests library required for URL testing. Install with: pip install requests"
        )
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to fetch URL: {e}")
        sys.exit(1)


def test_selector(html: str, selector: str, name: str) -> dict:
    """Test a single selector."""
    soup = BeautifulSoup(html, "html.parser")
    result = {
        "name": name,
        "selector": selector,
        "found": False,
        "count": 0,
        "preview": None,
    }

    if not selector:
        result["error"] = "Selector is None"
        return result

    try:
        matches = soup.select(selector)
        result["count"] = len(matches)
        result["found"] = len(matches) > 0

        if matches:
            # Get text preview from first match
            text = matches[0].get_text(strip=True)
            result["preview"] = text[:150] + "..." if len(text) > 150 else text

            # For job cards, show HTML structure
            if name == "job_card":
                result["html_preview"] = (
                    str(matches[0])[:300] + "..."
                    if len(str(matches[0])) > 300
                    else str(matches[0])
                )

    except Exception as e:
        result["error"] = str(e)

    return result


def test_config(html: str, config, show_all: bool = False):
    """Test all selectors in a config."""
    print(f"\n{'='*70}")
    print(f"Testing: {config.name.upper()}")
    print(f"{'='*70}")

    # Test job card selector first
    card_result = test_selector(html, config.job_card_selector, "job_card")
    print(
        f"\n{'✓' if card_result['found'] else '✗'} Job Cards: {card_result['count']} found"
    )
    print(f"   Selector: {card_result['selector']}")
    if card_result.get("error"):
        print(f"   ERROR: {card_result['error']}")
    elif card_result.get("html_preview") and show_all:
        print(f"   HTML: {card_result['html_preview']}")

    # Test other selectors (only if cards found, or if show_all)
    if not card_result["found"] and not show_all:
        print("\n⚠️  No job cards found. Skipping field selector tests.")
        print("   Use --all to test field selectors anyway.")
        return

    # Test on first job card if available
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select(config.job_card_selector)
    test_html = str(cards[0]) if cards else html

    selectors = {
        "title": config.title_selector,
        "company": config.company_selector,
        "location": config.location_selector,
        "url": config.url_selector,
        "published_date": config.published_date_selector,
        "description_snippet": config.description_snippet_selector,
    }

    print(
        f"\nField Selectors (testing on {'first job card' if cards else 'full HTML'}):"
    )
    for field, selector in selectors.items():
        if selector:
            result = test_selector(test_html, selector, field)
            status = "✓" if result["found"] else "✗"
            print(f"  {status} {field:20} {result['count']:2} matches")
            if result.get("error"):
                print(f"      ERROR: {result['error']}")
            elif result.get("preview") and show_all:
                print(f"      Preview: {result['preview']}")

    # Test full description selectors
    print(f"\nFull Description Selectors:")
    for i, selector in enumerate(config.full_description_selectors):
        result = test_selector(html, selector, f"full_desc[{i}]")
        status = "✓" if result["found"] else "✗"
        print(f"  {status} [{i}] {selector}")
        if result.get("error"):
            print(f"      ERROR: {result['error']}")
        elif result.get("preview") and show_all:
            print(f"      Preview: {result['preview'][:100]}...")


def main():
    parser = argparse.ArgumentParser(description="Test scraper selectors")
    parser.add_argument("--file", help="Path to HTML file")
    parser.add_argument("--url", help="URL to fetch HTML from")
    parser.add_argument(
        "--config", choices=["duunitori", "jobly", "indeed"], help="Config to test"
    )
    parser.add_argument(
        "--all", action="store_true", help="Test all configs against fixtures"
    )
    parser.add_argument(
        "--show-all", action="store_true", help="Show preview text for all matches"
    )

    args = parser.parse_args()

    if args.all:
        # Test all configs (requires fixtures)
        print("Testing all configs against fixtures...")
        fixtures_dir = Path(__file__).parent.parent / "tests" / "fixtures"

        configs = {
            "duunitori": (DUUNITORI_CONFIG, "duunitori_page_1.html"),
            "jobly": (JOBLY_CONFIG, "jobly_page_1.html"),
            "indeed": (INDEED_CONFIG, "indeed_page_1.html"),
        }

        for name, (config, fixture) in configs.items():
            fixture_path = fixtures_dir / fixture
            if fixture_path.exists():
                html = load_html_from_file(str(fixture_path))
                test_config(html, config, args.show_all)
            else:
                print(f"\n⚠️  Fixture not found: {fixture_path}")

    elif args.file or args.url:
        if not args.config:
            print("ERROR: --config required when using --file or --url")
            sys.exit(1)

        # Load HTML
        if args.file:
            html = load_html_from_file(args.file)
        else:
            html = load_html_from_url(args.url)

        # Get config
        configs = {
            "duunitori": DUUNITORI_CONFIG,
            "jobly": JOBLY_CONFIG,
            "indeed": INDEED_CONFIG,
        }
        config = configs[args.config]

        # Test
        test_config(html, config, args.show_all)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()

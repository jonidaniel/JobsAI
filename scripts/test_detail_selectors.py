#!/usr/bin/env python3
"""
Test full description selectors on job detail pages.

Full description selectors are used on job detail pages (not search results),
so they need to be tested against actual job detail page HTML.

Usage:
    # Test against a saved detail page HTML
    python scripts/test_detail_selectors.py --file path/to/detail.html --config duunitori

    # Test against a live job detail URL
    python scripts/test_detail_selectors.py --url https://duunitori.fi/tyopaikat/123456 --config duunitori

    # Test all configs against fixtures
    python scripts/test_detail_selectors.py --all
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


def test_detail_selectors(html: str, config):
    """Test full description selectors on a job detail page."""
    soup = BeautifulSoup(html, "html.parser")

    print(f"\n{'='*70}")
    print(f"Testing Full Description Selectors: {config.name.upper()}")
    print(f"{'='*70}")

    print(f"\nTesting {len(config.full_description_selectors)} selector(s):\n")

    found_any = False
    for i, selector in enumerate(config.full_description_selectors):
        result = soup.select_one(selector)

        if result:
            found_any = True
            text = result.get_text(strip=True)
            text_length = len(text)
            preview = text[:200] + "..." if text_length > 200 else text

            print(f"  ✓ [{i}] {selector}")
            print(f"     Found: {text_length} characters")
            print(f"     Preview: {preview}\n")

            # Show HTML structure
            html_preview = (
                str(result)[:500] + "..." if len(str(result)) > 500 else str(result)
            )
            print(f"     HTML structure:")
            print(f"     {html_preview}\n")
        else:
            print(f"  ✗ [{i}] {selector}")
            print(f"     No match found\n")

    if not found_any:
        print("\n⚠️  WARNING: None of the selectors matched!")
        print("   The full description will be empty when scraping.")
        print("\n   Suggestions:")
        print("   1. Inspect the HTML structure of the detail page")
        print("   2. Look for containers with job description text")
        print("   3. Try more generic selectors first, then narrow down")
        print("   4. Check if content is loaded via JavaScript (won't work)")

    # Also try to find any large text blocks that might be descriptions
    print("\n" + "=" * 70)
    print("Alternative: Finding large text blocks (potential descriptions)")
    print("=" * 70 + "\n")

    # Find all divs, sections, articles with substantial text
    candidates = []
    for tag in soup.find_all(["div", "section", "article", "main"]):
        text = tag.get_text(strip=True)
        if len(text) > 500:  # Substantial text block
            # Get classes/ids for identification
            classes = " ".join(tag.get("class", []))
            tag_id = tag.get("id", "")
            selector_hint = ""
            if tag_id:
                selector_hint = f"#{tag_id}"
            elif classes:
                selector_hint = "." + ".".join(tag.get("class", []))
            else:
                selector_hint = tag.name

            candidates.append(
                {
                    "selector_hint": selector_hint,
                    "length": len(text),
                    "preview": text[:150],
                    "tag": tag.name,
                }
            )

    # Sort by length (longest first)
    candidates.sort(key=lambda x: x["length"], reverse=True)

    if candidates:
        print(f"Found {len(candidates)} potential description containers:\n")
        for i, candidate in enumerate(candidates[:5]):  # Show top 5
            print(f"  [{i+1}] {candidate['selector_hint']} ({candidate['tag']})")
            print(f"      Length: {candidate['length']} characters")
            print(f"      Preview: {candidate['preview']}...\n")
    else:
        print("  No large text blocks found.")


def main():
    parser = argparse.ArgumentParser(
        description="Test full description selectors on job detail pages"
    )
    parser.add_argument("--file", help="Path to job detail page HTML file")
    parser.add_argument("--url", help="URL of job detail page")
    parser.add_argument(
        "--config", choices=["duunitori", "jobly", "indeed"], help="Config to test"
    )
    parser.add_argument(
        "--all", action="store_true", help="Test all configs against fixtures"
    )

    args = parser.parse_args()

    if args.all:
        # Test all configs (requires fixtures)
        print("Testing all configs against fixtures...")
        fixtures_dir = Path(__file__).parent.parent / "tests" / "fixtures"

        configs = {
            "duunitori": (DUUNITORI_CONFIG, "duunitori_detail.html"),
            "jobly": (JOBLY_CONFIG, "jobly_detail.html"),
            "indeed": (INDEED_CONFIG, "indeed_detail.html"),
        }

        for name, (config, fixture) in configs.items():
            fixture_path = fixtures_dir / fixture
            if fixture_path.exists():
                html = load_html_from_file(str(fixture_path))
                test_detail_selectors(html, config)
            else:
                print(f"\n⚠️  Fixture not found: {fixture_path}")
                print(
                    f"   Create it by saving a job detail page HTML to that location."
                )

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
        test_detail_selectors(html, config)

    else:
        parser.print_help()
        print("\nExample:")
        print(
            "  python scripts/test_detail_selectors.py --url https://duunitori.fi/tyopaikat/123456 --config duunitori"
        )


if __name__ == "__main__":
    main()

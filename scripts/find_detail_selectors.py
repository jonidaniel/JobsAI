#!/usr/bin/env python3
"""
Helper script to find the correct selectors for job detail pages.

This script analyzes a job detail page HTML and suggests selectors for
the full job description.

Usage:
    python scripts/find_detail_selectors.py --file detail_page.html
    python scripts/find_detail_selectors.py --url https://duunitori.fi/tyopaikat/123456
"""

import argparse
import sys
from pathlib import Path
from bs4 import BeautifulSoup

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def load_html(file_path: str = None, url: str = None) -> str:
    """Load HTML from file or URL."""
    if file_path:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    elif url:
        try:
            import requests
            from jobsai.config.headers import HEADERS_DUUNITORI

            response = requests.get(url, headers=HEADERS_DUUNITORI, timeout=10)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"ERROR: Failed to fetch URL: {e}")
            sys.exit(1)
    else:
        print("ERROR: Must provide --file or --url")
        sys.exit(1)


def find_description_candidates(soup: BeautifulSoup):
    """Find potential description containers."""
    candidates = []

    # Strategy 1: Look for elements with common description-related classes/ids
    description_keywords = [
        "description",
        "content",
        "body",
        "details",
        "job",
        "text",
        "main",
        "article",
    ]

    for keyword in description_keywords:
        # By class
        for tag in soup.find_all(
            class_=lambda x: x and keyword.lower() in " ".join(x).lower()
        ):
            text = tag.get_text(strip=True)
            if len(text) > 200:  # Substantial content
                classes = " ".join(tag.get("class", []))
                selector = f".{'.'.join(tag.get('class', []))}"
                candidates.append(
                    {
                        "selector": selector,
                        "type": "class",
                        "length": len(text),
                        "preview": text[:150],
                        "tag": tag.name,
                    }
                )

        # By id
        for tag in soup.find_all(id=lambda x: x and keyword.lower() in str(x).lower()):
            text = tag.get_text(strip=True)
            if len(text) > 200:
                tag_id = tag.get("id", "")
                selector = f"#{tag_id}"
                candidates.append(
                    {
                        "selector": selector,
                        "type": "id",
                        "length": len(text),
                        "preview": text[:150],
                        "tag": tag.name,
                    }
                )

    # Strategy 2: Find largest text blocks
    all_elements = soup.find_all(["div", "section", "article", "main"])
    text_blocks = []
    for tag in all_elements:
        text = tag.get_text(strip=True)
        if len(text) > 500:  # Substantial text
            classes = tag.get("class", [])
            tag_id = tag.get("id", "")
            selector = ""
            if tag_id:
                selector = f"#{tag_id}"
            elif classes:
                selector = f".{'.'.join(classes)}"
            else:
                continue  # Skip elements without identifiers

            text_blocks.append(
                {
                    "selector": selector,
                    "length": len(text),
                    "preview": text[:150],
                    "tag": tag.name,
                    "html_preview": str(tag)[:300],
                }
            )

    # Sort by length
    text_blocks.sort(key=lambda x: x["length"], reverse=True)

    return candidates, text_blocks


def main():
    parser = argparse.ArgumentParser(
        description="Find selectors for job description on detail pages"
    )
    parser.add_argument("--file", help="Path to HTML file")
    parser.add_argument("--url", help="URL to fetch")
    parser.add_argument("--show-html", action="store_true", help="Show HTML structure")

    args = parser.parse_args()

    html = load_html(args.file, args.url)
    soup = BeautifulSoup(html, "html.parser")

    print("=" * 70)
    print("Finding Job Description Selectors")
    print("=" * 70)

    # Find candidates
    keyword_candidates, text_blocks = find_description_candidates(soup)

    print("\n1. Elements with description-related keywords:")
    print("-" * 70)
    if keyword_candidates:
        # Remove duplicates
        seen = set()
        unique_candidates = []
        for c in keyword_candidates:
            key = (c["selector"], c["length"])
            if key not in seen:
                seen.add(key)
                unique_candidates.append(c)

        unique_candidates.sort(key=lambda x: x["length"], reverse=True)

        for i, candidate in enumerate(unique_candidates[:10], 1):
            print(f"\n  [{i}] {candidate['selector']} ({candidate['tag']})")
            print(f"      Length: {candidate['length']} characters")
            print(f"      Preview: {candidate['preview']}...")
    else:
        print("  No matches found")

    print("\n\n2. Largest text blocks (potential descriptions):")
    print("-" * 70)
    if text_blocks:
        for i, block in enumerate(text_blocks[:10], 1):
            print(f"\n  [{i}] {block['selector']} ({block['tag']})")
            print(f"      Length: {block['length']} characters")
            print(f"      Preview: {block['preview']}...")
            if args.show_html:
                print(f"      HTML: {block['html_preview']}...")
    else:
        print("  No large text blocks found")

    print("\n\n" + "=" * 70)
    print("Recommendations:")
    print("=" * 70)
    if text_blocks:
        best = text_blocks[0]
        print(f"\n✓ Best candidate: {best['selector']}")
        print(
            f"  This selector targets the largest text block ({best['length']} chars)"
        )
        print(f"\n  Add to configs.py:")
        print(f"  full_description_selectors=[")
        print(f"      \"{best['selector']}\",")
        print(f"  ]")
    else:
        print("\n⚠️  Could not find clear description container.")
        print("  Try:")
        print("  1. Inspect the page in browser DevTools")
        print("  2. Look for the main content area")
        print("  3. Check if content is loaded via JavaScript")


if __name__ == "__main__":
    main()

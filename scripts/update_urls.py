"""Auto-discover Claude Code doc pages from sitemap and update urls.json."""

import json
import re
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
URLS_FILE = ROOT / "urls.json"
SITEMAP_URL = "https://code.claude.com/docs/sitemap.xml"


def fetch_sitemap_urls() -> list[str]:
    """Fetch sitemap.xml and extract all English doc URLs."""
    resp = httpx.get(SITEMAP_URL, follow_redirects=True, timeout=30.0)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "xml")
    urls = []
    for loc in soup.find_all("loc"):
        url = loc.get_text(strip=True)
        # Only English pages
        if "/docs/en/" in url:
            urls.append(url)

    return sorted(urls)


def update_urls() -> dict:
    """Compare sitemap URLs with urls.json and update if needed.

    Returns: {
        "added": list of new URLs,
        "removed": list of removed URLs,
        "total": total count,
        "changed": bool,
    }
    """
    current = set(json.loads(URLS_FILE.read_text(encoding="utf-8")))
    sitemap = set(fetch_sitemap_urls())

    added = sorted(sitemap - current)
    removed = sorted(current - sitemap)

    if added or removed:
        updated = sorted(sitemap)
        URLS_FILE.write_text(json.dumps(updated, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return {
        "added": added,
        "removed": removed,
        "total": len(sitemap),
        "changed": bool(added or removed),
    }


def main():
    print("Checking sitemap for new/removed pages...")
    result = update_urls()

    if result["added"]:
        print(f"\n[NEW] {len(result['added'])} page(s) added:")
        for url in result["added"]:
            print(f"  + {url}")

    if result["removed"]:
        print(f"\n[REMOVED] {len(result['removed'])} page(s) no longer in sitemap:")
        for url in result["removed"]:
            print(f"  - {url}")

    if not result["changed"]:
        print(f"[OK] No changes. {result['total']} pages in sitemap.")
    else:
        print(f"\n[OK] urls.json updated. Total: {result['total']} pages.")

    return result


if __name__ == "__main__":
    main()

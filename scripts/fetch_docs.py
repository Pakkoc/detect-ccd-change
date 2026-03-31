"""Fetch all Claude Code documentation pages and save as text snapshots."""

import json
import asyncio
import hashlib
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
URLS_FILE = ROOT / "urls.json"
SNAPSHOTS_DIR = ROOT / "snapshots"


def extract_main_content(html: str) -> str:
    """Extract meaningful text content from an HTML page, ignoring nav/footer/scripts."""
    soup = BeautifulSoup(html, "html.parser")

    # Remove script, style, nav, footer, header elements
    for tag in soup.find_all(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()

    # Try to find the main content area
    main = soup.find("main") or soup.find("article") or soup.find(attrs={"role": "main"})
    if main:
        text = main.get_text(separator="\n", strip=True)
    else:
        text = soup.get_text(separator="\n", strip=True)

    # Clean up: collapse multiple blank lines
    lines = [line.strip() for line in text.splitlines()]
    cleaned = "\n".join(line for line in lines if line)
    return cleaned


def url_to_filename(url: str) -> str:
    """Convert URL to a safe filename."""
    # e.g. https://code.claude.com/docs/en/overview -> overview.txt
    slug = url.rstrip("/").split("/")[-1]
    return f"{slug}.txt"


async def fetch_single(client: httpx.AsyncClient, url: str) -> tuple[str, str | None, str | None]:
    """Fetch a single URL. Returns (url, content, error)."""
    try:
        resp = await client.get(url, follow_redirects=True)
        resp.raise_for_status()
        content = extract_main_content(resp.text)
        return (url, content, None)
    except Exception as e:
        return (url, None, str(e))


async def fetch_all() -> dict[str, str]:
    """Fetch all documentation pages. Returns {filename: content}."""
    urls = json.loads(URLS_FILE.read_text(encoding="utf-8"))
    results: dict[str, str] = {}
    errors: list[tuple[str, str]] = []

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Fetch in batches of 10 to avoid overwhelming the server
        batch_size = 10
        for i in range(0, len(urls), batch_size):
            batch = urls[i : i + batch_size]
            tasks = [fetch_single(client, url) for url in batch]
            batch_results = await asyncio.gather(*tasks)

            for url, content, error in batch_results:
                if error:
                    errors.append((url, error))
                elif content:
                    filename = url_to_filename(url)
                    results[filename] = content

            # Small delay between batches
            if i + batch_size < len(urls):
                await asyncio.sleep(0.5)

    if errors:
        print(f"[WARN] {len(errors)} pages failed to fetch:")
        for url, err in errors:
            print(f"  - {url}: {err}")

    return results


def save_snapshots(docs: dict[str, str]) -> None:
    """Save fetched docs to snapshots directory."""
    SNAPSHOTS_DIR.mkdir(exist_ok=True)
    for filename, content in docs.items():
        (SNAPSHOTS_DIR / filename).write_text(content, encoding="utf-8")


def main() -> dict[str, str]:
    """Fetch all docs and save. Returns the fetched docs dict."""
    print(f"Fetching {len(json.loads(URLS_FILE.read_text(encoding='utf-8')))} documentation pages...")
    docs = asyncio.run(fetch_all())
    print(f"Successfully fetched {len(docs)} pages.")
    save_snapshots(docs)
    print("Snapshots saved.")
    return docs


if __name__ == "__main__":
    main()

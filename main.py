"""
Claude Code Documentation Change Detector

Main entry point: fetches docs, compares with previous snapshot, sends email.
"""

import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SNAPSHOTS_DIR = ROOT / "snapshots"


def has_previous_snapshots() -> bool:
    """Check if there are any previously committed snapshots."""
    result = subprocess.run(
        ["git", "ls-files", "snapshots/"],
        capture_output=True, text=True, cwd=ROOT, encoding="utf-8"
    )
    return bool(result.stdout.strip())


def commit_snapshots(message: str) -> None:
    """Stage and commit all snapshot files."""
    subprocess.run(["git", "add", "snapshots/"], cwd=ROOT, check=True)
    subprocess.run(
        ["git", "commit", "-m", message],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8"
    )


def run() -> dict:
    """
    Main workflow:
    1. Check if previous snapshots exist
    2. Fetch current docs
    3. Compare with previous (if exists)
    4. Generate report
    5. Commit new snapshots

    Returns: {
        "is_first_run": bool,
        "has_changes": bool,
        "changes": dict | None,
        "html_email": str,
        "summary": str,
    }
    """
    from scripts.update_urls import update_urls
    from scripts.fetch_docs import main as fetch_main
    from scripts.diff_docs import get_git_diff, format_diff_summary
    from scripts.generate_email import generate_html_email, generate_no_changes_email

    # Step 0: Auto-update URL list from sitemap
    print("=" * 60)
    print("Step 0: Checking sitemap for new/removed pages...")
    print("=" * 60)
    url_result = update_urls()
    if url_result["changed"]:
        for u in url_result["added"]:
            print(f"  [NEW PAGE] {u}")
        for u in url_result["removed"]:
            print(f"  [REMOVED]  {u}")
        print(f"  urls.json updated: {url_result['total']} pages")
        # Commit updated urls.json
        subprocess.run(["git", "add", "urls.json"], cwd=ROOT, check=True)
        subprocess.run(
            ["git", "commit", "-m", f"urls: +{len(url_result['added'])} -{len(url_result['removed'])} pages from sitemap"],
            cwd=ROOT, capture_output=True, text=True, encoding="utf-8"
        )
    else:
        print(f"  [OK] {url_result['total']} pages, no changes.")

    first_run = not has_previous_snapshots()

    # Step 1: Fetch all docs
    print("\n" + "=" * 60)
    print("Step 1: Fetching documentation...")
    print("=" * 60)
    docs = fetch_main()

    if first_run:
        # First run: just save and commit baseline
        print("\n[INFO] First run detected. Saving baseline snapshots...")
        commit_snapshots("baseline: initial documentation snapshot")
        return {
            "is_first_run": True,
            "has_changes": False,
            "changes": None,
            "html_email": None,
            "summary": f"Baseline saved. {len(docs)} pages captured. Next run will detect changes.",
        }

    # Step 2: Compare with previous
    print("\n" + "=" * 60)
    print("Step 2: Comparing with previous snapshot...")
    print("=" * 60)
    changes = get_git_diff()

    if not changes:
        print("\n[OK] No changes detected.")
        commit_snapshots("check: no changes detected")
        return {
            "is_first_run": False,
            "has_changes": False,
            "changes": {},
            "html_email": generate_no_changes_email(),
            "summary": "No changes detected in any of the 75 documentation pages.",
        }

    # Step 3: Generate report
    print("\n" + "=" * 60)
    print("Step 3: Generating change report...")
    print("=" * 60)
    summary = format_diff_summary(changes)
    html_email = generate_html_email(changes)
    print(summary)

    # Step 4: Commit updated snapshots
    added_count = sum(1 for v in changes.values() if v["status"] == "added")
    modified_count = sum(1 for v in changes.values() if v["status"] == "modified")
    deleted_count = sum(1 for v in changes.values() if v["status"] == "deleted")
    commit_msg = f"update: +{added_count} ~{modified_count} -{deleted_count} changes detected"
    commit_snapshots(commit_msg)

    # Save HTML report to file for reference
    report_path = ROOT / "last_report.html"
    report_path.write_text(html_email, encoding="utf-8")
    print(f"\n[OK] HTML report saved to {report_path}")

    return {
        "is_first_run": False,
        "has_changes": True,
        "changes": changes,
        "html_email": html_email,
        "summary": summary,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--send-email", action="store_true", help="Send email report via Gmail SMTP")
    args = parser.parse_args()

    result = run()
    print("\n" + "=" * 60)
    print("RESULT:", result["summary"])
    print("=" * 60)

    if args.send_email and result["html_email"]:
        from scripts.send_email import send_report
        send_report(result["html_email"], has_changes=result["has_changes"])

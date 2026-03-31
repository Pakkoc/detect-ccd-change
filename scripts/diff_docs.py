"""Compare current snapshots with previous git-committed versions and generate diffs."""

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOTS_DIR = ROOT / "snapshots"


def get_git_diff() -> dict[str, dict]:
    """
    Use git diff to compare current snapshots with the last committed version.
    Returns a dict of changed files with their diff details.

    Structure: {
        "filename": {
            "status": "modified" | "added" | "deleted",
            "diff": "unified diff text",
        }
    }
    """
    changes: dict[str, dict] = {}

    # Check for new (untracked) files in snapshots/
    result = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "snapshots/"],
        capture_output=True, text=True, cwd=ROOT, encoding="utf-8"
    )
    for line in result.stdout.strip().splitlines():
        if line:
            filename = Path(line).name
            content = (ROOT / line).read_text(encoding="utf-8")
            changes[filename] = {
                "status": "added",
                "diff": f"+ (new page, {len(content.splitlines())} lines)",
                "content_preview": content[:500],
            }

    # Check for modified files
    result = subprocess.run(
        ["git", "diff", "--name-status", "snapshots/"],
        capture_output=True, text=True, cwd=ROOT, encoding="utf-8"
    )
    for line in result.stdout.strip().splitlines():
        if not line:
            continue
        parts = line.split("\t", 1)
        if len(parts) < 2:
            continue
        status_code, filepath = parts
        filename = Path(filepath).name

        if status_code == "D":
            changes[filename] = {"status": "deleted", "diff": "(page removed)"}
        elif status_code == "M":
            # Get the actual unified diff
            diff_result = subprocess.run(
                ["git", "diff", "-U3", filepath],
                capture_output=True, text=True, cwd=ROOT, encoding="utf-8"
            )
            changes[filename] = {
                "status": "modified",
                "diff": diff_result.stdout,
            }

    # Check for deleted files (were tracked but now missing)
    result = subprocess.run(
        ["git", "diff", "--name-status", "--diff-filter=D", "snapshots/"],
        capture_output=True, text=True, cwd=ROOT, encoding="utf-8"
    )
    for line in result.stdout.strip().splitlines():
        if not line:
            continue
        parts = line.split("\t", 1)
        if len(parts) < 2:
            continue
        _, filepath = parts
        filename = Path(filepath).name
        if filename not in changes:
            changes[filename] = {"status": "deleted", "diff": "(page removed)"}

    return changes


def filename_to_url(filename: str) -> str:
    """Convert snapshot filename back to URL."""
    slug = filename.replace(".txt", "")
    return f"https://code.claude.com/docs/en/{slug}"


def format_diff_summary(changes: dict[str, dict]) -> str:
    """Format changes into a human-readable summary."""
    if not changes:
        return "No changes detected."

    lines = [f"Total changes: {len(changes)} page(s)\n"]

    added = {k: v for k, v in changes.items() if v["status"] == "added"}
    modified = {k: v for k, v in changes.items() if v["status"] == "modified"}
    deleted = {k: v for k, v in changes.items() if v["status"] == "deleted"}

    if added:
        lines.append(f"[NEW] {len(added)} page(s) added:")
        for f in added:
            lines.append(f"  + {filename_to_url(f)}")
        lines.append("")

    if modified:
        lines.append(f"[MODIFIED] {len(modified)} page(s) changed:")
        for f, info in modified.items():
            lines.append(f"  ~ {filename_to_url(f)}")
            lines.append(info["diff"])
        lines.append("")

    if deleted:
        lines.append(f"[DELETED] {len(deleted)} page(s) removed:")
        for f in deleted:
            lines.append(f"  - {filename_to_url(f)}")

    return "\n".join(lines)


def main() -> dict[str, dict]:
    """Run diff and print summary. Returns the changes dict."""
    changes = get_git_diff()
    print(format_diff_summary(changes))
    return changes


if __name__ == "__main__":
    main()

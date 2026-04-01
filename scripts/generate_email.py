"""Generate HTML email content from diff results."""

import html
from datetime import datetime, timezone, timedelta

from scripts.diff_docs import filename_to_url


KST = timezone(timedelta(hours=9))


def diff_to_html_table(diff_text: str) -> str:
    """Convert unified diff text into an HTML table with color coding."""
    if not diff_text or diff_text.startswith("+ (new page") or diff_text == "(page removed)":
        return f"<p><em>{html.escape(diff_text)}</em></p>"

    rows = []
    for line in diff_text.splitlines():
        escaped = html.escape(line)
        if line.startswith("+++") or line.startswith("---"):
            rows.append(f'<tr style="background:#f0f0f0;color:#666"><td><code>{escaped}</code></td></tr>')
        elif line.startswith("@@"):
            rows.append(f'<tr style="background:#e8e8ff;color:#336"><td><code>{escaped}</code></td></tr>')
        elif line.startswith("+"):
            rows.append(f'<tr style="background:#e6ffec"><td><code>{escaped}</code></td></tr>')
        elif line.startswith("-"):
            rows.append(f'<tr style="background:#ffebe9"><td><code>{escaped}</code></td></tr>')
        else:
            rows.append(f'<tr><td><code>{escaped}</code></td></tr>')

    return f'<table style="width:100%;border-collapse:collapse;font-size:13px;border:1px solid #ddd;margin:8px 0">{"".join(rows)}</table>'


def generate_html_email(changes: dict[str, dict]) -> str:
    """Generate a full HTML email body from changes dict."""
    now = datetime.now(KST).strftime("%Y-%m-%d %H:%M KST")

    added = {k: v for k, v in changes.items() if v["status"] == "added"}
    modified = {k: v for k, v in changes.items() if v["status"] == "modified"}
    deleted = {k: v for k, v in changes.items() if v["status"] == "deleted"}

    sections = []

    # Summary section
    summary_items = []
    if added:
        summary_items.append(f'<span style="color:#1a7f37">+{len(added)} added</span>')
    if modified:
        summary_items.append(f'<span style="color:#9a6700">~{len(modified)} modified</span>')
    if deleted:
        summary_items.append(f'<span style="color:#cf222e">-{len(deleted)} deleted</span>')

    summary_text = " &nbsp;|&nbsp; ".join(summary_items)

    # Added pages
    if added:
        items = []
        for f, info in added.items():
            url = filename_to_url(f)
            preview = html.escape(info.get("content_preview", "")[:300])
            items.append(f'''
            <div style="margin:12px 0;padding:12px;border-left:4px solid #1a7f37;background:#f6fef9">
                <strong>NEW</strong> &mdash; <a href="{url}">{url}</a>
                <p style="color:#555;font-size:13px;margin:6px 0 0 0">{preview}...</p>
            </div>''')
        sections.append(f'<h2 style="color:#1a7f37">Added Pages ({len(added)})</h2>{"".join(items)}')

    # Modified pages
    if modified:
        items = []
        for f, info in modified.items():
            url = filename_to_url(f)
            diff_html = diff_to_html_table(info["diff"])
            items.append(f'''
            <div style="margin:12px 0;padding:12px;border-left:4px solid #9a6700;background:#fff8e1">
                <strong>MODIFIED</strong> &mdash; <a href="{url}">{url}</a>
                {diff_html}
            </div>''')
        sections.append(f'<h2 style="color:#9a6700">Modified Pages ({len(modified)})</h2>{"".join(items)}')

    # Deleted pages
    if deleted:
        items = []
        for f in deleted:
            url = filename_to_url(f)
            items.append(f'''
            <div style="margin:12px 0;padding:12px;border-left:4px solid #cf222e;background:#fff5f5">
                <strong>DELETED</strong> &mdash; <a href="{url}">{url}</a>
            </div>''')
        sections.append(f'<h2 style="color:#cf222e">Deleted Pages ({len(deleted)})</h2>{"".join(items)}')

    body_sections = "\n".join(sections)

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:800px;margin:0 auto;padding:20px;color:#24292f">

<div style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;padding:24px;border-radius:8px;margin-bottom:24px">
    <h1 style="margin:0;font-size:22px">Claude Code Docs Change Report</h1>
    <p style="margin:8px 0 0 0;opacity:0.9;font-size:14px">{now}</p>
</div>

<div style="background:#f6f8fa;padding:16px;border-radius:6px;margin-bottom:24px;text-align:center;font-size:16px">
    {summary_text}
</div>

<div style="background:#fff;border:1px solid #ddd;border-radius:6px;padding:16px;margin-bottom:24px;font-size:13px;color:#555">
    <strong style="color:#24292f">Color Guide</strong>
    <table style="width:100%;margin-top:8px;border-collapse:collapse">
        <tr>
            <td style="padding:4px 8px"><span style="display:inline-block;width:12px;height:12px;background:#e6ffec;border:1px solid #1a7f37;border-radius:2px;vertical-align:middle"></span> <code style="color:#1a7f37">+ Added</code></td>
            <td style="padding:4px 8px"><span style="display:inline-block;width:12px;height:12px;background:#ffebe9;border:1px solid #cf222e;border-radius:2px;vertical-align:middle"></span> <code style="color:#cf222e">- Removed</code></td>
            <td style="padding:4px 8px"><span style="display:inline-block;width:12px;height:12px;background:#e8e8ff;border:1px solid #336;border-radius:2px;vertical-align:middle"></span> <code style="color:#336">@@ Location</code></td>
            <td style="padding:4px 8px"><span style="display:inline-block;width:12px;height:12px;background:#f0f0f0;border:1px solid #999;border-radius:2px;vertical-align:middle"></span> <code style="color:#666">File info</code></td>
        </tr>
    </table>
</div>

{body_sections}

<hr style="border:none;border-top:1px solid #ddd;margin:32px 0 16px 0">
<p style="color:#888;font-size:12px;text-align:center">
    Generated by <strong>detect_ccd_change</strong> &mdash; Claude Code Documentation Change Detector
</p>

</body>
</html>"""


def generate_no_changes_email() -> str:
    """Generate email for when no changes are detected."""
    now = datetime.now(KST).strftime("%Y-%m-%d %H:%M KST")

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:800px;margin:0 auto;padding:20px;color:#24292f">

<div style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;padding:24px;border-radius:8px;margin-bottom:24px">
    <h1 style="margin:0;font-size:22px">Claude Code Docs Change Report</h1>
    <p style="margin:8px 0 0 0;opacity:0.9;font-size:14px">{now}</p>
</div>

<div style="background:#f6f8fa;padding:24px;border-radius:6px;text-align:center">
    <p style="font-size:18px;color:#1a7f37;margin:0">No changes detected</p>
    <p style="color:#666;margin:8px 0 0 0">All 75 documentation pages are unchanged since the last check.</p>
</div>

<hr style="border:none;border-top:1px solid #ddd;margin:32px 0 16px 0">
<p style="color:#888;font-size:12px;text-align:center">
    Generated by <strong>detect_ccd_change</strong> &mdash; Claude Code Documentation Change Detector
</p>

</body>
</html>"""

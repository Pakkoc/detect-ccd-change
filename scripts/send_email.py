"""Send HTML email report via Gmail SMTP."""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone, timedelta
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

KST = timezone(timedelta(hours=9))


def send_report(html_body: str, has_changes: bool = True) -> bool:
    """Send HTML email via Gmail SMTP.

    Reads credentials from environment variables:
    - EMAIL_TO: recipient address
    - GMAIL_USER: sender Gmail address (defaults to EMAIL_TO)
    - GMAIL_APP_PASSWORD: 16-char app password
    """
    to_addr = os.environ.get("EMAIL_TO", "")
    from_addr = os.environ.get("GMAIL_USER", to_addr)
    app_password = os.environ.get("GMAIL_APP_PASSWORD", "")

    if not all([to_addr, from_addr, app_password]):
        print("[ERROR] Missing email config. Set EMAIL_TO, GMAIL_APP_PASSWORD in .env or environment.")
        return False

    today = datetime.now(KST).strftime("%Y-%m-%d")
    status = "변경 감지" if has_changes else "변경 없음"
    subject = f"[Claude Code Docs {status}] {today}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(from_addr, app_password)
            server.sendmail(from_addr, [to_addr], msg.as_string())
        print(f"[OK] Email sent to {to_addr}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")
        return False

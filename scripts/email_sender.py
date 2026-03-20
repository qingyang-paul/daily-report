"""Send a generated HTML email report via Resend.

Reads a local HTML file and sends it to specified recipients using the Resend API.
Defaults to sending the latest generated report from the workspace.

Usage:
    python scripts/email_sender.py [--file <path_to_html>] [--subject <email_subject>]

Examples:
    python scripts/email_sender.py
    python scripts/email_sender.py --subject "Custom Subject"
"""
import os
import argparse
import logging
import sys
import resend
from pathlib import Path

# Ensure scripts directory is in sys.path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

from core import config

# Load environment logic at the top
config.load_config()

# Detailed logging format for debugging
logging.basicConfig(
    level=logging.INFO, 
    format='[%(filename)s:%(lineno)d] %(message)s'
)
logger = logging.getLogger(__name__)

def send_email_from_file(file_path: str, subject_suffix: str = "", attachment_path: str = None):
    """Send an email using HTML content from a file, optionally with an attachment."""
    api_key = os.getenv("RESEND_API_KEY")
    email_domain = os.getenv("EMAIL_DOMAIN")
    bot_display_name = os.getenv("BOT_DISPLAY_NAME")
    email_prefix = os.getenv("EMAIL_PREFIX")
    recipients_str = os.getenv("RECEIVER_EMAILS")
    
    recipients = [e.strip() for e in recipients_str.split(",")] if recipients_str else []

    if not api_key or not email_domain or not recipients:
        logger.error("Missing email configuration (API Key, Domain, or Recipients).")
        return False

    path = Path(file_path)
    if not path.exists():
        logger.error(f"HTML file not found: {file_path}")
        return False
        
    html_content = path.read_text(encoding='utf-8')
    resend.api_key = api_key
    from_email = f"{bot_display_name} <{email_prefix}@{email_domain}>"
    
    subject = f"Daily Insights {subject_suffix}".strip()
    
    logger.info(f"Sending email: '{subject}' to {recipients} using {file_path}")
    
    try:
        params = {
            "from": from_email,
            "to": recipients,
            "subject": subject,
            "html": html_content,
        }

        # Add attachment if provided
        if attachment_path:
            attach_p = Path(attachment_path)
            if attach_p.exists():
                logger.info(f"Attaching file: {attachment_path}")
                params["attachments"] = [
                    {
                        "filename": attach_p.name,
                        "content": list(attach_p.read_bytes()),
                    }
                ]
            else:
                logger.warning(f"Attachment not found: {attachment_path}, sending without it.")

        resp = resend.Emails.send(params)
        logger.info(f"Email sent successfully! ID: {resp['id']}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email via Resend: {e}", exc_info=True)
        return False

def main():
    parser = argparse.ArgumentParser(description="Send Daily Insights Email")
    parser.add_argument("--file", help="Path to the HTML file to send (defaults to latest.html)")
    parser.add_argument("--subject", default="Daily Report 🚀", help="Email subject suffix")
    parser.add_argument("--attach", help="Path to the file to attach (defaults to latest.pdf if it exists)")
    args = parser.parse_args()
    
    # Use config-defined paths
    file_to_send = args.file if args.file else str(config.EMAIL_HTML_DIR / "latest.html")
    
    # Default attachment logic
    attachment = args.attach
    if not attachment:
        latest_pdf = config.EMAIL_PDF_DIR / "latest.pdf"
        if latest_pdf.exists():
            attachment = str(latest_pdf.absolute())
    
    if send_email_from_file(file_to_send, args.subject, attachment):
        logger.info("Email process completed.")
    else:
        logger.error("Email process failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()

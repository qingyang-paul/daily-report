"""Convert HTML email reports to PDF format using WeasyPrint.

This tool reads the latest generated HTML report from EMAIL_HTML_DIR
and converts it to a PDF in EMAIL_PDF_DIR.

Usage:
    python scripts/pdf_generator.py [--html <path_to_html>]

Examples:
    python scripts/pdf_generator.py
    python scripts/pdf_generator.py --html email_outputs/latest.html
"""
import os
import sys
import logging
import argparse
from pathlib import Path
from weasyprint import HTML

# Ensure scripts directory is in sys.path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

from core import config

# Load configurations
config.load_config()

# Detailed logging format
logging.basicConfig(
    level=logging.INFO, 
    format='[%(filename)s:%(lineno)d] %(message)s'
)
logger = logging.getLogger(__name__)

def generate_pdf(html_path=None):
    """Convert HTML to PDF."""
    if not html_path:
        # Default to the latest.html in EMAIL_HTML_DIR
        html_path = config.EMAIL_HTML_DIR / "latest.html"
    else:
        html_path = Path(html_path)

    if not html_path.exists():
        logger.error(f"HTML file not found: {html_path}")
        return None

    # Define output PDF path
    pdf_filename = html_path.stem + ".pdf"
    output_path = config.EMAIL_PDF_DIR / pdf_filename
    
    logger.info(f"Converting {html_path} to PDF...")
    try:
        HTML(string=html_path.read_text(encoding='utf-8')).write_pdf(target=output_path)
        
        # Also create a 'latest.pdf' for easy reference
        latest_pdf = config.EMAIL_PDF_DIR / "latest.pdf"
        HTML(string=html_path.read_text(encoding='utf-8')).write_pdf(target=latest_pdf)
        
        logger.info(f"Successfully generated PDF at: {output_path}")
        return str(output_path.absolute())
    except Exception as e:
        logger.error(f"Failed to generate PDF: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Convert HTML email report to PDF.")
    parser.add_argument("--html", help="Path to the HTML file to convert.")
    args = parser.parse_args()

    pdf_path = generate_pdf(args.html)
    if pdf_path:
        print(f"PDF generated: {pdf_path}")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()

"""Fetch and parse Hugging Face Daily Papers.

Fetches the daily papers list from Hugging Face, extracts metadata
(title, summary, authors, links), and saves the results to a structured JSON file.

Usage:
    python scripts/huggingface_daily_papers.py [--timeframe {daily,weekly,monthly}]

Examples:
    python scripts/huggingface_daily_papers.py --timeframe daily
    python scripts/huggingface_daily_papers.py --timeframe weekly
"""
import argparse
import logging
import sys
from pathlib import Path

# Ensure scripts directory is in sys.path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

from core import config

# Load environment logic at the top
config.load_config()

from collectors.huggingface import huggingface_fetch_papers, huggingface_parse_data

# Detailed logging format for debugging
logging.basicConfig(
    level=logging.INFO, 
    format='[%(filename)s:%(lineno)d] %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Hugging Face Daily Papers Section Script")
    parser.add_argument(
        "--timeframe", 
        choices=["daily", "weekly", "monthly"], 
        default="daily",
        help="Timeframe to fetch papers for (default: daily)"
    )
    args = parser.parse_args()

    try:
        logger.info(f"Starting Hugging Face Daily Papers pipeline for: {args.timeframe}")
        
        # 1. Fetch data
        raw_file_path = huggingface_fetch_papers(timeframe=args.timeframe)
        
        # 2. Parse data
        papers = huggingface_parse_data(raw_file_path)
        
        logger.info(f"Hugging Face Daily Papers pipeline completed successfully. Parsed {len(papers)} papers.")
        
    except Exception as e:
        logger.error(f"Hugging Face Daily Papers pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

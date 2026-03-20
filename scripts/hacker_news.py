"""Fetch and parse Hacker News top stories.

Fetches the top stories from Hacker News using the Algolia API, parses details
(title, URL, points, author), and saves the results to both JSON and Markdown formats.

Usage:
    python scripts/hacker_news.py [--timeframe {daily,weekly,monthly}]

Examples:
    python scripts/hacker_news.py --timeframe daily
    python scripts/hacker_news.py --timeframe weekly
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

from collectors.hacker_news import hacker_news_fetch_data, hacker_news_parse_data, hacker_news_generate_markdown

# Detailed logging format for debugging
logging.basicConfig(
    level=logging.INFO, 
    format='[%(filename)s:%(lineno)d] %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Hacker News Section Script")
    parser.add_argument(
        "--timeframe", 
        choices=["daily", "weekly", "monthly"], 
        default="daily",
        help="Timeframe to fetch stories for (default: daily)"
    )
    args = parser.parse_args()

    try:
        logger.info(f"Starting Hacker News pipeline for timeframe: {args.timeframe}")
        
        # 1. Fetch data
        raw_file_path = hacker_news_fetch_data(timeframe=args.timeframe)
        
        # 2. Parse data
        parsed_data = hacker_news_parse_data(raw_file_path)
        
        # 3. Generate Markdown
        markdown_path = hacker_news_generate_markdown(parsed_data, timeframe=args.timeframe)
        
        logger.info(f"Hacker News pipeline completed successfully. Results in: {markdown_path}")
        
    except Exception as e:
        logger.error(f"Hacker News pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

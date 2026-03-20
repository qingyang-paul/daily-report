"""Fetch and parse trending products from Product Hunt.

Uses the Product Hunt GraphQL API to fetch daily, weekly, or monthly trending products,
including taglines, vote counts, and top comments.

Usage:
    python scripts/product_hunt.py [--timeframe {daily,weekly,monthly}]

Examples:
    python scripts/product_hunt.py --timeframe daily
    python scripts/product_hunt.py --timeframe weekly
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

from collectors.product_hunt import product_hunt_fetch_data, product_hunt_parse_data, product_hunt_generate_markdown

# Detailed logging format for debugging
logging.basicConfig(
    level=logging.INFO, 
    format='[%(filename)s:%(lineno)d] %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Product Hunt Section Script")
    parser.add_argument(
        "--timeframe", 
        choices=["daily", "weekly", "monthly"], 
        default="daily",
        help="Timeframe for trending products (default: daily)"
    )
    args = parser.parse_args()

    try:
        logger.info(f"Starting Product Hunt pipeline for: {args.timeframe}")
        
        # 1. Fetch data
        raw_file_path = product_hunt_fetch_data(timeframe=args.timeframe)
        
        # 2. Parse data
        products = product_hunt_parse_data(raw_file_path)
        
        # 3. Generate Markdown
        markdown_path = product_hunt_generate_markdown(products, timeframe=args.timeframe)
        
        logger.info(f"Product Hunt pipeline completed successfully. Results in: {markdown_path}")
        
    except Exception as e:
        logger.error(f"Product Hunt pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

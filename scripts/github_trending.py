"""Fetch and parse GitHub Trending repositories.

Gathers trending repositories from GitHub's trending page, parses the HTML,
and saves the results to the centralized parsed results directory.

Usage:
    python scripts/github_trending.py [--since {daily,weekly,monthly}]

Examples:
    python scripts/github_trending.py --since daily
    python scripts/github_trending.py --since weekly
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

from collectors.github import github_trending_fetch_html, github_trending_parse_html, github_trending_verify_results

# Detailed logging format for debugging
logging.basicConfig(
    level=logging.INFO, 
    format='[%(filename)s:%(lineno)d] %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="GitHub Trending Section Script")
    parser.add_argument(
        "--since", 
        choices=["daily", "weekly", "monthly"], 
        default="daily",
        help="Timeframe for trending repositories (default: daily)"
    )
    args = parser.parse_args()

    try:
        logger.info(f"Starting GitHub Trending pipeline for: {args.since}")
        
        # 1. Fetch HTML
        html_path = github_trending_fetch_html(since=args.since)
        
        # 2. Parse HTML
        projects = github_trending_parse_html(html_path)
        
        # 3. Verify (Optional but good for logging)
        # Assuming we save JSON in parsed_results/github/trending_{since}.json
        # The collector does this internally.
        
        logger.info(f"GitHub Trending pipeline completed successfully. Parsed {len(projects)} projects.")
        
    except Exception as e:
        logger.error(f"GitHub Trending pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

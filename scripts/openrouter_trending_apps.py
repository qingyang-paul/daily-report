"""Fetch and parse trending apps from OpenRouter.

Scrapes the OpenRouter apps page to discover trending applications using AI models,
and saves the results to a structured JSON and Markdown report.

Usage:
    python scripts/openrouter_trending_apps.py

Examples:
    python scripts/openrouter_trending_apps.py
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

from collectors.openrouter import openrouter_apps_fetch_data, openrouter_apps_parse_data, openrouter_apps_generate_markdown

# Detailed logging format for debugging
logging.basicConfig(
    level=logging.INFO, 
    format='[%(filename)s:%(lineno)d] %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="OpenRouter: Trending Apps Section Script")
    args = parser.parse_args()

    try:
        logger.info("Starting OpenRouter Trending Apps pipeline")
        
        # 1. Fetch data (HTML)
        raw_file_path = openrouter_apps_fetch_data()
        
        # 2. Parse data
        apps_data = openrouter_apps_parse_data(raw_file_path)
        
        # 3. Generate Markdown
        markdown_path = openrouter_apps_generate_markdown(apps_data)
        
        logger.info(f"OpenRouter Trending Apps pipeline completed successfully. Results in: {markdown_path}")
        
    except Exception as e:
        logger.error(f"OpenRouter Trending Apps pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

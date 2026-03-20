"""Fetch and parse latest LLMs from OpenRouter.

Fetches the list of newest models from the OpenRouter API, filters for LLMs,
and generates a structured list and a Markdown summary.

Usage:
    python scripts/openrouter_llms.py

Examples:
    python scripts/openrouter_llms.py
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

from collectors.openrouter import openrouter_fetch_data, openrouter_parse_data, openrouter_generate_markdown

# Detailed logging format for debugging
logging.basicConfig(
    level=logging.INFO, 
    format='[%(filename)s:%(lineno)d] %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="OpenRouter: Latest LLMs Section Script")
    args = parser.parse_args() # For now no specific args needed except maybe force fetch

    try:
        logger.info("Starting OpenRouter Latest LLMs pipeline")
        
        # 1. Fetch data
        raw_file_path = openrouter_fetch_data()
        
        # 2. Parse data
        models = openrouter_parse_data(raw_file_path)
        
        # 3. Generate Markdown
        markdown_path = openrouter_generate_markdown(models)
        
        logger.info(f"OpenRouter Latest LLMs pipeline completed successfully. Results in: {markdown_path}")
        
    except Exception as e:
        logger.error(f"OpenRouter Latest LLMs pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

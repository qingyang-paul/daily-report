"""Run system configuration and API health checks.

Verifies that all required environment variables are set and tests connectivity
to all data source APIs (GitHub, Hacker News, Hugging Face, Product Hunt, OpenRouter).

Usage:
    python scripts/health_check.py

Examples:
    python scripts/health_check.py
"""
import os
import sys
import logging
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

def main():
    logger.info("=== System Configuration Check ===")
    
    # Check key environment variables
    env_vars = {
        "Product_Hunt_Developer_Token": "Product Hunt API",
        "API_DATA_DIR": "Raw Data storage",
        "PARSED_DATA_DIR": "Parsed Data storage"
    }
    
    for var, desc in env_vars.items():
        val = os.getenv(var)
        if not val:
            logger.warning(f"WARNING: {var} ({desc}) is not set.")
        else:
            # Mask sensitive tokens
            display_val = f"{val[:5]}...{val[-5:]}" if len(val) > 10 and "Token" in var else val
            logger.info(f"{var}: {display_val}")


    logger.info("\n=== Running Health Checks ===")

    # Import collectors
    try:
        import collectors.arxiv
        import collectors.github
        import collectors.hacker_news
        import collectors.huggingface
        import collectors.product_hunt
        import collectors.openrouter
        
        # Map them for display
        arxiv_health_check = collectors.arxiv.arxiv_health_check
        github_trending_health_check = collectors.github.github_trending_health_check
        hacker_news_health_check = collectors.hacker_news.hacker_news_health_check
        huggingface_health_check = collectors.huggingface.huggingface_health_check
        product_hunt_health_check = collectors.product_hunt.product_hunt_health_check
        openrouter_health_check = collectors.openrouter.openrouter_health_check
    except ImportError as e:
        logger.error(f"Failed to import collectors: {e}")
        sys.exit(1)

    results = {
        "arXiv": arxiv_health_check(),
        "GitHub Trending": github_trending_health_check(),
        "Hacker News": hacker_news_health_check(),
        "Huggingface": huggingface_health_check(),
        "Product Hunt": product_hunt_health_check(),
        "OpenRouter": openrouter_health_check()
    }
    
    logger.info("\n=== Health Check Results ===")
    all_passed = True
    for service, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        logger.info(f"{service:20}: {status}")
        if not passed:
            all_passed = False
            
    if all_passed:
        logger.info("\nAll systems operational.")
    else:
        logger.error("\nSome systems failed. Please check your configurations and network connectivity.")
        sys.exit(1)

if __name__ == "__main__":
    main()

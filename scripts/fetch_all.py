"""Run the Daily Info data fetch and parse pipeline.

Executes a sequence of data-centric steps:
1. Performs a health check on all APIs.
2. Runs all data collection and parsing scripts (GitHub, HN, HF, OR, PH).
Results are saved to the centralized parsed results directory.

Usage:
    python scripts/fetch_all.py

Examples:
    python scripts/fetch_all.py
"""
import os
import sys
import logging
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Detailed logging format for debugging
logging.basicConfig(
    level=logging.INFO, 
    format='[%(filename)s:%(lineno)d] %(message)s'
)
logger = logging.getLogger(__name__)

def run_script(script_path, args=None):
    """Run a python script relative to the project root."""
    cmd = [sys.executable, script_path]
    if args:
        cmd.extend(args)
    
    logger.info(f"Running: {' '.join(cmd)}")
    try:
        # Run from the project root
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info(f"Finished {script_path}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running {script_path}: {e.stderr}")
        return False

def main():
    # Identify project root
    project_root = Path(__file__).parent.parent.absolute()
    
    # Load environment variables from .env.local in project root
    env_path = project_root / ".env.local"
    load_dotenv(env_path)
    
    # Ensure we are in the project root directory for execution
    os.chdir(project_root)
    logger.info(f"Execution directory set to: {project_root}")

    logger.info("=== Starting Daily Info Data Recruitment Pipeline ===")
    
    # 1. Health Check
    if not run_script("scripts/health_check.py"):
        logger.error("Health check failed. Aborting pipeline.")
        sys.exit(1)

    # 2. Run Section Pipelines (Fetch + Parse)
    sections = [
        ("scripts/github_trending.py", ["--since", "daily"]),
        ("scripts/hacker_news.py", ["--timeframe", "daily"]),
        ("scripts/huggingface_daily_papers.py", ["--timeframe", "daily"]),
        ("scripts/openrouter_llms.py", []),
        ("scripts/openrouter_trending_apps.py", []),
        ("scripts/product_hunt.py", ["--timeframe", "daily"]),
    ]
    
    for script, args in sections:
        run_script(script, args)

    logger.info("=== Data Recruitment Pipeline Completed ===")
    logger.info("Next Step: Enrich data fields or generate report using email_generator.py")

if __name__ == "__main__":
    main()

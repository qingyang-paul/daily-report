"""Generate a Daily Insights email report in HTML format.

Gathers parsed results from all data collectors, applies them to a Jinja2 template,
and saves the final HTML report to the configured Workspace EMAIL_HTML_DIR.

Usage:
    python scripts/email_generator.py

Examples:
    python scripts/email_generator.py
"""
import os
import json
import logging
from pathlib import Path
from datetime import datetime
import sys

# Ensure scripts directory is in sys.path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

from core import config

from jinja2 import Environment, FileSystemLoader

# Detailed logging format for debugging
logging.basicConfig(
    level=logging.INFO, 
    format='[%(filename)s:%(lineno)d] %(message)s'
)
logger = logging.getLogger(__name__)

# Constants and Path Setup
SCRIPTS_DIR = Path(__file__).parent.absolute()
WORKSPACE_ROOT = SCRIPTS_DIR.parent
TEMPLATE_DIR = WORKSPACE_ROOT / "templates"
OUTPUT_DIR = config.EMAIL_HTML_DIR

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Header Configuration
# (No header image needed, using CSS gradient)

def get_latest_file(directory, pattern):
    """Find the latest file in a directory matching a pattern."""
    if not os.path.exists(directory):
        return None
    files = [f for f in os.listdir(directory) if pattern in f and f.endswith(".json")]
    if not files:
        return None
    files.sort(reverse=True)
    return os.path.join(directory, files[0])

def load_json(filepath, default_value=None):
    if not filepath or not os.path.exists(filepath):
        logger.debug(f"File not found: {filepath}")
        return default_value if default_value is not None else []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading {filepath}: {e}")
        return default_value if default_value is not None else []

def format_k(value):
    try:
        val = float(value)
        if val >= 1000:
            return f"{val/1000:.1f}k"
        return str(int(val))
    except (ValueError, TypeError):
        return value

def format_timestamp(value):
    if not value: return ""
    if isinstance(value, datetime): return value.strftime("%Y-%m-%d")
    try:
        val_str = str(value).replace('Z', '+00:00')
        return datetime.fromisoformat(val_str).strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return value

def prepare_email_data():
    """Gather parsed data for the email template."""
    logger.info("Gathering data for Daily Insights email generation...")
    
    github_data = load_json(config.PARSED_DATA_DIR / "github" / "trending_daily.json")
    
    hf_latest = get_latest_file(config.PARSED_DATA_DIR / "huggingface", "huggingface_daily")
    hf_papers = load_json(hf_latest)
    
    or_models_latest = get_latest_file(config.PARSED_DATA_DIR / "openrouter", "openrouter_models")
    or_models = load_json(or_models_latest)
    
    or_apps_latest = get_latest_file(config.PARSED_DATA_DIR / "openrouter", "openrouter_apps")
    or_apps = load_json(or_apps_latest)
    
    ph_latest = get_latest_file(config.PARSED_DATA_DIR / "product_hunt", "product_hunt_daily")
    ph_data = load_json(ph_latest)
    
    # Updated path for Hacker News
    hn_data = load_json(config.PARSED_DATA_DIR / "hacker_news" / "hn_daily_parsed.json")

    # Load AI Overview
    overview_path = config.PARSED_DATA_DIR / "overviews" / "daily_overview.json"
    overview_data = load_json(overview_path, default_value={})

    # Select latest 5 OpenRouter LLMs
    or_llms = sorted(or_models, key=lambda x: str(x.get('created', '')), reverse=True)[:5] if isinstance(or_models, list) else []

    # Mapping limits from config
    github_limit = config.SECTION_LIMITS.get("github", 10)
    hf_limit = config.SECTION_LIMITS.get("huggingface", 10)
    or_llm_limit = config.SECTION_LIMITS.get("openrouter_llms", 10)
    or_app_limit = config.SECTION_LIMITS.get("openrouter_apps", 10)
    ph_limit = config.SECTION_LIMITS.get("product_hunt", 10)
    hn_limit = config.SECTION_LIMITS.get("hacker_news", 10)

    return {
        "date": datetime.now().strftime("%B %d, %Y"),
        "report_overview": overview_data.get("report_overview"),
        "github_trending_overview": overview_data.get("github_trending_overview"),
        "huggingface_daily_papers_overview": overview_data.get("huggingface_daily_papers_overview"),
        "openrouter_latest_llms_overview": overview_data.get("openrouter_latest_llms_overview"),
        "openrouter_trending_apps_overview": overview_data.get("openrouter_trending_apps_overview"),
        "producthunt_apps_overview": overview_data.get("producthunt_apps_overview"),
        "hackernews_post_overview": overview_data.get("hackernews_post_overview"),
        "github_trending": github_data[:github_limit] if isinstance(github_data, list) else [],
        "huggingface": hf_papers[:hf_limit] if isinstance(hf_papers, list) else [],
        "arxiv_papers": [],
        "openrouter_llms": or_llms[:or_llm_limit],
        "openrouter_apps": or_apps.get('trending', [])[:or_app_limit] if isinstance(or_apps, dict) else [],
        "product_hunt": ph_data[:ph_limit] if isinstance(ph_data, list) else [],
        "hacker_news": hn_data[:hn_limit] if isinstance(hn_data, list) else []
    }

def generate_email_html():
    """Main entry point to generate and save email HTML."""
    data = prepare_email_data()
    
    logger.info("Rendering email template...")
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    env.filters['format_k'] = format_k
    env.filters['format_timestamp'] = format_timestamp
    
    try:
        template = env.get_template("email_template.html.j2")
        html_content = template.render(**data)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = OUTPUT_DIR / f"daily_report_{timestamp}.html"
        output_file.write_text(html_content, encoding='utf-8')
        
        # Also create a 'latest.html' for easy access
        latest_file = OUTPUT_DIR / "latest.html"
        latest_file.write_text(html_content, encoding='utf-8')
        
        logger.info(f"Email HTML generated and saved to {output_file}")
        return str(output_file.absolute())
    except Exception as e:
        logger.error(f"Failed to generate email HTML: {e}", exc_info=True)
        return None

if __name__ == "__main__":
    generate_email_html()

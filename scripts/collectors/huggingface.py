"""Hugging Face Data Collector.

Fetches daily papers and model metadata from the Hugging Face API.
"""
import os
import json
import logging
from datetime import datetime, timedelta
from huggingface_hub import list_daily_papers
from pathlib import Path
import sys

# Ensure scripts directory is in sys.path
scripts_dir = Path(__file__).resolve().parent.parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from core import config

from core.schema import HuggingFacePaperSchema

# Load environment logic at the top
config.load_config()

# Detailed logging format for debugging
logging.basicConfig(
    level=logging.INFO, 
    format='[%(filename)s:%(lineno)d] %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
HUGGINGFACE_PERIODS = ["daily", "weekly", "monthly"]

# Retrieve base directories from core.config
BASE_API_DIR = config.API_DATA_DIR
BASE_PARSED_DIR = config.PARSED_DATA_DIR

# Define specific directories for this platform
HF_API_DATA_DIR = Path(BASE_API_DIR) / "huggingface" / "list_daily_papers"
HF_PARSED_DATA_DIR = Path(BASE_PARSED_DIR) / "huggingface"

# Ensure directories exist
HF_API_DATA_DIR.mkdir(parents=True, exist_ok=True)
HF_PARSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

logger.info(f"Loaded Huggingface configurations: API_DIR={HF_API_DATA_DIR}, PARSED_DIR={HF_PARSED_DATA_DIR}")

def huggingface_health_check() -> bool:
    """
    Perform a health check on the Huggingface Hub papers API.
    
    Platform: Huggingface
    Method: Daily Papers API Health Check
    Args:
        None
    Returns:
        bool: True if connection is successful, False otherwise.
    """
    try:
        logger.info("Performing Huggingface health check...")
        now = datetime.utcnow()
        date_str = now.strftime("%Y-%m-%d")
        papers = list(list_daily_papers(date=date_str))
        logger.info("Huggingface health check successful.")
        return True
    except Exception as e:
        logger.error(f"Huggingface health check failed: {e}")
        return False

def huggingface_fetch_papers(timeframe: str) -> str:
    """
    Fetch listed daily papers from Huggingface over the specified timeframe.
    
    Platform: Huggingface
    Method: API Fetch Papers
    Args:
        timeframe (str): The time duration ('daily', 'weekly', 'monthly').
    Returns:
        str: Absolute path to the generated JSON raw data file.
    API Return Data: JSON array containing paper attributes (title, abstract, link, etc.).
    """
    if timeframe not in HUGGINGFACE_PERIODS:
        raise ValueError(f"Invalid timeframe: {timeframe}. Must be one of {HUGGINGFACE_PERIODS}")

    now = datetime.utcnow()
    if timeframe == "daily":
        days = 1
    elif timeframe == "weekly":
        days = 7
    elif timeframe == "monthly":
        days = 30
        
    logger.info(f"Fetching {timeframe} Huggingface papers ({days} days)")
    
    raw_results = []
    for i in range(days):
        date_str = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        try:
            papers = list(list_daily_papers(date=date_str))
            for p in papers:
                raw_dict = {}
                for k, v in vars(p).items():
                    if not k.startswith('_'):
                        # Handle potential non-serializable like datetime or PaperAuthor
                        if isinstance(v, datetime):
                            raw_dict[k] = v.isoformat()
                        elif hasattr(v, '__dict__'):
                            raw_dict[k] = vars(v)
                        elif isinstance(v, list) and len(v) > 0 and hasattr(v[0], '__dict__'):
                            raw_dict[k] = [vars(item) for item in v]
                        else:
                            raw_dict[k] = v
                raw_dict["date"] = date_str
                raw_results.append(raw_dict)
        except Exception as e:
            logger.warning(f"Error fetching Huggingface papers for {date_str}: {e}")
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"huggingface_{timeframe}_{timestamp}.json"
    file_path = HF_API_DATA_DIR / filename
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump({"data": raw_results}, f, indent=2, ensure_ascii=False, default=str)
        
    logger.info(f"Saved Huggingface raw data to {file_path}")
    return str(file_path.absolute())

def huggingface_parse_data(file_path: str) -> list:
    """
    Parse raw Huggingface daily papers data from file.
    
    Platform: Huggingface
    Method: JSON parsing
    Args:
        file_path (str): Path to the locally saved raw JSON data file.
    Returns:
        list: A list of HuggingFacePaperSchema objects.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    results = []
    for item in data.get("data", []):
        paper = item.get("paper", item) # fallback if structure is different
        
        # safely extract common fields
        paper_id = paper.get("id", "")
        title = paper.get("title", "Unknown Title")
        upvotes = int(item.get("upvotes", 0)) if isinstance(item.get("upvotes"), (int, str)) else 0
        comments_cnt = int(item.get("num_comments", 0)) if isinstance(item.get("num_comments"), (int, str)) else 0
        # Handle organization (newly added)
        organization_obj = item.get("organization")
        organization_name = None
        organization_avatar = None
        
        if isinstance(organization_obj, dict):
            organization_name = organization_obj.get("name")
            organization_avatar = organization_obj.get("avatar")
        elif isinstance(organization_obj, str) and organization_obj.startswith("{"):
            try:
                import ast
                org_dict = ast.literal_eval(organization_obj)
                organization_name = org_dict.get("name")
                organization_avatar = org_dict.get("avatar")
            except:
                organization_name = organization_obj
        elif isinstance(organization_obj, str):
            organization_name = organization_obj

        authors_raw = paper.get("authors", [])
        authors = []
        
        if isinstance(authors_raw, list):
            for a in authors_raw:
                if isinstance(a, dict) and 'name' in a:
                    authors.append(a['name'])
                elif isinstance(a, str):
                    authors.append(a)
                    
        summary = paper.get("summary", paper.get("abstract", ""))
        
        pub_date_raw = paper.get("publishedAt", paper.get("published", paper.get("date", "")))
        try:
            if pub_date_raw:
                # Handle common ISO formats
                clean_date = pub_date_raw.replace('Z', '+00:00')
                published_at = datetime.fromisoformat(clean_date)
            else:
                published_at = datetime.utcnow()
        except:
            published_at = datetime.utcnow()
            
        github_url = paper.get("github_repo")
        github_stars = paper.get("github_stars")
        
        if github_url and not github_url.startswith("http"):
            github_url = f"https://github.com/{github_url}"
            
        if not github_url:
            import re
            # Search for github link in summary/abstract
            hf_gh_match = re.search(r'https?://github\.com/[\w\-\.]+/[\w\-\.]+', summary)
            if hf_gh_match:
                github_url = hf_gh_match.group(0).rstrip('.')

        try:
            model = HuggingFacePaperSchema(
                id=paper_id,
                title=title,
                upvotes=upvotes,
                comments=comments_cnt,
                authors=authors,
                organization_name=organization_name,
                organization_avatar=organization_avatar,
                summary=summary,
                published_at=published_at,
                github_url=github_url,
                github_stars=github_stars
            )
            results.append(model)
        except Exception as e:
            logger.error(f"Failed to validate HuggingFacePaperSchema for {paper_id}: {e}")
            
    output_path = HF_PARSED_DATA_DIR / f"{path.stem}_parsed.json"
    output_path.write_text(json.dumps([p.model_dump() for p in results], indent=2, ensure_ascii=False, default=str), encoding='utf-8')
    logger.info(f"Saved parsed Huggingface JSON to {output_path}")
    
    return results

if __name__ == "__main__":
    print("This module should not be run directly.")

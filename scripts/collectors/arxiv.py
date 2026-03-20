"""arXiv Data Collector.

Fetches and parses scientific papers from arXiv based on search queries.
"""
import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Ensure scripts directory is in sys.path
scripts_dir = Path(__file__).resolve().parent.parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from core import config

from core.schema import ArxivPaperSchema
import arxiv

# Load environment logic at the top
config.load_config()

# Detailed logging format for debugging
logging.basicConfig(
    level=logging.INFO, 
    format='[%(filename)s:%(lineno)d] %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
ARXIV_PERIODS = ["daily", "weekly", "monthly"]
ARXIV_CATEGORIES = ["cs.AI", "cs.CL", "cs.LG"]

# Retrieve base directories from core.config
BASE_API_DIR = config.API_DATA_DIR
BASE_PARSED_DIR = config.PARSED_DATA_DIR

# Define specific directories for this platform
ARXIV_API_DATA_DIR = Path(BASE_API_DIR) / "arxiv" / "search"
ARXIV_PARSED_DATA_DIR = Path(BASE_PARSED_DIR) / "arxiv"

# Ensure directories exist
ARXIV_API_DATA_DIR.mkdir(parents=True, exist_ok=True)
ARXIV_PARSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

logger.info(f"Loaded Arxiv configurations: API_DIR={ARXIV_API_DATA_DIR}, PARSED_DIR={ARXIV_PARSED_DATA_DIR}")

def arxiv_health_check(proxies: dict = None) -> bool:
    """
    Check if the arXiv API is responsive.
    
    Platform: arXiv
    Method: Search API Health Check
    Args:
        proxies (dict, optional): Proxy configuration.
    Returns:
        bool: True if the arXiv API query is successful and returns results, False otherwise.
    Docs: https://export.arxiv.org/api/query
    """
    import os
    old_http = os.environ.get("HTTP_PROXY")
    old_https = os.environ.get("HTTPS_PROXY")
    
    try:
        if proxies:
            os.environ["HTTP_PROXY"] = proxies.get("http", "")
            os.environ["HTTPS_PROXY"] = proxies.get("https", "")
            
        logger.info(f"Performing arXiv health check...{' (using proxy)' if proxies else ''}")
        client = arxiv.Client()
        search = arxiv.Search(
            query="cat:cs.AI",
            max_results=1,
            sort_by=arxiv.SortCriterion.SubmittedDate
        )
        results = list(client.results(search))
        if len(results) >= 0:
            logger.info("arXiv health check successful.")
            return True
        return False
    except Exception as e:
        logger.error(f"arXiv health check failed: {e}")
        return False
    finally:
        if proxies:
            if old_http is not None: os.environ["HTTP_PROXY"] = old_http
            else: os.environ.pop("HTTP_PROXY", None)
            if old_https is not None: os.environ["HTTPS_PROXY"] = old_https
            else: os.environ.pop("HTTPS_PROXY", None)

def arxiv_fetch_papers(timeframe: str, proxies: dict = None) -> str:
    """
    Fetch papers from the arXiv API for a specified timeframe and save the raw JSON response.
    
    Platform: arXiv
    Method: Search API Fetch
    Args:
        timeframe (str): The time window to fetch papers for. Must be 'daily', 'weekly', or 'monthly'.
        proxies (dict, optional): Proxy configuration.
    Returns:
        str: The absolute path to the saved raw JSON file containing the API response.
    """
    if timeframe not in ARXIV_PERIODS:
        raise ValueError(f"Invalid timeframe: {timeframe}. Must be one of {ARXIV_PERIODS}")

    now = datetime.utcnow()
    if timeframe == "daily":
        start_date = now - timedelta(days=1)
    elif timeframe == "weekly":
        start_date = now - timedelta(days=7)
    elif timeframe == "monthly":
        start_date = now - timedelta(days=30)
        
    start_str = start_date.strftime("%Y%m%d%H%M")
    end_str = now.strftime("%Y%m%d%H%M")

    cat_query = " OR ".join([f"cat:{c}" for c in ARXIV_CATEGORIES])
    full_query = f"({cat_query}) AND submittedDate:[{start_str} TO {end_str}]"
    
    logger.info(f"Fetching {timeframe} arXiv papers with query: {full_query}{' (using proxy)' if proxies else ''}")
    
    import os
    old_http = os.environ.get("HTTP_PROXY")
    old_https = os.environ.get("HTTPS_PROXY")
    
    try:
        if proxies:
            os.environ["HTTP_PROXY"] = proxies.get("http", "")
            os.environ["HTTPS_PROXY"] = proxies.get("https", "")

        client = arxiv.Client()
        search = arxiv.Search(
            query=full_query,
            max_results=100,
            sort_by=arxiv.SortCriterion.SubmittedDate
        )
        
        raw_results = []
        for r in client.results(search):
            raw_dict = {}
            for k, v in vars(r).items():
                if k.startswith('_'):
                    continue
                if isinstance(v, datetime):
                    raw_dict[k] = v.isoformat()
                elif isinstance(v, list) and len(v) > 0 and hasattr(v[0], '__dict__'):
                    raw_dict[k] = [vars(item) for item in v]
                else:
                    raw_dict[k] = v
            raw_results.append(raw_dict)
    except Exception as e:
        logger.error(f"Error fetching arXiv papers: {e}")
        raw_results = []
    finally:
        if proxies:
            if old_http is not None: os.environ["HTTP_PROXY"] = old_http
            else: os.environ.pop("HTTP_PROXY", None)
            if old_https is not None: os.environ["HTTPS_PROXY"] = old_https
            else: os.environ.pop("HTTPS_PROXY", None)
        raw_dict = {}
        for k, v in vars(r).items():
            if k.startswith('_'):
                continue
            if isinstance(v, datetime):
                raw_dict[k] = v.isoformat()
            elif isinstance(v, list) and len(v) > 0 and hasattr(v[0], '__dict__'):
                raw_dict[k] = [vars(item) for item in v]
            else:
                raw_dict[k] = v
        raw_results.append(raw_dict)
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"arxiv_{timeframe}_{timestamp}.json"
    file_path = ARXIV_API_DATA_DIR / filename
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump({"data": raw_results}, f, indent=2, ensure_ascii=False)
        
    logger.info(f"Saved arXiv raw data to {file_path}")
    return str(file_path.absolute())

def arxiv_parse_data(file_path: str) -> list:
    """
    Parse raw arXiv papers data from file.
    
    Platform: arXiv
    Method: JSON parsing
    Args:
        file_path (str): Path to the locally saved raw JSON data file.
    Returns:
        list: A list of ArxivPaperSchema objects.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    results = []
    for paper in data.get("data", []):
        entry_id = paper.get("entry_id", "")
        if not entry_id:
            continue
            
        short_id = entry_id.split('/')[-1]
        if 'v' in short_id:
            short_id = short_id.split('v')[0]
            
        comment = paper.get("comment", None)
        primary_category = paper.get("primary_category", "")
        categories = paper.get("categories", [])
        
        try:
            item = ArxivPaperSchema(
                id=short_id,
                comment=comment,
                primary_category=primary_category,
                categories=categories
            )
            results.append(item)
        except Exception as e:
            logger.error(f"Failed to validate ArxivPaperSchema for {short_id}: {e}")
            
    output_path = ARXIV_PARSED_DATA_DIR / f"{path.stem}_parsed.json"
    output_path.write_text(json.dumps([p.model_dump() for p in results], indent=2, ensure_ascii=False, default=str), encoding='utf-8')
    logger.info(f"Saved parsed arXiv JSON to {output_path}")
    
    return results

def arxiv_fetch_by_ids(paper_ids: list[str]) -> list[ArxivPaperSchema]:
    """
    Fetch papers from the arXiv API by a list of explicit IDs.
    
    Platform: arXiv
    Method: Search API Fetch by specific IDs
    Args:
        paper_ids (list[str]): A list of arXiv IDs to fetch (e.g. ['2105.12345']).
    Returns:
        list[ArxivPaperSchema]: A list of validated ArxivPaperSchema models.
    """
    if not paper_ids:
        return []
        
    logger.info(f"Fetching {len(paper_ids)} arXiv papers by IDs...")
    
    client = arxiv.Client()
    search = arxiv.Search(
        id_list=paper_ids
    )
    
    raw_results = []
    results = []
    for r in client.results(search):
        raw_dict = {}
        for k, v in vars(r).items():
            if k.startswith('_'): continue
            if isinstance(v, datetime):
                raw_dict[k] = v.isoformat()
            elif isinstance(v, list) and len(v) > 0 and hasattr(v[0], '__dict__'):
                raw_dict[k] = [vars(item) for item in v]
            else:
                raw_dict[k] = v
        raw_results.append(raw_dict)

        short_id = r.get_short_id()
        if "v" in short_id:
            short_id = short_id.split("v")[0]
            
        try:
            item = ArxivPaperSchema(
                id=short_id,
                comment=r.comment,
                primary_category=r.primary_category,
                categories=r.categories
            )
            results.append(item)
        except Exception as e:
            logger.error(f"Failed to validate ArxivPaperSchema for {short_id}: {e}")
            
    if raw_results:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"arxiv_by_ids_{timestamp}.json"
        file_path = ARXIV_API_DATA_DIR / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump({"data": raw_results}, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved raw arXiv data by IDs to {file_path}")
            
    return results

def arxiv_parse_by_ids(file_path: str) -> list[ArxivPaperSchema]:
    """
    Parse raw arXiv data fetched by specific IDs.
    
    Platform: arXiv
    Method: JSON parsing for ID-based results
    Args:
        file_path (str): Path to the locally saved raw JSON data file.
    Returns:
        list[ArxivPaperSchema]: A list of ArxivPaperSchema objects.
    """
    logger.info(f"Parsing arXiv results by IDs from {file_path}")
    return arxiv_parse_data(file_path)

if __name__ == "__main__":
    print("This module should not be run directly.")

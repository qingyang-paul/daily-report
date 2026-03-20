"""Hacker News data collector and parser using Algolia API.
"""
import os
import json
import time
import requests
import logging
from pathlib import Path
from bs4 import BeautifulSoup
import re
from typing import List
import sys

# Ensure scripts directory is in sys.path
scripts_dir = Path(__file__).resolve().parent.parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from core import config

from core.schema import HackerNewsStorySchema, CommentSchema

# Load environment logic at the top
config.load_config()

# Detailed logging format for debugging
logging.basicConfig(
    level=logging.INFO, 
    format='[%(filename)s:%(lineno)d] %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
HACKER_NEWS_API_BASE_URL = "https://hn.algolia.com/api/v1/search"
HACKER_NEWS_TIME_WINDOWS = {
    "daily": 86400,
    "weekly": 604800,
    "monthly": 2592000
}

# Retrieve base directories from core.config
BASE_API_DIR = config.API_DATA_DIR
BASE_PARSED_DIR = config.PARSED_DATA_DIR

# Define specific directories for this platform
HN_API_DATA_DIR = Path(BASE_API_DIR) / "hacker_news" / "algolia"
HN_PARSED_DATA_DIR = Path(BASE_PARSED_DIR) / "hacker_news"

# Ensure directories exist
HN_API_DATA_DIR.mkdir(parents=True, exist_ok=True)
HN_PARSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

logger.info(f"Loaded Hacker News configurations: API_DIR={HN_API_DATA_DIR}, PARSED_DIR={HN_PARSED_DATA_DIR}")

def hacker_news_health_check(proxies: dict = None) -> bool:
    """
    Check if the Hacker News Algolia API is responsive.
    
    Platform: Hacker News
    Method: Algolia Search API Health Check
    Args:
        proxies (dict, optional): Proxy configuration for the request.
    Returns:
        bool: True if the API is responsive, False otherwise.
    Docs URL: https://hn.algolia.com/api/v1/search
    """
    try:
        logger.info(f"Performing Hacker News health check on {HACKER_NEWS_API_BASE_URL}{' (using proxy)' if proxies else ''}")
        params = {"tags": "story", "hitsPerPage": 1}
        response = requests.get(HACKER_NEWS_API_BASE_URL, params=params, timeout=10, proxies=proxies)
        if response.status_code == 200:
            logger.info("Hacker News health check passed.")
            return True
        else:
            logger.warning(f"Hacker News health check failed with status code: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Hacker News health check failed with exception: {e}")
        return False

def hacker_news_fetch_data(timeframe: str = "daily", proxies: dict = None) -> str:
    """
    Fetch data from Hacker News Algolia API based on timeframe.
    
    Platform: Hacker News
    Method: Algolia Search API Fetch
    Args:
        timeframe (str): Time window to fetch stories for. Options: 'daily', 'weekly', or 'monthly'.
        proxies (dict, optional): Proxy configuration for the request.
    Returns:
        str: Absolute path to the saved raw JSON API response file.
    API Return Data: JSON payload containing a 'hits' array. Each hit represents a story with fields like objectID, story_id, title, url, author, points, num_comments, created_at, created_at_i.
    Docs URL: https://hn.algolia.com/api/v1/search
    """
    if timeframe not in HACKER_NEWS_TIME_WINDOWS:
        raise ValueError(f"Invalid timeframe: {timeframe}. Must be one of {list(HACKER_NEWS_TIME_WINDOWS.keys())}")
        
    since_timestamp = int(time.time()) - HACKER_NEWS_TIME_WINDOWS[timeframe]
    params = {
        "tags": "story",
        "numericFilters": f"created_at_i>{since_timestamp}",
        "hitsPerPage": 50 # Fetch top 50
    }
    
    logger.info(f"Fetching {timeframe} Hacker News data from Algolia API...{' (using proxy)' if proxies else ''}")
    response = requests.get(HACKER_NEWS_API_BASE_URL, params=params, timeout=30, proxies=proxies)
    response.raise_for_status()
    data = response.json()
    
    # Fetch comments for each hit
    for hit in data.get("hits", []):
        object_id = hit.get("objectID")
        if object_id:
            try:
                item_resp = requests.get(f"https://hn.algolia.com/api/v1/items/{object_id}", timeout=10, proxies=proxies)
                if item_resp.status_code == 200:
                    hit["item_details"] = item_resp.json()
            except Exception as e:
                logger.warning(f"Failed to fetch item details for {object_id}: {e}")
                
    output_file = HN_API_DATA_DIR / f"hn_{timeframe}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        
    logger.info(f"Saved Hacker News raw JSON to {output_file}")
    return str(output_file.absolute())

def hacker_news_parse_data(file_path: str) -> List[HackerNewsStorySchema]:
    """
    Parse raw data from file (JSON or HTML) and extract story fields.
    
    Platform: Hacker News
    Method: JSON/HTML parsing
    Args:
        file_path (str): Path to the locally saved raw data file (JSON or HTML).
    Returns:
        List[HackerNewsStorySchema]: A list of validated story models.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    if path.suffix == ".json":
        results = _hacker_news_parse_json(path)
    elif path.suffix == ".html":
        results = _hacker_news_parse_html(path)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")
        
    # Save parsed data to JSON for consistency
    output_path = HN_PARSED_DATA_DIR / f"{path.stem}_parsed.json"
    output_path.write_text(json.dumps([r.model_dump() for r in results], indent=2, ensure_ascii=False, default=str), encoding='utf-8')
    logger.info(f"Saved parsed Hacker News JSON to {output_path}")
    
    return results

def _hacker_news_parse_json(path: Path) -> List[HackerNewsStorySchema]:
    """Parse Algolia JSON response."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    results = []
    from datetime import datetime
    for hit in data.get("hits", []):
        object_id = str(hit.get("objectID", ""))
        title = hit.get("title", "No Title")
        url = hit.get("url") or (f"https://news.ycombinator.com/item?id={object_id}" if object_id else None)
        points = hit.get("points", 0)
        # Handle cases where points might be None
        if points is None: points = 0
            
        author = hit.get("author", "unknown")
        
        created_at_str = hit.get("created_at")
        if created_at_str:
            try:
                created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
            except ValueError:
                created_at = datetime.utcnow()
        else:
            created_at = datetime.utcnow()
            
        num_comments = hit.get("num_comments", 0)
        if num_comments is None: num_comments = 0
        
        details = hit.get("item_details", {})
        comments_raw = details.get("children", [])
        comments = []
        for c in comments_raw[:5]: # Take top 5
            if c.get("text"):
                text = BeautifulSoup(c["text"], "html.parser").get_text(strip=True)
                reply_text = ""
                if c.get("children") and len(c["children"]) > 0:
                    reply = c["children"][0]
                    if reply.get("text"):
                        reply_text = BeautifulSoup(reply["text"], "html.parser").get_text(strip=True)
                comments.append(CommentSchema(comment=text, reply=reply_text))
        
        # Better story_text extraction from highlightedResult if available
        raw_story_text = hit.get("_highlightResult", {}).get("story_text", {}).get("value", "")
        if not raw_story_text:
            raw_story_text = hit.get("story_text", "")
            
        story_text = ""
        if raw_story_text:
            story_text = BeautifulSoup(raw_story_text, "html.parser").get_text(strip=True)

        try:
            story = HackerNewsStorySchema(
                title=title,
                url=url,
                story_text=story_text if story_text else None,
                author=author,
                points=points,
                num_comments=num_comments,
                objectID=object_id,
                comments=comments,
                created_at=created_at
            )
            results.append(story)
        except Exception as e:
            logger.error(f"Failed to validate HackerNewsStorySchema for '{title}': {e}")
            
    return results

def _hacker_news_parse_html(path: Path) -> list:
    """Parse HTML using CSS selectors."""
    content = path.read_text(encoding="utf-8")
    soup = BeautifulSoup(content, 'html.parser')
    
    results = []
    story_elements = soup.select('article.Story')
    
    for story_element in story_elements:
        title_element = story_element.select_one('.Story_title a:first-child span')
        main_link_element = story_element.select_one('.Story_title a:first-child')
        meta_links = story_element.select('.Story_meta > span > a')
        
        title = title_element.get_text(strip=True) if title_element else "No Title"
        url = main_link_element['href'] if main_link_element else None
        
        points = 0
        author = "unknown"
        comments = 0
        created_at = "unknown"
        
        if len(meta_links) > 0:
            points_text = meta_links[0].get_text(strip=True)
            match = re.search(r'\d+', points_text)
            points = int(match.group()) if match else 0
            
        if len(meta_links) > 1:
            author = meta_links[1].get_text(strip=True)
            
        if len(meta_links) > 2:
            created_at = meta_links[2].get_text(strip=True)
            
        if len(meta_links) > 3:
            comments_text = meta_links[3].get_text(strip=True)
            match = re.search(r'\d+', comments_text)
            comments = int(match.group()) if match else 0
            
        results.append({
            "title": title,
            "url": url,
            "points": points,
            "comments": comments,
            "author": author,
            "created_at": created_at
        })
    return results

def hacker_news_generate_markdown(data: list, timeframe: str) -> str:
    """
    Generate a formatted markdown report from parsed Hacker News stories data.
    
    Platform: Hacker News
    Method: Markdown Generation
    Args:
        data (list): List of dictionaries containing story data.
        timeframe (str): The timeframe string used to name the file (e.g., 'daily').
    Returns:
        str: Absolute path to the generated markdown file.
    """
    lines = [
        f"# Hacker News Top Stories - {timeframe.capitalize()}\n",
        f"Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n",
        "---"
    ]
    
    for item in data:
        lines.append(f"\n## [{item.title}]({item.url})")
        lines.append(f"**Points:** {item.points} | **Comments:** {item.comments} | **Author:** {item.author} | **Time:** {item.created_at}")
        lines.append("\n---")
        
    output_path = HN_PARSED_DATA_DIR / f"hn_{timeframe}.md"
    output_path.write_text("\n".join(lines), encoding="utf-8")
    
    return str(output_path.absolute())

if __name__ == "__main__":
    print("This module should not be run directly.")

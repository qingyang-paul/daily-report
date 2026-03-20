"""GitHub Trending data collector and parser.
"""
from bs4 import BeautifulSoup
import requests
import os
from pathlib import Path
import logging
import re
import json
from typing import List
from pathlib import Path
import sys

# Ensure scripts directory is in sys.path
scripts_dir = Path(__file__).resolve().parent.parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from core import config
from core.schema import GithubTrendingSchema

# Load environment logic at the top
config.load_config()

# Detailed logging format for debugging
logging.basicConfig(
    level=logging.INFO, 
    format='[%(filename)s:%(lineno)d] %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
GITHUB_TRENDING_BASE_URL = "https://github.com/trending/python"
GITHUB_TRENDING_SINCE_OPTIONS = ["daily", "weekly", "monthly"]
GITHUB_TRENDING_DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://github.com/",
}

# Retrieve base directories from core.config
BASE_API_DIR = config.API_DATA_DIR
BASE_PARSED_DIR = config.PARSED_DATA_DIR

GITHUB_TRENDING_API_DATA_DIR = Path(BASE_API_DIR) / "github" / "trending"
GITHUB_TRENDING_PARSED_DATA_DIR = Path(BASE_PARSED_DIR) / "github"

# Ensure directories exist
GITHUB_TRENDING_API_DATA_DIR.mkdir(parents=True, exist_ok=True)
GITHUB_TRENDING_PARSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

logger.info(f"Loaded GitHub Trending configurations: API_DIR={GITHUB_TRENDING_API_DATA_DIR}, PARSED_DIR={GITHUB_TRENDING_PARSED_DATA_DIR}")

def github_trending_health_check() -> bool:
    """
    Check if the GitHub Trending page is accessible.
    
    Platform: GitHub Trending
    Method: HTTP GET Health Check
    Args:
        None
    Returns:
        bool: True if accessible (responses with status code 200), False otherwise.
    Docs URL: https://github.com/trending/python
    """
    try:
        logger.info(f"Performing GitHub Trending health check on {GITHUB_TRENDING_BASE_URL}")
        # Identify the specific URL for health check
        response = requests.get(GITHUB_TRENDING_BASE_URL, headers=GITHUB_TRENDING_DEFAULT_HEADERS, timeout=10)
        if response.status_code == 200:
            logger.info("GitHub Trending health check passed.")
            return True
        else:
            logger.warning(f"GitHub Trending health check failed with status code: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"GitHub Trending health check failed with exception: {e}")
        return False

def github_trending_fetch_html(since: str = "daily") -> Path:
    """
    Fetch trending repos from GitHub and save raw HTML.
    
    Platform: GitHub Trending
    Method: HTTP GET Fetch HTML
    Args:
        since (str): The timeframe to fetch trending repos. Options: 'daily', 'weekly', or 'monthly'.
    Returns:
        Path: Path to the saved HTML file.
    API Return Data: Raw HTML string of the GitHub Trending page containing elements like repository name, description, primary language, total stars, total forks, contributors, and trend count.
    Docs URL: https://github.com/trending/python
    """
    if since not in GITHUB_TRENDING_SINCE_OPTIONS:
        raise ValueError(f"Invalid 'since' option: {since}. Must be one of {GITHUB_TRENDING_SINCE_OPTIONS}")
        
    url = f"{GITHUB_TRENDING_BASE_URL}?since={since}"
    logger.info(f"Fetching GitHub trending data for {since} from {url}")
    
    response = requests.get(url, headers=GITHUB_TRENDING_DEFAULT_HEADERS, timeout=15)
    response.raise_for_status()
    
    output_file = GITHUB_TRENDING_API_DATA_DIR / f"trending_{since}.html"
    output_file.write_text(response.text, encoding='utf-8')
    
    logger.info(f"Saved GitHub Trending raw HTML to {output_file}")
    return output_file

def github_trending_parse_html(html_path: Path) -> Path:
    """
    Parse raw HTML of GitHub Trending and generate a Markdown report.
    
    Platform: GitHub Trending
    Method: HTML Parsing and Markdown Generation
    Args:
        html_path (Path): Path to the locally saved raw HTML file to parse.
    Returns:
        List[GithubTrendingSchema]: A list of validated GithubTrendingSchema objects.
    API Return Data: Not direct API, it extracts Title, Description, Language, Stars, and Forks from HTML DOM nodes.
    """
    if not html_path.exists():
        raise FileNotFoundError(f"HTML file not found: {html_path}")
        
    since_match = re.search(r'trending_(daily|weekly|monthly)\.html', html_path.name)
    since = since_match.group(1) if since_match else "unknown"
    
    content = html_path.read_text(encoding='utf-8')
    soup = BeautifulSoup(content, 'html.parser')
    
    projects_data = []
    for row in soup.select('article.Box-row'):
        title_element = row.select_one('h2.h3.lh-condensed a.Link')
        description_element = row.select_one('p.col-9.color-fg-muted.my-1.tmp-pr-4')
        language_element = row.select_one('span[itemprop="programmingLanguage"]')
        star_element = row.select_one('a[href*="/stargazers"].Link--muted')
        fork_element = row.select_one('a[href*="/forks"].Link--muted')
        trend_element = row.select_one('span.float-sm-right')

        title_raw = title_element.get_text(strip=True).replace('\\n', '').replace('  ', ' ') if title_element else "Unknown"
        if "/" in title_raw:
            owner, name = [part.strip() for part in title_raw.split("/", 1)]
        else:
            owner, name = "Unknown", title_raw

        url_path = title_element.get('href') if title_element else ""
        url = f"https://github.com{url_path}" if url_path else ""

        description = description_element.get_text(strip=True) if description_element else "No description provided."
        language = language_element.get_text(strip=True) if language_element else "Unknown"

        def parse_int(text: str) -> int:
            if not text:
                return 0
            digits = re.sub(r'\D', '', text)
            return int(digits) if digits else 0

        star = parse_int(star_element.get_text(strip=True)) if star_element else 0
        fork = parse_int(fork_element.get_text(strip=True)) if fork_element else 0

        stars_today = 0
        if trend_element:
            trend_text = trend_element.get_text(strip=True)
            trend_match = re.search(r'([\d,]+)\s+stars', trend_text)
            if trend_match:
                stars_today = parse_int(trend_match.group(1))

        growth_rate = 0.0
        if star > 0 and stars_today > 0:
            growth_rate = round(stars_today / star, 4)

        built_by = []
        # Look for the span that contains 'Built by'
        for span in row.select('span.d-inline-block'):
            if 'Built by' in span.get_text():
                for img in span.select('img.avatar'):
                    avatar_url = img.get('src')
                    if avatar_url:
                        built_by.append(avatar_url)
                break

        try:
            item = GithubTrendingSchema(
                owner=owner,
                name=name,
                url=url,
                description=description,
                language=language,
                stars=star,
                forks=fork,
                stars_today=stars_today,
                growth_rate=growth_rate,
                built_by=built_by
            )
            projects_data.append(item)
        except Exception as e:
            logger.error(f"Failed to validate GithubTrendingSchema for {owner}/{name}: {e}")

    # Generate JSON
    output_path = GITHUB_TRENDING_PARSED_DATA_DIR / f"trending_{since}.json"
    output_path.write_text(json.dumps([p.model_dump() for p in projects_data], indent=2, ensure_ascii=False), encoding='utf-8')
    
    logger.info(f"Successfully generated GitHub Trending json at {output_path.name} with {len(projects_data)} projects.")
    return projects_data

def github_trending_verify_results(html_path: Path, json_path: Path) -> bool:
    """
    Verify the parsing results by comparing counts in the HTML and the parsed JSON file.
    
    Platform: GitHub Trending
    Method: Cross-verification
    Args:
        html_path (Path): Path to the locally saved raw HTML file.
        json_path (Path): Path to the generated JSON file.
    Returns:
        bool: True if the count of parsed projects matches the count of articles, False otherwise.
    """
    if not html_path.exists() or not json_path.exists():
        return False
        
    html_content = html_path.read_text(encoding='utf-8')
    soup = BeautifulSoup(html_content, 'html.parser')
    html_count = len(soup.select('article.Box-row'))
    
    try:
        json_data = json.loads(json_path.read_text(encoding='utf-8'))
        json_count = len(json_data)
    except json.JSONDecodeError:
        logger.error(f"Failed to decode JSON file: {json_path}")
        return False
    
    return html_count == json_count

if __name__ == "__main__":
    print("This module should not be run directly.")


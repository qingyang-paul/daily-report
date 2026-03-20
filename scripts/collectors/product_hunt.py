"""Product Hunt Data Collector.

Fetches trending products and comments using the Product Hunt GraphQL API.
"""
import os
import requests
import logging
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Ensure scripts directory is in sys.path
scripts_dir = Path(__file__).resolve().parent.parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from core import config

import json
import shutil
import re

# Load environment logic at the top
config.load_config()

# Detailed logging format for debugging
logging.basicConfig(
    level=logging.INFO, 
    format='[%(filename)s:%(lineno)d] %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PRODUCT_HUNT_API_URL = "https://api.producthunt.com/v2/api/graphql"
PRODUCT_HUNT_PERIODS = ["daily", "weekly", "monthly"]

PRODUCT_HUNT_TOKEN = os.getenv("Product_Hunt_Developer_Token")

# Retrieve base directories from core.config
BASE_API_DIR = config.API_DATA_DIR
BASE_PARSED_DIR = config.PARSED_DATA_DIR

# Define specific directories for this platform
PH_API_DATA_DIR = Path(BASE_API_DIR) / "product_hunt" / "graphql"
PH_PARSED_DATA_DIR = Path(BASE_PARSED_DIR) / "product_hunt"

# Ensure directories exist
PH_API_DATA_DIR.mkdir(parents=True, exist_ok=True)
PH_PARSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

logger.info(f"Loaded Product Hunt configurations: API_DIR={PH_API_DATA_DIR}, PARSED_DIR={PH_PARSED_DATA_DIR}")

PRODUCT_HUNT_POSTS_QUERY = """
query ($postedAfter: DateTime, $postedBefore: DateTime) {
  posts(order: VOTES, postedAfter: $postedAfter, postedBefore: $postedBefore, first: 20) {
    edges {
      node {
        name
        tagline
        createdAt      # [NEW] Post creation time
        votesCount
        commentsCount
        url
        website
        thumbnail {
          url
        }
        topics(first: 3) {
          edges {
            node {
              name
            }
          }
        }
        # Fetch the first comment with 1 reply
        comments(first: 1) {
          edges {
            node {
              body
              votesCount
              createdAt  # [NEW] Comment creation time
              user {
                name
              }
              replies(first: 1) {
                edges {
                  node {
                    body
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
"""

def product_hunt_health_check(proxies: dict = None) -> bool:
    """
    Perform a health check by sending a simple GraphQL query to Product Hunt.
    Args:
        proxies (dict, optional): Proxy configuration for the request.
    """
    if not PRODUCT_HUNT_TOKEN:
        logger.error("Product_Hunt_Developer_Token is not set.")
        return False
        
    query = """
    query {
        viewer {
        user {
            id
            name
        }
        }
    }
    """
    headers = {
        "Authorization": f"Bearer {PRODUCT_HUNT_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    
    try:
        logger.info(f"Performing Product Hunt health check...{' (using proxy)' if proxies else ''}")
        response = requests.post(PRODUCT_HUNT_API_URL, json={"query": query}, headers=headers, timeout=10, proxies=proxies)
        response.raise_for_status()
        data = response.json()
        if "errors" in data:
            logger.error(f"GraphQL errors: {data['errors']}")
            return False
        logger.info("Product Hunt health check successful.")
        return True
    except Exception as e:
        logger.error(f"Product Hunt health check failed: {e}")
        return False

def product_hunt_fetch_data(timeframe: str, proxies: dict = None) -> str:
    """
    Fetch posts for a given timeframe and save as raw JSON.
    Args:
        timeframe (str): The time duration ('daily', 'weekly', 'monthly').
        proxies (dict, optional): Proxy configuration for the request.
    """
    if timeframe not in PRODUCT_HUNT_PERIODS:
        raise ValueError(f"Invalid timeframe: {timeframe}. Must be one of {PRODUCT_HUNT_PERIODS}")

    if not PRODUCT_HUNT_TOKEN:
        raise ValueError("Product_Hunt_Developer_Token is not set in environment.")

    now = datetime.utcnow()
    if timeframe == "daily":
        posted_after = now - timedelta(days=1)
    elif timeframe == "weekly":
        posted_after = now - timedelta(days=7)
    elif timeframe == "monthly":
        posted_after = now - timedelta(days=30)
    
    posted_after_str = posted_after.strftime("%Y-%m-%dT%H:%M:%SZ")
    logger.info(f"Fetching Product Hunt {timeframe} posts since {posted_after_str}...{' (using proxy)' if proxies else ''}")
    
    headers = {
        "Authorization": f"Bearer {PRODUCT_HUNT_TOKEN}",
        "Content-Type": "application/json",
    }
    variables = {
        "postedAfter": posted_after_str
    }
    
    response = requests.post(PRODUCT_HUNT_API_URL, json={"query": PRODUCT_HUNT_POSTS_QUERY, "variables": variables}, headers=headers, proxies=proxies)
    response.raise_for_status()
    
    data = response.json()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"product_hunt_{timeframe}_{timestamp}.json"
    file_path = PH_API_DATA_DIR / filename
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
    logger.info(f"Saved Product Hunt raw data to {file_path}")
    return str(file_path.absolute())

def clean_html(raw_html):
    """Clean HTML tags from a string."""
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext.strip()

def product_hunt_parse_data(json_file_path: str) -> list:
    """
    Parse raw JSON data into a list of ProductHuntAppSchema objects.
    """
    from core.schema import ProductHuntAppSchema, CommentSchema
    
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    posts_data = data.get("data", {}).get("posts", {}).get("edges", [])
    
    parsed_posts = []
    for edge in posts_data:
        node = edge.get("node", {})
        
        parsed_topics = [t.get("node", {}).get("name") for t in node.get("topics", {}).get("edges", [])]
        
        parsed_comments = []
        for c in node.get("comments", {}).get("edges", []):
            c_node = c.get("node", {})
            body = clean_html(c_node.get("body", ""))
            
            # Extract single reply
            reply_text = ""
            child_edges = c_node.get("replies", {}).get("edges", [])
            if child_edges:
                reply_text = clean_html(child_edges[0].get("node", {}).get("body", ""))
                
            try:
                c_model = CommentSchema(comment=body, reply=reply_text)
                parsed_comments.append(c_model)
            except Exception:
                pass
                
        try:
            launched_at_raw = node.get("createdAt")
            if launched_at_raw:
                launched_at = datetime.fromisoformat(launched_at_raw.replace("Z", "+00:00"))
            else:
                launched_at = datetime.utcnow()
                
            from urllib.parse import urlparse
            website_url = node.get("website")
            thumbnail_url = node.get("thumbnail", {}).get("url") if node.get("thumbnail") else ""
            
            domain = ""
            if website_url:
                parsed_url = urlparse(website_url)
                if "producthunt.com" in parsed_url.netloc and "/r/" in parsed_url.path:
                    avatar_url = thumbnail_url if thumbnail_url else f"https://www.google.com/s2/favicons?sz=128&domain=producthunt.com"
                else:
                    domain = parsed_url.netloc
                    avatar_url = f"https://www.google.com/s2/favicons?sz=128&domain={domain}" if domain else (thumbnail_url or "")
            else:
                avatar_url = thumbnail_url or ""

            item = ProductHuntAppSchema(
                name=node.get("name") or "Unknown",
                tagline=node.get("tagline") or "",
                votesCount=node.get("votesCount", 0),
                commentsCount=node.get("commentsCount", 0),
                tags=parsed_topics,
                comments=parsed_comments,
                product_hunt_page=node.get("url") or "",
                product_official_website=node.get("website"),
                avatar_url=avatar_url,
                launched_at=launched_at
            )
            parsed_posts.append(item)
        except Exception as e:
            logger.error(f"Failed to validate schema for Product Hunt: {e}")
            
    output_path = PH_PARSED_DATA_DIR / f"{Path(json_file_path).stem}_parsed.json"
    output_path.write_text(json.dumps([p.model_dump() for p in parsed_posts], indent=2, ensure_ascii=False, default=str), encoding='utf-8')
    logger.info(f"Saved parsed Product Hunt JSON to {output_path}")

    return parsed_posts

def product_hunt_generate_markdown(parsed_posts: list, timeframe: str) -> str:
    """
    Generate a Markdown report from parsed posts and save it.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    date_str = datetime.now().strftime("%Y%m%d")
    
    lines = [
        f"# Product Hunt {timeframe.capitalize()} Report",
        f"Generated at: {timestamp}\n",
        "| Name | Tagline | Votes | Topics | Link | Top Comments |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |"
    ]
    
    for post in parsed_posts:
        topics_str = ", ".join(post.tags)
        tagline = post.tagline.replace("|", "\\|") if post.tagline else ""
        
        comments_list = []
        for c in post.comments:
            c_text = c.comment.replace("|", "\\|").replace("\n", " ")
            if c.reply:
                r_text = c.reply.replace("|", "\\|").replace("\n", " ")
                comments_list.append(f"{c_text} (Reply: {r_text})")
            else:
                comments_list.append(c_text)
                
        comments_str = "<br>".join(comments_list)
        if len(comments_str) > 300: 
            comments_str = comments_str[:297] + "..." 
            
        name = post.name
        votes = post.votesCount
        url = post.product_hunt_page
        
        lines.append(f"| {name} | {tagline} | {votes} | {topics_str} | [Link]({url}) | {comments_str} |")
        
    markdown_content = "\n".join(lines)
    
    filename = f"report_{timeframe}_{date_str}.md"
    file_path = PH_PARSED_DATA_DIR / filename
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
        
    logger.info(f"Generated Product Hunt markdown report at {file_path}")
    return str(file_path.absolute())

def product_hunt_generate_cleaned_report(timeframe: str):
    """
    Execute the full pipeline for Product Hunt: Fetch, Parse, and Save.
    Also saves a copy to the current working directory for direct viewing.
    """
    raw_json_path = product_hunt_fetch_data(timeframe)
    parsed_posts = product_hunt_parse_data(raw_json_path)
    report_path = product_hunt_generate_markdown(parsed_posts, timeframe)
    
    dest_path = os.path.join(os.getcwd(), "product_hunt_report.md")
    shutil.copy(report_path, dest_path)
    logger.info(f"Saved Product Hunt cleaned report to {dest_path}")
    
    return dest_path

if __name__ == "__main__":
    print("This module should not be run directly.")

"""OpenRouter Data Collector.

Fetches model lists, pricing, and trending apps from the OpenRouter API.
"""
import os
import json
import time
import requests
import logging
from pathlib import Path
from datetime import datetime
import sys

# Ensure scripts directory is in sys.path
scripts_dir = Path(__file__).resolve().parent.parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from core import config

from core.schema import OpenRouterLLMSchema, OpenRouterAppTrendSchema, OpenRouterAppRankSchema

# Load environment logic at the top
config.load_config()

# Detailed logging format for debugging
logging.basicConfig(
    level=logging.INFO, 
    format='[%(filename)s:%(lineno)d] %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
OPENROUTER_API_BASE_URL = "https://openrouter.ai/api/v1/models"

# Retrieve base directories from core.config
BASE_API_DIR = config.API_DATA_DIR
BASE_PARSED_DIR = config.PARSED_DATA_DIR

# Define specific directories for this platform
OR_API_DATA_DIR = Path(BASE_API_DIR) / "openrouter"
OR_PARSED_DATA_DIR = Path(BASE_PARSED_DIR) / "openrouter"

# Ensure directories exist
OR_API_DATA_DIR.mkdir(parents=True, exist_ok=True)
OR_PARSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

logger.info(f"Loaded OpenRouter configurations: API_DIR={OR_API_DATA_DIR}, PARSED_DIR={OR_PARSED_DATA_DIR}")

def openrouter_health_check(proxies: dict = None) -> bool:
    """
    Check if the OpenRouter API is responsive.
    
    Platform: OpenRouter
    Method: API Health Check
    Args:
        proxies (dict, optional): Proxy configuration for the request.
    Returns:
        bool: True if the API is responsive, False otherwise.
    Docs URL: https://openrouter.ai/api/v1/models
    """
    try:
        logger.info(f"Performing OpenRouter health check on {OPENROUTER_API_BASE_URL}{' (using proxy)' if proxies else ''}")
        response = requests.get(OPENROUTER_API_BASE_URL, timeout=30, proxies=proxies)
        if response.status_code == 200:
            logger.info("OpenRouter health check passed.")
            return True
        else:
            logger.warning(f"OpenRouter health check failed with status code: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"OpenRouter health check failed with exception: {e}")
        return False

def openrouter_fetch_data(proxies: dict = None) -> str:
    """
    Fetch data from OpenRouter Models API.
    
    Platform: OpenRouter
    Method: Models API Fetch
    Args:
        proxies (dict, optional): Proxy configuration for the request.
    Returns:
        str: Absolute path to the saved raw JSON API response file.
    API Return Data: JSON payload containing a 'data' array. Each item is a model info dict.
    Docs URL: https://openrouter.ai/api/v1/models
    """
    logger.info(f"Fetching OpenRouter models data...{' (using proxy)' if proxies else ''}")
    response = requests.get(OPENROUTER_API_BASE_URL, timeout=60, proxies=proxies)
    response.raise_for_status()
    
    data = response.json()
    
    # Sort models by created (descending)
    if "data" in data and isinstance(data["data"], list):
        data["data"].sort(key=lambda x: x.get("created", 0), reverse=True)
        logger.info(f"Fetched and sorted {len(data['data'])} models from OpenRouter.")
    
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    output_file = OR_API_DATA_DIR / f"openrouter_models_{timestamp}.json"
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        
    logger.info(f"Saved OpenRouter raw JSON to {output_file}")
    return str(output_file.absolute())

def openrouter_parse_data(file_path: str) -> list:
    """
    Parse raw OpenRouter models data from file.
    
    Platform: OpenRouter
    Method: JSON parsing
    Args:
        file_path (str): Path to the locally saved raw JSON data file.
    Returns:
        list: A list of OpenRouterLLMSchema objects.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    results = []
    for model in data.get("data", []):
        name = model.get("name", "Unknown Name")
        created_at = datetime.fromtimestamp(model.get("created", 0))
        
        # safely parse context_length to int
        context_length_val = model.get("context_length", 0)
        try:
            context_length_int = int(context_length_val)
        except (ValueError, TypeError):
            context_length_int = 0
            
        architecture = model.get("architecture", {})
        modality = architecture.get("modality", "Unknown")
        if not isinstance(modality, str):
            modality = str(modality)
            
        pricing = model.get("pricing", {})
        
        prompt_price_str = pricing.get("prompt", "0")
        completion_price_str = pricing.get("completion", "0")
        
        try:
            prompt_price_per_m = float(prompt_price_str) * 1_000_000
        except ValueError:
            prompt_price_per_m = 0.0
            
        try:
            completion_price_per_m = float(completion_price_str) * 1_000_000
        except ValueError:
            completion_price_per_m = 0.0
        
        description = model.get("description", "No description available.")
        
        try:
            item = OpenRouterLLMSchema(
                owner=name.split('/')[0] if '/' in name else "Unknown",
                name=name.split('/')[-1] if '/' in name else name,
                canonical_slug=model.get("id", name),
                created=created_at,
                description=description,
                context_length=context_length_int,
                modality=modality,
                prompt_pricing=round(prompt_price_per_m, 4),
                completion_pricing=round(completion_price_per_m, 4)
            )
            results.append(item)
        except Exception as e:
            logger.error(f"Failed to validate OpenRouterLLMSchema for: {name}, error: {e}")
            
    output_path = OR_PARSED_DATA_DIR / f"{path.stem}_parsed.json"
    output_path.write_text(json.dumps([p.model_dump() for p in results], indent=2, ensure_ascii=False, default=str), encoding='utf-8')
    return results

def openrouter_generate_markdown(data: list) -> str:
    """
    Generate a formatted markdown report from parsed OpenRouter models data.
    
    Platform: OpenRouter
    Method: Markdown Generation
    Args:
        data (list): List of dictionaries containing model data.
    Returns:
        str: Absolute path to the generated markdown file.
    """
    lines = [
        "# OpenRouter Newest Models\n",
        f"Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n",
        "---"
    ]
    
    for item in data:
        lines.append(f"\n### {item.name}")
        lines.append(f"{item.created} | {item.context_length} | {item.modality} | ${item.prompt_pricing}/M input | ${item.completion_pricing}/M output")
        lines.append(f"\n{item.description}")
        lines.append("\n---")
        
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    output_path = OR_PARSED_DATA_DIR / f"openrouter_models_{timestamp}.md"
    output_path.write_text("\n".join(lines), encoding="utf-8")
    
    logger.info(f"Successfully generated OpenRouter markdown at {output_path}")
    return str(output_path.absolute())

def openrouter_apps_fetch_data(proxies: dict = None) -> str:
    """
    Fetch raw HTML from OpenRouter Apps page.
    """
    url = "https://openrouter.ai/apps"
    logger.info(f"Fetching OpenRouter apps data...{' (using proxy)' if proxies else ''}")
    response = requests.get(url, timeout=30, proxies=proxies)
    response.raise_for_status()
    
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    output_file = OR_API_DATA_DIR / f"openrouter_apps_{timestamp}.html"
    output_file.write_text(response.text, encoding="utf-8")
    
    logger.info(f"Saved OpenRouter apps HTML to {output_file}")
    return str(output_file.absolute())

def openrouter_apps_parse_data(file_path: str) -> dict:
    """
    Parse the Top 20 Global Ranking apps from the HTML file.
    """
    from bs4 import BeautifulSoup
    import re
    
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    app_links = soup.find_all("a", href=lambda h: h and h.startswith("/apps?url="))
    
    top_20 = []
    for link in app_links:
        spans = link.find_all("span")
        rank_span = None
        for s in spans:
            if re.match(r'^\d+\.$', s.text.strip()):
                rank_span = s
                break
                
        if rank_span:
            rank = int(rank_span.text.strip().replace('.', ''))
            
            name_tag = link.find("span", class_="truncate")
            name = name_tag.text if name_tag else "Unknown"
            
            desc_tag = link.find("p", class_="truncate")
            desc = desc_tag.text if desc_tag else ""
            
            tag = ""
            for s in link.find_all("span"):
                classes = " ".join(s.get("class", []))
                if "bg-" in classes and "text-" in classes and "rounded" in classes:
                    tag = s.text.strip()
                    break
                    
            import urllib.parse
            app_url_attr = link.get("href", "")
            app_url = urllib.parse.unquote(app_url_attr.replace("/apps?url=", "")) if app_url_attr else ""
            
            img_tag = link.find("img")
            avatar_url = img_tag.get("src") if img_tag else ""
            
            texts = list(link.stripped_strings)
            tokens = ""
            if len(texts) >= 2 and texts[-1] == "tokens":
                tokens = f"{texts[-2]} {texts[-1]}"
            
            try:
                item = OpenRouterAppRankSchema(
                    name=name,
                    description=desc,
                    app_url=app_url,
                    avatar_url=avatar_url,
                    token_usage=tokens,
                    rank=rank,
                    tags=[tag] if tag else [],
                    growth_rate=""
                )
                top_20.append(item)
            except Exception as e:
                pass
            
    # Filter to actual global top 20 list (first 20 sequential apps up to rank 20)
    global_ranking = []
    expected_rank = 1
    for app in top_20:
        if app.rank == expected_rank:
            global_ranking.append(app)
            expected_rank += 1
            if expected_rank > 20:
                break
        elif expected_rank > 1:
            break # Not sequential anymore
            
    # Extract Trending
    trending = []
    trending_h2 = soup.find("h2", string=re.compile("Trending", re.I))
    if trending_h2:
        container = trending_h2.find_next_sibling("div")
        if not container:
            parent = trending_h2.parent
            if parent:
                container = parent.find_next_sibling("div")
        if container:
            trend_apps = container.find_all("a", href=lambda h: h and h.startswith("/apps?url="))
            import urllib.parse
            for app in trend_apps:
                texts = list(app.stripped_strings)
                # e.g., ['OpenClaw', '4.51T', '+', '69', '%']
                if len(texts) >= 4 and texts[-1] == '%' and texts[-3] in ['+', '-']:
                    name = texts[0]
                    token_usage = texts[1] if len(texts) >= 5 else ""
                    growth = f"{texts[-3]}{texts[-2]}%"
                    
                    app_url_attr = app.get("href", "")
                    app_url = urllib.parse.unquote(app_url_attr.replace("/apps?url=", "")) if app_url_attr else ""
                    
                    img_tag = app.find("img")
                    avatar_url = img_tag.get("src") if img_tag else ""
                    
                    try:
                        t_item = OpenRouterAppTrendSchema(
                            name=name, 
                            description="",
                            app_url=app_url,
                            avatar_url=avatar_url,
                            token_usage=token_usage,
                            growth_rate=growth
                        )
                        trending.append(t_item)
                    except Exception:
                        pass
            
    result_dict = {"global_ranking": global_ranking, "trending": trending}
    output_path = OR_PARSED_DATA_DIR / f"{path.stem}_parsed.json"
    
    save_data = {
        "global_ranking": [g.model_dump() for g in global_ranking],
        "trending": [t.model_dump() for t in trending]
    }
    output_path.write_text(json.dumps(save_data, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    
    return result_dict

def openrouter_apps_generate_markdown(data: dict) -> str:
    """
    Generate markdown for Apps based on the expected extraction format.
    """
    lines = [
        "# OpenRouter App Trends\n",
        f"Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
    ]
    
    lines.append("## Trending\n")
    lines.append("Avatar | App Name | Growth Rate")
    lines.append("--- | --- | ---")
    if data.get("trending"):
        for app in data["trending"]:
            # Handle both dict and Pydantic object
            if hasattr(app, "model_dump"):
                app_dict = app.model_dump()
            else:
                app_dict = app
                
            avatar_md = f"<img src='{app_dict.get('avatar_url', '')}' width='32' height='32' />" if app_dict.get('avatar_url') else "N/A"
            name_md = f"[{app_dict['name']}]({app_dict['app_url']})" if app_dict.get('app_url') else app_dict['name']
            usage_str = f" ({app_dict.get('token_usage')})" if app_dict.get('token_usage') else ""
            lines.append(f"{avatar_md} | {name_md}{usage_str} | {app_dict['growth_rate']}")
    else:
        lines.append("N/A | N/A | N/A")
    
    lines.append("\n## Global ranking\n")
    lines.append("Top 20 Ranking\n")
    lines.append("Avatar | App Name | Description | Tags | Token Usage")
    lines.append("--- | --- | --- | --- | ---")
    
    for app in data.get("global_ranking", []):
        if hasattr(app, "model_dump"):
            app_dict = app.model_dump()
        else:
            app_dict = app
            
        avatar_md = f"<img src='{app_dict.get('avatar_url', '')}' width='32' height='32' />" if app_dict.get('avatar_url') else "N/A"
        name_md = f"[{app_dict['name']}]({app_dict['app_url']})" if app_dict.get('app_url') else app_dict['name']
        tags_str = ", ".join(app_dict.get('tags', []))
        lines.append(f"{avatar_md} | {name_md} | {app_dict.get('description', '')} | {tags_str} | {app_dict.get('token_usage', 'N/A')}")
        
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    output_path = OR_PARSED_DATA_DIR / f"openrouter_apps_{timestamp}.md"
    output_path.write_text("\n".join(lines), encoding="utf-8")
    
    logger.info(f"Successfully generated OpenRouter apps markdown at {output_path}")
    return str(output_path.absolute())

if __name__ == "__main__":
    print("This module should not be run directly.")

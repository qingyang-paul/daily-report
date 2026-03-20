"""Centralized configuration and path management for the Daily Info project.

Handles project root detection, .env.local loading, and defines absolute paths
for all data and output directories.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def find_project_root() -> Path:
    """
    Find the project root by searching for .env.local starting from the current file.
    """
    current = Path(__file__).resolve().parent
    for _ in range(5):  # Search up to 5 parent levels
        if (current / ".env.local").exists():
            return current
        current = current.parent
    
    # Fallback: traverse up from this file's directory until daily-info is found
    current = Path(__file__).resolve().parent
    while current.name != "daily-info" and current != current.parent:
        current = current.parent
    return current

# Default absolute paths, will be updated by load_config()
PROJECT_ROOT = find_project_root()
API_DATA_DIR = PROJECT_ROOT / "api_results/"
PARSED_DATA_DIR = PROJECT_ROOT / "parsed_results/"
EMAIL_HTML_DIR = PROJECT_ROOT / "email_htmls/"
EMAIL_PDF_DIR = PROJECT_ROOT / "report_pdf/"
SECTION_LIMITS = {}
PROXIES = {}

def load_config():
    """Find and load .env.local from project root and update path constants."""
    global API_DATA_DIR, PARSED_DATA_DIR, EMAIL_HTML_DIR, EMAIL_PDF_DIR, SECTION_LIMITS, PROXIES
    
    env_path = PROJECT_ROOT / ".env.local"
    
    if env_path.exists():
        load_dotenv(env_path)
        
        # Mapping from .env.local names to internal constants
        # 1. Workspace Path
        workspace_raw = os.getenv("WORKSPACE_PATH")
        if workspace_raw:
            workspace_base = Path(os.path.expanduser(workspace_raw))
            workspace_base.mkdir(parents=True, exist_ok=True)
            root_for_dirs = workspace_base
        else:
            root_for_dirs = PROJECT_ROOT

        # 2. Data Directories
        raw_api_dir = os.getenv("API_RESULTS_DIR", "api_results/")
        raw_parsed_dir = os.getenv("PARSED_RESULTS_DIR", "parsed_results/")
        raw_email_dir = os.getenv("EMAIL_HTML_DIR", "email_htmls/")
        raw_pdf_dir = os.getenv("EMAIL_PDF_DIR", "report_pdf")
        
        API_DATA_DIR = Path(raw_api_dir)
        if not API_DATA_DIR.is_absolute():
            API_DATA_DIR = root_for_dirs / API_DATA_DIR
            
        PARSED_DATA_DIR = Path(raw_parsed_dir)
        if not PARSED_DATA_DIR.is_absolute():
            PARSED_DATA_DIR = root_for_dirs / PARSED_DATA_DIR
            
        EMAIL_HTML_DIR = Path(raw_email_dir)
        if not EMAIL_HTML_DIR.is_absolute():
            EMAIL_HTML_DIR = root_for_dirs / EMAIL_HTML_DIR

        EMAIL_PDF_DIR = Path(raw_pdf_dir)
        if not EMAIL_PDF_DIR.is_absolute():
            EMAIL_PDF_DIR = root_for_dirs / EMAIL_PDF_DIR
            
        # Ensure directories exist
        for d in [API_DATA_DIR, PARSED_DATA_DIR, EMAIL_HTML_DIR, EMAIL_PDF_DIR]:
            d.mkdir(parents=True, exist_ok=True)
            
        # 3. Section Limits
        default_limit = int(os.getenv("DEFAULT_SECTION_LIMIT", 10))
        SECTION_LIMITS = {
            "github": int(os.getenv("GITHUB_TRENDING_TODAY_LIMIT", default_limit)),
            "huggingface": int(os.getenv("HUGGING_FACE_DAILY_PAPERS_LIMIT", default_limit)),
            "openrouter_llms": int(os.getenv("OPENROUTER_LATEST_LLMS_LIMIT", default_limit)),
            "openrouter_apps": int(os.getenv("OPENROUTER_TRENDING_APPS_LIMIT", default_limit)),
            "product_hunt": int(os.getenv("PRODUCT_HUNT_APPS_LIMIT", default_limit)),
            "hacker_news": int(os.getenv("HACKER_NEWS_POSTS_LIMIT", default_limit)),
        }
        
        # 4. Proxy Configuration
        PROXIES = {}
        for i in range(1, 4):
            val = os.getenv(f"WEBSHARE_PROXY{i}")
            if val:
                # Ensure scheme prefix
                if not (val.startswith("http://") or val.startswith("https://")):
                    val = f"http://{val}"
                PROXIES[i] = val
                
        print(f"[config.py] Loaded environment from {env_path}")
        print(f"[config.py] Project Root: {PROJECT_ROOT}")
        print(f"[config.py] API_DATA_DIR: {API_DATA_DIR}")
        print(f"[config.py] PARSED_DATA_DIR: {PARSED_DATA_DIR}")
    else:
        # Fallback to internal defaults if no .env.local
        API_DATA_DIR = PROJECT_ROOT / "tests/data/api_results/"
        PARSED_DATA_DIR = PROJECT_ROOT / "tests/data/parsed_results/"
        print(f"[config.py] WARNING: .env.local not found at {env_path}. Using internal defaults.")

# Initialize on import
load_config()

def get_proxy(index: int) -> dict:
    """Return a dictionary suitable for requests.get(..., proxies=get_proxy(1))."""
    url = PROXIES.get(index)
    if url:
        return {"http": url, "https": url}
    return {}

if __name__ == "__main__":
    print(f"Project root found at: {PROJECT_ROOT}")
    print(f"Final API_DATA_DIR: {API_DATA_DIR}")
    print(f"Final PARSED_DATA_DIR: {PARSED_DATA_DIR}")
    print(f"Available Proxies: {PROXIES}")

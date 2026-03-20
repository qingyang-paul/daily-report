"""Validation logic for AI-enriched data.

Ensures that all mandatory AI fields (summaries, keywords, overviews) are 
populated and non-empty before final report generation.
"""
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

def is_empty(value: Any) -> bool:
    """Check if a value is effectively empty (None, empty string/list, or whitespace)."""
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, dict)):
        return len(value) == 0
    return False

def validate_section_overview(overview_data: Dict[str, Any], section_name: str) -> List[str]:
    """Validate a SectionOverviewSchema object."""
    errors = []
    if not overview_data:
        errors.append(f"Missing overview data for section: {section_name}")
        return errors
        
    if is_empty(overview_data.get("overview")):
        errors.append(f"Empty 'overview' string in section: {section_name}")
    
    keypoints = overview_data.get("keypoints", [])
    if is_empty(keypoints):
        errors.append(f"Empty 'keypoints' list in section: {section_name}")
    
    return errors

def validate_ai_fields(data: Dict[str, Any]) -> bool:
    """
    Validate all AI-enhanced fields in the prepared email data.
    
    Args:
        data (dict): The data dictionary prepared for template rendering.
        
    Returns:
        bool: True if all fields pass validation, False otherwise.
    """
    errors = []
    
    # 1. Validate Overviews
    overview_sections = [
        "report_overview",
        "github_trending_overview",
        "huggingface_daily_papers_overview",
        "openrouter_latest_llms_overview",
        "openrouter_trending_apps_overview",
        "producthunt_apps_overview",
        "hackernews_post_overview"
    ]
    
    for section in overview_sections:
        section_errors = validate_section_overview(data.get(section), section)
        errors.extend(section_errors)
        
    # 2. Validate Individual Items
    item_sections = [
        "github_trending",
        "huggingface",
        "openrouter_llms",
        "openrouter_apps",
        "product_hunt",
        "hacker_news"
    ]
    
    for section in item_sections:
        items = data.get(section, [])
        if not items:
            logger.warning(f"No items found in section: {section}")
            continue
            
        for i, item in enumerate(items):
            item_id = item.get("id") or item.get("name") or item.get("title") or f"Index {i}"
            
            # Check ai_summary
            if is_empty(item.get("ai_summary")):
                errors.append(f"Missing 'ai_summary' for {section} item: {item_id}")
            
            # Check ai_keywords
            if is_empty(item.get("ai_keywords")):
                errors.append(f"Missing 'ai_keywords' for {section} item: {item_id}")
                
            # Check ai_comment_summary (only for Product Hunt and Hacker News)
            if section in ["product_hunt", "hacker_news"]:
                if is_empty(item.get("ai_comment_summary")):
                    errors.append(f"Missing 'ai_comment_summary' for {section} item: {item_id}")

    if errors:
        logger.error("AI Enrichment Validation Failed:")
        for err in errors:
            logger.error(f"  - {err}")
        return False
        
    logger.info("AI Enrichment Validation Passed.")
    return True

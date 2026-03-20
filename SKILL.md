---
name: daily-ai-trend-generator
description: |
  Automated pipeline to generate AI-related industry trend daily reports. 
  Collects data from GitHub, Hugging Face, OpenRouter, Product Hunt, and Hacker News, 
  and enriches it with AI-driven insights on practical value and commercial potential.
---

# Daily AI Trend Generator

This skill manages the end-to-end process of creating high-value daily reports on AI industry shifts and innovations.

## Core Objective

To produce a curated daily report that synthesizes data from global tech sources, specifically highlighting the commercial impact and practical utility of AI developments.

## Key Data Sources

- **GitHub Trending**: Emerging AI repositories and frameworks.
- **Hugging Face Daily Papers**: Cutting-edge AI research and model drops.
- **OpenRouter**: Latest LLMs and trending AI-powered applications.
- **Product Hunt**: New AI product launches and startup activity.
- **Hacker News**: High-signal technical and industry discussions.

## Execution & Communication Rules

- **Progress Updates**: After each step in the `Standard Workflow` below, the Agent **MUST** notify the user with a brief message explaining:
  - What was just successfully executed.
  - What the next step is and what it will do.
- **Intervention**: This allows the user to monitor progress and intervene if necessary before the next script runs.

## Standard Workflow

### 1. Project Initialization & Environment Check

- Verify that the workspace is correctly configured.
- Ensure all required API keys and path constants are set in `.env.local` (located in the project root).
- Ensure `scripts/core/config.py` is operational for unified path management.

### 2. Data Collection & Transformation

- Execute scripts within the `scripts/` directory to fetch raw data from all enabled sources.
- Scripts generate standardized JSON datasets in the workspace's designated data directories.
- **Primary Tool**: `python scripts/fetch_all.py` (Orchestrates the full fetch-and-parse sequence).

### 3. AI Based Content Enrichment

- **Full Enrichment**: The Agent **MUST** enrich ALL items found within the parsed JSON files. Since the data is already truncated to the limits (defined in `.env.local`) during the parsing stage, every single item in the `parsed_results/` directory is intended for the final report.
- **Explicit File Paths**: Enrichment must be applied to the following files (relative to the configured `PARSED_DATA_DIR`):
  - `github/trending_{period}.json`
  - `huggingface/huggingface_{period}_{timestamp}_parsed.json`
  - `openrouter/openrouter_llms_{timestamp}_parsed.json`
  - `openrouter/openrouter_apps_{timestamp}_parsed.json`
  - `product_hunt/product_hunt_{period}_{timestamp}_parsed.json`
  - `hacker_news/hn_{timeframe}_{timestamp}_parsed.json`
- **Focus**: Practical utility, real-world problems solved, and commercial potential.
- **Constraint**: Do not over-index on technical implementation; prioritize "Industry Trends" and "Business Value".
- **Reference**: Follow the Pydantic models in `scripts/core/schema.py` for exact data structures.

### 4. Enrichment Validation

Before proceeding to overview generation or final reporting, the Agent must verify the integrity of the AI-enhanced data.

- **Integrity Check**: Run `scripts/core/validator.py` (or ensure the logic is invoked) to confirm that no `ai_summary`, `ai_keywords`, or `SectionOverview` fields are empty.
- **Mandatory**: Email generation via `scripts/email_generator.py` will automatically abort if this validation fails.

### 5. Multi-Section Overview Generation

After enriching all individual items, the pipeline generates a high-level summary for each major section and for the entire report.

- **Tooling**: The Agent must synthesize the enriched data into a concise summary (`overview`) and 3 highlight points (`keypoints`) for each section.
- **Data Structure**: Use `OverviewSchema` from `scripts/core/schema.py`.
- **Storage**: Save the generated overview as a JSON file at `{{PARSED_RESULTS_DIR}}/overviews/daily_overview.json`. Ensure the directory exists.
- **Timing**: This occurs after individual item enrichment but before final report generation.

### 6. Report Generation & Email Dispatch

- **Data Preparation**: `scripts/email_generator.py` (via `prepare_email_data`) automatically loads `daily_overview.json` from the `overviews/` directory and passes it to the Jinja2 template.
- **Rendering**: Invoke `scripts/email_generator.py` to synthesize the enriched data and section overviews into a premium HTML report.
- **PDF Conversion**: Use `scripts/pdf_generator.py` to convert the HTML report into a PDF for archiving and attachment.
- **Dispatch**: Send the final report via `scripts/email_sender.py`, which automatically includes the PDF as an attachment.

## Usage Examples

```bash
# Full pipeline sequence
python scripts/fetch_all.py
# (Enrichment step here)
python scripts/email_generator.py
python scripts/pdf_generator.py
python scripts/email_sender.py
```

# Individual section refresh

python scripts/github_trending.py --since daily
python scripts/hacker_news.py --timeframe daily

# Verify system health

python scripts/health_check.py

> [!TIP]
> If health checks fail (usually due to network restrictions), try configuring and activating a proxy before running them again. The system will automatically detect and apply the proxy configuration from `.env.local`.


## Proxy Management
The project supports up to 3 rotating proxies configured via `WEBSHARE_PROXY1/2/3` in `.env.local`.

### Shell Usage

To set proxy environment variables for the current shell session:

```bash
eval $(python scripts/set_proxy.py 1)  # Use proxy 1, 2, or 3
```

### Script Usage

To use proxies within Python scripts:

```python
from scripts.core.config import get_proxy
proxies = get_proxy(1)  # Returns requests-compatible proxy dict
response = requests.get(url, proxies=proxies)
```

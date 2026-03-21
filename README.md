# 📰 Daily AI Insights

**Daily AI Insights** is a highly automated AI industry trend tracking and report generation system. The system fetches data from multiple high-quality information sources daily, utilizes Large Language Models (LLMs) for deep analysis and value extraction, and automatically generates beautiful responsive HTML/PDF reports pushed directly to subscriber emails.

Whether you are tracking cutting-edge papers, viral open-source projects, or the latest large model releases, **Daily AI Insights** provides the most efficient "signal-to-noise" ratio filtering for your information diet.

## ✨ Core Features

- **🌐 Multi-Source Data Aggregation**: Covers code repositories, academic papers, LLM ecosystems, application launches, and geek community hotspots.
- **🧠 Comprehensive AI Enhancement**: We refuse simple machine translations. Every section—and every specific product, paper, or project—includes a dedicated AI-generated summary. By adding industry context and extracting core highlights, we help readers instantly grasp the value of any project.
- **⚡️ Automated Pipeline**: Provides a one-click workflow from data collection and parsing to enrichment and dispatch. Fully embraces `uv` for modern Python environment and dependency management.
- **🎨 Superior Layout & Spatial Efficiency**: Traditional PDF formats are often rigid and poor for displaying dense information. This project directly renders responsive HTML emails based on Jinja2 templates, significantly increasing space utilization and ensuring an elegant, highlighted layout that is ready to read at a glance (with synchronized PDF archiving).

## 📡 Data Source & API Matrix

The system spans five core dimensions of information sources to ensure comprehensive and cutting-edge coverage:

| **Dimension** | **Source**      | **Content Fetched**         | **API / Tech Stack**            |
| ------------- | --------------- | --------------------------- | ------------------------------- |
| **Code**      | GitHub          | Daily Trending Repos        | GitHub REST API / Web Scraper   |
| **Academic**  | Hugging Face    | Daily Hot Papers            | Hugging Face Hub API / Crawler  |
| **Models**    | OpenRouter      | Latest Models & Rankings    | OpenRouter Models API & Scraper |
| **Apps**      | Product Hunt    | Daily New Product Launches  | Product Hunt GraphQL API (V2)   |
| **Community** | Hacker News     | Top Geek Discussions        | Algolia Hacker News API         |

## ⚙️ Overall Workflow

1.  **Initialization (Init)**: Use `uv` to verify the Python environment and dependencies, loading `.env.local` variables.
2.  **Data Collection (Fetch)**: Parallel scheduling of collection scripts for each module to obtain raw JSON data.
3.  **Parsing & Transformation (Parse)**: Clean raw data and map/validate it into a unified Schema defined by `Pydantic`.
4.  **Content Enrichment (Enrichment)**: Invoke AI models (or via deep Agent research) to dig into the potential value of each entry, adding background knowledge and highlighted summaries.
5.  **Global Overview (Overview)**: Synthesize cleaned data to generate a multi-section industry insight report covering critical daily trends.
6.  **Report Generation (Generate)**: Efficiently render high-information-density HTML email templates via Jinja2 and generate high-definition PDF attachments using WeasyPrint.
7.  **Reach & Dispatch (Dispatch)**: Interface with the Resend API to deliver reports accurately to the pre-configured subscriber list.

## 🚀 Project Highlights

- **Skill-Based Architecture & OpenClaw Integration**: Moves away from traditional hard-coded or cumbersome ReAct Agent structures by encapsulating core capabilities into standard "Skills." Paired with **OpenClaw**, it elegantly enables multi-channel interaction (Lark, WhatsApp), scheduled task management, and hot-updates for retrieval configurations.
- **Immersive Native Email Rendering**: For high-density AI briefings, we abandoned a PDF-only route. Using Jinja2 for direct rendering inside email clients ensures clear visual hierarchies in limited space, allowing you to catch all insights and key points with a simple scroll.
- **Official API Priority & Engineering Trade-offs**: Core data sources use official APIs to ensure stability and timeliness. **The project has fully validated technical workflows for Twitter and Reddit data via RapidAPI**; however, due to the ambiguity of third-party nodes and potential instability, we have **purposefully opted out** of these sources in favor of official, compliant data paths.
- **Precise Academic & Model Tracking**:
    - **Academic**: Instead of unselective arXiv scraping, we use Hugging Face Daily Papers (which includes community weighting) to hit high-value research directly.
    - **Models**: Introduced OpenRouter as a primary intelligence source to monitor the industry's latest model modalities, context windows, and performance metrics in real-time.
- **Deep Community Insight**: For Product Hunt and Hacker News, we capture not just the main threads but full **top-voted comments and replies**, giving you instant access to community consensus and points of contention.

## 🛠️ Quick Start

### 1. Configuration

Before running the project, copy or create a `daily-report/.env.local` file in the project root and fill in the following key configurations:

```bash
# Core API Keys
OPENROUTER_API_KEY="your_openrouter_key"
PRODUCT_HUNT_API_KEY="your_ph_key"
RESEND_API_KEY="your_resend_key"

# Email Dispatch Config
RESEND_EMAIL_FROM="Daily Insights <report@yourdomain.com>"
RESEND_EMAIL_TO="recipient1@email.com,recipient2@email.com"

# Network Proxy (Optional, based on environment)
HTTP_PROXY="http://127.0.0.1:xxxx"
HTTPS_PROXY="http://127.0.0.1:xxxx"
```

### 2. Execution Guide

This project recommends using the ultra-fast Python package manager [uv](https://github.com/astral-sh/uv):

```bash
# 1. Sync and install project dependencies
uv sync

# 2. Execute system health check (API connectivity test)
uv run daily-report/scripts/health_check.py

# 3. Run the full workflow
uv run daily-report/scripts/fetch_all.py          # Parallel data collection
# ... (Optional: Run intermediate Parse & Enrichment scripts) ...
uv run daily-report/scripts/email_generator.py    # Generate HTML/PDF report
uv run daily-report/scripts/email_sender.py       # Trigger email delivery
```

## 🗺️ Roadmap

We are continuously optimizing information breadth and compliance. Next steps include:

- [x] **Technical Validation Complete**: Successfully implemented and ran fully automated workflows for Twitter and Reddit trends via RapidAPI (code archived for technical readiness).
- [ ] **Expand Social Media Sources**: Searching for high-quality, compliant official access for Twitter and Reddit.
    - *Reddit*: Following up on official developer API approval.
    - *Twitter*: Evaluating official Enterprise API costs and ROI; avoiding non-official scraping sources to ensure data integrity.

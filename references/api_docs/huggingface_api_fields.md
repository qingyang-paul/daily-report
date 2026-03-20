# Hugging Face Daily Papers API Expected Fields

The raw JSON payload saved by our HuggingfaceParser (located under `api_results/huggingface/list_daily_papers/`) is an array of dictionaries, representing the top papers curated daily on the Hugging Face hub.

## Request Details
- **API Endpoint:** The Python `huggingface_hub` library abstracts the endpoint `GET https://huggingface.co/api/daily_papers`.
- **Parameters:**
  - `date`: The target date in `YYYY-MM-DD` format (e.g., `date=2026-03-20`).
- **Environment Variables:** None required (this specific daily endpoint is public).

The data is serialized directly from the `DailyPaper` objects returned by the `huggingface_hub` library. As a result, it contains an exhaustive set of fields including GitHub repository addresses.

### Fields in the Array Elements (`data[i]`)

- `id` (String): The arXiv ID of the paper (e.g., "2603.17187").
- `title` (String): The title of the paper.
- `authors` (Array of Strings/Objects): The author(s) of the paper, serialized representation of `PaperAuthor` objects.
- `published_at` (String - ISO 8601 DateTime): The originally published time of the paper.
- `source` (String or null): Origin source of the paper.
- `summary` (String): The abstract or summary of the paper.
- `upvotes` (Integer or null): The number of upvotes the paper has received on Hugging Face.
- `discussion_id` (String): Internal ID for the discussion thread on Hugging Face.
- `comments` (Integer): The number of comments on the paper's Hugging Face page.
- `submitted_at` (String - ISO 8601 DateTime): Time when the paper was submitted to the Hugging Face daily list.
- `submitted_by` (String/Object): User who submitted the paper to the platform.
- `ai_summary` (String or null): An AI-generated summary of the paper, if available.
- `ai_keywords` (Array or null): AI-extracted keywords.
- `organization` (String/Object or null): The organization associated with the paper or submitter.
- `project_page` (String or null): URL to the project's official landing page, if set.
- `github_repo` (String or null): **The GitHub repository address associated with the paper.**
- `github_stars` (Integer or null): **Number of stars on the associated GitHub repository.**
- `mediaUrls` (Array of Strings): URLs to media/images associated with the paper in Hugging Face.
- `thumbnail` (String): URL to the thumbnail image for social sharing.
- `isAuthorParticipating` (Boolean): Whether the original authors are participating in the Hub discussion.
- `date` (String - YYYY-MM-DD): The date the daily parsing corresponds to.



### Retained Fields Specification




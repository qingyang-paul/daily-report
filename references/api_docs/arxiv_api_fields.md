# arXiv API Expected Fields

The raw JSON payload saved by our ArxivParser (located under `api_results/arxiv/search/`) is an array of dictionaries representing papers fetched using the `arxiv` Python library. 

## Request Details
- **API Endpoint:** The Python `arxiv` library abstracts the official API located at `https://export.arxiv.org/api/query`.
- **Parameters:**
  - `query`: The search query (e.g., `(cat:cs.AI OR cat:cs.CL OR cat:cs.LG) AND submittedDate:[YYYYMMDDHHMM TO YYYYMMDDHHMM]`).
  - `max_results`: Maximum items to fetch (e.g., `100`).
  - `sortBy`: Sorting criterion (e.g., `arxiv.SortCriterion.SubmittedDate`).
- **Environment Variables:** None required.

Crucially, **we do not truncate fields**—we serialize the entire `arxiv.Result` structure returned by the dataset. This preserves the absolute information boundary supplied by the API.

### Exhaustive Fields in the Array Elements

- `entry_id` (String): The unique URL/identifier for the paper on arXiv.
- `updated` (String - ISO 8601 DateTime): The date and time the paper was last updated.
- `published` (String - ISO 8601 DateTime): The date and time the paper was originally published.
- `title` (String): The original title of the paper.
- `authors` (Array of Strings): Mapped array of author names.
- `summary` (String): The full abstract and summary text.
- `comment` (String): Meta-comments left by the submitter (e.g. "Accepted to CVPR 2026", "10 pages").
- `journal_ref` (String): Journal reference metric, if applicable.
- `doi` (String): Digital Object Identifier for officially published assets.
- `primary_category` (String): The primary arXiv taxonomy label (e.g., "cs.LG").
- `categories` (Array of Strings): Complete list of all applicable sub-categories cross-listed.
- `links` (Array of Objects): Relatonal links representing PDFs, alternate references, etc. Structured organically as dictionaries.
- `pdf_url` (String): A direct URL shortcut to the PDF rendition.
- `_raw` (Dict): The original, completely unadulterated feed parser XML dictionary as fallback.

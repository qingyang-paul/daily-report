# Hacker News Algolia Search API Expected Fields

The raw JSON payload returned by the Hacker News Algolia Search API (located under `api_results/hacker_news/algolia/`) returns a root object containing a `hits` array. We query for hits over a specific time range (yesterday to today).

## Request Details
- **API Endpoint:** `GET https://hn.algolia.com/api/v1/search`
- **Parameters:**
  - `numericFilters`: Specifies the time range (e.g., `created_at_i>{timestamp_threshold}`).
  - `tags`: Filters the type of post (e.g., `story`).
  - `hitsPerPage`: The number of hits to return (e.g., `30`).
- **Environment Variables:** None required.

Each item in the `hits` array contains the full data for a single Hacker News story. The fields provided in each hit are:

### Fields at `hits[i]`

- `objectID` (String): The Algolia object identifier (usually identical to story_id stringified).
- `story_id` (Integer): Unique integer ID of the Hacker News story.
- `title` (String): The title of the story on Hacker News.
- `url` (String): The external URL the story links to.
- `author` (String): The username of the user who submitted the story.
- `points` (Integer): The score (upvotes minus downvotes) of the story.
- `num_comments` (Integer): The number of comments on the story.
- `story_text` (String or null): The text content of the post if it is an "Ask HN" or text submission; otherwise null for link submissions.
- `created_at` (String - ISO 8601 DateTime): When the story was submitted.
- `created_at_i` (Integer - Unix Timestamp): POSIX timestamp for when the story was submitted.
- `updated_at` (String - ISO 8601 DateTime): When the story was last updated.
- `children` (Array of Integers): The IDs of top-level comments for this story.
- `_tags` (Array of Strings): Informational tags set by Algolia (e.g., "story", "author_username", "story_ID").
- `_highlightResult` (Object): Algolia's highlighting metadata containing matching info on `title`, `url`, `author`, etc.

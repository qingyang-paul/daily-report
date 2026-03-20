# GitHub Trending Expected Fields (HTML Extraction)

The raw response saved by our GithubTrendingParser (located under `api_results/github/trending/`) is the raw HTML page returned by `https://github.com/trending/*`. Since GitHub does not offer an official trending API, we document the structural elements that can be extracted from each repository `<article class="Box-row">`.

## Request Details

- **API Endpoint:** `GET https://github.com/trending/{language}`
- **Parameters:**
  - `since`: The timeframe for trending (e.g., `daily`, `weekly`, `monthly`).
- **Environment Variables:** None required.

### Extracted/Available Entities in HTML

- **Repository Name and Link**: Found within an `<h2 class="h3">` containing an `<a href="/owner/repo">`. This yields both the relative URL and the owner/repo string.
- **Description**: Found within a `<p class="col-9 color-fg-muted my-1 pr-4">`. It contains the short project summary.
- **Primary Language**: Found within `<span itemprop="programmingLanguage">`. e.g., "Python", "TypeScript".
- **Total Stars**: Found in an `<a>` tag mapping to `/owner/repo/stargazers`. Represents the total stars the repo has accumulated.
- **Total Forks**: Found in an `<a>` tag mapping to `/owner/repo/forks`. Represents the total network forks.
- **Built By (Contributors)**: Found within a `<span>` containing multiple `<img class="avatar">` tags wrapped in links pointing to user profiles.
- **Trend Count / Period Stars**: Found in a `<span class="d-inline-block float-sm-right">` containing text such as "X stars today" or "X stars this week". This is the trending metric.

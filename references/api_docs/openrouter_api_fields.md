# OpenRouter Models API Expected Fields

The raw JSON payload returned by the OpenRouter Models API returns a root object containing a `data` array. We query this endpoint to get the latest available models on the OpenRouter platform.

## Request Details

- **API Endpoint:** `GET https://openrouter.ai/api/v1/models`
- **Parameters:** None
- **Environment Variables:** None required for public model listing.

Each item in the `data` array contains the full data for a single OpenRouter model. The main fields provided in each model object are:

### Fields at `data[i]`

- `id` (String): Unique identifier/slug of the model.
- `name` (String): Display name of the model, usually formatted as "Provider: Model Name".
- `created` (Integer): Unix timestamp indicating when the model was added to OpenRouter. We sort by this field in descending order to get the newest models.
- `description` (String): A description of the model's capabilities, parameters, and intended use cases.
- `context_length` (Integer): The maximum context window size in tokens.
- `architecture` (Object): Details about the model's architecture.
  - `modality` (String): The supported input and output modalities, e.g., `"text+image+audio+video->text"`.
- `pricing` (Object): Pricing details per token in USD.
  - `prompt` (String): Price for input tokens. Multiplying by 1,000,000 gives the price per 1M input tokens.
  - `completion` (String): Price for output tokens. Multiplying by 1,000,000 gives the price per 1M output tokens.

---

## OpenRouter Apps Trends

For the App Trends (Trending and Global Rankings), OpenRouter does not provide a public API endpoint. Instead, the data is embedded within the Next.js static HTML payload retrieved directly from the /apps page.

### Apps Request Details

- **Page Endpoint:** `GET https://openrouter.ai/apps`
- **Method:** HTML Parsing using BeautifulSoup
- **Environment Variables:** None required.

The script fetches the raw HTML page, parses the `a` tags containing `href="/apps?url=..."`, and extracts the top 20 applications categorized under the Global Ranking based on the item index.

### Extracted Fields

- `name` (String): The name of the application.
- `desc` (String): A short description of the application.
- `app_url` (String): The direct URL to the application (extracted from `href="/apps?url=..."`).
- `avatar_url` (String): The application's icon/avatar URL (often fetched via Google's Favicon service based on the target URL).
- `tokens` (String): The total volume of tokens processed by the app (e.g., "12.5T tokens").

**Section-Specific Fields:**

- `rank` (Integer): Only available in the **Global Ranking** section (1 to 20).
- `tag` (String): Only available in the **Global Ranking** section (e.g., Roleplay, Cloud Agents).
- `growth` (String): Only available in the **Trending** section (e.g., "+69%").

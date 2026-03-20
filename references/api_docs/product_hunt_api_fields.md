# Product Hunt GraphQL API Expected Fields

The raw JSON payload returned by our Product Hunt GraphQL API call (located under `api_results/product_hunt/graphql/`) includes a highly detailed nested structure to prevent truncation and maintain information boundaries. We query for the top posts of the previous day, requesting all available post metrics and relationships.

## Request Details
- **API Endpoint:** `POST https://api.producthunt.com/v2/api/graphql`
- **Parameters:**
  - `query`: The GraphQL query string (e.g., `query ($postedAfter: DateTime, $postedBefore: DateTime) { posts(...) ... }`).
  - `variables`: A JSON object with the query variables (e.g., `{"postedAfter": "2026-03-20T00:00:00Z"}`).
- **Headers:** 
  - `Authorization: Bearer <TOKEN>`
- **Environment Variables:** 
  - `Product_Hunt_Developer_Token` (Required for the Authorization Header. Expected to be loaded from `.env.local`).

Structure: `data` -> `posts` -> `edges` -> array of objects containing `node`

Each `node` object contains the full extracted data for a single post. The fields provided in each node are:

### Fields at `data.posts.edges[i].node`

- `id` (String): Unique identifier for the Product Hunt post.
- `name` (String): The name of the product.
- `tagline` (String): A short pitch or tagline.
- `description` (String): Detailed product description.
- `votesCount` (Integer): Total upvotes based on the ranking algorithm.
- `commentsCount` (Integer): Total comments on the post.
- `url` (String): URL to the post on Product Hunt.
- `website` (String): The direct URL to the product's external website.
- `createdAt` (String - ISO 8601): Timestamp of creation.
- `featuredAt` (String - ISO 8601): Timestamp of feature placement.
- `dailyRank` (Integer): Daily ranking position.
- `weeklyRank` (Integer): Weekly ranking position.
- `monthlyRank` (Integer): Monthly ranking position.
- `yearlyRank` (Integer): Yearly ranking position.
- `slug` (String): The URL-friendly identifier string.
- `reviewsCount` (Integer): Number of user reviews.
- `reviewsRating` (Float): Average user review rating.
- `isCollected` (Boolean): Status indicator.
- `isVoted` (Boolean): User vote status indicator.

#### Relationships

- `makers` (Array of Users): A list of the product creators containing `id, name, username, profileImage, twitterUsername, websiteUrl, followersCount, followingCount, headline`.
- `user` (User Object): The profile of the submitter with the same fields as the makers above.
- `media` (Array of Media Objects): Detailed assets containing `type, url, videoUrl`.
- `thumbnail` (Media Object): The asset corresponding to the product thumbnail `type, url, videoUrl`.
- `productLinks` (Array of Links): Additional destination URLs containing `type, url`.
- `topics` (Object): A nested connection for tags/categories. Sub-node fields include `id, name, description, slug, followersCount`.

This represents the maximum boundary of information we explicitly extract from the ProductHunt GraphQL API layer without manually truncating essential meta-features.

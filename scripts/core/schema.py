"""Data schemas and Pydantic models for the Daily Info project.

Defines the structure of objects fetched from various APIs (GitHub, HN, HF, etc.)
to ensure data consistency across the pipelines.
"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class HuggingFacePaperSchema(BaseModel):
    id: str
    title: str
    upvotes: int
    comments: int
    authors: List[str]
    organization_name: Optional[str] = None
    organization_avatar: Optional[str] = None
    summary: str
    published_at: datetime
    github_url: Optional[str] = None
    github_stars: Optional[int] = None
    ai_keywords: List[str] = Field(default_factory=list)
    ai_summary: str = ""

class ArxivPaperSchema(BaseModel):
    id: str
    comment: Optional[str] = None
    primary_category: str
    categories: List[str]

class ReportPaperSchema(BaseModel):
    id: str
    title: str
    upvotes: int
    comments: int
    organizations: List[str]
    authors: List[str]
    summary: str
    published_at: datetime
    categories: List[str]
    github_url: str
    github_stars: Optional[int] = None

class GithubTrendingSchema(BaseModel):
    owner: str
    name: str
    url: str
    description: str
    language: str
    stars: int
    forks: int
    stars_today: int
    growth_rate: float
    built_by: List[str] = Field(default_factory=list)
    ai_keywords: List[str] = Field(default_factory=list)
    ai_summary: str = ""

class OpenRouterLLMSchema(BaseModel):
    owner: str
    name: str
    canonical_slug: str
    created: datetime
    description: Optional[str] = None
    context_length: int
    modality: str
    prompt_pricing: float
    completion_pricing: float
    ai_keywords: List[str] = Field(default_factory=list)
    ai_summary: str = ""

class OpenRouterAppTrendSchema(BaseModel):
    name: str
    description: str
    app_url: str
    avatar_url: str
    token_usage: str
    growth_rate: str
    ai_keywords: List[str] = Field(default_factory=list)
    ai_summary: str = ""

class OpenRouterAppRankSchema(BaseModel):
    name: str
    description: str
    app_url: str
    avatar_url: str
    token_usage: str
    rank: int
    tags: List[str]
    growth_rate: str

class CommentSchema(BaseModel):
    comment: str
    reply: str

class ProductHuntAppSchema(BaseModel):
    name: str
    tagline: str
    votesCount: int
    commentsCount: int
    tags: List[str]
    comments: List[CommentSchema]
    product_hunt_page: str
    product_official_website: Optional[str] = None
    avatar_url: Optional[str] = None
    launched_at: datetime
    ai_keywords: List[str] = Field(default_factory=list)
    ai_summary: str = ""
    ai_comment_summary: List[str] = Field(default_factory=list)

class HackerNewsStorySchema(BaseModel):
    title: str
    url: Optional[str] = None
    story_text: Optional[str] = None
    author: str
    points: int
    num_comments: int
    objectID: str
    comments: List[CommentSchema]
    created_at: datetime
    ai_keywords: List[str] = Field(default_factory=list)
    ai_summary: str = ""
    ai_comment_summary: List[str] = Field(default_factory=list)

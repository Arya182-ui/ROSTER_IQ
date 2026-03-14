"""Tavily-backed web search utilities for external operational context."""

from __future__ import annotations

import os
import re
from typing import Any


SEARCH_CONTEXT_KEYWORDS = (
    "regulation",
    "regulations",
    "cms",
    "compliance",
    "provider organization",
    "provider organizations",
    "validation failure",
    "validation failures",
    "data standard",
    "data standards",
)


def needs_search_context(query: str) -> bool:
    """Return whether a query likely needs external web context."""

    normalized = query.strip().lower()
    return any(keyword in normalized for keyword in SEARCH_CONTEXT_KEYWORDS)


def _build_client(api_key: str):
    """Return a Tavily client or raise a descriptive dependency error."""

    try:
        from tavily import TavilyClient
    except ImportError as exc:
        raise RuntimeError("tavily-python is not installed.") from exc

    return TavilyClient(api_key=api_key)


def _summarize_results(results: list[dict[str, Any]]) -> str:
    """Create a short context summary from the top search results."""

    snippets: list[str] = []
    for item in results[:3]:
        content = str(item.get("snippet", item.get("content", "")) or "").strip()
        if not content:
            continue
        first_sentence = re.split(r"(?<=[.!?])\s+", content)[0].strip()
        if first_sentence:
            snippets.append(first_sentence)
    if not snippets:
        return "No relevant external operational context was found."
    return " ".join(snippets[:2])


def search_web(query: str, max_results: int = 5) -> dict[str, Any]:
    """Run a Tavily search and return a simplified result payload."""

    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return {
            "query": query,
            "results": [],
            "error": "TAVILY_API_KEY not configured",
        }

    client = _build_client(api_key)
    response = client.search(query=query, max_results=max_results)
    results = response.get("results", [])

    return {
        "query": query,
        "results": [
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": item.get("snippet", item.get("content", "")),
            }
            for item in results
        ],
    }


def search_context(query: str) -> dict[str, Any]:
    """Return condensed operational web context for the given query."""

    raw_result = search_web(query=query, max_results=3)
    if raw_result.get("error"):
        return {
            "query": query,
            "context_summary": raw_result["error"],
            "sources": [],
            "results": [],
        }

    top_results = raw_result.get("results", [])[:3]
    normalized_results = [
        {
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "snippet": item.get("snippet", ""),
        }
        for item in top_results
    ]
    return {
        "query": query,
        "context_summary": _summarize_results(top_results),
        "sources": [
            {"title": item.get("title", ""), "url": item.get("url", "")}
            for item in top_results
        ],
        "results": normalized_results,
    }

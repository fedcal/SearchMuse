"""Prompt templates for the Ollama LLM adapter.

All constants are plain strings with {placeholders} for .format() substitution.
No f-strings are used here; formatting is deferred to the adapter at call time.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Chat context section (injected into strategy prompt when available)
# ---------------------------------------------------------------------------

CONTEXT_SECTION: str = """
PREVIOUS RESEARCH IN THIS CONVERSATION:
{context_entries}

Use this prior research to avoid repeating work and to build on previous findings.
"""

# ---------------------------------------------------------------------------
# Strategy generation
# ---------------------------------------------------------------------------

STRATEGY_PROMPT: str = """You are a research assistant helping to find high-quality information
on the web. Your task is to generate an effective search strategy for the query below.

QUERY: {query}
{context_block}
PREVIOUS ITERATION SUMMARIES:
{previous_summaries}

Based on the query and what has already been searched, generate:
1. A list of specific search terms (2-6 terms) that are likely to surface relevant pages.
   Prefer precise, varied phrasings over generic keywords.
2. A list of target domains (0-4 entries) to restrict results to trustworthy sources.
   Leave empty if no domain restriction is appropriate.
3. A brief reasoning explaining why these terms and domains were chosen.

Avoid repeating search terms or domains used in previous iterations.

Respond with ONLY a valid JSON object — no markdown fences, no extra text:
{{
  "search_terms": ["term one", "term two"],
  "target_domains": ["example.com", "trusted.org"],
  "reasoning": "Explanation of strategy choices."
}}"""


# ---------------------------------------------------------------------------
# Content relevance assessment
# ---------------------------------------------------------------------------

RELEVANCE_PROMPT: str = """You are a relevance assessor. Read the content excerpt below and
decide how relevant it is to the given query.

QUERY: {query}

CONTENT TITLE: {title}
CONTENT URL: {url}
CONTENT EXCERPT (up to 2000 words):
{content_text}

Relevance levels:
- "high"       : Directly answers the query with substantial detail.
- "medium"     : Partially relevant; provides useful context or supporting information.
- "low"        : Tangentially related; minimal direct usefulness to the query.
- "irrelevant" : Off-topic; does not address the query in any meaningful way.

Respond with ONLY a valid JSON object — no markdown fences, no extra text:
{{
  "relevance": "high" | "medium" | "low" | "irrelevant"
}}"""


# ---------------------------------------------------------------------------
# Coverage assessment
# ---------------------------------------------------------------------------

COVERAGE_PROMPT: str = """You are a research coverage analyst. Evaluate how well the sources
collected so far answer the query, then identify any remaining gaps.

QUERY: {query}

SOURCES COLLECTED ({source_count} total):
{source_summaries}

A coverage score of 1.0 means the query is fully and comprehensively answered.
A score of 0.0 means no useful information has been found yet.

Respond with ONLY a valid JSON object — no markdown fences, no extra text:
{{
  "coverage_score": 0.75,
  "assessment": "The sources cover X and Y well, but lack detail on Z and W."
}}"""


# ---------------------------------------------------------------------------
# Answer synthesis
# ---------------------------------------------------------------------------

SYNTHESIS_PROMPT: str = """You are a research synthesis expert. Write a comprehensive,
well-structured answer to the query below using ONLY the provided sources.

QUERY: {query}

SOURCES ({source_count} total):
{source_details}

Instructions:
- Cite each source inline using its bracketed index, e.g. [1], [2], [3].
- Cover all major aspects of the query that the sources support.
- Be factual and objective; do not introduce information absent from the sources.
- Use clear paragraphs; avoid bullet lists unless the content is inherently list-like.
- If sources contradict each other, acknowledge the disagreement explicitly.
- Do NOT include a reference list at the end; inline citations are sufficient.

Write your answer as plain text below (no JSON, no markdown headers):"""

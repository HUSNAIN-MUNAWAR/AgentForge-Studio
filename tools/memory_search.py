from __future__ import annotations
import re
from collections import Counter
from tools.base import BaseTool


class MemorySearchTool(BaseTool):
    name = "memory.search"
    description = "Search indexed project memory chunks using simple keyword scoring."
    risk_level = "low"
    input_schema = {"type": "object", "properties": {"query": {"type": "string"}, "memory_corpus": {"type": "array"}}}
    output_schema = {"type": "object", "properties": {"results": {"type": "array"}, "query": {"type": "string"}}}

    def execute(self, tool_input: dict) -> dict:
        query = str(tool_input.get("query", "")).strip()
        corpus = tool_input.get("memory_corpus") or []
        q_tokens = _tokens(query)
        scored = []
        for item in corpus:
            text = str(item.get("text", ""))
            token_counts = Counter(_tokens(text))
            score = sum(token_counts[t] for t in q_tokens)
            if query and query.lower() in text.lower():
                score += 5
            if score > 0 or not query:
                scored.append({
                    "score": score,
                    "document_id": item.get("document_id"),
                    "chunk_id": item.get("chunk_id"),
                    "title": item.get("title"),
                    "snippet": text[:700],
                    "metadata": item.get("metadata", {}),
                })
        scored.sort(key=lambda x: x["score"], reverse=True)
        return {"query": query, "results": scored[: int(tool_input.get("limit", 5) or 5)], "engine": "keyword"}


def _tokens(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-zA-Z0-9_]{3,}", text.lower()) if t not in {"the", "and", "for", "with"}]

"""Semantic-memory loader for domain knowledge used by the RosterIQ agent."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path


SEMANTIC_MEMORY_PATH = Path(__file__).resolve().parent / "semantic_memory.json"


@lru_cache(maxsize=1)
def load_semantic_memory() -> dict[str, str]:
    """Load semantic memory definitions from the JSON knowledge store."""

    with SEMANTIC_MEMORY_PATH.open("r", encoding="utf-8-sig") as semantic_file:
        return json.load(semantic_file)



def get_definition(term: str) -> str | None:
    """Return the semantic definition for a pipeline term when available."""

    memory = load_semantic_memory()
    if term in memory:
        return memory[term]
    normalized = term.strip().upper()
    return memory.get(normalized)

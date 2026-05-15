import json
import re
import os
from functools import lru_cache
from pathlib import Path
from typing import Any
from rank_bm25 import BM25Okapi
import chromadb
from sentence_transformers import SentenceTransformer
from app.core.config import settings


BASE_DIR = Path(__file__).resolve().parent
KNOWLEDGE_BASE_PATH = BASE_DIR / "knowledge_base.json"
CHROMA_DIR = BASE_DIR / ".chroma"
COLLECTION_NAME = "medhelp_symptom_specialists"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

def _configure_huggingface_token() -> None:
    """
    Makes the Hugging Face token from settings available to huggingface_hub.

    settings.HF_TOKEN reads from .env, but Hugging Face libraries check
    os.environ["HF_TOKEN"]. This bridges the two.
    """
    hf_token = getattr(settings, "HF_TOKEN", "") or ""

    if hf_token.strip():
        os.environ.setdefault("HF_TOKEN", hf_token.strip())


def _tokenize(text: str) -> list[str]:
    """
    Simple tokenizer for BM25.
    Keeps only lowercase words/numbers.
    """
    return re.findall(r"[a-zA-Z0-9]+", text.lower())


@lru_cache(maxsize=1)
def load_knowledge_base() -> list[dict[str, Any]]:
    """
    Loads symptom-specialist knowledge base from JSON.
    Cached so it is not read from disk every request.
    """
    with open(KNOWLEDGE_BASE_PATH, "r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("knowledge_base.json must contain a list of entries")

    required = {"id", "symptoms", "specialist", "reason", "urgency", "red_flags"}

    for entry in data:
        missing = required - set(entry.keys())
        if missing:
            raise ValueError(f"Knowledge base entry missing fields: {missing}")

    return data


@lru_cache(maxsize=1)
def _get_bm25_index():
    """
    Creates BM25 index over the local knowledge base.
    If rank-bm25 is not installed, returns None and fallback scoring is used.
    """
    entries = load_knowledge_base()

    corpus_tokens = [
        _tokenize(
            f"{entry['symptoms']} {entry['specialist']} {entry['reason']} {entry['red_flags']}"
        )
        for entry in entries
    ]

    if BM25Okapi is None:
        return None, entries, corpus_tokens

    return BM25Okapi(corpus_tokens), entries, corpus_tokens


def _fallback_keyword_scores(query: str, entries: list[dict[str, Any]]) -> list[tuple[float, dict[str, Any]]]:
    """
    Fallback lexical search if rank-bm25 is not installed.
    """
    query_tokens = set(_tokenize(query))
    scored = []

    for entry in entries:
        entry_tokens = set(
            _tokenize(
                f"{entry['symptoms']} {entry['specialist']} {entry['reason']} {entry['red_flags']}"
            )
        )
        score = len(query_tokens.intersection(entry_tokens))
        scored.append((float(score), entry))

    scored.sort(key=lambda item: item[0], reverse=True)
    return scored


def _bm25_rank(query: str, limit: int = 8) -> list[dict[str, Any]]:
    """
    Returns top BM25/keyword matches.
    """
    bm25, entries, _ = _get_bm25_index()

    if bm25 is None:
        scored = _fallback_keyword_scores(query, entries)
        return [entry for score, entry in scored[:limit] if score > 0]

    query_tokens = _tokenize(query)
    scores = bm25.get_scores(query_tokens)

    ranked_indexes = sorted(
        range(len(scores)),
        key=lambda index: scores[index],
        reverse=True
    )

    results = []
    for index in ranked_indexes[:limit]:
        if scores[index] <= 0:
            continue
        results.append(entries[index])

    return results


@lru_cache(maxsize=1)
def _get_vector_store():
    """
    Creates or loads local ChromaDB collection.

    If chromadb or sentence-transformers is not installed,
    returns (None, None), and vector search is skipped.
    """
    if chromadb is None or SentenceTransformer is None:
        return None, None

    entries = load_knowledge_base()

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    _configure_huggingface_token()
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    ids = [entry["id"] for entry in entries]
    documents = [entry["symptoms"] for entry in entries]
    metadatas = [
        {
            "entry_id": entry["id"],
            "specialist": entry["specialist"],
            "reason": entry["reason"],
            "urgency": entry["urgency"],
            "red_flags": entry["red_flags"],
        }
        for entry in entries
    ]


    if collection.count() == 0:
        embeddings = model.encode(documents).tolist()
        collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
        )

    return collection, model


def _vector_rank(query: str, limit: int = 8) -> list[dict[str, Any]]:
    """
    Returns top semantic matches using ChromaDB + sentence-transformers.
    If anything fails, returns empty list so BM25 still works.
    """
    try:
        collection, model = _get_vector_store()

        if collection is None or model is None:
            return []

        entries_by_id = {
            entry["id"]: entry
            for entry in load_knowledge_base()
        }

        query_embedding = model.encode(query).tolist()

        result = collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
        )

        ids = result.get("ids", [[]])[0]

        matches = []
        for entry_id in ids:
            entry = entries_by_id.get(entry_id)
            if entry:
                matches.append(entry)

        return matches

    except Exception:
        # Do not break chatbot if vector search has a package/model issue.
        return []


def hybrid_search(query: str, top_k: int = 3) -> list[dict[str, Any]]:
    """
    Hybrid search:
    1. BM25 keyword search
    2. Vector semantic search
    3. Reciprocal Rank Fusion

    Returns top symptom-specialist knowledge base entries.
    """
    if not query or not query.strip():
        return []

    bm25_results = _bm25_rank(query, limit=8)
    vector_results = _vector_rank(query, limit=8)

    scores: dict[str, float] = {}
    entries_by_id: dict[str, dict[str, Any]] = {}

    # Reciprocal Rank Fusion constant
    k = 60

    for rank, entry in enumerate(bm25_results, start=1):
        entry_id = entry["id"]
        scores[entry_id] = scores.get(entry_id, 0.0) + 1.0 / (k + rank)
        entries_by_id[entry_id] = entry

    for rank, entry in enumerate(vector_results, start=1):
        entry_id = entry["id"]
        scores[entry_id] = scores.get(entry_id, 0.0) + 1.0 / (k + rank)
        entries_by_id[entry_id] = entry

    ranked_ids = sorted(
        scores.keys(),
        key=lambda entry_id: scores[entry_id],
        reverse=True
    )

    results = []
    for entry_id in ranked_ids[:top_k]:
        entry = dict(entries_by_id[entry_id])
        entry["rag_score"] = round(scores[entry_id], 5)
        results.append(entry)

    return results


def format_rag_context(results: list[dict[str, Any]]) -> str:
    """
    Converts RAG results into a compact prompt context for the LLM.
    """
    if not results:
        return ""

    lines = [
        "Medical knowledge base context:",
        "Use this context to recommend the most appropriate specialist.",
        "Do not diagnose. If urgency is emergency, advise immediate emergency care first.",
        "",
    ]

    for index, entry in enumerate(results, start=1):
        lines.append(f"{index}. Matching symptom pattern: {entry['symptoms']}")
        lines.append(f"   Suggested specialist: {entry['specialist']}")
        lines.append(f"   Reason: {entry['reason']}")
        lines.append(f"   Urgency: {entry['urgency']}")
        lines.append(f"   Red flags: {entry['red_flags']}")
        lines.append("")

    return "\n".join(lines).strip()
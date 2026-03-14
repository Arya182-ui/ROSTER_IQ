"""Firestore-backed episodic memory utilities for RosterIQ."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from backend.data_engine.data_engine import get_failed_ros, get_stuck_ros


QUERY_COLLECTION_NAME = "rosteriq_queries"
INVESTIGATION_COLLECTION_NAME = "rosteriq_investigations"
TOKEN_URI = "https://oauth2.googleapis.com/token"
AUTH_URI = "https://accounts.google.com/o/oauth2/auth"
AUTH_PROVIDER_CERT_URL = "https://www.googleapis.com/oauth2/v1/certs"
LOCAL_MEMORY_PATH = Path(__file__).resolve().parent / "episodic_memory_local.json"


def _now_iso() -> str:
    """Return an ISO timestamp for local-memory records."""

    return datetime.now(timezone.utc).isoformat()


def _read_local_memory() -> dict[str, list[dict[str, Any]]]:
    """Load local episodic memory from disk when Firestore is unavailable."""

    if not LOCAL_MEMORY_PATH.exists():
        return {"queries": [], "investigations": []}

    try:
        payload = json.loads(LOCAL_MEMORY_PATH.read_text(encoding="utf-8"))
        queries = payload.get("queries", []) if isinstance(payload, dict) else []
        investigations = payload.get("investigations", []) if isinstance(payload, dict) else []
        return {
            "queries": queries if isinstance(queries, list) else [],
            "investigations": investigations if isinstance(investigations, list) else [],
        }
    except Exception:
        return {"queries": [], "investigations": []}


def _write_local_memory(payload: dict[str, list[dict[str, Any]]]) -> None:
    """Persist local episodic memory payload safely."""

    LOCAL_MEMORY_PATH.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")


def _firebase_enabled() -> bool:
    """Return whether Firebase credentials are present and usable."""

    required = [
        os.getenv("FIREBASE_PROJECT_ID"),
        os.getenv("FIREBASE_CLIENT_EMAIL"),
        os.getenv("FIREBASE_PRIVATE_KEY"),
    ]
    return all(required)


def _sort_recent(records: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    """Sort records by created timestamp descending with defensive parsing."""

    def _sort_key(record: dict[str, Any]) -> str:
        value = record.get("created_at")
        if isinstance(value, str):
            return value
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return ""

    ranked = sorted(records, key=_sort_key, reverse=True)
    return ranked[:limit]


def _firebase_modules():
    """Import Firebase Admin modules lazily so the backend can boot without them."""

    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
    except ImportError as exc:
        raise RuntimeError("firebase-admin is not installed.") from exc
    return firebase_admin, credentials, firestore


def _service_account_info() -> dict[str, str]:
    """Build Firebase service-account credentials from environment variables."""

    project_id = os.getenv("FIREBASE_PROJECT_ID")
    client_email = os.getenv("FIREBASE_CLIENT_EMAIL")
    private_key = os.getenv("FIREBASE_PRIVATE_KEY")

    missing = [
        name
        for name, value in [
            ("FIREBASE_PROJECT_ID", project_id),
            ("FIREBASE_CLIENT_EMAIL", client_email),
            ("FIREBASE_PRIVATE_KEY", private_key),
        ]
        if not value
    ]
    if missing:
        missing_list = ", ".join(missing)
        raise RuntimeError(f"Firebase not configured. Missing: {missing_list}")

    return {
        "type": "service_account",
        "project_id": project_id,
        "client_email": client_email,
        "private_key": private_key.replace("\\n", "\n"),
        "token_uri": TOKEN_URI,
        "auth_uri": AUTH_URI,
        "auth_provider_x509_cert_url": AUTH_PROVIDER_CERT_URL,
    }


def _initialize_app():
    """Initialize Firebase Admin once and return the active app."""

    firebase_admin, credentials, _ = _firebase_modules()

    try:
        return firebase_admin.get_app()
    except ValueError:
        project_id = os.getenv("FIREBASE_PROJECT_ID")
        cred = credentials.Certificate(_service_account_info())
        return firebase_admin.initialize_app(
            cred,
            options={"projectId": project_id},
        )


def _get_client():
    """Return a Firestore client for the configured Firebase project."""

    _, _, firestore = _firebase_modules()
    _initialize_app()
    return firestore.client()


def _state_from_text(text: str) -> str | None:
    """Extract a two-letter state code from free-form text when present."""

    if not text:
        return None

    context_match = re.search(
        r"\b(?:in|for|state|market)\s+([A-Za-z]{2})\b",
        text,
        flags=re.IGNORECASE,
    )
    if context_match:
        return context_match.group(1).upper()

    trailing_match = re.search(r"\b([A-Za-z]{2})\s+market\b", text, flags=re.IGNORECASE)
    if trailing_match:
        return trailing_match.group(1).upper()

    return None


def _safe_summary_dict(result_summary: Any) -> dict[str, Any]:
    """Normalize saved investigation summaries to Firestore-safe mappings."""

    if isinstance(result_summary, dict):
        return result_summary
    return {"text": str(result_summary)}


def _recent_investigation_docs(limit: int = 50) -> list[dict[str, Any]]:
    """Return recent investigation records ordered by creation time."""

    if _firebase_enabled():
        try:
            _, _, firestore = _firebase_modules()
            stream = (
                _get_client()
                .collection(INVESTIGATION_COLLECTION_NAME)
                .order_by("created_at", direction=firestore.Query.DESCENDING)
                .limit(limit)
                .stream()
            )
            records: list[dict[str, Any]] = []
            for doc in stream:
                payload = doc.to_dict() or {}
                payload["id"] = doc.id
                records.append(payload)
            return records
        except Exception:
            pass

    local_payload = _read_local_memory()
    investigations = local_payload.get("investigations", [])
    return _sort_recent(investigations, limit)


def save_query(query: str, response: str) -> str:
    """Persist a query-response pair into Firestore episodic memory."""

    document = {
        "query": query,
        "response": response,
        "created_at": datetime.now(timezone.utc),
    }
    if _firebase_enabled():
        try:
            doc_ref = _get_client().collection(QUERY_COLLECTION_NAME).document()
            doc_ref.set(document)
            return doc_ref.id
        except Exception:
            pass

    payload = _read_local_memory()
    local_id = str(uuid4())
    payload["queries"].append(
        {
            "id": local_id,
            "query": query,
            "response": response,
            "created_at": _now_iso(),
        }
    )
    _write_local_memory(payload)
    return local_id


def get_recent_queries(limit: int = 10) -> list[dict[str, Any]]:
    """Return the most recent saved query-response pairs from Firestore."""

    if _firebase_enabled():
        try:
            _, _, firestore = _firebase_modules()
            query_stream = (
                _get_client()
                .collection(QUERY_COLLECTION_NAME)
                .order_by("created_at", direction=firestore.Query.DESCENDING)
                .limit(limit)
                .stream()
            )
            results = []
            for doc in query_stream:
                payload = doc.to_dict()
                payload["id"] = doc.id
                results.append(payload)
            return results
        except Exception:
            pass

    payload = _read_local_memory()
    return _sort_recent(payload.get("queries", []), limit)


def save_investigation(query: str, tool_used: str, result_summary: Any) -> str:
    """Persist a structured investigation summary for later trend comparison."""

    summary = _safe_summary_dict(result_summary)
    state = summary.get("state") or summary.get("market") or _state_from_text(query)
    document = {
        "query": query,
        "query_type": tool_used,
        "tool_used": tool_used,
        "state": state,
        "result_summary": summary,
        "created_at": datetime.now(timezone.utc),
    }
    if _firebase_enabled():
        try:
            doc_ref = _get_client().collection(INVESTIGATION_COLLECTION_NAME).document()
            doc_ref.set(document)
            return doc_ref.id
        except Exception:
            pass

    payload = _read_local_memory()
    local_id = str(uuid4())
    payload["investigations"].append(
        {
            "id": local_id,
            "query": query,
            "query_type": tool_used,
            "tool_used": tool_used,
            "state": state,
            "result_summary": summary,
            "created_at": _now_iso(),
        }
    )
    _write_local_memory(payload)
    return local_id


def get_recent_investigations(limit: int = 10) -> list[dict[str, Any]]:
    """Return recent investigation summaries for UI history views."""

    return _recent_investigation_docs(limit=limit)


def get_previous_investigations(query_type: str) -> list[dict[str, Any]]:
    """Return recent investigations for the same query type."""

    return [
        record
        for record in _recent_investigation_docs(limit=50)
        if record.get("query_type") == query_type
    ][:5]


def compare_state_changes(state: str) -> dict[str, Any]:
    """Compare the current operational state against the most recent saved investigation."""

    normalized_state = (state or "").upper()
    current_stuck_ros = int(len(get_stuck_ros().loc[lambda df: df["CNT_STATE"].fillna("").eq(normalized_state)]))
    current_failed_ros = int(len(get_failed_ros().loc[lambda df: df["CNT_STATE"].fillna("").eq(normalized_state)]))

    previous_records = [
        record
        for record in _recent_investigation_docs(limit=50)
        if str(record.get("state", "")).upper() == normalized_state
    ]
    if not previous_records:
        return {
            "state": normalized_state,
            "previous_stuck_ros": None,
            "current_stuck_ros": current_stuck_ros,
            "previous_failed_ros": None,
            "current_failed_ros": current_failed_ros,
            "change": "no_history",
        }

    previous_summary = previous_records[0].get("result_summary", {}) or {}
    previous_stuck_ros = previous_summary.get("stuck_ros")
    previous_failed_ros = previous_summary.get("failed_ros")

    delta_stuck = None if previous_stuck_ros is None else current_stuck_ros - int(previous_stuck_ros)
    delta_failed = None if previous_failed_ros is None else current_failed_ros - int(previous_failed_ros)

    comparable_deltas = [delta for delta in [delta_stuck, delta_failed] if delta is not None]
    if not comparable_deltas:
        change = "no_history"
    elif any(delta < 0 for delta in comparable_deltas) and not any(delta > 0 for delta in comparable_deltas):
        change = "improved"
    elif any(delta > 0 for delta in comparable_deltas) and not any(delta < 0 for delta in comparable_deltas):
        change = "regressed"
    else:
        change = "mixed"

    return {
        "state": normalized_state,
        "previous_stuck_ros": previous_stuck_ros,
        "current_stuck_ros": current_stuck_ros,
        "previous_failed_ros": previous_failed_ros,
        "current_failed_ros": current_failed_ros,
        "change": change,
    }


def get_memory_backend_status() -> dict[str, Any]:
    """Return active episodic-memory backend health for observability."""

    firebase_configured = _firebase_enabled()
    firebase_available = False
    if firebase_configured:
        try:
            _get_client()
            firebase_available = True
        except Exception:
            firebase_available = False

    if firebase_available:
        active_backend = "firebase"
    else:
        active_backend = "local_json"

    local_memory_exists = LOCAL_MEMORY_PATH.exists()
    local_entries = _read_local_memory()
    return {
        "active_backend": active_backend,
        "firebase_configured": firebase_configured,
        "firebase_available": firebase_available,
        "local_memory_path": str(LOCAL_MEMORY_PATH),
        "local_memory_exists": local_memory_exists,
        "local_query_count": len(local_entries.get("queries", [])),
        "local_investigation_count": len(local_entries.get("investigations", [])),
    }

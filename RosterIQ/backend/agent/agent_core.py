"""Core reasoning workflow for the RosterIQ AI agent."""

from __future__ import annotations

from collections import Counter
import json
import re
from typing import Any

from backend.agent.groq_client import query_agent
from backend.agent.reasoning_loop import decide_tool
from backend.agent.root_cause_analyzer import analyze_market_drop
from backend.agent.tool_registry import TOOL_REGISTRY
from backend.analytics.report_generator import generate_pipeline_health_report
from backend.memory.firebase_memory import (
    compare_state_changes,
    get_previous_investigations,
    get_recent_queries,
    save_investigation,
    save_query,
)
from backend.memory.semantic_loader import load_semantic_memory
from backend.tools.web_search_tool import needs_search_context, search_context


SYSTEM_PROMPT = (
    "You are RosterIQ, an AI operations analyst for healthcare provider roster "
    "pipelines. Give direct, concise answers. Start with the answer, then add "
    "the strongest evidence. Default to 2 short paragraphs or 3 brief bullets. "
    "Do not mention internal tool names, semantic memory, or chain-of-thought "
    "unless the user explicitly asks. If the user is just greeting you or asking "
    "what you can do, reply naturally and briefly."
)

STATE_CODES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "IA",
    "ID", "IL", "IN", "KS", "KY", "LA", "MA", "MD", "ME", "MI", "MN", "MO",
    "MS", "MT", "NC", "ND", "NE", "NH", "NJ", "NM", "NV", "NY", "OH", "OK",
    "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VA", "VT", "WA", "WI",
    "WV", "WY",
}



OPERATIONAL_KEYWORDS = {
    "stuck",
    "failed",
    "failure",
    "failures",
    "market",
    "pipeline",
    "pipelines",
    "report",
    "compliance",
    "cms",
    "rejection",
    "rejections",
    "retry",
    "duration",
    "anomaly",
    "anomalies",
    "state",
    "organization",
    "org",
    "root cause",
    "roster",
}


def _is_conversational_query(query: str) -> bool:
    """Return whether the user is making small talk rather than asking for analysis."""

    normalized = re.sub(r"\s+", " ", (query or "").strip().lower())
    if not normalized:
        return True

    if any(keyword in normalized for keyword in OPERATIONAL_KEYWORDS):
        return False

    conversational_patterns = [
        r"(?:hi|hey|hello|yo|hola)",
        r"(?:hi|hey|hello) there",
        r"how are you",
        r"what can you do",
        r"who are you",
        r"help",
        r"thanks?",
        r"thank you",
        r"good (?:morning|afternoon|evening)",
    ]
    return any(re.fullmatch(pattern, normalized) for pattern in conversational_patterns)


def _conversation_response(query: str) -> str:
    """Return a short, user-friendly response for greetings and simple help."""

    normalized = re.sub(r"\s+", " ", (query or "").strip().lower())

    if any(token in normalized for token in {"thanks", "thank you"}):
        return (
            "You're welcome. Ask me about stuck pipelines, failed roster operations, market drops, "
            "or request an operational report for a state like CA."
        )

    if "how are you" in normalized:
        return (
            "Ready. I can investigate stuck pipelines, failure spikes, rejection patterns, market success, "
            "and build operational reports."
        )

    return (
        "Hi. I can triage stuck or failed pipelines, explain market regressions, surface rejection or retry "
        "patterns, and generate operational reports. Try 'Which pipelines are stuck?' or 'Generate an operational report for CA.'"
    )


def _pluralize(word: str, count: int) -> str:
    """Return a basic pluralized label for simple fallback messages."""

    return word if count == 1 else f"{word}s"


def _format_number(value: Any, decimals: int = 1) -> str:
    """Render numeric values consistently for user-facing fallback text."""

    try:
        number = float(value)
    except (TypeError, ValueError):
        return "unknown"

    if number.is_integer():
        return str(int(number))
    return f"{number:.{decimals}f}"


def _common_values(rows: list[dict[str, Any]], key: str, limit: int = 3) -> list[tuple[str, int]]:
    """Return the most common non-empty values for a field in structured tool data."""

    counts = Counter(str(row.get(key)).strip() for row in rows if row.get(key))
    return counts.most_common(limit)


def _small_record_list(rows: list[dict[str, Any]]) -> str:
    """Return a compact record list for very small result sets."""

    if not rows:
        return ""

    items = []
    for row in rows[:3]:
        parts = [row.get("RO_ID"), row.get("ORG_NM"), row.get("CNT_STATE"), row.get("LATEST_STAGE_NM")]
        compact = " / ".join(str(part) for part in parts if part)
        if compact:
            items.append(compact)

    if not items:
        return ""
    return f" Affected records: {'; '.join(items)}."


def _stuck_or_failed_summary(tool_name: str, tool_result: dict[str, Any]) -> str:
    """Return a readable summary for stuck and failed roster-operation tools."""

    rows = tool_result.get("data", [])
    count = int(tool_result.get("count", 0))
    label = "stuck" if tool_name == "stuck_ros" else "failed"
    base = f"There {'is' if count == 1 else 'are'} {count} {label} roster {_pluralize('operation', count)} right now."

    if count == 0:
        return base

    if count <= 3:
        return base + _small_record_list(rows)

    top_stage = _common_values(rows, "LATEST_STAGE_NM", limit=1)
    top_state = _common_values(rows, "CNT_STATE", limit=1)
    details = []
    if top_stage:
        details.append(f"Most are currently in {top_stage[0][0]} ({top_stage[0][1]}).")
    if top_state:
        details.append(f"The largest concentration is in {top_state[0][0]} ({top_state[0][1]}).")
    return " ".join([base, *details]).strip()


def _rejection_summary(entity_key: str, label: str, tool_result: dict[str, Any]) -> str:
    """Return a readable summary for state or organization rejection-rate tools."""

    rows = tool_result.get("data", [])
    if not rows:
        return f"No {label} rejection data is available."

    leaders = []
    for row in rows[:3]:
        entity = row.get(entity_key)
        rate = _format_number(row.get("rejection_rate_pct"))
        denominator = row.get("total_rosters") or row.get("total_records")
        if entity:
            leaders.append(f"{entity} at {rate}% across {denominator} records")

    if not leaders:
        return f"{label.capitalize()} rejection data is available, but the top entities could not be summarized."

    return f"Highest {label} rejection rates are: " + "; ".join(leaders) + "."


def _market_success_summary(user_query: str, tool_result: dict[str, Any]) -> str:
    """Return a readable snapshot for market success trends."""

    rows = tool_result.get("data", [])
    if not rows:
        return "No market success data is available."

    dated_rows = [row for row in rows if row.get("MONTH")]
    latest_month = max((row["MONTH"] for row in dated_rows), default=None)
    latest_rows = [row for row in rows if row.get("MONTH") == latest_month] if latest_month else rows
    sortable_rows = [row for row in latest_rows if row.get("SCS_PERCENT") is not None]
    sortable_rows.sort(key=lambda row: float(row["SCS_PERCENT"]))

    if not sortable_rows:
        return "Market success data is available, but the latest snapshot could not be summarized."

    worst = sortable_rows[0]
    best = sortable_rows[-1]
    month_label = str(latest_month).split("T")[0] if latest_month else "the latest period"
    state = _extract_state(user_query)

    if state:
        state_row = next((row for row in sortable_rows if str(row.get("MARKET", "")).upper() == state), None)
        if state_row:
            return (
                f"In {month_label}, {state} market success is {_format_number(state_row.get('SCS_PERCENT'), decimals=2)}%. "
                f"Across all visible markets, the range is {_format_number(worst.get('SCS_PERCENT'), decimals=2)}% "
                f"in {worst.get('MARKET')} to {_format_number(best.get('SCS_PERCENT'), decimals=2)}% in {best.get('MARKET')}."
            )

    return (
        f"In {month_label}, market success ranges from {_format_number(worst.get('SCS_PERCENT'), decimals=2)}% "
        f"in {worst.get('MARKET')} to {_format_number(best.get('SCS_PERCENT'), decimals=2)}% in {best.get('MARKET')}."
    )


def _retry_summary(tool_result: dict[str, Any]) -> str:
    """Return a readable summary for retry-analysis output."""

    rows = tool_result.get("data", [])
    count = int(tool_result.get("count", 0))
    if not rows:
        return "No retry operations were found."

    top_retry = max(rows, key=lambda row: row.get("RUN_NO") or 0)
    top_state = _common_values(rows, "CNT_STATE", limit=1)
    base = f"There are {count} retry roster operations in the dataset."
    detail = (
        f" The deepest retry chain is {top_retry.get('RO_ID')} for {top_retry.get('ORG_NM')} "
        f"in {top_retry.get('CNT_STATE')} at run {top_retry.get('RUN_NO')}."
    )
    if top_state:
        detail += f" The most active retry state is {top_state[0][0]} ({top_state[0][1]})."
    return base + detail


def _duration_summary(tool_result: dict[str, Any]) -> str:
    """Return a readable summary for duration anomaly output."""

    rows = tool_result.get("data", [])
    count = int(tool_result.get("count", 0))
    if not rows:
        return "No duration anomalies were detected."

    worst = max(rows, key=lambda row: row.get("anomaly_ratio") or 0)
    top_stage = _common_values(rows, "stage_name", limit=1)
    stage_detail = f" The most common anomalous stage is {top_stage[0][0]} ({top_stage[0][1]} records)." if top_stage else ""
    return (
        f"There are {count} duration anomalies. The most extreme case is {worst.get('RO_ID')} for "
        f"{worst.get('ORG_NM')} in {worst.get('CNT_STATE')}, where {worst.get('stage_name')} is running at "
        f"{_format_number(worst.get('anomaly_ratio'), decimals=1)}x the baseline.{stage_detail}"
    )


def _root_cause_summary(tool_result: dict[str, Any]) -> str:
    """Return a readable summary for root-cause analysis output."""

    payload = (tool_result.get("data") or [{}])[0]
    market = payload.get("market", "the selected market")
    explanation = payload.get("explanation")
    if explanation:
        return f"{explanation} Confidence score: {_format_number(payload.get('confidence_score'), decimals=2)}."
    return (
        f"Root-cause analysis for {market} points to {payload.get('primary_org', 'Unknown')} and "
        f"stage {payload.get('likely_stage_issue', 'Unknown')} with confidence "
        f"{_format_number(payload.get('confidence_score'), decimals=2)}."
    )

def _safe_get_recent_queries(limit: int = 5) -> list[dict[str, Any]]:
    """Return recent memory entries without failing the agent flow."""

    try:
        return get_recent_queries(limit=limit)
    except Exception:
        return []


def _safe_get_previous_investigations(query_type: str) -> list[dict[str, Any]]:
    """Return prior investigations without failing the agent flow."""

    try:
        return get_previous_investigations(query_type=query_type)
    except Exception:
        return []


def _safe_compare_state_changes(state: str | None) -> dict[str, Any] | None:
    """Return state change comparisons when available."""

    if not state:
        return None
    try:
        return compare_state_changes(state)
    except Exception:
        return None


def _safe_save_query(query: str, response: str) -> None:
    """Persist query history when Firebase is available and continue otherwise."""

    try:
        save_query(query, response)
    except Exception:
        return


def _safe_save_investigation(query: str, tool_used: str, result_summary: dict[str, Any]) -> None:
    """Persist investigation history when Firebase is available and continue otherwise."""

    try:
        save_investigation(query=query, tool_used=tool_used, result_summary=result_summary)
    except Exception:
        return


def _fallback_analysis(
    tool_result: dict[str, Any],
    user_query: str,
    state_change: dict[str, Any] | None = None,
) -> str:
    """Generate a deterministic fallback explanation when the LLM is unavailable."""

    tool_name = tool_result.get("tool_name", "unknown_tool")

    if tool_result.get("report"):
        report = tool_result["report"]
        summary = report.get("summary", {})
        market_context = report.get("market_context", {})
        base = (
            f"RosterIQ generated a pipeline report for {summary.get('state', 'ALL')}. "
            f"It found {summary.get('stuck_ros', 0)} stuck roster operations and "
            f"{summary.get('failed_ros', 0)} failed roster operations. "
            f"Current market success is {market_context.get('success_rate', 0)}% and the trend is "
            f"{market_context.get('trend', 'stable')}."
        )
    elif tool_name == "root_cause_analysis":
        base = _root_cause_summary(tool_result)
    elif tool_result.get("context_summary"):
        base = (
            f"RosterIQ gathered external context for '{user_query}'. "
            f"{tool_result.get('context_summary', 'No external context was found.')}"
        )
    elif tool_name in {"stuck_ros", "failed_ros"}:
        base = _stuck_or_failed_summary(tool_name=tool_name, tool_result=tool_result)
    elif tool_name == "org_rejections":
        base = _rejection_summary(entity_key="ORG_NM", label="organization", tool_result=tool_result)
    elif tool_name == "state_rejections":
        base = _rejection_summary(entity_key="CNT_STATE", label="state", tool_result=tool_result)
    elif tool_name == "market_success":
        base = _market_success_summary(user_query=user_query, tool_result=tool_result)
    elif tool_name == "retry_analysis":
        base = _retry_summary(tool_result)
    elif tool_name == "duration_anomalies":
        base = _duration_summary(tool_result)
    else:
        count = tool_result.get("count", 0)
        base = (
            f"RosterIQ used the `{tool_name}` tool for the query '{user_query}'. "
            f"The result set contains {count} records. Review the returned data for "
            "the highest-priority operational patterns."
        )

    trend = _trend_summary(state_change=state_change, previous_investigations=[])
    return f"{trend}\n\n{base}" if trend else base


def _detect_root_cause_query(query: str) -> bool:
    """Return whether the query is asking for a root-cause investigation."""

    normalized = query.lower()
    return any(
        phrase in normalized
        for phrase in [
            "why is market success dropping",
            "root cause",
            "what caused failures",
            "why is",
        ]
    ) and any(keyword in normalized for keyword in ["market", "failure", "failures", "success"])


def _detect_report_query(query: str) -> bool:
    """Return whether the query is asking for a structured operational report."""

    normalized = query.lower()
    return any(
        phrase in normalized
        for phrase in [
            "pipeline report",
            "operational report",
            "health report",
            "pipeline health report",
            "operations summary",
            "operational summary",
        ]
    )


def _extract_state(query: str) -> str | None:
    """Extract a two-letter state code from a user query when present."""

    context_match = re.search(
        r"\b(?:in|for|state|market)\s+([A-Za-z]{2})\b",
        query,
        flags=re.IGNORECASE,
    )
    if context_match:
        candidate = context_match.group(1).upper()
        if candidate in STATE_CODES:
            return candidate

    trailing_match = re.search(r"\b([A-Za-z]{2})\s+market\b", query, flags=re.IGNORECASE)
    if trailing_match:
        candidate = trailing_match.group(1).upper()
        if candidate in STATE_CODES:
            return candidate

    for token in re.findall(r"\b[A-Z]{2}\b", query.upper()):
        if token in STATE_CODES:
            return token
    return None


def _extract_org(query: str) -> str | None:
    """Extract an organization filter from simple natural-language patterns."""

    quoted_match = re.search(r'"([^"]+)"', query)
    if quoted_match:
        return quoted_match.group(1).strip()

    org_match = re.search(
        r"(?:organization|org)\s+([A-Za-z0-9&.,'()\-\s]+?)(?:\s+in\s+[A-Za-z]{2}\b|$)",
        query,
        flags=re.IGNORECASE,
    )
    if org_match:
        candidate = org_match.group(1).strip(" .")
        return candidate or None
    return None


def _semantic_context(query: str, tool_result: dict[str, Any]) -> dict[str, str]:
    """Return semantic definitions relevant to the query and tool output."""

    semantic_memory = load_semantic_memory()
    matched_terms = {}
    uppercase_query = query.upper()

    for term, definition in semantic_memory.items():
        if term in uppercase_query:
            matched_terms[term] = definition

    data_preview = tool_result.get("data", [])
    if not matched_terms and data_preview:
        first_row = data_preview[0]
        for key in first_row.keys():
            definition = semantic_memory.get(str(key).upper())
            if definition:
                matched_terms[str(key).upper()] = definition

    report = tool_result.get("report")
    if report and report.get("market_context"):
        market_definition = semantic_memory.get("MARKET")
        if market_definition:
            matched_terms["MARKET"] = market_definition

    return matched_terms


def _build_messages(
    user_query: str,
    recent_queries: list[dict[str, Any]],
    previous_investigations: list[dict[str, Any]],
    state_change: dict[str, Any] | None,
    tool_name: str,
    tool_result: dict[str, Any],
    semantic_context: dict[str, str],
) -> list[dict[str, str]]:
    """Construct the chat payload for the Groq explanation request."""

    memory_context = json.dumps(recent_queries[:3], default=str)
    historical_context = json.dumps(previous_investigations[:3], default=str)
    tool_context = json.dumps(
        {
            "tool_name": tool_name,
            "count": tool_result.get("count", 0),
            "data_preview": tool_result.get("data", [])[:10],
            "report": tool_result.get("report"),
            "context_summary": tool_result.get("context_summary"),
            "sources": tool_result.get("sources", []),
            "semantic_context": semantic_context,
            "state_change": state_change,
        },
        default=str,
    )
    user_prompt = (
        f"User query: {user_query}\n"
        f"Recent investigation memory: {memory_context}\n"
        f"Previous investigations of this type: {historical_context}\n"
        f"Tool result: {tool_context}\n"
        "Answer the user's question directly. Keep the response concise and operationally useful. "
        "Lead with the answer, then add the strongest supporting evidence. Avoid mentioning internal tool names unless necessary. "
        "If there is limited evidence, say that in one sentence."
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


def _report_tool_result(state: str | None, org: str | None) -> dict[str, Any]:
    """Return a structured tool result for pipeline report queries."""

    report = generate_pipeline_health_report(state=state, org=org)
    return {
        "tool_name": "pipeline_report",
        "count": len(report.get("pipeline_issues", [])),
        "data": report.get("pipeline_issues", []),
        "report": report,
    }


def _execute_tool(query: str) -> tuple[str, dict[str, Any]]:
    """Dispatch the user query to the appropriate tool or analysis path."""

    if _detect_report_query(query):
        return "pipeline_report", _report_tool_result(
            state=_extract_state(query),
            org=_extract_org(query),
        )

    if _detect_root_cause_query(query):
        state = _extract_state(query) or "CA"
        result = analyze_market_drop(state)
        return "root_cause_analysis", {
            "tool_name": "root_cause_analysis",
            "count": 1,
            "data": [result],
            "report": None,
        }

    if needs_search_context(query):
        tool_result = search_context(query)
        return "web_search", {
            "tool_name": "web_search",
            "count": len(tool_result.get("sources", [])),
            "data": tool_result.get("results", []),
            "context_summary": tool_result.get("context_summary"),
            "sources": tool_result.get("sources", []),
            "query": tool_result.get("query", query),
        }

    tool_name = decide_tool(query)
    tool_callable = TOOL_REGISTRY[tool_name]
    return tool_name, tool_callable()


def _summarize_tool_result(
    tool_name: str,
    tool_result: dict[str, Any],
    query: str,
) -> dict[str, Any]:
    """Build a compact investigation summary for episodic memory."""

    state = _extract_state(query)
    summary: dict[str, Any] = {
        "state": state,
        "count": tool_result.get("count", 0),
    }

    if tool_name == "pipeline_report" and tool_result.get("report"):
        report = tool_result["report"]
        report_summary = report.get("summary", {})
        top_issue = report.get("pipeline_issues", [])
        summary.update(
            {
                "state": report_summary.get("state", state),
                "organization": report_summary.get("organization"),
                "total_ros": report_summary.get("total_ros", 0),
                "stuck_ros": report_summary.get("stuck_ros", 0),
                "failed_ros": report_summary.get("failed_ros", 0),
                "dominant_stage": top_issue[0]["stage"] if top_issue else None,
                "market_trend": report.get("market_context", {}).get("trend"),
            }
        )
        return summary

    if tool_name == "root_cause_analysis":
        payload = tool_result.get("data", [{}])[0]
        summary.update(
            {
                "state": payload.get("market", state),
                "market": payload.get("market", state),
                "likely_stage_issue": payload.get("likely_stage_issue"),
            }
        )
        return summary

    if tool_name == "web_search":
        summary.update(
            {
                "context_summary": tool_result.get("context_summary"),
                "source_count": len(tool_result.get("sources", [])),
            }
        )
        return summary

    if tool_name == "stuck_ros":
        summary["stuck_ros"] = tool_result.get("count", 0)
    if tool_name == "failed_ros":
        summary["failed_ros"] = tool_result.get("count", 0)
    if tool_name == "duration_anomalies" and tool_result.get("data"):
        summary["dominant_stage"] = tool_result["data"][0].get("stage_name")
    return summary


def _trend_summary(
    state_change: dict[str, Any] | None,
    previous_investigations: list[dict[str, Any]],
) -> str:
    """Return a deterministic trend-comparison sentence when history exists."""

    if not state_change or state_change.get("change") == "no_history":
        return ""

    state = state_change.get("state")
    previous_summary = None
    for record in previous_investigations:
        result_summary = record.get("result_summary", {}) or {}
        if str(result_summary.get("state", "")).upper() == str(state or "").upper():
            previous_summary = result_summary
            break

    previous_stuck = state_change.get("previous_stuck_ros")
    current_stuck = state_change.get("current_stuck_ros")
    dominant_stage = (previous_summary or {}).get("dominant_stage")
    stage_suffix = f" in {dominant_stage}" if dominant_stage else ""

    if previous_stuck is not None and current_stuck is not None:
        if current_stuck < previous_stuck:
            direction = "partial resolution"
        elif current_stuck > previous_stuck:
            direction = "a regression"
        else:
            direction = "no net change"
        return (
            f"Last session you investigated {state} pipelines and identified {previous_stuck} stuck ROs{stage_suffix}. "
            f"Currently {current_stuck} remain stuck, indicating {direction}."
        )

    previous_failed = state_change.get("previous_failed_ros")
    current_failed = state_change.get("current_failed_ros")
    if previous_failed is not None and current_failed is not None:
        if current_failed < previous_failed:
            direction = "improvement"
        elif current_failed > previous_failed:
            direction = "regression"
        else:
            direction = "no net change"
        return (
            f"The latest comparison for {state} shows failed roster operations changed from "
            f"{previous_failed} to {current_failed}, indicating {direction}."
        )

    return ""


def run_agent(query: str) -> dict[str, Any]:
    """Execute the end-to-end agent workflow for a natural-language query."""

    normalized_query = (query or "").strip()
    if _is_conversational_query(normalized_query):
        analysis = _conversation_response(normalized_query)
        _safe_save_query(query=normalized_query, response=analysis)
        return {
            "query": normalized_query,
            "tool_used": "conversation",
            "analysis": analysis,
            "data": [],
            "count": 0,
            "recent_memory": [],
            "previous_investigations": [],
            "state_change": None,
            "semantic_context": {},
            "report": None,
            "sources": [],
        }

    recent_queries = _safe_get_recent_queries()
    tool_name, tool_result = _execute_tool(normalized_query)
    state = _extract_state(normalized_query)
    previous_investigations = _safe_get_previous_investigations(tool_name)
    state_change = _safe_compare_state_changes(state)
    semantic_context = _semantic_context(normalized_query, tool_result)

    try:
        analysis = query_agent(
            _build_messages(
                user_query=normalized_query,
                recent_queries=recent_queries,
                previous_investigations=previous_investigations,
                state_change=state_change,
                tool_name=tool_name,
                tool_result=tool_result,
                semantic_context=semantic_context,
            )
        )
    except Exception:
        analysis = _fallback_analysis(
            tool_result=tool_result,
            user_query=normalized_query,
            state_change=state_change,
        )

    trend_summary = _trend_summary(
        state_change=state_change,
        previous_investigations=previous_investigations,
    )
    if trend_summary and trend_summary not in analysis:
        analysis = f"{trend_summary}\n\n{analysis}"


    investigation_summary = _summarize_tool_result(
        tool_name=tool_name,
        tool_result=tool_result,
        query=normalized_query,
    )

    _safe_save_query(query=normalized_query, response=analysis)
    _safe_save_investigation(
        query=normalized_query,
        tool_used=tool_name,
        result_summary=investigation_summary,
    )

    return {
        "query": normalized_query,
        "tool_used": tool_name,
        "analysis": analysis,
        "data": tool_result.get("data", []),
        "count": tool_result.get("count", 0),
        "recent_memory": recent_queries,
        "previous_investigations": previous_investigations,
        "state_change": state_change,
        "semantic_context": semantic_context,
        "report": tool_result.get("report"),
        "sources": tool_result.get("sources", []),
    }

"""Smoke tests for hackathon judging-critical behaviors."""

from __future__ import annotations

import unittest

from backend.analytics.report_generator import generate_pipeline_health_report
from backend.memory.firebase_memory import get_memory_backend_status
from backend.procedures.registry import PROCEDURE_REGISTRY, run_procedure


class JudgingReadinessTests(unittest.TestCase):
    """Validate critical capabilities expected by judges."""

    def test_procedure_registry_has_four_required_workflows(self) -> None:
        required = {
            "triage_stuck_ros",
            "market_health_report",
            "retry_effectiveness_analysis",
            "quality_drift_watch",
        }
        self.assertTrue(required.issubset(set(PROCEDURE_REGISTRY.keys())))

    def test_run_procedure_returns_standard_shape(self) -> None:
        result = run_procedure("triage_stuck_ros")
        self.assertIn("tool_name", result)
        self.assertIn("count", result)
        self.assertIn("data", result)
        self.assertIn("procedure_summary", result)

    def test_memory_backend_status_is_available(self) -> None:
        status = get_memory_backend_status()
        self.assertIn("active_backend", status)
        self.assertIn(status["active_backend"], {"firebase", "local_json"})

    def test_pipeline_report_contains_cross_table_correlation(self) -> None:
        report = generate_pipeline_health_report(state="CA")
        self.assertIn("cross_table_correlation", report)
        correlation = report["cross_table_correlation"]
        self.assertIn("summary", correlation)
        self.assertIn("top_rows", correlation)


if __name__ == "__main__":
    unittest.main()

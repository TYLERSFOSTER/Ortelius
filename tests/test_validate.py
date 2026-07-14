from __future__ import annotations

from pathlib import Path

from ortelius.graph_io import load_graph_bundle
from ortelius.validate import ValidationIssue, ValidationReport, validate_graph_bundle

FIXTURE_BASE = Path("tests/fixtures/graph_assets")
TYPE_GRAPH_ID = "tg"
FIBER_GRAPH_ID = "fg"


def test_validation_report_ok() -> None:
    assert ValidationReport(()).ok
    assert not ValidationReport((ValidationIssue("error", "x", "bad"),)).ok
    assert ValidationReport((ValidationIssue("warning", "x", "soft"),)).ok


def test_valid_minimal_fixture_has_no_errors() -> None:
    bundle = _load_fixture_bundle("minimal_generic")

    report = validate_graph_bundle(bundle, mode="strict")

    assert report.ok
    assert report.issues == ()


def test_duplicate_ids_are_errors() -> None:
    bundle = _load_fixture_bundle("invalid_duplicate_id")

    report = validate_graph_bundle(bundle)

    assert report.has_code("duplicate_id")
    assert not report.ok


def test_unknown_node_type_is_error() -> None:
    bundle = _load_fixture_bundle("invalid_unknown_type")

    report = validate_graph_bundle(bundle)

    assert report.has_code("node_unknown_type_id")
    assert not report.ok


def test_missing_edge_endpoint_is_error() -> None:
    bundle = _load_fixture_bundle("invalid_missing_endpoint")

    report = validate_graph_bundle(bundle)

    assert report.has_code("edge_unknown_target_id")
    assert not report.ok


def test_edge_endpoint_type_mismatch_is_error() -> None:
    bundle = _load_fixture_bundle("invalid_bad_edge_type")

    report = validate_graph_bundle(bundle)

    assert report.has_code("edge_target_type_mismatch")
    assert not report.ok


def test_unknown_field_is_warning_in_bootstrap_mode() -> None:
    bundle = _load_fixture_bundle("invalid_unknown_field")

    report = validate_graph_bundle(bundle, mode="bootstrap")

    assert report.has_code("unknown_field")
    assert report.warning_count == 1
    assert report.error_count == 0
    assert report.ok


def test_unknown_field_is_error_in_strict_mode() -> None:
    bundle = _load_fixture_bundle("invalid_unknown_field")

    report = validate_graph_bundle(bundle, mode="strict")

    assert report.has_code("unknown_field")
    assert report.error_count == 1
    assert not report.ok


def _load_fixture_bundle(name: str):
    return load_graph_bundle(
        FIXTURE_BASE / f"{name}/graphs",
        type_graph_id=TYPE_GRAPH_ID,
        fiber_graph_id=FIBER_GRAPH_ID,
    )

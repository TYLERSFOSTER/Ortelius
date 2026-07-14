from __future__ import annotations

from pathlib import Path

import pytest

from ortelius.cli import main
from ortelius.protocol_assets import (
    inspect_protocol_bundle,
    validate_protocol_bundle,
    validate_system_protocol_assets,
)

SYSTEM_ROOT = Path("assets/protocol_assets/system/graph_population/v001")
FIXTURE_ROOT = Path("tests/fixtures/protocol_assets")
VALID_BUNDLE = FIXTURE_ROOT / "minimal_generated_bundle"


def test_validate_system_protocol_assets_accepts_current_system_assets() -> None:
    report = validate_system_protocol_assets(SYSTEM_ROOT)

    assert report.ok


def test_validate_protocol_bundle_accepts_minimal_generated_bundle() -> None:
    report = validate_protocol_bundle(VALID_BUNDLE)

    assert report.ok


def test_inspect_protocol_bundle_returns_run_summary() -> None:
    summary = inspect_protocol_bundle(VALID_BUNDLE)

    assert summary["protocol_id"] == "minimal_protocol_001"
    assert summary["domain_slug"] == "fixture_domain"
    assert summary["type_graph_id"] == "tg"
    assert summary["fiber_graph_id"] == "fg"
    assert summary["ordered_loop_specs"] == 11
    assert summary["run_contract_status"] == "complete"


@pytest.mark.parametrize(
    ("fixture_name", "expected_code"),
    [
        ("invalid_missing_manifest", "missing_bundle_file"),
        ("invalid_missing_ordered_loop_specs", "incomplete_run_contract"),
        ("invalid_missing_loop_spec_file", "missing_loop_spec_file"),
        ("invalid_missing_loop_spec_heading", "missing_loop_spec_heading"),
        ("invalid_missing_source_boundary", "missing_source_boundary"),
        ("invalid_missing_validation_rule", "missing_validation_rule"),
        ("invalid_path_reconciliation", "path_reconciliation_required"),
        ("invalid_malformed_cursor", "invalid_cursor_json"),
    ],
)
def test_validate_protocol_bundle_rejects_invalid_fixtures(
    fixture_name: str,
    expected_code: str,
) -> None:
    report = validate_protocol_bundle(FIXTURE_ROOT / fixture_name)

    assert not report.ok
    assert report.has_code(expected_code)


def test_protocol_validate_system_cli_reports_ok(capsys) -> None:
    exit_code = main(
        [
            "protocol",
            "validate-system",
            "--system-root",
            str(SYSTEM_ROOT),
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "protocol_system_validation: ok" in output


def test_protocol_validate_bundle_cli_reports_ok(capsys) -> None:
    exit_code = main(
        [
            "protocol",
            "validate-bundle",
            "--protocol-root",
            str(VALID_BUNDLE),
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "protocol_bundle_validation: ok" in output


def test_protocol_validate_bundle_cli_reports_failure(capsys) -> None:
    exit_code = main(
        [
            "protocol",
            "validate-bundle",
            "--protocol-root",
            str(FIXTURE_ROOT / "invalid_missing_loop_spec_file"),
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "missing_loop_spec_file" in output


def test_protocol_inspect_bundle_cli_reports_summary(capsys) -> None:
    exit_code = main(
        [
            "protocol",
            "inspect-bundle",
            "--protocol-root",
            str(VALID_BUNDLE),
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "protocol_id: minimal_protocol_001" in output
    assert "ordered_loop_specs: 11" in output

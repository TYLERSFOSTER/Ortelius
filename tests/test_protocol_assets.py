from __future__ import annotations

import json
import shutil
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



MAKE_GRAPH_TABLES = (
    "Type Node Semantic Review Table",
    "Type Edge Semantic Review Table",
    "Primitive Relation Family Summary",
    "Endpoint Variant / Inverse Group Table",
    "Fiber Node Batch Review Table",
    "Fiber Edge Batch Review Table",
    "Field Richness Review Table",
    "Source Landscape Review Table",
    "Domain Membership Review Table",
    "Joint Population Feasibility Table",
    "Endpoint Reservation Review Table",
    "Generated Code Runtime Audit Table",
    "Counter Reconciliation Table",
    "Final Decision",
)


def _promote_fixture_to_make_graph(bundle: Path) -> dict:
    manifest_path = bundle / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["front_door_mode"] = "MAKE-GRAPH"
    manifest["graph_build_target"] = {
        "mode": "MAKE-GRAPH",
        "completion_target": "graph_build_targets_met",
        "type_graph_targets": {"node_type_count": 1, "edge_type_count": 1},
        "fiber_graph_targets": {
            "instances_per_node_type": 1,
            "instances_per_edge_type": 1,
            "expected_node_instances": 1,
            "expected_edge_instances": 1,
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def _write_make_graph_artifacts(bundle: Path, *, placeholder_packet: bool = False) -> None:
    run = bundle / "runs" / "run_001"
    reports = run / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (bundle / "control_loop_plan.md").write_text(
        "# Control Loop Plan\n\nstatus: initialized\n", encoding="utf-8"
    )
    (reports / "generated_bundle_acceptance_report.md").write_text(
        "# Generated Bundle Acceptance Report\n\ngenerated_bundle_acceptance: passed\n",
        encoding="utf-8",
    )
    (reports / "source_landscape_map.md").write_text(
        "# Source Landscape Map\n\n"
        "source_family: source_family_alpha\n"
        "source_adapter: alpha_api\n"
        "source_endpoint: https://example.test/alpha\n"
        "source_record: alpha record rows\n"
        "source_family: source_family_beta\n"
        "source_adapter: beta_catalog\n"
        "source_endpoint: https://example.test/beta\n"
        "source_record: beta catalog pages\n",
        encoding="utf-8",
    )
    (reports / "source_family_registry.md").write_text(
        "# Source Family Registry\n\n"
        "source_family: source_family_alpha\n"
        "source_family: source_family_beta\n",
        encoding="utf-8",
    )
    (run / "source_adapter_candidate_frontier.md").write_text(
        "# Source Adapter Candidate Frontier\n\nsource_adapter: alpha_api\n",
        encoding="utf-8",
    )
    (reports / "source_strategy_decision_log.md").write_text(
        "# Source Strategy Decision Log\n\n"
        "source_family: source_family_alpha\n"
        "source_adapter: alpha_api\n"
        "source_endpoint: https://example.test/alpha\n"
        "source_record: alpha rows\n",
        encoding="utf-8",
    )
    (reports / "joint_population_feasibility_plan.md").write_text(
        "# Joint Population Feasibility Plan\n\nstatus: initialized\n",
        encoding="utf-8",
    )
    (reports / "endpoint_reservation_plan.md").write_text(
        "# Endpoint Reservation Plan\n\nstatus: initialized\n",
        encoding="utf-8",
    )
    semantic = [
        "# Semantic Acceptance Report",
        "",
        "semantic_acceptance_status: semantic_acceptance_incomplete",
        "",
        "domain_field_complete: pending",
    ]
    for table in MAKE_GRAPH_TABLES:
        semantic.extend(
            ["", f"## {table}", "", "| key | value |", "|---|---|", "| initialized | true |"]
        )
    (reports / "semantic_acceptance_report.md").write_text(
        "\n".join(semantic) + "\n", encoding="utf-8"
    )

    packet_dir = run / "batch_packets"
    packet_dir.mkdir(parents=True, exist_ok=True)
    if placeholder_packet:
        packet = "# Batch Packet\n\nstatus: see execution log and reports\n"
    else:
        packet = """# Batch Packet

parent_loop_id: type_node_discovery
batch_goal: evaluate one fixture item
ordered_item_list:
- fixture_item_001
acceptance_criteria: source-backed domain evidence exists
rejection_criteria: evidence missing
per_item_status_table:
| item | status |
|---|---|
| fixture_item_001 | pending |
write_targets: candidate_graphs/tg/nodes.json
cursor_update_rule: advance after item
resume_point: next pending item
"""
    (packet_dir / "fixture_batch.md").write_text(packet, encoding="utf-8")


def _write_shallow_make_graph_records(bundle: Path) -> None:
    type_node = {
        "id": "tg.node.artist",
        "label": "Artist",
        "status": "accepted",
        "fiber_population_eligible": True,
        "type_membership_predicate": "source record says artist",
        "domain_membership_predicate": "source record says domain relevant",
        "domain_exclusion_predicate": "exclude generic source-only matches",
        "type_fields": {
            "fields": {
                "name": {
                    "label": "Name",
                    "value_kind": "string",
                    "cardinality": "required_one",
                    "description": "Fixture identity field.",
                    "source_policy": "recommended",
                    "field_tier": "identity_field",
                },
                "source_url": {
                    "label": "Source URL",
                    "value_kind": "uri",
                    "cardinality": "optional_one",
                    "description": "Fixture source pointer.",
                    "source_policy": "recommended",
                    "field_tier": "source_adapter_field",
                },
            }
        },
    }
    (bundle / "candidate_graphs" / "tg" / "nodes.json").write_text(
        json.dumps(
            {
                "schema_version": "ortelius.graph.v0",
                "graph_id": "tg",
                "record_kind": "nodes",
                "records": [type_node],
            },
            indent=2,
        ),
        encoding="utf-8",
    )


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


@pytest.mark.parametrize(
    ("heading", "expected_code"),
    [
        ("Semantic Acceptance Gate", "missing_semantic_acceptance_gate"),
        ("Recovery Policy", "missing_recovery_policy"),
        ("Batch Execution", "missing_batch_execution_rule"),
    ],
)
def test_validate_protocol_bundle_rejects_missing_semantic_loop_surfaces(
    tmp_path: Path,
    heading: str,
    expected_code: str,
) -> None:
    bundle = tmp_path / "bundle"
    shutil.copytree(VALID_BUNDLE, bundle)
    loop_spec = bundle / "loop_specs" / "01_domain_suitability.md"
    text = loop_spec.read_text(encoding="utf-8")
    start = text.index(f"\n## {heading}\n")
    next_start = text.find("\n## ", start + 1)
    if next_start == -1:
        next_start = len(text)
    loop_spec.write_text(text[:start] + text[next_start:], encoding="utf-8")

    report = validate_protocol_bundle(bundle)

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


def test_validate_protocol_bundle_rejects_make_graph_without_required_runtime_artifacts(
    tmp_path: Path,
) -> None:
    bundle = tmp_path / "bundle"
    shutil.copytree(VALID_BUNDLE, bundle)
    _promote_fixture_to_make_graph(bundle)

    report = validate_protocol_bundle(bundle)

    assert not report.ok
    assert report.has_code("missing_make_graph_artifact")


def test_validate_protocol_bundle_rejects_placeholder_markdown_batch_packet(
    tmp_path: Path,
) -> None:
    bundle = tmp_path / "bundle"
    shutil.copytree(VALID_BUNDLE, bundle)
    _promote_fixture_to_make_graph(bundle)
    _write_make_graph_artifacts(bundle, placeholder_packet=True)

    report = validate_protocol_bundle(bundle)

    assert not report.ok
    assert report.has_code("placeholder_batch_packet")


def test_validate_protocol_bundle_rejects_shallow_make_graph_type_fields(
    tmp_path: Path,
) -> None:
    bundle = tmp_path / "bundle"
    shutil.copytree(VALID_BUNDLE, bundle)
    _promote_fixture_to_make_graph(bundle)
    _write_make_graph_artifacts(bundle)
    _write_shallow_make_graph_records(bundle)

    report = validate_protocol_bundle(bundle)

    assert not report.ok
    assert report.has_code("type_field_richness_incomplete")

# ruff: noqa: E501

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
    "Graph Intent Alignment Review Table",
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
    "Accepted Target Reconciliation Table",
    "Semantic Sample Audit Table",
    "Source Probe Order Audit Table",
    "Counter Reconciliation Table",
    "Final Decision",
)


def _promote_fixture_to_make_graph(bundle: Path) -> dict:
    manifest_path = bundle / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["front_door_mode"] = "MAKE-GRAPH"
    manifest["graph_intent"] = {
        "required": True,
        "contract_path": "runs/run_001/reports/graph_intent_contract.md",
        "domain_lens": "fixture validation lens",
        "graph_intent_status": "confirmed",
        "intent_resolution_mode": "user_confirmed",
        "confirmed_or_authorized_lens": "fixture validation lens",
        "confirmation_status": "confirmed",
        "intent_confirmation_policy": "user_supplied_confirmed",
        "downstream_gate": "all graph-shaping candidates must fit graph_intent_contract",
    }
    ordered = manifest.get("ordered_loop_specs", [])
    graph_intent_spec = "loop_specs/01_graph_intent_alignment.md"
    if graph_intent_spec not in ordered:
        manifest["ordered_loop_specs"] = [graph_intent_spec, *ordered]
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
    cursor_path = bundle / "runs" / "run_001" / "cursor.json"
    cursor = json.loads(cursor_path.read_text(encoding="utf-8"))
    cursor.update(
        {
            "graph_intent_status": "confirmed",
            "semantic_plan_authority_status": "initialized",
            "source_probe_order_status": "initialized",
            "type_field_richness_status": "initialized",
            "edge_family_diversity_status": "initialized",
            "domain_membership_boundary_status": "initialized",
            "label_quality_status": "initialized",
            "source_evidence_accounting_status": "initialized",
            "semantic_sample_audit_status": "initialized",
            "semantic_acceptance_status": "semantic_acceptance_incomplete",
            "next_legal_action": "SourceReconnaissance.PlanWrite",
        }
    )
    cursor_path.write_text(json.dumps(cursor, indent=2), encoding="utf-8")
    _write_graph_intent_loop_spec(bundle)
    return manifest


def _write_graph_intent_loop_spec(bundle: Path) -> None:
    loop_specs = bundle / "loop_specs"
    loop_specs.mkdir(parents=True, exist_ok=True)
    (loop_specs / "01_graph_intent_alignment.md").write_text(
        """# Graph Intent Alignment

## Loop Identity

loop_id: graph_intent_alignment
graph_level: bundle
manifest_order_index: 1

## Inputs

input_files: manifest.json
required_manifest_fields: domain, graph_intent

## Iterator

iterator_name: graph_intent_contract_check
iterator_source: domain label and graph intent metadata
target_count: 1

## Current Item Shape

current_item_fields: domain.label, graph_intent.domain_lens
cursor_fields: active_loop_id, active_action_id, active_iteration

## Action Template

action_id_template: graph_intent_alignment.<domain_slug>
action_prompt_template: Verify graph intent contract before source or type discovery.

## Allowed Writes

output_files: runs/run_001/reports/graph_intent_contract.md, runs/run_001/execution_log.md,\
  runs/run_001/cursor.json
write_rule: write graph intent contract only
max_records_written_per_action: 0

## Source Boundaries

allowed_source_types: supplied domain description and graph intent examples
allowed_source_locations: repository fixture only
disallowed_sources: live web
evidence_threshold: fixture graph intent metadata is sufficient

## Evidence Required

record_evidence_required: graph intent status and downstream gate
field_evidence_required: none
unsupported_claim_rule: no graph facts are written

## Validation Required

validation_checklist: graph_intent_contract.md has required fields
validation_unavailable_rule: stop

## Completion Rule

action_completion_rule: graph intent contract initialized
loop_completion_rule: graph intent status confirmed

## Semantic Acceptance Gate

semantic_gate: graph intent status must be confirmed before target progress
accepted_counting_rule: graph intent setup does not count toward graph targets

## Recovery Policy

recoverable_failure_classes: missing examples, ambiguous lens
recovery_ladder: request_examples_or_mark_needs_human_confirmation
recovery_attempt_budget: 1
resume_condition: graph intent confirmed
exhaustion_condition: graph intent remains ambiguous

## Batch Execution

batch_execution_meaning: single_fixture_batch_not_generated_code_loop
batch_plan_path: runs/run_001/source_batch_plan.md
batch_packet_path: runs/run_001/batch_packets/fixture_batch.md
batch_size: fixture_small
checkpoint_rule: update cursor and execution log after fixture action

## Stop Conditions

stop_conditions: graph_intent_contract_missing, graph_intent_unconfirmed
failure_report_fields: failure_kind, next_required_input

## Handoff

handoff_to_next_loop: domain_suitability
cursor_update_rule: set active_loop_id to domain_suitability
""",
        encoding="utf-8",
    )


def _write_make_graph_artifacts(bundle: Path, *, placeholder_packet: bool = False) -> None:
    run = bundle / "runs" / "run_001"
    reports = run / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (bundle / "control_loop_plan.md").write_text(
        "# Control Loop Plan\n\nstatus: initialized\n", encoding="utf-8"
    )
    (reports / "generated_bundle_acceptance_report.md").write_text(
        "# Generated Bundle Acceptance Report\n\n"
        "generated_bundle_acceptance: passed\n"
        "semantic_plan_authority_report_present: true\n"
        "source_probe_event_ledger_present: true\n"
        "row_backed_semantic_reports_initialized: true\n",
        encoding="utf-8",
    )
    (reports / "graph_intent_contract.md").write_text(
        "# Graph Intent Contract\n\n"
        "domain_label: Fixture Domain\n"
        "graph_intent_status: confirmed\n"
        "intent_resolution_mode: user_confirmed\n"
        "confirmed_or_authorized_lens: fixture validation lens\n"
        "included_lenses: fixture validation lens\n"
        "excluded_lenses: out-of-scope fixture lens\n"
        "ordinary_entity_scope: fixture entities\n"
        "relation_scope: fixture primitive relations\n"
        "source_scope: fixture sources\n"
        "domain_membership_rule: accepted fixture rows must fit the fixture lens\n"
        "type_membership_rule: accepted rows must match declared fixture type\n"
        "edge_evidence_rule: accepted edges require pair-specific fixture evidence\n"
        "domain_lens: fixture validation lens\n"
        "positive_type_examples: Fixture Type\n"
        "positive_relation_examples: fixture relation\n"
        "positive_instance_examples: Fixture Instance\n"
        "negative_type_examples: out-of-scope type\n"
        "negative_relation_examples: out-of-scope relation\n"
        "negative_scope: fixture exclusions\n"
        "competency_questions: What fixture records validate the protocol?\n"
        "inferred_candidate_lenses: fixture validation lens\n"
        "chosen_lens: fixture validation lens\n"
        "confirmation_status: confirmed\n"
        "intent_confirmation_policy: user_supplied_confirmed\n"
        "downstream_gate: all graph-shaping candidates must fit graph_intent_contract\n"
        "created_before_source_probe: true\n"
        "next_legal_action_after_contract: SourceReconnaissance.PlanWrite\n",
        encoding="utf-8",
    )
    (reports / "semantic_plan_authority_report.md").write_text(
        "# Semantic Plan Authority Report\n\n"
        "semantic_plan_authority: markdown_json_bundle\n"
        "generated_code_semantic_authority_allowed: false\n\n"
        "## Markdown Source Artifacts\n\n"
        "| artifact_path | semantic_role | exists | used_by |\n"
        "|---|---|---|---|\n"
        "| runs/run_001/reports/graph_intent_contract.md | graph intent | true | fixture |\n\n"
        "## Generated Code Artifacts\n\n"
        "| code_artifact_path | used | purpose | mechanical_only | semantic_decisions_present | markdown_inputs_read | graph_outputs_written | reports_written | authority_decision | notes |\n"
        "|---|---|---|---|---|---|---|---|---|---|\n"
        "| none | false | none | true | false | none | none | none | markdown_only | fixture |\n\n"
        "## Semantic Decisions\n\n"
        "| decision_kind | decision_artifact | row_or_section | generated_code_involved | accepted_authority | notes |\n"
        "|---|---|---|---|---|---|\n"
        "| graph_intent | runs/run_001/reports/graph_intent_contract.md | contract | false | true | fixture |\n\n"
        "## Final Authority Decision\n\n"
        "semantic_plan_authority_gate_result: passed\n",
        encoding="utf-8",
    )
    (reports / "source_probe_event_ledger.md").write_text(
        "# Source Probe Event Ledger\n\n"
        "## Event Rows\n\n"
        "| event_id | sequence | event_kind | source_family | source_adapter_id | source_endpoint_or_artifact | triggering_markdown_artifact | triggering_batch_id | allowed_by_contract | result_artifact_path | notes |\n"
        "|---|---|---|---|---|---|---|---|---|---|---|\n"
        "| event_001 | 1 | graph_intent_contract_materialized | setup | setup | repo-local | runs/run_001/reports/graph_intent_contract.md | setup | true | runs/run_001/reports/graph_intent_contract.md | fixture setup |\n"
        "| event_002 | 2 | source_reconnaissance_plan_materialized | setup | setup | repo-local | runs/run_001/reports/source_reconnaissance_plan.md | setup | true | runs/run_001/reports/source_reconnaissance_plan.md | fixture setup |\n"
        "| event_003 | 3 | batch_packet_materialized | setup | setup | repo-local | runs/run_001/batch_packets/fixture_batch.md | fixture_batch | true | runs/run_001/batch_packets/fixture_batch.md | fixture setup |\n"
        "| event_004 | 4 | source_probe | source_family_alpha | alpha_api | https://example.test/alpha | runs/run_001/batch_packets/fixture_batch.md | fixture_batch | true | runs/run_001/source_batches/fixture_batch.json | fixture source event |\n\n"
        "source_probe_order_gate_result: passed\n",
        encoding="utf-8",
    )
    (reports / "source_reconnaissance_plan.md").write_text(
        "# Source Reconnaissance Plan\n\n"
        "graph_intent_contract_path: runs/run_001/reports/graph_intent_contract.md\n"
        "source_scope: fixture source scope\n"
        "source_families: source_family_alpha, source_family_beta\n"
        "source_adapters: alpha_api, beta_catalog\n"
        "source_family_priority: alpha then beta\n"
        "source_adapter_recovery_order: alpha_api -> beta_catalog\n"
        "minimum_domain_membership_evidence: fixture domain evidence\n"
        "minimum_type_membership_evidence: fixture type evidence\n"
        "minimum_edge_pair_evidence: fixture pair evidence\n"
        "batching_strategy: one fixture batch\n"
        "failure_policy: stop with source_reconnaissance_limited\n"
        "next_legal_action: SourceReconnaissance.BatchPacketWrite\n",
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
    (reports / "source_adapter_recovery_plan.md").write_text(
        "# Source Adapter Recovery Plan\n\n"
        "source_adapter_recovery_order: alpha_api -> beta_catalog\n"
        "failure_policy: try next admissible source family before terminal stop\n",
        encoding="utf-8",
    )
    (reports / "source_strategy_decision_log.md").write_text(
        "# Source Strategy Decision Log\n\n"
        "source_family: source_family_alpha\n"
        "source_adapter: alpha_api\n"
        "source_endpoint: https://example.test/alpha\n"
        "source_record: alpha rows\n"
        "source_family: source_family_beta\n"
        "source_adapter: beta_catalog\n"
        "source_endpoint: https://example.test/beta\n"
        "source_record: beta rows\n",
        encoding="utf-8",
    )
    (reports / "type_candidate_review.md").write_text(
        "# Type Candidate Review\n\n"
        "| candidate_type_id | candidate_label | candidate_description | candidate_source_evidence | source_family | source_adapter_id | domain_intent_fit | ordinary_entity_type | fiber_population_eligible | rejection_or_acceptance_reason | accepted_for_type_graph |\n"
        "|---|---|---|---|---|---|---|---|---|---|---|\n"
        "| tg.node.artist | Fixture Type | Fixture entity type | fixture source | source_family_alpha | alpha_api | fits fixture lens | true | true | fixture accepted | true |\n",
        encoding="utf-8",
    )
    (reports / "type_field_discovery_report.md").write_text(
        "# Type Field Discovery Report\n\n"
        "| type_id | type_label | field_key | field_label | field_kind | field_semantic_role | value_kind | cardinality | source_policy | evidence_source | evidence_summary | domain_descriptive | identity_field | source_adapter_field | provenance_field | accepted | rejection_or_deferral_reason |\n"
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n"
        "| tg.node.artist | Fixture Type | name | Name | scalar | identity | string | required_one | required | fixture source | identity evidence | false | true | false | false | true | accepted |\n"
        "| tg.node.artist | Fixture Type | practice_area | Practice Area | scalar | domain | string | optional_one | recommended | fixture source | domain field evidence | true | false | false | false | true | accepted |\n"
        "| tg.node.artist | Fixture Type | active_period | Active Period | scalar | domain | string | optional_one | recommended | fixture source | domain field evidence | true | false | false | false | true | accepted |\n"
        "| tg.node.artist | Fixture Type | institutional_role | Institutional Role | scalar | domain | string | optional_one | recommended | fixture source | domain field evidence | true | false | false | false | true | accepted |\n",
        encoding="utf-8",
    )
    (reports / "edge_candidate_review.md").write_text(
        "# Edge Candidate Review\n\n"
        "| candidate_edge_type_id | candidate_edge_label | source_type_id | target_type_id | primitive_relation_claim | relation_family | inverse_or_variant_group | source_evidence | source_family | source_adapter_id | pair_specific_evidence_available | domain_centrality | not_query_derived | not_domain_membership_evidence | not_source_metadata | expected_instance_availability | accepted_for_type_graph | rejection_or_acceptance_reason |\n"
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n"
        "| tg.edge.related_to | Fixture relation | tg.node.artist | tg.node.artist | fixture entity has primitive relation to fixture entity | fixture_relation_family | canonical | fixture evidence | source_family_beta | beta_catalog | true | central to fixture lens | true | true | true | available | true | fixture accepted |\n",
        encoding="utf-8",
    )
    (reports / "edge_family_diversity_report.md").write_text(
        "# Edge Family Diversity Report\n\n"
        "| relation_family | accepted_edge_type_count | accepted_edge_instance_target | source_type_coverage | target_type_coverage | domain_centrality_rationale | dominance_risk | domain_membership_evidence_overlap | decision | notes |\n"
        "|---|---|---|---|---|---|---|---|---|---|\n"
        "| fixture_relation_family | 1 | 1 | tg.node.artist | tg.node.artist | fixture relation is central | low | false | accepted | fixture |\n",
        encoding="utf-8",
    )
    (reports / "edge_field_discovery_report.md").write_text(
        "# Edge Field Discovery Report\n\n"
        "| edge_type_id | edge_label | field_key | field_label | field_kind | field_semantic_role | value_kind | cardinality | source_policy | evidence_source | evidence_quote_or_summary | relation_descriptive | pair_evidence_field | provenance_field | accepted | rejection_or_deferral_reason |\n"
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n"
        "| tg.edge.related_to | Fixture relation | relation_context | Relation Context | scalar | relation | string | optional_one | recommended | fixture source | relation field evidence | true | false | false | true | accepted |\n",
        encoding="utf-8",
    )
    (reports / "domain_membership_boundary_report.md").write_text(
        "# Domain Membership Boundary Report\n\n"
        "| record_or_candidate_id | label | record_kind | type_id_or_candidate_type_id | membership_claim | evidence_source | evidence_kind | domain_intent_fit | geographic_or_administrative_only | source_taxonomy_only | accepted_as_domain_member | rejection_or_deferral_reason |\n"
        "|---|---|---|---|---|---|---|---|---|---|---|---|\n"
        "| fg.node.fixture | Fixture Instance | fiber_node | tg.node.artist | fixture member | fixture source | domain evidence | fits fixture lens | false | false | true | accepted |\n",
        encoding="utf-8",
    )
    (reports / "source_evidence_accounting_report.md").write_text(
        "# Source Evidence Accounting Report\n\n"
        "| source_family | source_adapter_id | declared_role | accepted_type_records_supported | accepted_edge_type_records_supported | accepted_fiber_nodes_supported | accepted_fiber_edges_supported | audit_only_count | fallback_only | limitation_or_exception | decision |\n"
        "|---|---|---|---|---|---|---|---|---|---|---|\n"
        "| source_family_alpha | alpha_api | actual_evidence | 1 | 0 | 1 | 0 | 0 | false | none | accepted |\n"
        "| source_family_beta | beta_catalog | actual_evidence | 0 | 1 | 0 | 1 | 0 | false | none | accepted |\n",
        encoding="utf-8",
    )
    (reports / "label_quality_report.md").write_text(
        "# Label Quality Report\n\n"
        "| record_id | record_kind | type_id | label | label_source | opaque_label | source_id_only | human_readable | accepted_for_semantic_count | repair_action | notes |\n"
        "|---|---|---|---|---|---|---|---|---|---|---|\n"
        "| fg.node.fixture | fiber_node | tg.node.artist | Fixture Instance | fixture source | false | false | true | true | none | fixture |\n",
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
    (reports / "domain_membership_audit.md").write_text(
        "# Domain Membership Audit\n\n"
        "domain_membership_audit_status: pending\n",
        encoding="utf-8",
    )
    (reports / "semantic_sample_audit.md").write_text(
        "# Semantic Sample Audit\n\n"
        "semantic_sample_audit_status: pending\n\n"
        "| sample_id | record_id | record_kind | type_id_or_edge_type_id | label | source_id | source_url_or_artifact | field_keys_checked | domain_membership_evidence_checked | pair_specific_edge_evidence_checked | label_quality_checked | judgment | failure_reason | reviewer_notes |\n"
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n"
        "| sample_001 | fg.node.fixture | fiber_node | tg.node.artist | Fixture Instance | fixture_source_001 | https://example.test/alpha | name, practice_area | fixture evidence checked | not applicable for node | passed | passed | no failure | fixture sample |\n",
        encoding="utf-8",
    )
    (reports / "generated_code_runtime_audit.md").write_text(
        "# Generated Code Runtime Audit\n\n"
        "generated_code_used: false\n",
        encoding="utf-8",
    )
    semantic = [
        "# Semantic Acceptance Report",
        "",
        "semantic_acceptance_status: semantic_acceptance_incomplete",
        "graph_build_targets_met: false",
        "candidate_records_counted_toward_target: false",
        "synthetic_or_completion_records_counted_toward_target: false",
        "final_narration_starts_with_incomplete_status: true",
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

batch_id: fixture_batch
parent_loop_id: type_node_discovery
batch_goal: evaluate one fixture item
ordered_item_list:
- fixture_item_001
candidate_items_to_consider:
- fixture_item_001
acceptance_criteria: source-backed domain evidence exists
rejection_criteria: evidence missing
source_batch_cache_path: runs/run_001/source_batches/fixture_batch.json
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
        "graph_intent_fit": "fits fixture validation lens",
        "supported_competency_questions": [
            "What fixture records validate the protocol?"
        ],
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


def test_validate_system_protocol_assets_rejects_missing_make_graph_front_door(
    tmp_path: Path,
) -> None:
    system_root = tmp_path / "system"
    shutil.copytree(SYSTEM_ROOT, system_root)
    schema_path = system_root / "graph_population_protocol_schema.md"
    schema_text = schema_path.read_text(encoding="utf-8")
    schema_text = schema_text.replace("MAKE-GRAPH Front-Door Intent Triage", "")
    schema_path.write_text(schema_text, encoding="utf-8")

    report = validate_system_protocol_assets(system_root)

    assert not report.ok
    assert report.has_code("missing_graph_intent_front_door")


def test_validate_system_protocol_assets_rejects_generate_prompt_without_front_door(
    tmp_path: Path,
) -> None:
    system_root = tmp_path / "system"
    shutil.copytree(SYSTEM_ROOT, system_root)
    prompt_path = system_root / "prompts" / "generate_bundle.md"
    prompt_text = prompt_path.read_text(encoding="utf-8")
    prompt_text = prompt_text.replace(
        "minimal prompt with only domain + target",
        "generated bundle prompt may include a domain and target",
    )
    prompt_path.write_text(prompt_text, encoding="utf-8")

    report = validate_system_protocol_assets(system_root)

    assert not report.ok
    assert report.has_code("missing_graph_intent_front_door")


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


def test_validate_protocol_bundle_rejects_make_graph_without_graph_intent_contract(
    tmp_path: Path,
) -> None:
    bundle = tmp_path / "bundle"
    shutil.copytree(VALID_BUNDLE, bundle)
    _promote_fixture_to_make_graph(bundle)
    _write_make_graph_artifacts(bundle)
    (bundle / "runs" / "run_001" / "reports" / "graph_intent_contract.md").unlink()

    report = validate_protocol_bundle(bundle)

    assert not report.ok
    assert report.has_code("missing_make_graph_artifact") or report.has_code(
        "graph_intent_contract_missing"
    )


def test_validate_protocol_bundle_rejects_incomplete_graph_intent_contract(
    tmp_path: Path,
) -> None:
    bundle = tmp_path / "bundle"
    shutil.copytree(VALID_BUNDLE, bundle)
    _promote_fixture_to_make_graph(bundle)
    _write_make_graph_artifacts(bundle)
    (bundle / "runs" / "run_001" / "reports" / "graph_intent_contract.md").write_text(
        "# Graph Intent Contract\n\ndomain_label: Fixture Domain\n",
        encoding="utf-8",
    )

    report = validate_protocol_bundle(bundle)

    assert not report.ok
    assert report.has_code("graph_intent_contract_incomplete")


def test_validate_protocol_bundle_rejects_semantic_report_without_graph_intent_table(
    tmp_path: Path,
) -> None:
    bundle = tmp_path / "bundle"
    shutil.copytree(VALID_BUNDLE, bundle)
    _promote_fixture_to_make_graph(bundle)
    _write_make_graph_artifacts(bundle)
    report_path = bundle / "runs" / "run_001" / "reports" / "semantic_acceptance_report.md"
    text = report_path.read_text(encoding="utf-8")
    text = text.replace(
        "\n## Graph Intent Alignment Review Table\n\n"
        "| key | value |\n|---|---|\n| initialized | true |\n",
        "\n",
    )
    report_path.write_text(text, encoding="utf-8")

    report = validate_protocol_bundle(bundle)

    assert not report.ok
    assert report.has_code("semantic_acceptance_report_incomplete")


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

def test_validate_protocol_bundle_rejects_source_batch_without_declared_packet(
    tmp_path: Path,
) -> None:
    bundle = tmp_path / "bundle"
    shutil.copytree(VALID_BUNDLE, bundle)
    _promote_fixture_to_make_graph(bundle)
    _write_make_graph_artifacts(bundle)
    source_batches = bundle / "runs" / "run_001" / "source_batches"
    source_batches.mkdir(parents=True, exist_ok=True)
    (source_batches / "orphan_batch.json").write_text(
        json.dumps({"records": []}), encoding="utf-8"
    )

    report = validate_protocol_bundle(bundle)

    assert not report.ok
    assert report.has_code("source_result_without_declared_batch")


def test_validate_protocol_bundle_rejects_generated_code_audit_with_semantic_authority(
    tmp_path: Path,
) -> None:
    bundle = tmp_path / "bundle"
    shutil.copytree(VALID_BUNDLE, bundle)
    _promote_fixture_to_make_graph(bundle)
    _write_make_graph_artifacts(bundle)
    audit = bundle / "runs" / "run_001" / "reports" / "generated_code_runtime_audit.md"
    audit.write_text(
        "# Generated Code Runtime Audit\n\n"
        "generated_code_used: true\n"
        "declared_markdown_authority: runs/run_001/batch_packets/fixture_batch.md\n"
        "mechanical_purpose: validate fixture serialization\n"
        "semantic_non_authority_statement: helper cannot decide graph content\n"
        "inputs: fixture batch\n"
        "outputs: fixture output\n"
        "executed_at: fixture time\n"
        "cleanup_status: retained in fixture\n"
        "safe_to_resume: true\n"
        "semantic_authority: true\n",
        encoding="utf-8",
    )

    report = validate_protocol_bundle(bundle)

    assert not report.ok
    assert report.has_code("generated_code_semantic_authority_detected")


def test_validate_protocol_bundle_rejects_generated_code_with_semantic_specs(
    tmp_path: Path,
) -> None:
    bundle = tmp_path / "bundle"
    shutil.copytree(VALID_BUNDLE, bundle)
    _promote_fixture_to_make_graph(bundle)
    _write_make_graph_artifacts(bundle)
    script = bundle / ".tmp_populate.py"
    script.write_text(
        "TYPE_SPECS = [{'id': 'tg.node.bad'}]\n"
        "EDGE_SPECS = [{'id': 'tg.edge.bad'}]\n",
        encoding="utf-8",
    )
    audit = bundle / "runs" / "run_001" / "reports" / "generated_code_runtime_audit.md"
    audit.write_text(
        "# Generated Code Runtime Audit\n\n"
        "generated_code_used: true\n"
        "declared_markdown_authority: runs/run_001/batch_packets/fixture_batch.md\n"
        "mechanical_purpose: fixture serialization\n"
        "semantic_non_authority_statement: helper cannot decide graph content\n"
        "inputs: fixture batch\n"
        "outputs: fixture output\n"
        "executed_at: fixture time\n"
        "cleanup_status: retained in fixture\n"
        "safe_to_resume: true\n\n"
        "| code_artifact_path | used | purpose | mechanical_only | semantic_decisions_present | markdown_inputs_read | graph_outputs_written | reports_written | authority_decision | notes |\n"
        "|---|---|---|---|---|---|---|---|---|---|\n"
        "| .tmp_populate.py | true | fixture serialization | true | false | runs/run_001/batch_packets/fixture_batch.md | candidate_graphs | none | mechanical_only | fixture |\n",
        encoding="utf-8",
    )

    report = validate_protocol_bundle(bundle)

    assert not report.ok
    assert report.has_code("generated_code_semantic_authority_detected")


def test_validate_protocol_bundle_rejects_source_probe_before_markdown_authority(
    tmp_path: Path,
) -> None:
    bundle = tmp_path / "bundle"
    shutil.copytree(VALID_BUNDLE, bundle)
    _promote_fixture_to_make_graph(bundle)
    _write_make_graph_artifacts(bundle)
    ledger = bundle / "runs" / "run_001" / "reports" / "source_probe_event_ledger.md"
    ledger.write_text(
        "# Source Probe Event Ledger\n\n"
        "| event_id | sequence | event_kind | source_family | source_adapter_id | source_endpoint_or_artifact | triggering_markdown_artifact | triggering_batch_id | allowed_by_contract | result_artifact_path | notes |\n"
        "|---|---|---|---|---|---|---|---|---|---|---|\n"
        "| event_001 | 1 | source_probe | source_family_alpha | alpha_api | https://example.test/alpha | runs/run_001/batch_packets/fixture_batch.md | fixture_batch | true | runs/run_001/source_batches/fixture_batch.json | source came first |\n",
        encoding="utf-8",
    )

    report = validate_protocol_bundle(bundle)

    assert not report.ok
    assert report.has_code("source_probe_before_markdown_authority")


def test_validate_protocol_bundle_rejects_summary_only_semantic_sample_audit(
    tmp_path: Path,
) -> None:
    bundle = tmp_path / "bundle"
    shutil.copytree(VALID_BUNDLE, bundle)
    _promote_fixture_to_make_graph(bundle)
    _write_make_graph_artifacts(bundle)
    _write_shallow_make_graph_records(bundle)
    sample = bundle / "runs" / "run_001" / "reports" / "semantic_sample_audit.md"
    sample.write_text(
        "# Semantic Sample Audit\n\n"
        "semantic_sample_audit_status: passed\n"
        "sampled_node_records: 90\n"
        "sampled_edge_records: 90\n",
        encoding="utf-8",
    )

    report = validate_protocol_bundle(bundle)

    assert not report.ok
    assert report.has_code("semantic_sample_rows_missing")


def test_validate_protocol_bundle_rejects_domain_membership_edge_family(
    tmp_path: Path,
) -> None:
    bundle = tmp_path / "bundle"
    shutil.copytree(VALID_BUNDLE, bundle)
    _promote_fixture_to_make_graph(bundle)
    _write_make_graph_artifacts(bundle)
    _write_shallow_make_graph_records(bundle)
    edge_review = bundle / "runs" / "run_001" / "reports" / "edge_candidate_review.md"
    edge_review.write_text(
        "# Edge Candidate Review\n\n"
        "| candidate_edge_type_id | candidate_edge_label | source_type_id | target_type_id | primitive_relation_claim | relation_family | inverse_or_variant_group | source_evidence | source_family | source_adapter_id | pair_specific_evidence_available | domain_centrality | not_query_derived | not_domain_membership_evidence | not_source_metadata | expected_instance_availability | accepted_for_type_graph | rejection_or_acceptance_reason |\n"
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n"
        "| tg.edge.member_of_source_bucket | Source bucket membership | tg.node.artist | tg.node.artist | source bucket membership | membership_family | canonical | fixture evidence | source_family_alpha | alpha_api | true | weak | true | false | true | available | true | bad edge |\n",
        encoding="utf-8",
    )

    report = validate_protocol_bundle(bundle)

    assert not report.ok
    assert report.has_code("domain_membership_evidence_used_as_target_edge_family")


def test_validate_protocol_bundle_rejects_type_field_padding(
    tmp_path: Path,
) -> None:
    bundle = tmp_path / "bundle"
    shutil.copytree(VALID_BUNDLE, bundle)
    _promote_fixture_to_make_graph(bundle)
    _write_make_graph_artifacts(bundle)
    _write_shallow_make_graph_records(bundle)
    fields = bundle / "runs" / "run_001" / "reports" / "type_field_discovery_report.md"
    fields.write_text(
        "# Type Field Discovery Report\n\n"
        "| type_id | type_label | field_key | field_label | field_kind | field_semantic_role | value_kind | cardinality | source_policy | evidence_source | evidence_summary | domain_descriptive | identity_field | source_adapter_field | provenance_field | accepted | rejection_or_deferral_reason |\n"
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n"
        "| tg.node.artist | Fixture Type | name | Name | scalar | identity | string | required_one | required | fixture source | identity evidence | false | true | false | false | true | accepted |\n"
        "| tg.node.artist | Fixture Type | source_query_context | Source Query Context | scalar | domain | string | optional_one | recommended | fixture source | padding evidence | true | false | false | false | true | padding |\n",
        encoding="utf-8",
    )

    report = validate_protocol_bundle(bundle)

    assert not report.ok
    assert report.has_code("type_field_padding_detected")


def test_validate_protocol_bundle_rejects_opaque_accepted_label(
    tmp_path: Path,
) -> None:
    bundle = tmp_path / "bundle"
    shutil.copytree(VALID_BUNDLE, bundle)
    _promote_fixture_to_make_graph(bundle)
    _write_make_graph_artifacts(bundle)
    _write_shallow_make_graph_records(bundle)
    label = bundle / "runs" / "run_001" / "reports" / "label_quality_report.md"
    label.write_text(
        "# Label Quality Report\n\n"
        "| record_id | record_kind | type_id | label | label_source | opaque_label | source_id_only | human_readable | accepted_for_semantic_count | repair_action | notes |\n"
        "|---|---|---|---|---|---|---|---|---|---|---|\n"
        "| fg.node.fixture | fiber_node | tg.node.artist | Q12345 | fixture source | true | true | false | true | repair required | opaque |\n",
        encoding="utf-8",
    )

    report = validate_protocol_bundle(bundle)

    assert not report.ok
    assert report.has_code("label_quality_limited")


def test_validate_protocol_bundle_rejects_candidate_records_counted_toward_target(
    tmp_path: Path,
) -> None:
    bundle = tmp_path / "bundle"
    shutil.copytree(VALID_BUNDLE, bundle)
    _promote_fixture_to_make_graph(bundle)
    _write_make_graph_artifacts(bundle)
    report_path = bundle / "runs" / "run_001" / "reports" / "semantic_acceptance_report.md"
    text = report_path.read_text(encoding="utf-8")
    text = text.replace(
        "candidate_records_counted_toward_target: false",
        "candidate_records_counted_toward_target: true",
    )
    report_path.write_text(text, encoding="utf-8")

    report = validate_protocol_bundle(bundle)

    assert not report.ok
    assert report.has_code("candidate_records_counted_toward_target")


def test_validate_protocol_bundle_rejects_semantic_completion_counter_contradiction(
    tmp_path: Path,
) -> None:
    bundle = tmp_path / "bundle"
    shutil.copytree(VALID_BUNDLE, bundle)
    _promote_fixture_to_make_graph(bundle)
    _write_make_graph_artifacts(bundle)
    report_path = bundle / "runs" / "run_001" / "reports" / "semantic_acceptance_report.md"
    text = report_path.read_text(encoding="utf-8")
    text = text.replace(
        "semantic_acceptance_status: semantic_acceptance_incomplete",
        "semantic_acceptance_status: edge_evidence_limited",
    )
    text = text.replace("graph_build_targets_met: false", "graph_build_targets_met: true")
    report_path.write_text(text, encoding="utf-8")

    report = validate_protocol_bundle(bundle)

    assert not report.ok
    assert report.has_code("semantic_report_counter_contradiction")


def test_validate_protocol_bundle_rejects_passed_semantic_status_without_audits(
    tmp_path: Path,
) -> None:
    bundle = tmp_path / "bundle"
    shutil.copytree(VALID_BUNDLE, bundle)
    _promote_fixture_to_make_graph(bundle)
    _write_make_graph_artifacts(bundle)
    report_path = bundle / "runs" / "run_001" / "reports" / "semantic_acceptance_report.md"
    text = report_path.read_text(encoding="utf-8")
    text = text.replace(
        "semantic_acceptance_status: semantic_acceptance_incomplete",
        "semantic_acceptance_status: passed",
    )
    text = text.replace("graph_build_targets_met: false", "graph_build_targets_met: true")
    report_path.write_text(text, encoding="utf-8")

    report = validate_protocol_bundle(bundle)

    assert not report.ok
    assert report.has_code("domain_membership_audit_failed")
    assert report.has_code("semantic_sample_audit_missing")


def test_validate_protocol_bundle_rejects_incomplete_status_with_success_narration(
    tmp_path: Path,
) -> None:
    bundle = tmp_path / "bundle"
    shutil.copytree(VALID_BUNDLE, bundle)
    _promote_fixture_to_make_graph(bundle)
    _write_make_graph_artifacts(bundle)
    report_path = bundle / "runs" / "run_001" / "reports" / "semantic_acceptance_report.md"
    text = report_path.read_text(encoding="utf-8")
    text = text.replace(
        "final_narration_starts_with_incomplete_status: true",
        "final_narration_starts_with_incomplete_status: false",
    )
    report_path.write_text(text, encoding="utf-8")

    report = validate_protocol_bundle(bundle)

    assert not report.ok
    assert report.has_code("completion_narration_inconsistent")

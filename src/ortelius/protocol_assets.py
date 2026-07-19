"""Read-only validation for graph-population protocol assets."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from ortelius.graph_io import GraphLoadError, load_graph_bundle
from ortelius.validate import validate_graph_bundle

IssueSeverity = Literal["error", "warning"]

REQUIRED_LOOP_SPEC_HEADINGS = (
    "Loop Identity",
    "Inputs",
    "Iterator",
    "Current Item Shape",
    "Action Template",
    "Allowed Writes",
    "Source Boundaries",
    "Evidence Required",
    "Validation Required",
    "Completion Rule",
    "Semantic Acceptance Gate",
    "Recovery Policy",
    "Batch Execution",
    "Stop Conditions",
    "Handoff",
)

REQUIRED_BUNDLE_MANIFEST_FIELDS = (
    "schema_version",
    "protocol_id",
    "domain",
    "graphs",
    "documents",
    "ordered_loop_specs",
    "runs",
    "run_contract_completeness",
)

MAKE_GRAPH_REQUIRED_ARTIFACT_TEMPLATES = (
    "control_loop_plan.md",
    "runs/<run_id>/reports/generated_bundle_acceptance_report.md",
    "runs/<run_id>/reports/graph_intent_contract.md",
    "runs/<run_id>/reports/source_landscape_map.md",
    "runs/<run_id>/reports/source_family_registry.md",
    "runs/<run_id>/source_adapter_candidate_frontier.md",
    "runs/<run_id>/reports/source_strategy_decision_log.md",
    "runs/<run_id>/reports/joint_population_feasibility_plan.md",
    "runs/<run_id>/reports/endpoint_reservation_plan.md",
    "runs/<run_id>/reports/semantic_acceptance_report.md",
)

SEMANTIC_ACCEPTANCE_REQUIRED_TABLES = (
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
    "Counter Reconciliation Table",
    "Final Decision",
)

GRAPH_INTENT_CONTRACT_REQUIRED_TERMS = (
    "domain_label",
    "domain_lens",
    "confirmation_status",
    "intent_confirmation_policy",
    "downstream_gate",
)

PASSING_GRAPH_INTENT_STATUS_MARKERS = (
    "graph_intent_status: confirmed",
    "graph_intent_status: explicitly_authorized_inference",
    "confirmation_status: confirmed",
    "confirmation_status: explicitly_authorized_inference",
)

GRAPH_INTENT_RECORD_KEYS = (
    "graph_intent_fit",
    "intent_fit",
    "supported_competency_questions",
)

BATCH_PACKET_REQUIRED_TERMS = (
    "parent_loop_id",
    "batch_goal",
    "ordered_item_list",
    "acceptance_criteria",
    "rejection_criteria",
    "write_targets",
    "cursor_update_rule",
    "resume_point",
)

BATCH_PACKET_PLACEHOLDER_MARKERS = (
    "status: see execution log and reports",
    "see execution log and reports",
    "see generated output",
    "see report",
)

SOURCE_OR_IDENTITY_FIELD_NAMES = frozenset(
    {
        "id",
        "name",
        "label",
        "title",
        "description",
        "source",
        "sources",
        "source_url",
        "source_urls",
        "source_scope",
        "source_category",
        "source_class",
        "source_adapter",
        "source_adapter_id",
        "source_endpoint",
        "source_record",
        "wikidata_qid",
        "wikidata_url",
        "external_id",
        "external_url",
        "type_membership_basis",
        "domain_note",
        "coordinate",
        "coordinates",
        "latitude",
        "longitude",
    }
)


@dataclass(frozen=True)
class ProtocolAssetIssue:
    severity: IssueSeverity
    code: str
    message: str
    file_path: str | None = None


@dataclass(frozen=True)
class ProtocolAssetReport:
    issues: tuple[ProtocolAssetIssue, ...]

    @property
    def ok(self) -> bool:
        return not any(issue.severity == "error" for issue in self.issues)

    @property
    def error_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "warning")

    def has_code(self, code: str) -> bool:
        return any(issue.code == code for issue in self.issues)


def validate_system_protocol_assets(system_root: str | Path) -> ProtocolAssetReport:
    root = Path(system_root)
    issues: list[ProtocolAssetIssue] = []

    manifest = _read_json_object(root / "manifest.json", issues, missing_code="missing_manifest")
    if manifest is None:
        return ProtocolAssetReport(tuple(issues))

    if not manifest.get("domain_agnostic"):
        _add(
            issues,
            "error",
            "system_protocol_not_domain_agnostic",
            "System protocol manifest must declare domain_agnostic: true.",
            root / "manifest.json",
        )

    version = _str_value(manifest.get("version"))
    if version and root.name != version:
        _add(
            issues,
            "error",
            "system_protocol_version_mismatch",
            f"Manifest version {version!r} does not match directory {root.name!r}.",
            root / "manifest.json",
        )

    documents = _dict_value(manifest.get("documents"))
    protocol_schema = _require_relative_file(
        root,
        documents,
        "protocol_schema",
        issues,
        "missing_system_protocol_document",
    )
    control_protocol = _require_relative_file(
        root,
        documents,
        "control_protocol",
        issues,
        "missing_system_protocol_document",
    )
    _require_relative_file(root, documents, "readme", issues, "missing_system_protocol_document")

    prompts = _dict_value(manifest.get("prompts"))
    generate_prompt = _require_relative_file(
        root,
        prompts,
        "generate_bundle",
        issues,
        "missing_system_protocol_prompt",
    )
    execute_prompt = _require_relative_file(
        root,
        prompts,
        "execute_bundle",
        issues,
        "missing_system_protocol_prompt",
    )

    if protocol_schema is not None:
        _require_text(protocol_schema, "GENERATE-BUNDLE", issues, "missing_trigger_phrase")
        _require_text(
            protocol_schema,
            "Graph Tool Compatibility Contract",
            issues,
            "missing_graph_tool_compatibility_section",
        )
        _require_text(
            protocol_schema,
            "MAKE-GRAPH Front-Door Intent Triage",
            issues,
            "missing_graph_intent_front_door",
        )
        _require_text(
            protocol_schema,
            "minimal human prompt containing only `MAKE-GRAPH`",
            issues,
            "missing_graph_intent_front_door",
        )
        _require_text(
            protocol_schema,
            "Source probing before this front-door triage passes is a loop-order violation.",
            issues,
            "missing_graph_intent_front_door",
        )
        _require_text(
            protocol_schema,
            "Graph Intent Alignment Directive",
            issues,
            "missing_graph_intent_contract",
        )
        _require_text(
            protocol_schema,
            "graph_intent_contract.md",
            issues,
            "missing_graph_intent_contract",
        )
        _require_text(
            protocol_schema,
            "domain_lens",
            issues,
            "missing_graph_intent_contract",
        )
        _require_text(
            protocol_schema,
            "competency_questions",
            issues,
            "missing_graph_intent_contract",
        )
        _require_text(
            protocol_schema,
            "Source Landscape, Domain Membership, And Joint Planning Directive",
            issues,
            "missing_source_landscape_contract",
        )
        _require_text(
            protocol_schema,
            "joint_population_feasibility_gate",
            issues,
            "missing_joint_population_contract",
        )
    if control_protocol is not None:
        _require_text(control_protocol, "EXECUTE-BUNDLE", issues, "missing_trigger_phrase")
        _require_text(
            control_protocol,
            "Graph Tool Compatibility Gates",
            issues,
            "missing_graph_tool_compatibility_section",
        )
        _require_text(
            control_protocol,
            "Raw MAKE-GRAPH Front-Door Rule",
            issues,
            "missing_graph_intent_front_door",
        )
        _require_text(
            control_protocol,
            "GraphIntentAlignment.Domain.ResolveIntent",
            issues,
            "missing_graph_intent_front_door",
        )
        _require_text(
            control_protocol,
            "Graph Intent Contract Gate",
            issues,
            "missing_graph_intent_contract",
        )
        _require_text(
            control_protocol,
            "graph_intent_contract_missing",
            issues,
            "missing_graph_intent_contract",
        )
        _require_text(
            control_protocol,
            "Graph Intent Alignment Review Table",
            issues,
            "missing_graph_intent_contract",
        )
        _require_text(
            control_protocol,
            "Source Landscape And Joint Population Gates",
            issues,
            "missing_source_landscape_contract",
        )
        _require_text(
            control_protocol,
            "Markdown-Controlled Runtime Boundary",
            issues,
            "missing_markdown_runtime_boundary",
        )
    if generate_prompt is not None:
        _require_text(generate_prompt, "GENERATE-BUNDLE", issues, "missing_trigger_phrase")
        _require_text(generate_prompt, "domain_lens", issues, "missing_graph_intent_contract")
        _require_text(
            generate_prompt,
            "minimal prompt with only domain + target",
            issues,
            "missing_graph_intent_front_door",
        )
    if execute_prompt is not None:
        _require_text(execute_prompt, "EXECUTE-BUNDLE", issues, "missing_trigger_phrase")
        _require_text(
            execute_prompt,
            "graph_intent_contract.md",
            issues,
            "missing_graph_intent_contract",
        )

    return ProtocolAssetReport(tuple(issues))


def validate_protocol_bundle(protocol_root: str | Path) -> ProtocolAssetReport:
    root = Path(protocol_root)
    issues: list[ProtocolAssetIssue] = []

    manifest_path = root / "manifest.json"
    manifest = _read_json_object(manifest_path, issues, missing_code="missing_bundle_file")
    if manifest is None:
        return ProtocolAssetReport(tuple(issues))

    _validate_required_manifest_fields(manifest, manifest_path, issues)

    documents = _dict_value(manifest.get("documents"))
    domain_protocol_path = _str_value(documents.get("domain_protocol"))
    if domain_protocol_path:
        _require_file(root / domain_protocol_path, issues, "missing_bundle_file")
    else:
        _add(
            issues,
            "error",
            "missing_bundle_file",
            "Manifest documents.domain_protocol is missing.",
            manifest_path,
        )

    ordered_loop_specs = manifest.get("ordered_loop_specs")
    if not isinstance(ordered_loop_specs, list) or not ordered_loop_specs:
        _add(
            issues,
            "error",
            "incomplete_run_contract",
            "Manifest must contain a nonempty ordered_loop_specs list.",
            manifest_path,
        )
    else:
        for spec_path_value in ordered_loop_specs:
            if not isinstance(spec_path_value, str):
                _add(
                    issues,
                    "error",
                    "incomplete_run_contract",
                    "Each ordered_loop_specs entry must be a string.",
                    manifest_path,
                )
                continue
            _validate_loop_spec(root / spec_path_value, issues)

    run_contract = _dict_value(manifest.get("run_contract_completeness"))
    if run_contract.get("status") != "complete":
        _add(
            issues,
            "error",
            "incomplete_run_contract",
            "run_contract_completeness.status must be complete.",
            manifest_path,
        )

    _validate_cursor_and_log(root, manifest, issues)
    _validate_graph_contract(root, manifest, issues)
    _validate_make_graph_semantic_contract(root, manifest, issues)

    return ProtocolAssetReport(tuple(issues))


def inspect_protocol_bundle(protocol_root: str | Path) -> dict[str, Any]:
    root = Path(protocol_root)
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    graphs = _dict_value(manifest.get("graphs"))
    runs = _dict_value(manifest.get("runs"))
    ordered_loop_specs = manifest.get("ordered_loop_specs", [])
    return {
        "protocol_id": manifest.get("protocol_id", ""),
        "domain_slug": _dict_value(manifest.get("domain")).get("slug", ""),
        "type_graph_id": graphs.get("type_graph_id", ""),
        "fiber_graph_id": graphs.get("fiber_graph_id", ""),
        "candidate_graph_root": graphs.get("candidate_graph_root", ""),
        "ordered_loop_specs": (
            len(ordered_loop_specs) if isinstance(ordered_loop_specs, list) else 0
        ),
        "default_run_id": runs.get("default_run_id", ""),
        "run_contract_status": _dict_value(
            manifest.get("run_contract_completeness")
        ).get("status", ""),
    }


def _validate_required_manifest_fields(
    manifest: dict[str, Any],
    manifest_path: Path,
    issues: list[ProtocolAssetIssue],
) -> None:
    for field in REQUIRED_BUNDLE_MANIFEST_FIELDS:
        if field not in manifest:
            code = (
                "incomplete_run_contract"
                if field in {"ordered_loop_specs", "run_contract_completeness"}
                else "missing_manifest_field"
            )
            _add(issues, "error", code, f"Manifest is missing {field!r}.", manifest_path)


def _validate_loop_spec(path: Path, issues: list[ProtocolAssetIssue]) -> None:
    if not _require_file(path, issues, "missing_loop_spec_file"):
        return
    text = path.read_text(encoding="utf-8")
    sections = _markdown_sections(text)
    for heading in REQUIRED_LOOP_SPEC_HEADINGS:
        if heading in sections:
            continue
        code = "missing_loop_spec_heading"
        if heading == "Source Boundaries":
            code = "missing_source_boundary"
        elif heading == "Validation Required":
            code = "missing_validation_rule"
        elif heading == "Semantic Acceptance Gate":
            code = "missing_semantic_acceptance_gate"
        elif heading == "Recovery Policy":
            code = "missing_recovery_policy"
        elif heading == "Batch Execution":
            code = "missing_batch_execution_rule"
        _add(issues, "error", code, f"Loop spec is missing heading {heading!r}.", path)

    validation_section = sections.get("Validation Required", "")
    if validation_section and not _section_has_nonempty_value(
        validation_section,
        ("validation_command", "validation_checklist", "validation_unavailable_rule"),
    ):
        _add(
            issues,
            "error",
            "missing_validation_rule",
            "Validation Required section must define command, checklist, or unavailable rule.",
            path,
        )

    semantic_section = sections.get("Semantic Acceptance Gate", "")
    if semantic_section and not _section_has_nonempty_value(
        semantic_section,
        (
            "candidate_counting_rule",
            "accepted_counting_rule",
            "semantic_gate",
            "target_progress_rule",
        ),
    ):
        _add(
            issues,
            "error",
            "missing_semantic_acceptance_gate",
            "Semantic Acceptance Gate section must define candidate/accepted "
            "counting, semantic gate, or target progress rule.",
            path,
        )

    recovery_section = sections.get("Recovery Policy", "")
    if recovery_section and not _section_has_nonempty_value(
        recovery_section,
        (
            "recoverable_failure_classes",
            "recovery_ladder",
            "recovery_attempt_budget",
            "resume_condition",
            "exhaustion_condition",
        ),
    ):
        _add(
            issues,
            "error",
            "missing_recovery_policy",
            "Recovery Policy section must define failure classes, ladder, "
            "budget, resume condition, or exhaustion condition.",
            path,
        )

    batch_section = sections.get("Batch Execution", "")
    if batch_section and not _section_has_nonempty_value(
        batch_section,
        (
            "batch_execution_meaning",
            "batch_plan_path",
            "batch_packet_path",
            "batch_size",
            "checkpoint_rule",
        ),
    ):
        _add(
            issues,
            "error",
            "missing_batch_execution_rule",
            "Batch Execution section must define meaning, plan path, packet "
            "path, size, or checkpoint rule.",
            path,
        )


def _validate_cursor_and_log(
    root: Path,
    manifest: dict[str, Any],
    issues: list[ProtocolAssetIssue],
) -> None:
    runs = _dict_value(manifest.get("runs"))
    cursor = _str_value(runs.get("default_cursor"))
    execution_log = _str_value(runs.get("default_execution_log"))

    if cursor:
        _read_json_object(
            root / cursor,
            issues,
            missing_code="missing_bundle_file",
            invalid_code="invalid_cursor_json",
        )
    else:
        _add(issues, "error", "missing_bundle_file", "Default cursor path is missing.", root)

    if execution_log:
        _require_file(root / execution_log, issues, "missing_bundle_file")
    else:
        _add(issues, "error", "missing_bundle_file", "Default execution log path is missing.", root)


def _validate_graph_contract(
    root: Path,
    manifest: dict[str, Any],
    issues: list[ProtocolAssetIssue],
) -> None:
    graphs = _dict_value(manifest.get("graphs"))
    candidate_graph_root = _str_value(graphs.get("candidate_graph_root"))
    type_graph_id = _str_value(graphs.get("type_graph_id"))
    fiber_graph_id = _str_value(graphs.get("fiber_graph_id"))

    if not candidate_graph_root or not type_graph_id or not fiber_graph_id:
        _add(
            issues,
            "error",
            "incomplete_run_contract",
            "graphs must define candidate_graph_root, type_graph_id, and fiber_graph_id.",
            root / "manifest.json",
        )
        return

    declared_paths = _dict_value(graphs.get("declared_graph_paths"))
    expected_paths = {
        "type_nodes": f"{candidate_graph_root}/{type_graph_id}/nodes.json",
        "type_edges": f"{candidate_graph_root}/{type_graph_id}/edges.json",
        "fiber_nodes": f"{candidate_graph_root}/{fiber_graph_id}/nodes.json",
        "fiber_edges": f"{candidate_graph_root}/{fiber_graph_id}/edges.json",
    }
    for key, expected in expected_paths.items():
        if declared_paths.get(key) != expected:
            _add(
                issues,
                "error",
                "path_reconciliation_required",
                f"declared_graph_paths.{key} must be {expected!r}.",
                root / "manifest.json",
            )

    graph_root = root / candidate_graph_root
    try:
        bundle = load_graph_bundle(
            graph_root,
            type_graph_id=type_graph_id,
            fiber_graph_id=fiber_graph_id,
        )
    except GraphLoadError as exc:
        _add(issues, "error", "invalid_graph_json", str(exc), graph_root)
        return

    graph_report = validate_graph_bundle(bundle)
    if not graph_report.ok:
        summary = ", ".join(issue.code for issue in graph_report.issues[:5])
        _add(issues, "error", "validation_failed", summary, graph_root)


def _validate_make_graph_semantic_contract(
    root: Path,
    manifest: dict[str, Any],
    issues: list[ProtocolAssetIssue],
) -> None:
    if not _is_make_graph_manifest(manifest):
        return

    run_id = _default_run_id(manifest)
    if not run_id:
        _add(
            issues,
            "error",
            "missing_bundle_file",
            "MAKE-GRAPH manifest must define runs.default_run_id.",
            root / "manifest.json",
        )
        return

    for template in MAKE_GRAPH_REQUIRED_ARTIFACT_TEMPLATES:
        _require_file(
            root / template.replace("<run_id>", run_id),
            issues,
            "missing_make_graph_artifact",
        )

    semantic_report_path = root / f"runs/{run_id}/reports/semantic_acceptance_report.md"
    semantic_report = _read_text_or_empty(semantic_report_path)
    if semantic_report:
        _validate_semantic_acceptance_report(semantic_report_path, semantic_report, issues)

    _validate_graph_intent_surface(root, run_id, manifest, issues)
    _validate_source_family_surface(root, run_id, manifest, issues)
    _validate_batch_packet_surfaces(root, run_id, manifest, issues)
    _validate_make_graph_record_semantics(root, manifest, issues)


def _is_make_graph_manifest(manifest: dict[str, Any]) -> bool:
    graph_build_target = _dict_value(manifest.get("graph_build_target"))
    return (
        manifest.get("front_door_mode") == "MAKE-GRAPH"
        or graph_build_target.get("mode") == "MAKE-GRAPH"
        or graph_build_target.get("front_door_mode") == "MAKE-GRAPH"
        or graph_build_target.get("completion_target") == "graph_build_targets_met"
    )


def _default_run_id(manifest: dict[str, Any]) -> str:
    return _str_value(_dict_value(manifest.get("runs")).get("default_run_id"))


def _validate_semantic_acceptance_report(
    path: Path,
    text: str,
    issues: list[ProtocolAssetIssue],
) -> None:
    for table in SEMANTIC_ACCEPTANCE_REQUIRED_TABLES:
        if table not in text:
            _add(
                issues,
                "error",
                "semantic_acceptance_report_incomplete",
                f"Semantic acceptance report is missing {table!r}.",
                path,
            )

    if "accepted_field_complete_fiber_nodes" in text and "domain_field_complete" not in text:
        _add(
            issues,
            "error",
            "semantic_acceptance_report_incomplete",
            "Semantic acceptance report claims field-complete fiber nodes without "
            "distinguishing domain_field_complete from identity scaffold state.",
            path,
        )


def _validate_graph_intent_surface(
    root: Path,
    run_id: str,
    manifest: dict[str, Any],
    issues: list[ProtocolAssetIssue],
) -> None:
    manifest_path = root / "manifest.json"
    graph_intent = _dict_value(manifest.get("graph_intent"))
    if not graph_intent:
        _add(
            issues,
            "error",
            "graph_intent_contract_missing",
            "MAKE-GRAPH manifest must define graph_intent metadata.",
            manifest_path,
        )

    contract_path_value = _str_value(graph_intent.get("contract_path"))
    if not contract_path_value:
        contract_path_value = f"runs/{run_id}/reports/graph_intent_contract.md"
        _add(
            issues,
            "error",
            "graph_intent_contract_incomplete",
            "MAKE-GRAPH graph_intent must define contract_path.",
            manifest_path,
        )

    contract_path = root / contract_path_value
    if not _require_file(contract_path, issues, "graph_intent_contract_missing"):
        return

    contract_text = contract_path.read_text(encoding="utf-8")
    contract_lower = contract_text.lower()
    combined = f"{contract_text}\n{json.dumps(graph_intent, sort_keys=True)}".lower()
    for term in GRAPH_INTENT_CONTRACT_REQUIRED_TERMS:
        if term.lower() not in contract_lower:
            _add(
                issues,
                "error",
                "graph_intent_contract_incomplete",
                f"Graph intent contract is missing required term {term!r}.",
                contract_path,
            )

    if not any(marker in combined for marker in PASSING_GRAPH_INTENT_STATUS_MARKERS):
        _add(
            issues,
            "error",
            "graph_intent_unconfirmed",
            "Graph intent contract must record confirmed or explicitly authorized status.",
            contract_path,
        )

    if "downstream_gate" not in combined:
        _add(
            issues,
            "error",
            "graph_intent_downstream_gate_missing",
            "Graph intent contract must define a downstream_gate.",
            contract_path,
        )

    ordered_loop_specs = manifest.get("ordered_loop_specs")
    if isinstance(ordered_loop_specs, list):
        lowered_specs = [str(item).lower() for item in ordered_loop_specs]
        intent_indexes = [
            idx for idx, value in enumerate(lowered_specs) if "graph_intent" in value
        ]
        if not intent_indexes:
            _add(
                issues,
                "error",
                "graph_intent_loop_order_invalid",
                "MAKE-GRAPH ordered_loop_specs must include graph-intent alignment.",
                manifest_path,
            )
        else:
            intent_index = intent_indexes[0]
            first_semantic_index = next(
                (
                    idx
                    for idx, value in enumerate(lowered_specs)
                    if "source_landscape" in value
                    or "type_set" in value
                    or "type_node_discovery" in value
                ),
                None,
            )
            if first_semantic_index is not None and intent_index > first_semantic_index:
                _add(
                    issues,
                    "error",
                    "graph_intent_loop_order_invalid",
                    "Graph-intent alignment must precede source/type discovery loops.",
                    manifest_path,
                )


def _validate_source_family_surface(
    root: Path,
    run_id: str,
    manifest: dict[str, Any],
    issues: list[ProtocolAssetIssue],
) -> None:
    registry_path = root / f"runs/{run_id}/reports/source_family_registry.md"
    landscape_path = root / f"runs/{run_id}/reports/source_landscape_map.md"
    decision_path = root / f"runs/{run_id}/reports/source_strategy_decision_log.md"
    combined = "\n".join(
        _read_text_or_empty(path) for path in (registry_path, landscape_path, decision_path)
    )
    if not combined.strip():
        return

    required_terms = ("source_family", "source_adapter", "source_endpoint", "source_record")
    for term in required_terms:
        if term not in combined:
            _add(
                issues,
                "error",
                "source_landscape_incomplete",
                f"Source landscape artifacts must distinguish {term}.",
                landscape_path,
            )

    if _graph_has_target_scale_records(root, manifest):
        families = _extract_source_families(combined)
        has_exception = "single_authoritative_source_family_exception" in combined
        if len(families) < 2 and not has_exception:
            _add(
                issues,
                "error",
                "source_family_monoculture",
                "Target-scale MAKE-GRAPH records require at least two source "
                "families or a logged single_authoritative_source_family_exception.",
                registry_path,
            )


def _extract_source_families(text: str) -> set[str]:
    families: set[str] = set()
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        if key.strip().lower() not in {"source_family", "source family"}:
            continue
        cleaned = value.strip().strip("`* -").lower()
        if cleaned:
            families.add(cleaned)
    return families


def _validate_batch_packet_surfaces(
    root: Path,
    run_id: str,
    manifest: dict[str, Any],
    issues: list[ProtocolAssetIssue],
) -> None:
    packet_root = root / f"runs/{run_id}/batch_packets"
    if not packet_root.exists():
        if _graph_has_target_scale_records(root, manifest):
            _add(
                issues,
                "error",
                "missing_batch_packet",
                "MAKE-GRAPH target-scale records require Markdown batch packets.",
                packet_root,
            )
        return

    packets = sorted(packet_root.glob("*.md"))
    if not packets and _graph_has_target_scale_records(root, manifest):
        _add(
            issues,
            "error",
            "missing_batch_packet",
            "MAKE-GRAPH target-scale records require Markdown batch packets.",
            packet_root,
        )
        return

    for packet in packets:
        text = packet.read_text(encoding="utf-8")
        lowered = text.lower()
        if any(marker in lowered for marker in BATCH_PACKET_PLACEHOLDER_MARKERS):
            _add(
                issues,
                "error",
                "placeholder_batch_packet",
                "Batch packet is a placeholder instead of a nested Markdown work program.",
                packet,
            )
        missing_terms = [term for term in BATCH_PACKET_REQUIRED_TERMS if term not in text]
        if missing_terms:
            _add(
                issues,
                "error",
                "incomplete_batch_packet",
                f"Batch packet is missing required terms: {', '.join(missing_terms)}.",
                packet,
            )


def _validate_make_graph_record_semantics(
    root: Path,
    manifest: dict[str, Any],
    issues: list[ProtocolAssetIssue],
) -> None:
    graphs = _dict_value(manifest.get("graphs"))
    graph_root = root / _str_value(graphs.get("candidate_graph_root"))
    type_graph_id = _str_value(graphs.get("type_graph_id"))
    fiber_graph_id = _str_value(graphs.get("fiber_graph_id"))
    if not graph_root or not type_graph_id or not fiber_graph_id:
        return

    try:
        bundle = load_graph_bundle(
            graph_root,
            type_graph_id=type_graph_id,
            fiber_graph_id=fiber_graph_id,
        )
    except GraphLoadError:
        return

    for record in bundle.type_node_records:
        raw = record.raw
        if record.status not in {"accepted", "candidate", "reviewed"}:
            continue
        if not isinstance(raw.get("fiber_population_eligible"), bool):
            _add(
                issues,
                "error",
                "missing_fiber_population_eligibility",
                "MAKE-GRAPH type nodes must explicitly set fiber_population_eligible.",
                graph_root,
            )
            break

    accepted_or_eligible_type_nodes = [
        record
        for record in bundle.type_node_records
        if record.status == "accepted" or record.raw.get("fiber_population_eligible") is True
    ]
    for record in accepted_or_eligible_type_nodes:
        raw = record.raw
        for key in (
            "type_membership_predicate",
            "domain_membership_predicate",
            "domain_exclusion_predicate",
        ):
            if not _contains_key(raw, key):
                _add(
                    issues,
                    "error",
                    "missing_domain_membership_policy",
                    f"Type node {record.id or '<unknown>'} is missing {key}.",
                    graph_root,
                )
                break
        if not _contains_any_key(raw, GRAPH_INTENT_RECORD_KEYS):
            _add(
                issues,
                "error",
                "record_graph_intent_fit_missing",
                f"Type node {record.id or '<unknown>'} is missing graph-intent fit metadata.",
                graph_root,
            )
        domain_field_count = _domain_descriptive_field_count(raw)
        if domain_field_count < 3:
            _add(
                issues,
                "error",
                "type_field_richness_incomplete",
                f"Type node {record.id or '<unknown>'} has fewer than three "
                "domain_descriptive_field entries.",
                graph_root,
            )

    if bundle.fiber_node_records:
        for record in bundle.fiber_node_records:
            raw = record.raw
            if record.status != "accepted":
                continue
            if not _contains_key(raw, "domain_membership_basis") and not _contains_key(
                raw, "domain_membership_evidence"
            ):
                _add(
                    issues,
                    "error",
                    "fiber_node_domain_membership_missing",
                    "Accepted MAKE-GRAPH fiber nodes must record domain-membership evidence, "
                    "not only source/type membership.",
                    graph_root,
                )
                break

    expected_edges = _expected_edge_instances(manifest)
    if expected_edges > 0:
        for record in bundle.type_edge_records:
            if record.status != "accepted":
                continue
            if not _contains_any_key(record.raw, GRAPH_INTENT_RECORD_KEYS):
                _add(
                    issues,
                    "error",
                    "record_graph_intent_fit_missing",
                    f"Type edge {record.id or '<unknown>'} is missing graph-intent fit metadata.",
                    graph_root,
                )
                break
            if not _contains_key(record.raw, "pair_evidence_feasibility_status"):
                _add(
                    issues,
                    "error",
                    "edge_feasibility_missing",
                    f"Type edge {record.id or '<unknown>'} is missing "
                    "pair_evidence_feasibility_status for edge-target planning.",
                    graph_root,
                )
                break


def _graph_has_target_scale_records(root: Path, manifest: dict[str, Any]) -> bool:
    graphs = _dict_value(manifest.get("graphs"))
    graph_root = root / _str_value(graphs.get("candidate_graph_root"))
    type_graph_id = _str_value(graphs.get("type_graph_id"))
    fiber_graph_id = _str_value(graphs.get("fiber_graph_id"))
    if not graph_root or not type_graph_id or not fiber_graph_id:
        return False
    try:
        bundle = load_graph_bundle(
            graph_root,
            type_graph_id=type_graph_id,
            fiber_graph_id=fiber_graph_id,
        )
    except GraphLoadError:
        return False
    return bool(
        bundle.type_node_records
        or bundle.type_edge_records
        or bundle.fiber_node_records
        or bundle.fiber_edge_records
    )


def _expected_edge_instances(manifest: dict[str, Any]) -> int:
    graph_build_target = _dict_value(manifest.get("graph_build_target"))
    fiber_targets = _dict_value(graph_build_target.get("fiber_graph_targets"))
    for key in ("expected_edge_instances", "edge_instance_count"):
        value = fiber_targets.get(key)
        if isinstance(value, int):
            return value
    instances_per_edge_type = fiber_targets.get("instances_per_edge_type")
    edge_targets = _dict_value(graph_build_target.get("type_graph_targets"))
    edge_type_count = edge_targets.get("edge_type_count")
    if isinstance(instances_per_edge_type, int) and isinstance(edge_type_count, int):
        return instances_per_edge_type * edge_type_count
    return 0


def _record_status(record: dict[str, Any]) -> str:
    return _str_value(record.get("status"))


def _domain_descriptive_field_count(record: dict[str, Any]) -> int:
    fields = _type_field_mapping(record)
    count = 0
    for name, metadata in fields.items():
        if name in SOURCE_OR_IDENTITY_FIELD_NAMES:
            continue
        if isinstance(metadata, dict) and metadata.get("field_tier") == "domain_descriptive_field":
            count += 1
    return count


def _type_field_mapping(record: dict[str, Any]) -> dict[str, Any]:
    type_fields = record.get("type_fields")
    if isinstance(type_fields, dict):
        nested = type_fields.get("fields")
        if isinstance(nested, dict):
            return nested
        return type_fields
    if isinstance(type_fields, list):
        result: dict[str, Any] = {}
        for item in type_fields:
            if not isinstance(item, dict):
                continue
            name = _str_value(item.get("name")) or _str_value(item.get("field_id"))
            if name:
                result[name] = item
        return result
    return {}


def _contains_any_key(value: Any, keys: tuple[str, ...]) -> bool:
    return any(_contains_key(value, key) for key in keys)


def _contains_key(value: Any, key: str) -> bool:
    if isinstance(value, dict):
        if key in value:
            return True
        return any(_contains_key(child, key) for child in value.values())
    if isinstance(value, list):
        return any(_contains_key(child, key) for child in value)
    return False


def _read_text_or_empty(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def _read_json_object(
    path: Path,
    issues: list[ProtocolAssetIssue],
    *,
    missing_code: str,
    invalid_code: str = "invalid_json",
) -> dict[str, Any] | None:
    if not path.exists():
        _add(issues, "error", missing_code, f"Missing file: {path}", path)
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        _add(issues, "error", invalid_code, f"Invalid JSON in {path}: {exc}", path)
        return None
    if not isinstance(raw, dict):
        _add(issues, "error", invalid_code, f"JSON file must contain an object: {path}", path)
        return None
    return raw


def _require_relative_file(
    root: Path,
    mapping: dict[str, Any],
    key: str,
    issues: list[ProtocolAssetIssue],
    code: str,
) -> Path | None:
    value = _str_value(mapping.get(key))
    if not value:
        _add(issues, "error", code, f"Missing path for {key!r}.", root)
        return None
    path = root / value
    return path if _require_file(path, issues, code) else None


def _require_file(path: Path, issues: list[ProtocolAssetIssue], code: str) -> bool:
    if path.exists() and path.is_file():
        return True
    _add(issues, "error", code, f"Missing file: {path}", path)
    return False


def _require_text(
    path: Path,
    needle: str,
    issues: list[ProtocolAssetIssue],
    code: str,
) -> None:
    text = path.read_text(encoding="utf-8")
    if needle not in text:
        _add(issues, "error", code, f"Missing required text {needle!r}.", path)


def _markdown_sections(text: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in text.splitlines():
        if line.startswith("## ") and not line.startswith("### "):
            current = line[3:].strip()
            sections.setdefault(current, [])
            continue
        if current is not None:
            sections[current].append(line)
    return {key: "\n".join(value).strip() for key, value in sections.items()}


def _section_has_nonempty_value(section: str, keys: tuple[str, ...]) -> bool:
    for line in section.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        if key.strip() in keys and value.strip():
            return True
    return False


def _dict_value(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _str_value(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _add(
    issues: list[ProtocolAssetIssue],
    severity: IssueSeverity,
    code: str,
    message: str,
    path: Path | None = None,
) -> None:
    issues.append(
        ProtocolAssetIssue(
            severity=severity,
            code=code,
            message=message,
            file_path=str(path) if path is not None else None,
        )
    )

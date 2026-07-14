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
    if control_protocol is not None:
        _require_text(control_protocol, "EXECUTE-BUNDLE", issues, "missing_trigger_phrase")
        _require_text(
            control_protocol,
            "Graph Tool Compatibility Gates",
            issues,
            "missing_graph_tool_compatibility_section",
        )
    if generate_prompt is not None:
        _require_text(generate_prompt, "GENERATE-BUNDLE", issues, "missing_trigger_phrase")
    if execute_prompt is not None:
        _require_text(execute_prompt, "EXECUTE-BUNDLE", issues, "missing_trigger_phrase")

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

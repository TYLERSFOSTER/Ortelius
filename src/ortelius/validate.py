"""Validation for typed/fibered graph bundles."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from ortelius.model import (
    GraphBundle,
    GraphRecord,
    InstanceEdgeRecord,
    InstanceNodeRecord,
    RawObject,
    TypeEdgeRecord,
    TypeFields,
    TypeNodeRecord,
    ValidationMode,
)

IssueSeverity = Literal["error", "warning"]

SUPPORTED_STATUSES = {"candidate", "accepted", "rejected", "deprecated", "superseded"}
SUPPORTED_VALUE_KINDS = {
    "string",
    "text",
    "integer",
    "number",
    "boolean",
    "date",
    "year",
    "uri",
    "id_ref",
    "id_ref_list",
    "object",
    "array",
}
SUPPORTED_CARDINALITIES = {"required_one", "optional_one", "zero_or_more", "one_or_more"}
SUPPORTED_SOURCE_POLICIES = {"required", "recommended", "optional", "not_applicable"}


@dataclass(frozen=True)
class ValidationIssue:
    severity: IssueSeverity
    code: str
    message: str
    record_id: str | None = None
    file_path: str | None = None


@dataclass(frozen=True)
class ValidationReport:
    issues: tuple[ValidationIssue, ...]

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


def validate_graph_bundle(
    bundle: GraphBundle,
    mode: ValidationMode = "bootstrap",
) -> ValidationReport:
    issues: list[ValidationIssue] = []
    _validate_ids(bundle, issues)
    _validate_type_graph(bundle, issues)
    _validate_concrete_graph(bundle, issues)
    _validate_fields(bundle, mode, issues)
    return ValidationReport(tuple(issues))


def _validate_ids(bundle: GraphBundle, issues: list[ValidationIssue]) -> None:
    seen: dict[str, GraphRecord] = {}
    for record in bundle.all_records():
        if not record.id:
            _add(issues, "error", "missing_id", "Record is missing id.", record)
            continue

        if record.id in seen:
            _add(
                issues,
                "error",
                "duplicate_id",
                f"Duplicate record id {record.id!r}.",
                record,
            )
        else:
            seen[record.id] = record

        expected_prefix = _expected_prefix(bundle, record)
        if expected_prefix and not record.id.startswith(expected_prefix):
            _add(
                issues,
                "error",
                "invalid_id_prefix",
                f"Record id {record.id!r} must start with {expected_prefix!r}.",
                record,
            )

        if record.status and record.status not in SUPPORTED_STATUSES:
            _add(
                issues,
                "error",
                "unsupported_status",
                f"Record status {record.status!r} is not supported.",
                record,
            )


def _validate_type_graph(bundle: GraphBundle, issues: list[ValidationIssue]) -> None:
    for record in bundle.type_node_records:
        _validate_type_fields(record.type_fields, record, issues)

    for record in bundle.type_edge_records:
        if not record.source_type_id:
            _add(
                issues,
                "error",
                "type_edge_missing_source_type_id",
                "Missing source_type_id.",
                record,
            )
        elif record.source_type_id not in bundle.type_nodes:
            _add(
                issues,
                "error",
                "type_edge_unknown_source_type",
                f"Unknown source_type_id {record.source_type_id!r}.",
                record,
            )

        if not record.target_type_id:
            _add(
                issues,
                "error",
                "type_edge_missing_target_type_id",
                "Missing target_type_id.",
                record,
            )
        elif record.target_type_id not in bundle.type_nodes:
            _add(
                issues,
                "error",
                "type_edge_unknown_target_type",
                f"Unknown target_type_id {record.target_type_id!r}.",
                record,
            )

        _validate_type_fields(record.type_fields, record, issues)


def _validate_concrete_graph(bundle: GraphBundle, issues: list[ValidationIssue]) -> None:
    for record in bundle.fiber_node_records:
        if not record.type_id:
            _add(issues, "error", "node_missing_type_id", "Missing type_id.", record)
        elif record.type_id not in bundle.type_nodes:
            _add(
                issues,
                "error",
                "node_unknown_type_id",
                f"Unknown node type_id {record.type_id!r}.",
                record,
            )
        elif bundle.type_nodes[record.type_id].status == "rejected" and record.status == "accepted":
            _add(
                issues,
                "error",
                "accepted_record_references_rejected_record",
                f"Accepted node references rejected type_id {record.type_id!r}.",
                record,
            )

    for record in bundle.fiber_edge_records:
        _validate_concrete_edge(bundle, record, issues)


def _validate_concrete_edge(
    bundle: GraphBundle,
    record: InstanceEdgeRecord,
    issues: list[ValidationIssue],
) -> None:
    source_node: InstanceNodeRecord | None = None
    target_node: InstanceNodeRecord | None = None
    edge_type: TypeEdgeRecord | None = None

    if not record.source_id:
        _add(issues, "error", "edge_missing_source_id", "Missing source_id.", record)
    elif record.source_id not in bundle.fiber_nodes:
        _add(
            issues,
            "error",
            "edge_unknown_source_id",
            f"Unknown source_id {record.source_id!r}.",
            record,
        )
    else:
        source_node = bundle.fiber_nodes[record.source_id]

    if not record.target_id:
        _add(issues, "error", "edge_missing_target_id", "Missing target_id.", record)
    elif record.target_id not in bundle.fiber_nodes:
        _add(
            issues,
            "error",
            "edge_unknown_target_id",
            f"Unknown target_id {record.target_id!r}.",
            record,
        )
    else:
        target_node = bundle.fiber_nodes[record.target_id]

    if not record.type_id:
        _add(issues, "error", "edge_missing_type_id", "Missing type_id.", record)
    elif record.type_id not in bundle.type_edges:
        _add(
            issues,
            "error",
            "edge_unknown_type_id",
            f"Unknown edge type_id {record.type_id!r}.",
            record,
        )
    else:
        edge_type = bundle.type_edges[record.type_id]

    if source_node is None or target_node is None or edge_type is None:
        return

    if source_node.type_id != edge_type.source_type_id:
        _add(
            issues,
            "error",
            "edge_source_type_mismatch",
            (
                f"Edge source type {source_node.type_id!r} does not match "
                f"{edge_type.source_type_id!r}."
            ),
            record,
        )

    if target_node.type_id != edge_type.target_type_id:
        _add(
            issues,
            "error",
            "edge_target_type_mismatch",
            (
                f"Edge target type {target_node.type_id!r} does not match "
                f"{edge_type.target_type_id!r}."
            ),
            record,
        )


def _validate_fields(
    bundle: GraphBundle,
    mode: ValidationMode,
    issues: list[ValidationIssue],
) -> None:
    for record in bundle.fiber_node_records:
        type_record = bundle.type_nodes.get(record.type_id)
        if type_record is None:
            continue
        _validate_record_fields(record, type_record.type_fields, mode, issues)

    for record in bundle.fiber_edge_records:
        type_record = bundle.type_edges.get(record.type_id)
        if type_record is None:
            continue
        _validate_record_fields(record, type_record.type_fields, mode, issues)


def _validate_record_fields(
    record: InstanceNodeRecord | InstanceEdgeRecord,
    type_fields: TypeFields,
    mode: ValidationMode,
    issues: list[ValidationIssue],
) -> None:
    field_definitions = _field_definitions(type_fields)
    unknown_severity: IssueSeverity = "warning" if mode == "bootstrap" else "error"

    for field_key, field_value in record.fields.items():
        field_definition = field_definitions.get(field_key)
        if field_definition is None:
            _add(
                issues,
                unknown_severity,
                "unknown_field",
                f"Field {field_key!r} is not declared by type_fields.",
                record,
            )
            continue

        values = _field_values(field_value)
        if values is None:
            _add(
                issues,
                "error",
                "invalid_field_values_shape",
                f"Field {field_key!r} must contain a values array.",
                record,
            )
            continue

        for value_record in values:
            if not isinstance(value_record, dict):
                _add(
                    issues,
                    "error",
                    "invalid_field_value_record",
                    f"Field {field_key!r} value entries must be objects.",
                    record,
                )
                continue
            if "value" in value_record and not _value_matches_kind(
                value_record["value"],
                _str_from_mapping(field_definition, "value_kind"),
            ):
                _add(
                    issues,
                    "error",
                    "field_value_kind_mismatch",
                    f"Field {field_key!r} value does not match declared value_kind.",
                    record,
                )

    for field_key, field_definition in field_definitions.items():
        cardinality = _str_from_mapping(field_definition, "cardinality")
        values = _field_values(record.fields.get(field_key, {})) or []
        accepted_count = sum(
            1
            for value_record in values
            if isinstance(value_record, dict) and value_record.get("status") == "accepted"
        )
        _validate_cardinality(record, field_key, cardinality, accepted_count, mode, issues)
        _validate_required_sources(record, field_key, field_definition, values, issues)


def _validate_type_fields(
    type_fields: TypeFields,
    record: TypeNodeRecord | TypeEdgeRecord,
    issues: list[ValidationIssue],
) -> None:
    if not isinstance(type_fields, dict) or not isinstance(type_fields.get("fields"), dict):
        _add(
            issues,
            "error",
            "invalid_type_fields_shape",
            "type_fields must contain a fields object.",
            record,
        )
        return

    for field_key, field_definition in type_fields["fields"].items():
        if not isinstance(field_key, str):
            _add(issues, "error", "invalid_field_key", "Field key must be a string.", record)
            continue
        if not isinstance(field_definition, dict):
            _add(
                issues,
                "error",
                "invalid_field_definition",
                f"Field {field_key!r} definition must be an object.",
                record,
            )
            continue

        value_kind = _str_from_mapping(field_definition, "value_kind")
        if value_kind not in SUPPORTED_VALUE_KINDS:
            _add(
                issues,
                "error",
                "unsupported_value_kind",
                f"Field {field_key!r} has unsupported value_kind {value_kind!r}.",
                record,
            )

        cardinality = _str_from_mapping(field_definition, "cardinality")
        if cardinality not in SUPPORTED_CARDINALITIES:
            _add(
                issues,
                "error",
                "unsupported_cardinality",
                f"Field {field_key!r} has unsupported cardinality {cardinality!r}.",
                record,
            )

        source_policy = _str_from_mapping(field_definition, "source_policy")
        if source_policy not in SUPPORTED_SOURCE_POLICIES:
            _add(
                issues,
                "error",
                "unsupported_source_policy",
                f"Field {field_key!r} has unsupported source_policy {source_policy!r}.",
                record,
            )


def _validate_cardinality(
    record: InstanceNodeRecord | InstanceEdgeRecord,
    field_key: str,
    cardinality: str,
    accepted_count: int,
    mode: ValidationMode,
    issues: list[ValidationIssue],
) -> None:
    severity: IssueSeverity = (
        "error" if mode == "strict" or record.status == "accepted" else "warning"
    )

    if cardinality == "required_one" and accepted_count != 1:
        _add(
            issues,
            severity,
            "field_cardinality_violation",
            f"Field {field_key!r} requires exactly one accepted value.",
            record,
        )
    elif cardinality == "optional_one" and accepted_count > 1:
        _add(
            issues,
            "error",
            "field_cardinality_violation",
            f"Field {field_key!r} allows at most one accepted value.",
            record,
        )
    elif cardinality == "one_or_more" and accepted_count < 1:
        _add(
            issues,
            severity,
            "field_cardinality_violation",
            f"Field {field_key!r} requires at least one accepted value.",
            record,
        )


def _validate_required_sources(
    record: InstanceNodeRecord | InstanceEdgeRecord,
    field_key: str,
    field_definition: RawObject,
    values: list[Any],
    issues: list[ValidationIssue],
) -> None:
    if _str_from_mapping(field_definition, "source_policy") != "required":
        return
    for value_record in values:
        if not isinstance(value_record, dict):
            continue
        sources = value_record.get("sources")
        if not isinstance(sources, list) or not sources:
            _add(
                issues,
                "error",
                "required_source_missing",
                f"Field {field_key!r} requires sources.",
                record,
            )


def _expected_prefix(bundle: GraphBundle, record: GraphRecord) -> str:
    if isinstance(record, TypeNodeRecord):
        return f"{bundle.type_graph_id}.node."
    if isinstance(record, TypeEdgeRecord):
        return f"{bundle.type_graph_id}.edge."
    if isinstance(record, InstanceNodeRecord):
        return f"{bundle.fiber_graph_id}.node."
    return f"{bundle.fiber_graph_id}.edge."


def _field_definitions(type_fields: TypeFields) -> dict[str, RawObject]:
    fields = type_fields.get("fields")
    if not isinstance(fields, dict):
        return {}
    return {
        key: value
        for key, value in fields.items()
        if isinstance(key, str) and isinstance(value, dict)
    }


def _field_values(field_value: Any) -> list[Any] | None:
    if not isinstance(field_value, dict):
        return None
    values = field_value.get("values")
    return values if isinstance(values, list) else None


def _value_matches_kind(value: Any, value_kind: str) -> bool:
    match value_kind:
        case "string" | "text" | "uri" | "id_ref" | "date":
            return isinstance(value, str)
        case "integer":
            return isinstance(value, int) and not isinstance(value, bool)
        case "number":
            return isinstance(value, int | float) and not isinstance(value, bool)
        case "boolean":
            return isinstance(value, bool)
        case "year":
            return (isinstance(value, int) and not isinstance(value, bool)) or (
                isinstance(value, str) and len(value) == 4 and value.isdigit()
            )
        case "id_ref_list":
            return isinstance(value, list) and all(isinstance(item, str) for item in value)
        case "object":
            return isinstance(value, dict)
        case "array":
            return isinstance(value, list)
        case _:
            return True


def _str_from_mapping(mapping: RawObject, key: str) -> str:
    value = mapping.get(key)
    return value if isinstance(value, str) else ""


def _add(
    issues: list[ValidationIssue],
    severity: IssueSeverity,
    code: str,
    message: str,
    record: GraphRecord,
) -> None:
    issues.append(
        ValidationIssue(
            severity=severity,
            code=code,
            message=message,
            record_id=record.id or None,
            file_path=str(record.file_path),
        )
    )

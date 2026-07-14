"""PyTorch Geometric materialization for graph bundles."""

from __future__ import annotations

import importlib
import re
from dataclasses import dataclass
from typing import Any

from ortelius.model import GraphBundle, TypeEdgeRecord, TypeNodeRecord
from ortelius.validate import ValidationIssue, ValidationReport, validate_graph_bundle

_SAFE_NAME = re.compile(r"[^a-z0-9_]+")


class OptionalPyGDependencyError(Exception):
    """Raised when PyG materialization is requested without PyG installed."""


class PyGReadinessError(Exception):
    """Raised when a graph bundle is not PyG-ready."""


@dataclass(frozen=True)
class PyGFeatureEncoderSpec:
    field_key: str
    encoder: str
    dtype: str
    shape: tuple[int, ...]
    missing_value_policy: str


@dataclass(frozen=True)
class PyGFeatureConfig:
    node_features: dict[str, dict[str, PyGFeatureEncoderSpec]]
    edge_features: dict[tuple[str, str, str], dict[str, PyGFeatureEncoderSpec]]


@dataclass(frozen=True)
class PyGFeatureReport:
    node_feature_names: dict[str, tuple[str, ...]]
    edge_feature_names: dict[tuple[str, str, str], tuple[str, ...]]
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class PyGMaterializationConfig:
    include_statuses: tuple[str, ...] = ("accepted",)


@dataclass(frozen=True)
class PyGMaterialization:
    data: Any
    node_id_maps: dict[str, dict[str, int]]
    reverse_node_id_maps: dict[str, dict[int, str]]
    edge_id_maps: dict[tuple[str, str, str], dict[str, int]]
    reverse_edge_id_maps: dict[tuple[str, str, str], dict[int, str]]
    feature_report: PyGFeatureReport
    materialization_config: PyGMaterializationConfig


@dataclass(frozen=True)
class PyGStructureMaps:
    node_id_maps: dict[str, dict[str, int]]
    reverse_node_id_maps: dict[str, dict[int, str]]
    edge_id_maps: dict[tuple[str, str, str], dict[str, int]]
    reverse_edge_id_maps: dict[tuple[str, str, str], dict[int, str]]
    edge_index_lists: dict[tuple[str, str, str], tuple[list[int], list[int]]]
    num_nodes_dict: dict[str, int]


def derive_pyg_node_type(record: TypeNodeRecord) -> str:
    pyg_metadata = record.raw.get("pyg")
    if isinstance(pyg_metadata, dict):
        node_type = pyg_metadata.get("node_type") or pyg_metadata.get("ntype")
        if isinstance(node_type, str):
            return _safe_name(node_type)
    return _safe_name(_strip_record_prefix(record.id, "node"))


def derive_pyg_relation_name(record: TypeEdgeRecord, bundle: GraphBundle) -> str:
    pyg_metadata = record.raw.get("pyg")
    if isinstance(pyg_metadata, dict) and isinstance(pyg_metadata.get("relation_name"), str):
        return _safe_name(pyg_metadata["relation_name"])

    source_slug = _strip_record_prefix(record.source_type_id, "node")
    target_slug = _strip_record_prefix(record.target_type_id, "node")
    edge_slug = _strip_record_prefix(record.id, "edge")
    prefix = f"{source_slug}_"
    suffix = f"_{target_slug}"
    if edge_slug.startswith(prefix) and edge_slug.endswith(suffix):
        edge_slug = edge_slug[len(prefix) : -len(suffix)]
    return _safe_name(edge_slug or record.id)


def derive_pyg_canonical_etype(
    record: TypeEdgeRecord,
    bundle: GraphBundle,
) -> tuple[str, str, str]:
    source_type = bundle.type_nodes.get(record.source_type_id)
    target_type = bundle.type_nodes.get(record.target_type_id)
    source_name = (
        derive_pyg_node_type(source_type) if source_type else _safe_name(record.source_type_id)
    )
    target_name = (
        derive_pyg_node_type(target_type) if target_type else _safe_name(record.target_type_id)
    )
    return (source_name, derive_pyg_relation_name(record, bundle), target_name)


def validate_pyg_readiness(
    bundle: GraphBundle,
    *,
    include_statuses: tuple[str, ...] = ("accepted",),
    feature_config: PyGFeatureConfig | None = None,
) -> ValidationReport:
    issues = list(validate_graph_bundle(bundle).issues)
    _validate_pyg_names(bundle, include_statuses, issues)
    _validate_pyg_feature_config(bundle, feature_config, issues)
    return ValidationReport(tuple(issues))


def build_pyg_structure_maps(
    bundle: GraphBundle,
    *,
    include_statuses: tuple[str, ...] = ("accepted",),
) -> PyGStructureMaps:
    node_id_maps: dict[str, dict[str, int]] = {}
    reverse_node_id_maps: dict[str, dict[int, str]] = {}
    type_name_by_type_id = {
        type_record.id: derive_pyg_node_type(type_record)
        for type_record in bundle.type_node_records
        if type_record.status in include_statuses
    }

    for node in bundle.fiber_node_records:
        if node.status not in include_statuses:
            continue
        node_type = type_name_by_type_id.get(node.type_id)
        if node_type is None:
            continue
        node_id_maps.setdefault(node_type, {})
        reverse_node_id_maps.setdefault(node_type, {})
        node_index = len(node_id_maps[node_type])
        node_id_maps[node_type][node.id] = node_index
        reverse_node_id_maps[node_type][node_index] = node.id

    for node_type in type_name_by_type_id.values():
        node_id_maps.setdefault(node_type, {})
        reverse_node_id_maps.setdefault(node_type, {})

    edge_id_maps: dict[tuple[str, str, str], dict[str, int]] = {}
    reverse_edge_id_maps: dict[tuple[str, str, str], dict[int, str]] = {}
    edge_index_lists: dict[tuple[str, str, str], tuple[list[int], list[int]]] = {}

    for edge_type in bundle.type_edge_records:
        if edge_type.status not in include_statuses:
            continue
        canonical_etype = derive_pyg_canonical_etype(edge_type, bundle)
        edge_id_maps.setdefault(canonical_etype, {})
        reverse_edge_id_maps.setdefault(canonical_etype, {})
        edge_index_lists.setdefault(canonical_etype, ([], []))

    for edge in bundle.fiber_edge_records:
        if edge.status not in include_statuses:
            continue
        edge_type = bundle.type_edges.get(edge.type_id)
        source_node = bundle.fiber_nodes.get(edge.source_id)
        target_node = bundle.fiber_nodes.get(edge.target_id)
        if edge_type is None or source_node is None or target_node is None:
            continue
        canonical_etype = derive_pyg_canonical_etype(edge_type, bundle)
        source_map = node_id_maps.get(canonical_etype[0], {})
        target_map = node_id_maps.get(canonical_etype[2], {})
        if edge.source_id not in source_map or edge.target_id not in target_map:
            continue
        _add_edge_mapping(
            canonical_etype,
            edge.id,
            source_map[edge.source_id],
            target_map[edge.target_id],
            edge_id_maps,
            reverse_edge_id_maps,
            edge_index_lists,
        )

    return PyGStructureMaps(
        node_id_maps=node_id_maps,
        reverse_node_id_maps=reverse_node_id_maps,
        edge_id_maps=edge_id_maps,
        reverse_edge_id_maps=reverse_edge_id_maps,
        edge_index_lists=edge_index_lists,
        num_nodes_dict={node_type: len(id_map) for node_type, id_map in node_id_maps.items()},
    )


def to_pyg_fiber_graph(
    bundle: GraphBundle,
    *,
    include_statuses: tuple[str, ...] = ("accepted",),
    feature_config: PyGFeatureConfig | None = None,
) -> PyGMaterialization:
    readiness = validate_pyg_readiness(
        bundle,
        include_statuses=include_statuses,
        feature_config=feature_config,
    )
    if not readiness.ok:
        summary = ", ".join(issue.code for issue in readiness.issues[:5])
        raise PyGReadinessError(f"Graph bundle is not PyG-ready: {summary}")

    try:
        torch = importlib.import_module("torch")
        hetero_data_module = importlib.import_module("torch_geometric.data")
    except ImportError as exc:
        raise OptionalPyGDependencyError(
            "PyG materialization requires optional dependencies torch and torch-geometric."
        ) from exc

    structure = build_pyg_structure_maps(bundle, include_statuses=include_statuses)
    data = hetero_data_module.HeteroData()

    for node_type, num_nodes in structure.num_nodes_dict.items():
        data[node_type].num_nodes = num_nodes

    for canonical_etype, (sources, targets) in structure.edge_index_lists.items():
        data[canonical_etype].edge_index = torch.tensor([sources, targets], dtype=torch.long)

    return PyGMaterialization(
        data=data,
        node_id_maps=structure.node_id_maps,
        reverse_node_id_maps=structure.reverse_node_id_maps,
        edge_id_maps=structure.edge_id_maps,
        reverse_edge_id_maps=structure.reverse_edge_id_maps,
        feature_report=_build_feature_report(feature_config),
        materialization_config=PyGMaterializationConfig(include_statuses=include_statuses),
    )


def _validate_pyg_names(
    bundle: GraphBundle,
    include_statuses: tuple[str, ...],
    issues: list[ValidationIssue],
) -> None:
    node_names: dict[str, str] = {}
    for node_type in bundle.type_node_records:
        if node_type.status not in include_statuses:
            continue
        pyg_node_type = derive_pyg_node_type(node_type)
        if not pyg_node_type:
            _add_pyg_issue(issues, "pyg_empty_node_type_name", "PyG node type name is empty.")
        elif pyg_node_type in node_names:
            _add_pyg_issue(
                issues,
                "pyg_duplicate_node_type_name",
                f"PyG node type name {pyg_node_type!r} is duplicated.",
                node_type.id,
            )
        else:
            node_names[pyg_node_type] = node_type.id

    canonical_etypes: dict[tuple[str, str, str], str] = {}
    for edge_type in bundle.type_edge_records:
        if edge_type.status not in include_statuses:
            continue
        canonical_etype = derive_pyg_canonical_etype(edge_type, bundle)
        if any(not part for part in canonical_etype):
            _add_pyg_issue(
                issues,
                "pyg_empty_canonical_etype_part",
                "PyG canonical edge type contains an empty part.",
                edge_type.id,
            )
        elif canonical_etype in canonical_etypes:
            _add_pyg_issue(
                issues,
                "pyg_duplicate_canonical_etype",
                f"PyG canonical edge type {canonical_etype!r} is duplicated.",
                edge_type.id,
            )
        else:
            canonical_etypes[canonical_etype] = edge_type.id


def _validate_pyg_feature_config(
    bundle: GraphBundle,
    feature_config: PyGFeatureConfig | None,
    issues: list[ValidationIssue],
) -> None:
    if feature_config is None:
        return

    node_type_by_name = {
        derive_pyg_node_type(type_record): type_record for type_record in bundle.type_node_records
    }
    edge_type_by_canonical = {
        derive_pyg_canonical_etype(edge_record, bundle): edge_record
        for edge_record in bundle.type_edge_records
    }

    for node_type, feature_specs in feature_config.node_features.items():
        type_record = node_type_by_name.get(node_type)
        if type_record is None:
            _add_pyg_issue(
                issues,
                "pyg_unknown_node_feature_type",
                f"Unknown PyG node feature type {node_type!r}.",
            )
            continue
        declared_fields = _declared_fields(type_record.raw.get("type_fields"))
        _validate_feature_specs(node_type, feature_specs, declared_fields, issues, "node")

    for canonical_etype, feature_specs in feature_config.edge_features.items():
        type_record = edge_type_by_canonical.get(canonical_etype)
        if type_record is None:
            _add_pyg_issue(
                issues,
                "pyg_unknown_edge_feature_type",
                f"Unknown PyG edge feature type {canonical_etype!r}.",
            )
            continue
        declared_fields = _declared_fields(type_record.raw.get("type_fields"))
        _validate_feature_specs(
            str(canonical_etype),
            feature_specs,
            declared_fields,
            issues,
            "edge",
        )


def _validate_feature_specs(
    feature_group: str,
    feature_specs: dict[str, PyGFeatureEncoderSpec],
    declared_fields: dict[str, dict[str, Any]],
    issues: list[ValidationIssue],
    feature_kind: str,
) -> None:
    for feature_name, spec in feature_specs.items():
        field_definition = declared_fields.get(spec.field_key)
        if field_definition is None:
            _add_pyg_issue(
                issues,
                f"pyg_unknown_{feature_kind}_feature_field",
                f"Feature {feature_group}.{feature_name} uses undeclared field {spec.field_key!r}.",
            )
            continue
        if spec.encoder in {"raw", "identity"} and field_definition.get("value_kind") in {
            "text",
            "string",
        }:
            _add_pyg_issue(
                issues,
                "pyg_direct_raw_text_feature",
                f"Feature {feature_group}.{feature_name} needs an encoder for text-like data.",
            )


def _add_edge_mapping(
    canonical_etype: tuple[str, str, str],
    edge_id: str,
    source_index: int,
    target_index: int,
    edge_id_maps: dict[tuple[str, str, str], dict[str, int]],
    reverse_edge_id_maps: dict[tuple[str, str, str], dict[int, str]],
    edge_index_lists: dict[tuple[str, str, str], tuple[list[int], list[int]]],
) -> None:
    edge_id_maps.setdefault(canonical_etype, {})
    reverse_edge_id_maps.setdefault(canonical_etype, {})
    sources, targets = edge_index_lists.setdefault(canonical_etype, ([], []))
    edge_index = len(sources)
    edge_id_maps[canonical_etype][edge_id] = edge_index
    reverse_edge_id_maps[canonical_etype][edge_index] = edge_id
    sources.append(source_index)
    targets.append(target_index)


def _build_feature_report(feature_config: PyGFeatureConfig | None) -> PyGFeatureReport:
    if feature_config is None:
        return PyGFeatureReport(node_feature_names={}, edge_feature_names={})
    return PyGFeatureReport(
        node_feature_names={
            node_type: tuple(features.keys())
            for node_type, features in feature_config.node_features.items()
        },
        edge_feature_names={
            edge_type: tuple(features.keys())
            for edge_type, features in feature_config.edge_features.items()
        },
    )


def _declared_fields(type_fields: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(type_fields, dict):
        return {}
    fields = type_fields.get("fields")
    if not isinstance(fields, dict):
        return {}
    return {
        key: value
        for key, value in fields.items()
        if isinstance(key, str) and isinstance(value, dict)
    }


def _add_pyg_issue(
    issues: list[ValidationIssue],
    code: str,
    message: str,
    record_id: str | None = None,
) -> None:
    issues.append(
        ValidationIssue(
            severity="error",
            code=code,
            message=message,
            record_id=record_id,
        )
    )


def _safe_name(value: str) -> str:
    return _SAFE_NAME.sub("_", value.lower()).strip("_")


def _strip_record_prefix(value: str, record_role: str) -> str:
    marker = f".{record_role}."
    if marker not in value:
        return value
    return value.split(marker, 1)[1]

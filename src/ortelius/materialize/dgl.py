"""DGL readiness and optional DGL materialization for graph bundles."""

from __future__ import annotations

import importlib
import re
from dataclasses import dataclass
from typing import Any

from ortelius.model import GraphBundle, TypeEdgeRecord, TypeNodeRecord
from ortelius.validate import ValidationIssue, ValidationReport, validate_graph_bundle

_SAFE_NAME = re.compile(r"[^a-z0-9_]+")


class OptionalDGLDependencyError(Exception):
    """Raised when DGL materialization is requested without DGL installed."""


class DGLReadinessError(Exception):
    """Raised when a graph bundle is not DGL-ready."""


@dataclass(frozen=True)
class FeatureEncoderSpec:
    field_key: str
    encoder: str
    dtype: str
    shape: tuple[int, ...]
    missing_value_policy: str


@dataclass(frozen=True)
class DGLFeatureConfig:
    node_features: dict[str, dict[str, FeatureEncoderSpec]]
    edge_features: dict[tuple[str, str, str], dict[str, FeatureEncoderSpec]]


@dataclass(frozen=True)
class DGLFeatureReport:
    node_feature_names: dict[str, tuple[str, ...]]
    edge_feature_names: dict[tuple[str, str, str], tuple[str, ...]]
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class DGLMaterializationConfig:
    include_statuses: tuple[str, ...] = ("accepted",)
    add_synthetic_reverse_edges: bool = False
    add_synthetic_self_loops: bool = False


@dataclass(frozen=True)
class DGLMaterialization:
    graph: Any
    node_id_maps: dict[str, dict[str, int]]
    reverse_node_id_maps: dict[str, dict[int, str]]
    edge_id_maps: dict[tuple[str, str, str], dict[str, int]]
    reverse_edge_id_maps: dict[tuple[str, str, str], dict[int, str]]
    feature_report: DGLFeatureReport
    materialization_config: DGLMaterializationConfig


@dataclass(frozen=True)
class DGLStructureMaps:
    node_id_maps: dict[str, dict[str, int]]
    reverse_node_id_maps: dict[str, dict[int, str]]
    edge_id_maps: dict[tuple[str, str, str], dict[str, int]]
    reverse_edge_id_maps: dict[tuple[str, str, str], dict[int, str]]
    edge_index_lists: dict[tuple[str, str, str], tuple[list[int], list[int]]]
    num_nodes_dict: dict[str, int]


def derive_dgl_node_type(record: TypeNodeRecord) -> str:
    dgl_metadata = record.raw.get("dgl")
    if isinstance(dgl_metadata, dict) and isinstance(dgl_metadata.get("ntype"), str):
        return _safe_name(dgl_metadata["ntype"])
    return _safe_name(_strip_record_prefix(record.id, "node"))


def derive_dgl_relation_name(record: TypeEdgeRecord, bundle: GraphBundle) -> str:
    dgl_metadata = record.raw.get("dgl")
    if isinstance(dgl_metadata, dict) and isinstance(dgl_metadata.get("relation_name"), str):
        return _safe_name(dgl_metadata["relation_name"])

    source_slug = _strip_record_prefix(record.source_type_id, "node")
    target_slug = _strip_record_prefix(record.target_type_id, "node")
    edge_slug = _strip_record_prefix(record.id, "edge")
    prefix = f"{source_slug}_"
    suffix = f"_{target_slug}"
    if edge_slug.startswith(prefix) and edge_slug.endswith(suffix):
        edge_slug = edge_slug[len(prefix) : -len(suffix)]
    return _safe_name(edge_slug or record.id)


def derive_dgl_canonical_etype(
    record: TypeEdgeRecord,
    bundle: GraphBundle,
) -> tuple[str, str, str]:
    source_type = bundle.type_nodes.get(record.source_type_id)
    target_type = bundle.type_nodes.get(record.target_type_id)
    source_name = (
        derive_dgl_node_type(source_type) if source_type else _safe_name(record.source_type_id)
    )
    target_name = (
        derive_dgl_node_type(target_type) if target_type else _safe_name(record.target_type_id)
    )
    return (source_name, derive_dgl_relation_name(record, bundle), target_name)


def validate_dgl_readiness(
    bundle: GraphBundle,
    *,
    include_statuses: tuple[str, ...] = ("accepted",),
    feature_config: DGLFeatureConfig | None = None,
) -> ValidationReport:
    issues = list(validate_graph_bundle(bundle).issues)
    _validate_dgl_names(bundle, include_statuses, issues)
    _validate_dgl_feature_config(bundle, feature_config, issues)
    return ValidationReport(tuple(issues))


def build_dgl_structure_maps(
    bundle: GraphBundle,
    *,
    include_statuses: tuple[str, ...] = ("accepted",),
    add_synthetic_reverse_edges: bool = False,
    add_synthetic_self_loops: bool = False,
) -> DGLStructureMaps:
    node_id_maps: dict[str, dict[str, int]] = {}
    reverse_node_id_maps: dict[str, dict[int, str]] = {}
    type_name_by_type_id = {
        type_record.id: derive_dgl_node_type(type_record)
        for type_record in bundle.type_node_records
        if type_record.status in include_statuses
    }

    for node in bundle.fiber_node_records:
        if node.status not in include_statuses:
            continue
        ntype = type_name_by_type_id.get(node.type_id)
        if ntype is None:
            continue
        node_id_maps.setdefault(ntype, {})
        reverse_node_id_maps.setdefault(ntype, {})
        node_index = len(node_id_maps[ntype])
        node_id_maps[ntype][node.id] = node_index
        reverse_node_id_maps[ntype][node_index] = node.id

    for type_name in type_name_by_type_id.values():
        node_id_maps.setdefault(type_name, {})
        reverse_node_id_maps.setdefault(type_name, {})

    edge_id_maps: dict[tuple[str, str, str], dict[str, int]] = {}
    reverse_edge_id_maps: dict[tuple[str, str, str], dict[int, str]] = {}
    edge_index_lists: dict[tuple[str, str, str], tuple[list[int], list[int]]] = {}

    for edge in bundle.fiber_edge_records:
        if edge.status not in include_statuses:
            continue
        edge_type = bundle.type_edges.get(edge.type_id)
        source_node = bundle.fiber_nodes.get(edge.source_id)
        target_node = bundle.fiber_nodes.get(edge.target_id)
        if edge_type is None or source_node is None or target_node is None:
            continue
        canonical_etype = derive_dgl_canonical_etype(edge_type, bundle)
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

        if add_synthetic_reverse_edges:
            reverse_etype = (
                canonical_etype[2],
                f"reverse__{canonical_etype[1]}",
                canonical_etype[0],
            )
            _add_edge_mapping(
                reverse_etype,
                f"synthetic.reverse.{edge.id}",
                target_map[edge.target_id],
                source_map[edge.source_id],
                edge_id_maps,
                reverse_edge_id_maps,
                edge_index_lists,
            )

    if add_synthetic_self_loops:
        for ntype, id_map in node_id_maps.items():
            etype = (ntype, f"self__{ntype}", ntype)
            for node_id, node_index in id_map.items():
                _add_edge_mapping(
                    etype,
                    f"synthetic.self.{node_id}",
                    node_index,
                    node_index,
                    edge_id_maps,
                    reverse_edge_id_maps,
                    edge_index_lists,
                )

    return DGLStructureMaps(
        node_id_maps=node_id_maps,
        reverse_node_id_maps=reverse_node_id_maps,
        edge_id_maps=edge_id_maps,
        reverse_edge_id_maps=reverse_edge_id_maps,
        edge_index_lists=edge_index_lists,
        num_nodes_dict={ntype: len(id_map) for ntype, id_map in node_id_maps.items()},
    )


def to_dgl_fiber_graph(
    bundle: GraphBundle,
    *,
    include_statuses: tuple[str, ...] = ("accepted",),
    feature_config: DGLFeatureConfig | None = None,
    add_synthetic_reverse_edges: bool = False,
    add_synthetic_self_loops: bool = False,
) -> DGLMaterialization:
    readiness = validate_dgl_readiness(
        bundle,
        include_statuses=include_statuses,
        feature_config=feature_config,
    )
    if not readiness.ok:
        summary = ", ".join(issue.code for issue in readiness.issues[:5])
        raise DGLReadinessError(f"Graph bundle is not DGL-ready: {summary}")

    try:
        dgl = importlib.import_module("dgl")
        torch = importlib.import_module("torch")
    except ImportError as exc:
        raise OptionalDGLDependencyError(
            "DGL materialization requires optional dependencies dgl and torch."
        ) from exc

    structure = build_dgl_structure_maps(
        bundle,
        include_statuses=include_statuses,
        add_synthetic_reverse_edges=add_synthetic_reverse_edges,
        add_synthetic_self_loops=add_synthetic_self_loops,
    )
    data_dict = {
        canonical_etype: (torch.tensor(sources), torch.tensor(targets))
        for canonical_etype, (sources, targets) in structure.edge_index_lists.items()
    }
    graph = dgl.heterograph(data_dict, num_nodes_dict=structure.num_nodes_dict)

    return DGLMaterialization(
        graph=graph,
        node_id_maps=structure.node_id_maps,
        reverse_node_id_maps=structure.reverse_node_id_maps,
        edge_id_maps=structure.edge_id_maps,
        reverse_edge_id_maps=structure.reverse_edge_id_maps,
        feature_report=_build_feature_report(feature_config),
        materialization_config=DGLMaterializationConfig(
            include_statuses=include_statuses,
            add_synthetic_reverse_edges=add_synthetic_reverse_edges,
            add_synthetic_self_loops=add_synthetic_self_loops,
        ),
    )


def _validate_dgl_names(
    bundle: GraphBundle,
    include_statuses: tuple[str, ...],
    issues: list[ValidationIssue],
) -> None:
    node_names: dict[str, str] = {}
    for node_type in bundle.type_node_records:
        if node_type.status not in include_statuses:
            continue
        ntype = derive_dgl_node_type(node_type)
        if not ntype:
            _add_dgl_issue(issues, "dgl_empty_node_type_name", "DGL node type name is empty.")
        elif ntype in node_names:
            _add_dgl_issue(
                issues,
                "dgl_duplicate_node_type_name",
                f"DGL node type name {ntype!r} is duplicated.",
                node_type.id,
            )
        else:
            node_names[ntype] = node_type.id

    canonical_etypes: dict[tuple[str, str, str], str] = {}
    for edge_type in bundle.type_edges.values():
        if edge_type.status not in include_statuses:
            continue
        canonical_etype = derive_dgl_canonical_etype(edge_type, bundle)
        if any(not part for part in canonical_etype):
            _add_dgl_issue(
                issues,
                "dgl_empty_canonical_etype_part",
                "DGL canonical edge type contains an empty part.",
                edge_type.id,
            )
        elif canonical_etype in canonical_etypes:
            _add_dgl_issue(
                issues,
                "dgl_duplicate_canonical_etype",
                f"DGL canonical edge type {canonical_etype!r} is duplicated.",
                edge_type.id,
            )
        else:
            canonical_etypes[canonical_etype] = edge_type.id


def _validate_dgl_feature_config(
    bundle: GraphBundle,
    feature_config: DGLFeatureConfig | None,
    issues: list[ValidationIssue],
) -> None:
    if feature_config is None:
        return

    node_type_by_name = {
        derive_dgl_node_type(type_record): type_record for type_record in bundle.type_node_records
    }
    edge_type_by_canonical = {
        derive_dgl_canonical_etype(edge_record, bundle): edge_record
        for edge_record in bundle.type_edge_records
    }

    for ntype, feature_specs in feature_config.node_features.items():
        type_record = node_type_by_name.get(ntype)
        if type_record is None:
            _add_dgl_issue(
                issues,
                "dgl_unknown_node_feature_type",
                f"Unknown DGL node feature type {ntype!r}.",
            )
            continue
        declared_fields = _declared_fields(type_record.raw.get("type_fields"))
        _validate_feature_specs(ntype, feature_specs, declared_fields, issues, "node")

    for canonical_etype, feature_specs in feature_config.edge_features.items():
        type_record = edge_type_by_canonical.get(canonical_etype)
        if type_record is None:
            _add_dgl_issue(
                issues,
                "dgl_unknown_edge_feature_type",
                f"Unknown DGL edge feature type {canonical_etype!r}.",
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
    feature_specs: dict[str, FeatureEncoderSpec],
    declared_fields: dict[str, dict[str, Any]],
    issues: list[ValidationIssue],
    feature_kind: str,
) -> None:
    for feature_name, spec in feature_specs.items():
        field_definition = declared_fields.get(spec.field_key)
        if field_definition is None:
            _add_dgl_issue(
                issues,
                f"dgl_unknown_{feature_kind}_feature_field",
                f"Feature {feature_group}.{feature_name} uses undeclared field {spec.field_key!r}.",
            )
            continue
        if spec.encoder in {"raw", "identity"} and field_definition.get("value_kind") in {
            "text",
            "string",
        }:
            _add_dgl_issue(
                issues,
                "dgl_direct_raw_text_feature",
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


def _build_feature_report(feature_config: DGLFeatureConfig | None) -> DGLFeatureReport:
    if feature_config is None:
        return DGLFeatureReport(node_feature_names={}, edge_feature_names={})
    return DGLFeatureReport(
        node_feature_names={
            ntype: tuple(features.keys())
            for ntype, features in feature_config.node_features.items()
        },
        edge_feature_names={
            etype: tuple(features.keys())
            for etype, features in feature_config.edge_features.items()
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


def _add_dgl_issue(
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
    name = _SAFE_NAME.sub("_", value.lower()).strip("_")
    return name


def _strip_record_prefix(value: str, record_role: str) -> str:
    marker = f".{record_role}."
    if marker not in value:
        return value
    return value.split(marker, 1)[1]

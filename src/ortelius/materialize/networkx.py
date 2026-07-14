"""NetworkX materializers for typed/fibered graph bundles."""

from __future__ import annotations

from typing import Any

import networkx as nx

from ortelius.model import GraphBundle
from ortelius.validate import ValidationReport, validate_graph_bundle


class GraphMaterializationError(Exception):
    """Raised when a graph bundle cannot be safely materialized."""


def to_networkx_fiber_graph(
    bundle: GraphBundle,
    report: ValidationReport | None = None,
) -> nx.MultiDiGraph:
    _ensure_valid(bundle, report)
    graph = nx.MultiDiGraph(graph_id=bundle.fiber_graph_id, graph_role="fiber")

    for node in bundle.fiber_node_records:
        graph.add_node(
            node.id,
            type_id=node.type_id,
            label=node.label,
            status=node.status,
            fields=node.fields,
            sources=node.raw.get("sources", []),
            raw=node.raw,
        )

    for edge in bundle.fiber_edge_records:
        graph.add_edge(
            edge.source_id,
            edge.target_id,
            key=edge.id,
            id=edge.id,
            type_id=edge.type_id,
            label=edge.label,
            status=edge.status,
            fields=edge.fields,
            sources=edge.raw.get("sources", []),
            raw=edge.raw,
        )

    return graph


def to_networkx_type_graph(
    bundle: GraphBundle,
    report: ValidationReport | None = None,
) -> nx.MultiDiGraph:
    _ensure_valid(bundle, report)
    graph = nx.MultiDiGraph(graph_id=bundle.type_graph_id, graph_role="type")

    for node in bundle.type_node_records:
        graph.add_node(
            node.id,
            label=node.label,
            status=node.status,
            type_fields=node.type_fields,
            raw=node.raw,
        )

    for edge in bundle.type_edge_records:
        graph.add_edge(
            edge.source_type_id,
            edge.target_type_id,
            key=edge.id,
            id=edge.id,
            label=edge.label,
            status=edge.status,
            type_fields=edge.type_fields,
            raw=edge.raw,
        )

    return graph


def _ensure_valid(bundle: GraphBundle, report: ValidationReport | None) -> None:
    validation_report = report or validate_graph_bundle(bundle)
    if validation_report.ok:
        return

    issue_summary = ", ".join(_issue_label(issue) for issue in validation_report.issues[:5])
    raise GraphMaterializationError(f"Graph bundle has validation errors: {issue_summary}")


def _issue_label(issue: Any) -> str:
    record_suffix = f" on {issue.record_id}" if issue.record_id else ""
    return f"{issue.code}{record_suffix}"

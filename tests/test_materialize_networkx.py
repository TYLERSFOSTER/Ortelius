from __future__ import annotations

from pathlib import Path

import networkx as nx
import pytest

from ortelius.graph_io import load_graph_bundle
from ortelius.materialize.networkx import (
    GraphMaterializationError,
    to_networkx_fiber_graph,
    to_networkx_type_graph,
)

FIXTURE_BASE = Path("tests/fixtures/graph_assets")
TYPE_GRAPH_ID = "tg"
FIBER_GRAPH_ID = "fg"


def test_to_networkx_fiber_graph_materializes_directed_multigraph() -> None:
    bundle = _load_fixture_bundle("minimal_generic")

    graph = to_networkx_fiber_graph(bundle)

    assert isinstance(graph, nx.MultiDiGraph)
    assert graph.number_of_nodes() == 3
    assert graph.number_of_edges() == 1


def test_to_networkx_fiber_graph_preserves_node_and_edge_ids() -> None:
    bundle = _load_fixture_bundle("minimal_generic")

    graph = to_networkx_fiber_graph(bundle)

    assert "fg.node.example_person" in graph
    assert graph.nodes["fg.node.example_person"]["type_id"] == "tg.node.person"
    assert graph.has_edge(
        "fg.node.example_person",
        "fg.node.example_organization",
        "fg.edge.example_person_member_of_example_organization",
    )
    edge_data = graph.edges[
        "fg.node.example_person",
        "fg.node.example_organization",
        "fg.edge.example_person_member_of_example_organization",
    ]
    assert edge_data["type_id"] == "tg.edge.person_member_of_organization"


def test_to_networkx_fiber_graph_supports_traversal() -> None:
    bundle = _load_fixture_bundle("minimal_generic")

    graph = to_networkx_fiber_graph(bundle)

    assert nx.has_path(graph, "fg.node.example_person", "fg.node.example_organization")


def test_to_networkx_type_graph_materializes_type_graph() -> None:
    bundle = _load_fixture_bundle("minimal_generic")

    graph = to_networkx_type_graph(bundle)

    assert graph.number_of_nodes() == 3
    assert graph.has_edge(
        "tg.node.person",
        "tg.node.organization",
        "tg.edge.person_member_of_organization",
    )
    person_fields = graph.nodes["tg.node.person"]["type_fields"]["fields"]
    assert person_fields["name"]["value_kind"] == "string"


def test_networkx_materializer_rejects_invalid_bundle() -> None:
    bundle = _load_fixture_bundle("invalid_bad_edge_type")

    with pytest.raises(GraphMaterializationError):
        to_networkx_fiber_graph(bundle)


def _load_fixture_bundle(name: str):
    return load_graph_bundle(
        FIXTURE_BASE / f"{name}/graphs",
        type_graph_id=TYPE_GRAPH_ID,
        fiber_graph_id=FIBER_GRAPH_ID,
    )

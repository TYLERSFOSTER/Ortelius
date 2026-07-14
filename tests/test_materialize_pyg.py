from __future__ import annotations

from pathlib import Path

import pytest
from torch_geometric.data import HeteroData

from ortelius.graph_io import load_graph_bundle
from ortelius.materialize.dgl import derive_dgl_canonical_etype
from ortelius.materialize.networkx import to_networkx_fiber_graph
from ortelius.materialize.pyg import (
    PyGFeatureConfig,
    PyGFeatureEncoderSpec,
    PyGReadinessError,
    build_pyg_structure_maps,
    derive_pyg_canonical_etype,
    derive_pyg_node_type,
    to_pyg_fiber_graph,
    validate_pyg_readiness,
)

FIXTURE_BASE = Path("tests/fixtures/graph_assets")
MINIMAL_CANONICAL_ETYPE = ("person", "member_of", "organization")
TYPE_GRAPH_ID = "tg"
FIBER_GRAPH_ID = "fg"


def test_pyg_names_are_derived_from_type_records() -> None:
    bundle = _load_fixture_bundle("minimal_generic")

    assert derive_pyg_node_type(bundle.type_nodes["tg.node.person"]) == "person"
    assert (
        derive_pyg_canonical_etype(
            bundle.type_edges["tg.edge.person_member_of_organization"], bundle
        )
        == MINIMAL_CANONICAL_ETYPE
    )


def test_minimal_fixture_is_pyg_ready() -> None:
    bundle = _load_fixture_bundle("minimal_generic")

    report = validate_pyg_readiness(bundle)

    assert report.ok


def test_invalid_projection_fixture_is_not_pyg_ready() -> None:
    bundle = _load_fixture_bundle("invalid_bad_edge_type")

    report = validate_pyg_readiness(bundle)

    assert report.has_code("edge_target_type_mismatch")
    assert not report.ok


def test_pyg_feature_config_must_use_declared_fields() -> None:
    bundle = _load_fixture_bundle("minimal_generic")
    feature_config = PyGFeatureConfig(
        node_features={
            "person": {
                "bad_feature": PyGFeatureEncoderSpec(
                    field_key="not_declared",
                    encoder="year_to_float",
                    dtype="float32",
                    shape=(1,),
                    missing_value_policy="nan",
                )
            }
        },
        edge_features={},
    )

    report = validate_pyg_readiness(bundle, feature_config=feature_config)

    assert report.has_code("pyg_unknown_node_feature_field")
    assert not report.ok


def test_pyg_structure_maps_preserve_canonical_ids() -> None:
    bundle = _load_fixture_bundle("minimal_generic")

    maps = build_pyg_structure_maps(bundle)

    assert maps.node_id_maps["person"]["fg.node.example_person"] == 0
    assert maps.reverse_node_id_maps["organization"][0] == "fg.node.example_organization"
    assert (
        maps.edge_id_maps[MINIMAL_CANONICAL_ETYPE][
            "fg.edge.example_person_member_of_example_organization"
        ]
        == 0
    )
    assert maps.reverse_edge_id_maps[MINIMAL_CANONICAL_ETYPE][0] == (
        "fg.edge.example_person_member_of_example_organization"
    )
    assert maps.edge_index_lists[MINIMAL_CANONICAL_ETYPE] == ([0], [0])


def test_to_pyg_fiber_graph_materializes_nonempty_heterodata_without_features() -> None:
    bundle = _load_fixture_bundle("minimal_generic")

    materialization = to_pyg_fiber_graph(bundle)

    assert isinstance(materialization.data, HeteroData)
    assert set(materialization.data.node_types) == {"person", "organization", "place"}
    assert materialization.data.edge_types == [MINIMAL_CANONICAL_ETYPE]
    assert materialization.data["person"].num_nodes == 1
    assert materialization.data["organization"].num_nodes == 1
    assert materialization.data["place"].num_nodes == 1
    assert tuple(materialization.data[MINIMAL_CANONICAL_ETYPE].edge_index.shape) == (2, 1)
    assert materialization.data[MINIMAL_CANONICAL_ETYPE].edge_index.tolist() == [[0], [0]]
    assert materialization.data.validate(raise_on_error=False)
    assert "x" not in materialization.data["person"]
    assert "y" not in materialization.data["person"]
    assert "train_mask" not in materialization.data["person"]


def test_to_pyg_fiber_graph_rejects_invalid_bundle() -> None:
    bundle = _load_fixture_bundle("invalid_bad_edge_type")

    with pytest.raises(PyGReadinessError, match="edge_target_type_mismatch"):
        to_pyg_fiber_graph(bundle)


def test_pyg_and_networkx_preserve_the_same_concrete_edge() -> None:
    bundle = _load_fixture_bundle("minimal_generic")

    materialization = to_pyg_fiber_graph(bundle)
    graph = to_networkx_fiber_graph(bundle)
    source_index = materialization.data[MINIMAL_CANONICAL_ETYPE].edge_index[0, 0].item()
    target_index = materialization.data[MINIMAL_CANONICAL_ETYPE].edge_index[1, 0].item()
    source_id = materialization.reverse_node_id_maps["person"][source_index]
    target_id = materialization.reverse_node_id_maps["organization"][target_index]

    assert source_id == "fg.node.example_person"
    assert target_id == "fg.node.example_organization"
    assert graph.has_edge(
        source_id, target_id, "fg.edge.example_person_member_of_example_organization"
    )


def test_default_pyg_and_dgl_canonical_edge_derivation_agree() -> None:
    bundle = _load_fixture_bundle("minimal_generic")
    edge_type = bundle.type_edges["tg.edge.person_member_of_organization"]

    assert derive_pyg_canonical_etype(edge_type, bundle) == derive_dgl_canonical_etype(
        edge_type,
        bundle,
    )


def _load_fixture_bundle(name: str):
    return load_graph_bundle(
        FIXTURE_BASE / f"{name}/graphs",
        type_graph_id=TYPE_GRAPH_ID,
        fiber_graph_id=FIBER_GRAPH_ID,
    )

from __future__ import annotations

from pathlib import Path

import pytest

from ortelius.graph_io import load_graph_bundle
from ortelius.materialize.dgl import (
    DGLFeatureConfig,
    FeatureEncoderSpec,
    OptionalDGLDependencyError,
    build_dgl_structure_maps,
    derive_dgl_canonical_etype,
    derive_dgl_node_type,
    to_dgl_fiber_graph,
    validate_dgl_readiness,
)

FIXTURE_BASE = Path("tests/fixtures/graph_assets")
TYPE_GRAPH_ID = "tg"
FIBER_GRAPH_ID = "fg"


def test_dgl_names_are_derived_from_type_records() -> None:
    bundle = _load_fixture_bundle("minimal_generic")

    assert derive_dgl_node_type(bundle.type_nodes["tg.node.person"]) == "person"
    assert derive_dgl_canonical_etype(
        bundle.type_edges["tg.edge.person_member_of_organization"],
        bundle,
    ) == ("person", "member_of", "organization")


def test_minimal_fixture_is_dgl_ready() -> None:
    bundle = _load_fixture_bundle("minimal_generic")

    report = validate_dgl_readiness(bundle)

    assert report.ok


def test_invalid_projection_fixture_is_not_dgl_ready() -> None:
    bundle = _load_fixture_bundle("invalid_bad_edge_type")

    report = validate_dgl_readiness(bundle)

    assert report.has_code("edge_target_type_mismatch")
    assert not report.ok


def test_dgl_feature_config_must_use_declared_fields() -> None:
    bundle = _load_fixture_bundle("minimal_generic")
    feature_config = DGLFeatureConfig(
        node_features={
            "person": {
                "bad_feature": FeatureEncoderSpec(
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

    report = validate_dgl_readiness(bundle, feature_config=feature_config)

    assert report.has_code("dgl_unknown_node_feature_field")
    assert not report.ok


def test_dgl_structure_maps_preserve_canonical_ids() -> None:
    bundle = _load_fixture_bundle("minimal_generic")

    maps = build_dgl_structure_maps(bundle)

    assert maps.node_id_maps["person"]["fg.node.example_person"] == 0
    assert maps.reverse_node_id_maps["organization"][0] == "fg.node.example_organization"
    canonical_etype = ("person", "member_of", "organization")
    assert (
        maps.edge_id_maps[canonical_etype]["fg.edge.example_person_member_of_example_organization"]
        == 0
    )
    assert maps.edge_index_lists[canonical_etype] == ([0], [0])


def test_to_dgl_fiber_graph_raises_when_dgl_is_missing() -> None:
    if _dgl_available():
        pytest.skip("DGL is installed in this environment.")
    bundle = _load_fixture_bundle("minimal_generic")

    with pytest.raises(OptionalDGLDependencyError):
        to_dgl_fiber_graph(bundle)


def test_to_dgl_fiber_graph_materializes_when_dgl_is_available() -> None:
    pytest.importorskip("dgl")
    bundle = _load_fixture_bundle("minimal_generic")

    materialization = to_dgl_fiber_graph(bundle)

    assert materialization.node_id_maps["person"]["fg.node.example_person"] == 0
    assert ("person", "member_of", "organization") in materialization.edge_id_maps


def _dgl_available() -> bool:
    try:
        __import__("dgl")
    except ImportError:
        return False
    return True


def _load_fixture_bundle(name: str):
    return load_graph_bundle(
        FIXTURE_BASE / f"{name}/graphs",
        type_graph_id=TYPE_GRAPH_ID,
        fiber_graph_id=FIBER_GRAPH_ID,
    )

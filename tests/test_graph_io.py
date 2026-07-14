from __future__ import annotations

import json
from pathlib import Path

import pytest

from ortelius.graph_io import (
    GraphFileIdentityError,
    InvalidGraphFileShapeError,
    MissingGraphFileError,
    load_graph_bundle,
)
from ortelius.validate import validate_graph_bundle

FIXTURE_ROOT = Path("tests/fixtures/graph_assets/minimal_generic/graphs")
TYPE_GRAPH_ID = "tg"
FIBER_GRAPH_ID = "fg"


def test_load_graph_bundle_reads_minimal_fixture() -> None:
    bundle = _load_fixture_bundle()

    assert len(bundle.type_node_records) == 3
    assert len(bundle.type_edge_records) == 1
    assert len(bundle.fiber_node_records) == 3
    assert len(bundle.fiber_edge_records) == 1


def test_load_graph_bundle_indexes_records_by_id() -> None:
    bundle = _load_fixture_bundle()

    assert bundle.type_nodes["tg.node.person"].label == "Person"
    assert bundle.type_edges["tg.edge.person_member_of_organization"].source_type_id == (
        "tg.node.person"
    )
    assert bundle.fiber_nodes["fg.node.example_person"].type_id == "tg.node.person"
    assert (
        bundle.fiber_edges["fg.edge.example_person_member_of_example_organization"].target_id
        == "fg.node.example_organization"
    )


def test_load_graph_bundle_preserves_raw_metadata() -> None:
    bundle = _load_fixture_bundle()
    record = bundle.fiber_nodes["fg.node.example_person"]

    assert record.raw["provenance"]["created_by"] == "fixture"
    assert record.file_path == FIXTURE_ROOT / "fg/nodes.json"
    assert record.record_index == 0


def test_load_graph_bundle_preserves_duplicate_record_occurrences() -> None:
    bundle = _load_fixture_bundle("tests/fixtures/graph_assets/invalid_duplicate_id/graphs")

    assert len(bundle.type_node_records) == 3
    assert len(bundle.type_nodes) == 2


def test_load_graph_bundle_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(MissingGraphFileError):
        load_graph_bundle(tmp_path)


def test_load_graph_bundle_rejects_wrong_file_identity(tmp_path: Path) -> None:
    graph_root = _write_minimal_file_set(tmp_path)
    path = graph_root / "tg/nodes.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["graph_id"] = "fg"
    path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(GraphFileIdentityError):
        load_graph_bundle(graph_root, type_graph_id=TYPE_GRAPH_ID, fiber_graph_id=FIBER_GRAPH_ID)


def test_load_graph_bundle_rejects_missing_records_array(tmp_path: Path) -> None:
    graph_root = _write_minimal_file_set(tmp_path)
    path = graph_root / "tg/nodes.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data.pop("records")
    path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(InvalidGraphFileShapeError):
        load_graph_bundle(graph_root, type_graph_id=TYPE_GRAPH_ID, fiber_graph_id=FIBER_GRAPH_ID)


def test_load_graph_bundle_supports_protocol_defined_graph_ids(tmp_path: Path) -> None:
    graph_root = _write_rekeyed_minimal_file_set(
        tmp_path,
        type_graph_id="type_graph",
        fiber_graph_id="fiber_graph",
    )

    bundle = load_graph_bundle(graph_root, type_graph_id="type_graph", fiber_graph_id="fiber_graph")
    report = validate_graph_bundle(bundle, mode="strict")

    assert report.ok
    assert bundle.type_graph_id == "type_graph"
    assert bundle.fiber_graph_id == "fiber_graph"
    assert "type_graph.node.person" in bundle.type_nodes
    assert "fiber_graph.node.example_person" in bundle.fiber_nodes


def _load_fixture_bundle(graph_root: str | Path = FIXTURE_ROOT):
    return load_graph_bundle(
        graph_root,
        type_graph_id=TYPE_GRAPH_ID,
        fiber_graph_id=FIBER_GRAPH_ID,
    )


def _write_minimal_file_set(tmp_path: Path) -> Path:
    graph_root = tmp_path / "graphs"
    for source in FIXTURE_ROOT.rglob("*.json"):
        relative = source.relative_to(FIXTURE_ROOT)
        target = graph_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    return graph_root


def _write_rekeyed_minimal_file_set(
    tmp_path: Path,
    *,
    type_graph_id: str,
    fiber_graph_id: str,
) -> Path:
    graph_root = tmp_path / "graphs"
    replacements = {TYPE_GRAPH_ID: type_graph_id, FIBER_GRAPH_ID: fiber_graph_id}
    for source in FIXTURE_ROOT.rglob("*.json"):
        relative = source.relative_to(FIXTURE_ROOT)
        relative_parts = tuple(replacements.get(part, part) for part in relative.parts)
        target = graph_root.joinpath(*relative_parts)
        text = source.read_text(encoding="utf-8")
        for old, new in replacements.items():
            text = text.replace(old, new)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    return graph_root

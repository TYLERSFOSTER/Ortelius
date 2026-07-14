from __future__ import annotations

from pathlib import Path

from ortelius.cli import main

FIXTURE_BASE = Path("tests/fixtures/graph_assets")
TYPE_GRAPH_ID = "tg"
FIBER_GRAPH_ID = "fg"


def test_validate_exits_zero_for_valid_fixture(capsys) -> None:
    exit_code = main(
        [
            "validate",
            "--graph-root",
            str(FIXTURE_BASE / "minimal_generic/graphs"),
            *_graph_id_args(),
            "--mode",
            "strict",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "validation: ok" in output


def test_validate_exits_nonzero_for_invalid_fixture(capsys) -> None:
    exit_code = main(
        [
            "validate",
            "--graph-root",
            str(FIXTURE_BASE / "invalid_bad_edge_type/graphs"),
            *_graph_id_args(),
            "--mode",
            "strict",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "edge_target_type_mismatch" in output


def test_inspect_prints_counts(capsys) -> None:
    exit_code = main(
        ["inspect", "--graph-root", str(FIXTURE_BASE / "minimal_generic/graphs"), *_graph_id_args()]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "type_nodes: 3" in output
    assert "fiber_edges: 1" in output


def test_materialize_networkx_prints_counts(capsys) -> None:
    exit_code = main(
        [
            "materialize",
            "networkx",
            "--graph-root",
            str(FIXTURE_BASE / "minimal_generic/graphs"),
            *_graph_id_args(),
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "networkx_materialization: ok" in output
    assert "fiber_nodes: 3" in output


def test_materialize_dgl_reports_readiness_and_optional_dependency(capsys) -> None:
    exit_code = main(
        [
            "materialize",
            "dgl",
            "--graph-root",
            str(FIXTURE_BASE / "minimal_generic/graphs"),
            *_graph_id_args(),
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "dgl_readiness: ok" in output
    assert "dgl_materialization:" in output


def test_materialize_pyg_builds_nonempty_graph(capsys) -> None:
    exit_code = main(
        [
            "materialize",
            "pyg",
            "--graph-root",
            str(FIXTURE_BASE / "minimal_generic/graphs"),
            *_graph_id_args(),
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "pyg_readiness: ok" in output
    assert "pyg_materialization: ok" in output
    assert "pyg_node_types: 3" in output
    assert "pyg_edge_types: 1" in output
    assert "pyg_nodes: 3" in output
    assert "pyg_edges: 1" in output
    assert "pyg_features: none" in output


def test_materialize_pyg_exits_nonzero_for_invalid_fixture(capsys) -> None:
    exit_code = main(
        [
            "materialize",
            "pyg",
            "--graph-root",
            str(FIXTURE_BASE / "invalid_bad_edge_type/graphs"),
            *_graph_id_args(),
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "pyg_readiness: failed" in output
    assert "edge_target_type_mismatch" in output


def _graph_id_args() -> list[str]:
    return ["--type-graph-id", TYPE_GRAPH_ID, "--fiber-graph-id", FIBER_GRAPH_ID]

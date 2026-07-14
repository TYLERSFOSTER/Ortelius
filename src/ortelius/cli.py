"""Command-line interface for graph JSON validation and materialization checks."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from ortelius.graph_io import GraphLoadError, load_graph_bundle
from ortelius.materialize.dgl import (
    DGLReadinessError,
    OptionalDGLDependencyError,
    to_dgl_fiber_graph,
    validate_dgl_readiness,
)
from ortelius.materialize.networkx import (
    GraphMaterializationError,
    to_networkx_fiber_graph,
    to_networkx_type_graph,
)
from ortelius.materialize.pyg import (
    OptionalPyGDependencyError,
    PyGReadinessError,
    to_pyg_fiber_graph,
    validate_pyg_readiness,
)
from ortelius.paths import DEFAULT_FIBER_GRAPH_ID, DEFAULT_GRAPH_ROOT, DEFAULT_TYPE_GRAPH_ID
from ortelius.protocol_assets import (
    ProtocolAssetReport,
    inspect_protocol_bundle,
    validate_protocol_bundle,
    validate_system_protocol_assets,
)
from ortelius.validate import ValidationReport, validate_graph_bundle


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except GraphLoadError as exc:
        print(f"load_error: {exc}", file=sys.stderr)
        return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ortelius")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate")
    _add_graph_root_arg(validate_parser)
    validate_parser.add_argument("--mode", choices=("bootstrap", "strict"), default="bootstrap")
    validate_parser.set_defaults(func=_validate_command)

    inspect_parser = subparsers.add_parser("inspect")
    _add_graph_root_arg(inspect_parser)
    inspect_parser.set_defaults(func=_inspect_command)

    materialize_parser = subparsers.add_parser("materialize")
    materialize_subparsers = materialize_parser.add_subparsers(dest="target", required=True)

    networkx_parser = materialize_subparsers.add_parser("networkx")
    _add_graph_root_arg(networkx_parser)
    networkx_parser.set_defaults(func=_materialize_networkx_command)

    dgl_parser = materialize_subparsers.add_parser("dgl")
    _add_graph_root_arg(dgl_parser)
    dgl_parser.set_defaults(func=_materialize_dgl_command)

    pyg_parser = materialize_subparsers.add_parser("pyg")
    _add_graph_root_arg(pyg_parser)
    pyg_parser.set_defaults(func=_materialize_pyg_command)

    protocol_parser = subparsers.add_parser("protocol")
    protocol_subparsers = protocol_parser.add_subparsers(dest="target", required=True)

    validate_system_parser = protocol_subparsers.add_parser("validate-system")
    validate_system_parser.add_argument("--system-root", type=Path, required=True)
    validate_system_parser.set_defaults(func=_protocol_validate_system_command)

    validate_bundle_parser = protocol_subparsers.add_parser("validate-bundle")
    validate_bundle_parser.add_argument("--protocol-root", type=Path, required=True)
    validate_bundle_parser.set_defaults(func=_protocol_validate_bundle_command)

    inspect_bundle_parser = protocol_subparsers.add_parser("inspect-bundle")
    inspect_bundle_parser.add_argument("--protocol-root", type=Path, required=True)
    inspect_bundle_parser.set_defaults(func=_protocol_inspect_bundle_command)

    return parser


def _add_graph_root_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--graph-root",
        type=Path,
        default=DEFAULT_GRAPH_ROOT,
        help="Path to a graph root containing type/fiber graph JSON files.",
    )
    parser.add_argument("--type-graph-id", default=DEFAULT_TYPE_GRAPH_ID)
    parser.add_argument("--fiber-graph-id", default=DEFAULT_FIBER_GRAPH_ID)


def _validate_command(args: argparse.Namespace) -> int:
    bundle = _load_bundle_from_args(args)
    report = validate_graph_bundle(bundle, mode=args.mode)
    _print_report(report)
    return 0 if report.ok else 1


def _inspect_command(args: argparse.Namespace) -> int:
    bundle = _load_bundle_from_args(args)
    report = validate_graph_bundle(bundle)
    print(f"type_graph_id: {bundle.type_graph_id}")
    print(f"fiber_graph_id: {bundle.fiber_graph_id}")
    print(f"type_nodes: {len(bundle.type_node_records)}")
    print(f"type_edges: {len(bundle.type_edge_records)}")
    print(f"fiber_nodes: {len(bundle.fiber_node_records)}")
    print(f"fiber_edges: {len(bundle.fiber_edge_records)}")
    print(f"validation_errors: {report.error_count}")
    print(f"validation_warnings: {report.warning_count}")
    return 0 if report.ok else 1


def _materialize_networkx_command(args: argparse.Namespace) -> int:
    bundle = _load_bundle_from_args(args)
    try:
        fiber_graph = to_networkx_fiber_graph(bundle)
        type_graph = to_networkx_type_graph(bundle)
    except GraphMaterializationError as exc:
        print(f"networkx_materialization_error: {exc}", file=sys.stderr)
        return 1

    print("networkx_materialization: ok")
    print(f"type_graph_id: {bundle.type_graph_id}")
    print(f"fiber_graph_id: {bundle.fiber_graph_id}")
    print(f"fiber_nodes: {fiber_graph.number_of_nodes()}")
    print(f"fiber_edges: {fiber_graph.number_of_edges()}")
    print(f"type_nodes: {type_graph.number_of_nodes()}")
    print(f"type_edges: {type_graph.number_of_edges()}")
    return 0


def _materialize_dgl_command(args: argparse.Namespace) -> int:
    bundle = _load_bundle_from_args(args)
    readiness = validate_dgl_readiness(bundle)
    _print_report(readiness, prefix="dgl_readiness")
    if not readiness.ok:
        return 1

    try:
        materialization = to_dgl_fiber_graph(bundle)
    except OptionalDGLDependencyError as exc:
        print(f"dgl_materialization: unavailable ({exc})")
        return 0
    except DGLReadinessError as exc:
        print(f"dgl_materialization_error: {exc}", file=sys.stderr)
        return 1

    print("dgl_materialization: ok")
    print(f"dgl_node_types: {len(materialization.node_id_maps)}")
    print(f"dgl_canonical_edge_types: {len(materialization.edge_id_maps)}")
    return 0


def _materialize_pyg_command(args: argparse.Namespace) -> int:
    bundle = _load_bundle_from_args(args)
    readiness = validate_pyg_readiness(bundle)
    _print_report(readiness, prefix="pyg_readiness")
    if not readiness.ok:
        return 1

    try:
        materialization = to_pyg_fiber_graph(bundle)
    except OptionalPyGDependencyError as exc:
        print(f"pyg_materialization: unavailable ({exc})", file=sys.stderr)
        return 1
    except PyGReadinessError as exc:
        print(f"pyg_materialization_error: {exc}", file=sys.stderr)
        return 1

    total_nodes = sum(len(node_ids) for node_ids in materialization.node_id_maps.values())
    total_edges = sum(len(edge_ids) for edge_ids in materialization.edge_id_maps.values())
    print("pyg_materialization: ok")
    print(f"pyg_node_types: {len(materialization.node_id_maps)}")
    print(f"pyg_edge_types: {len(materialization.edge_id_maps)}")
    print(f"pyg_nodes: {total_nodes}")
    print(f"pyg_edges: {total_edges}")
    print("pyg_features: none")
    return 0


def _protocol_validate_system_command(args: argparse.Namespace) -> int:
    report = validate_system_protocol_assets(args.system_root)
    _print_protocol_asset_report(report, prefix="protocol_system_validation")
    return 0 if report.ok else 1


def _protocol_validate_bundle_command(args: argparse.Namespace) -> int:
    report = validate_protocol_bundle(args.protocol_root)
    _print_protocol_asset_report(report, prefix="protocol_bundle_validation")
    return 0 if report.ok else 1


def _protocol_inspect_bundle_command(args: argparse.Namespace) -> int:
    report = validate_protocol_bundle(args.protocol_root)
    if not report.ok:
        _print_protocol_asset_report(report, prefix="protocol_bundle_validation")
        return 1

    summary = inspect_protocol_bundle(args.protocol_root)
    for key, value in summary.items():
        print(f"{key}: {value}")
    return 0


def _load_bundle_from_args(args: argparse.Namespace):
    return load_graph_bundle(
        args.graph_root,
        type_graph_id=args.type_graph_id,
        fiber_graph_id=args.fiber_graph_id,
    )


def _print_report(report: ValidationReport, prefix: str = "validation") -> None:
    print(f"{prefix}: {'ok' if report.ok else 'failed'}")
    print(f"{prefix}_errors: {report.error_count}")
    print(f"{prefix}_warnings: {report.warning_count}")
    for issue in report.issues:
        location = f" record={issue.record_id}" if issue.record_id else ""
        print(f"{issue.severity}:{issue.code}:{issue.message}{location}")


def _print_protocol_asset_report(
    report: ProtocolAssetReport,
    prefix: str = "protocol_asset_validation",
) -> None:
    print(f"{prefix}: {'ok' if report.ok else 'failed'}")
    print(f"{prefix}_errors: {report.error_count}")
    print(f"{prefix}_warnings: {report.warning_count}")
    for issue in report.issues:
        location = f" file={issue.file_path}" if issue.file_path else ""
        print(f"{issue.severity}:{issue.code}:{issue.message}{location}")


if __name__ == "__main__":
    raise SystemExit(main())

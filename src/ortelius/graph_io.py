"""Load typed/fibered graph JSON into Python records."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol

from ortelius.model import (
    GraphBundle,
    GraphFile,
    GraphId,
    InstanceEdgeRecord,
    InstanceNodeRecord,
    RawObject,
    RecordKind,
    TypeEdgeRecord,
    TypeNodeRecord,
)
from ortelius.paths import (
    DEFAULT_FIBER_GRAPH_ID,
    DEFAULT_GRAPH_ROOT,
    DEFAULT_TYPE_GRAPH_ID,
    graph_file_specs,
)


class GraphLoadError(Exception):
    """Base class for graph JSON loading failures."""


class MissingGraphFileError(GraphLoadError):
    """Raised when an expected graph JSON file is missing."""


class InvalidGraphJsonError(GraphLoadError):
    """Raised when an expected graph JSON file is not valid JSON."""


class InvalidGraphFileShapeError(GraphLoadError):
    """Raised when a graph JSON file has the wrong top-level shape."""


class GraphFileIdentityError(GraphLoadError):
    """Raised when a graph JSON file has the wrong graph_id or record_kind."""


class _HasId(Protocol):
    id: str


def load_graph_bundle(
    graph_root: str | Path = DEFAULT_GRAPH_ROOT,
    *,
    type_graph_id: str = DEFAULT_TYPE_GRAPH_ID,
    fiber_graph_id: str = DEFAULT_FIBER_GRAPH_ID,
) -> GraphBundle:
    root = Path(graph_root)
    files: dict[tuple[GraphId, RecordKind], GraphFile] = {}
    specs = graph_file_specs(type_graph_id=type_graph_id, fiber_graph_id=fiber_graph_id)

    for (graph_id, record_kind), relative_path in specs.items():
        path = root / relative_path
        files[(graph_id, record_kind)] = _load_graph_file(path, graph_id, record_kind)

    type_node_records = _build_type_nodes(files[(type_graph_id, "nodes")])
    type_edge_records = _build_type_edges(files[(type_graph_id, "edges")])
    fiber_node_records = _build_instance_nodes(files[(fiber_graph_id, "nodes")])
    fiber_edge_records = _build_instance_edges(files[(fiber_graph_id, "edges")])

    return GraphBundle(
        graph_root=root,
        files=files,
        type_graph_id=type_graph_id,
        fiber_graph_id=fiber_graph_id,
        type_node_records=type_node_records,
        type_edge_records=type_edge_records,
        fiber_node_records=fiber_node_records,
        fiber_edge_records=fiber_edge_records,
        type_nodes=_index_first_by_id(type_node_records),
        type_edges=_index_first_by_id(type_edge_records),
        fiber_nodes=_index_first_by_id(fiber_node_records),
        fiber_edges=_index_first_by_id(fiber_edge_records),
    )


def _load_graph_file(path: Path, graph_id: GraphId, record_kind: RecordKind) -> GraphFile:
    if not path.exists():
        raise MissingGraphFileError(f"Missing graph file: {path}")

    try:
        with path.open(encoding="utf-8") as file:
            raw = json.load(file)
    except json.JSONDecodeError as exc:
        raise InvalidGraphJsonError(f"Invalid JSON in graph file {path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise InvalidGraphFileShapeError(f"Graph file {path} must contain a top-level object")

    actual_graph_id = raw.get("graph_id")
    actual_record_kind = raw.get("record_kind")
    if actual_graph_id != graph_id or actual_record_kind != record_kind:
        raise GraphFileIdentityError(
            f"Graph file {path} expected graph_id={graph_id!r}, record_kind={record_kind!r}; "
            f"got graph_id={actual_graph_id!r}, record_kind={actual_record_kind!r}"
        )

    records = raw.get("records")
    if not isinstance(records, list):
        raise InvalidGraphFileShapeError(f"Graph file {path} must contain a records array")

    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise InvalidGraphFileShapeError(
                f"Graph file {path} record {index} must contain an object"
            )

    schema_version = raw.get("schema_version")
    if not isinstance(schema_version, str):
        raise InvalidGraphFileShapeError(f"Graph file {path} must contain schema_version")

    return GraphFile(
        path=path,
        graph_id=graph_id,
        record_kind=record_kind,
        schema_version=schema_version,
        records=tuple(records),
        raw=raw,
    )


def _build_type_nodes(graph_file: GraphFile) -> tuple[TypeNodeRecord, ...]:
    return tuple(
        TypeNodeRecord(
            id=_str_value(raw.get("id")),
            label=_str_value(raw.get("label")),
            status=_str_value(raw.get("status")),
            type_fields=_dict_value(raw.get("type_fields")),
            raw=raw,
            file_path=graph_file.path,
            record_index=index,
        )
        for index, raw in enumerate(graph_file.records)
    )


def _build_type_edges(graph_file: GraphFile) -> tuple[TypeEdgeRecord, ...]:
    return tuple(
        TypeEdgeRecord(
            id=_str_value(raw.get("id")),
            label=_str_value(raw.get("label")),
            status=_str_value(raw.get("status")),
            source_type_id=_str_value(raw.get("source_type_id")),
            target_type_id=_str_value(raw.get("target_type_id")),
            type_fields=_dict_value(raw.get("type_fields")),
            raw=raw,
            file_path=graph_file.path,
            record_index=index,
        )
        for index, raw in enumerate(graph_file.records)
    )


def _build_instance_nodes(graph_file: GraphFile) -> tuple[InstanceNodeRecord, ...]:
    return tuple(
        InstanceNodeRecord(
            id=_str_value(raw.get("id")),
            type_id=_str_value(raw.get("type_id")),
            label=_str_value(raw.get("label")),
            status=_str_value(raw.get("status")),
            fields=_dict_value(raw.get("fields")),
            raw=raw,
            file_path=graph_file.path,
            record_index=index,
        )
        for index, raw in enumerate(graph_file.records)
    )


def _build_instance_edges(graph_file: GraphFile) -> tuple[InstanceEdgeRecord, ...]:
    return tuple(
        InstanceEdgeRecord(
            id=_str_value(raw.get("id")),
            type_id=_str_value(raw.get("type_id")),
            source_id=_str_value(raw.get("source_id")),
            target_id=_str_value(raw.get("target_id")),
            label=_str_value(raw.get("label")),
            status=_str_value(raw.get("status")),
            fields=_dict_value(raw.get("fields")),
            raw=raw,
            file_path=graph_file.path,
            record_index=index,
        )
        for index, raw in enumerate(graph_file.records)
    )


def _index_first_by_id[RecordT: _HasId](records: tuple[RecordT, ...]) -> dict[str, RecordT]:
    index: dict[str, RecordT] = {}
    for record in records:
        record_id = record.id
        if record_id and record_id not in index:
            index[record_id] = record
    return index


def _str_value(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _dict_value(value: Any) -> RawObject:
    return value if isinstance(value, dict) else {}

"""Core in-memory model for typed/fibered graph JSON."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

GraphId = str
RecordKind = Literal["nodes", "edges"]
ValidationMode = Literal["bootstrap", "strict"]
RawObject = dict[str, Any]
TypeFields = dict[str, Any]


@dataclass(frozen=True)
class GraphFile:
    path: Path
    graph_id: GraphId
    record_kind: RecordKind
    schema_version: str
    records: tuple[RawObject, ...]
    raw: RawObject


@dataclass(frozen=True)
class TypeNodeRecord:
    id: str
    label: str
    status: str
    type_fields: TypeFields
    raw: RawObject
    file_path: Path
    record_index: int


@dataclass(frozen=True)
class TypeEdgeRecord:
    id: str
    label: str
    status: str
    source_type_id: str
    target_type_id: str
    type_fields: TypeFields
    raw: RawObject
    file_path: Path
    record_index: int


@dataclass(frozen=True)
class InstanceNodeRecord:
    id: str
    type_id: str
    label: str
    status: str
    fields: RawObject
    raw: RawObject
    file_path: Path
    record_index: int


@dataclass(frozen=True)
class InstanceEdgeRecord:
    id: str
    type_id: str
    source_id: str
    target_id: str
    label: str
    status: str
    fields: RawObject
    raw: RawObject
    file_path: Path
    record_index: int


GraphRecord = TypeNodeRecord | TypeEdgeRecord | InstanceNodeRecord | InstanceEdgeRecord


@dataclass(frozen=True)
class GraphBundle:
    graph_root: Path
    files: dict[tuple[GraphId, RecordKind], GraphFile]
    type_graph_id: GraphId
    fiber_graph_id: GraphId
    type_node_records: tuple[TypeNodeRecord, ...]
    type_edge_records: tuple[TypeEdgeRecord, ...]
    fiber_node_records: tuple[InstanceNodeRecord, ...]
    fiber_edge_records: tuple[InstanceEdgeRecord, ...]
    type_nodes: dict[str, TypeNodeRecord]
    type_edges: dict[str, TypeEdgeRecord]
    fiber_nodes: dict[str, InstanceNodeRecord]
    fiber_edges: dict[str, InstanceEdgeRecord]

    def all_records(self) -> tuple[GraphRecord, ...]:
        return (
            *self.type_node_records,
            *self.type_edge_records,
            *self.fiber_node_records,
            *self.fiber_edge_records,
        )

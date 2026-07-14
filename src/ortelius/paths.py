"""Path helpers for typed/fibered graph assets."""

from __future__ import annotations

from pathlib import Path

DEFAULT_GRAPH_ROOT = Path("assets/graph_assets/graphs")
DEFAULT_TYPE_GRAPH_ID = "tg"
DEFAULT_FIBER_GRAPH_ID = "fg"

def graph_file_specs(
    type_graph_id: str = DEFAULT_TYPE_GRAPH_ID,
    fiber_graph_id: str = DEFAULT_FIBER_GRAPH_ID,
) -> dict[tuple[str, str], Path]:
    return {
        (type_graph_id, "nodes"): Path(f"{type_graph_id}/nodes.json"),
        (type_graph_id, "edges"): Path(f"{type_graph_id}/edges.json"),
        (fiber_graph_id, "nodes"): Path(f"{fiber_graph_id}/nodes.json"),
        (fiber_graph_id, "edges"): Path(f"{fiber_graph_id}/edges.json"),
    }


def id_prefixes(
    type_graph_id: str = DEFAULT_TYPE_GRAPH_ID,
    fiber_graph_id: str = DEFAULT_FIBER_GRAPH_ID,
) -> dict[tuple[str, str], str]:
    return {
        (type_graph_id, "nodes"): f"{type_graph_id}.node.",
        (type_graph_id, "edges"): f"{type_graph_id}.edge.",
        (fiber_graph_id, "nodes"): f"{fiber_graph_id}.node.",
        (fiber_graph_id, "edges"): f"{fiber_graph_id}.edge.",
    }


GRAPH_FILE_SPECS = graph_file_specs()
ID_PREFIXES = id_prefixes()

# Ortelius LLM Context

## One-Sentence Summary

Ortelius is a Codex-facing graph-population protocol system and Python toolkit
for building, validating, inspecting, and materializing typed/fibered graph
JSON.

## What Ortelius Does

Ortelius gives Codex a repo-local workflow surface for creating candidate graph
data. The workflow begins with a human graph-building request and a system
protocol document. Codex compiles that request into a generated protocol bundle,
then executes bounded graph-population actions through Markdown loop specs,
JSON graph files, cursor state, execution logs, reports, and source-batch
artifacts.

The key workflow prompt is:

```text
MAKE-GRAPH

Use assets/protocol_assets/system/graph_population/v001/graph_population_protocol_schema.md
as the graph-build request compilation schema.

Make graph on domain: <domain>, with <N> node types and <M> instances of each
type, and then <E> edge types and <K> instances of each.

graph_intent:
  domain_lens: <optional modeling lens>
  positive_type_examples:
    - <optional>
  positive_relation_examples:
    - <optional>
  negative_scope:
    - <optional>
  competency_questions:
    - <optional>
```

For broad domains, graph intent is the modeling-lens contract that tells Codex
what kind of graph to build before source/type/edge loops begin.

## What Ortelius Does Not Do

Ortelius v0.1.0 does not itself call Codex, crawl the web, persist to a graph
database, train graph ML models, guarantee source completeness, or guarantee
graph quality.

The protocol docs tell Codex how to structure the workflow. The Python package
validates and materializes the graph JSON that workflow produces.

## Graph Model

Ortelius uses two graph IDs:

```text
<fiber_graph_id> -> <type_graph_id>
```

The type graph defines admissible node types and edge types. Type records also
define field schemas expected on concrete records.

The fiber graph contains concrete nodes and concrete edges. Every fiber node has
a `type_id` pointing to a type node. Every fiber edge has a `type_id` pointing
to a type edge.

Core projection invariant:

```text
edge = fiber_edges[e]
edge_type = type_edges[edge.type_id]
source_node = fiber_nodes[edge.source_id]
target_node = fiber_nodes[edge.target_id]

source_node.type_id == edge_type.source_type_id
target_node.type_id == edge_type.target_type_id
```

## System Protocol Pair

The v001 system protocol pair lives here:

```text
assets/protocol_assets/system/graph_population/v001/
```

Important files:

- [Protocol schema](../assets/protocol_assets/system/graph_population/v001/graph_population_protocol_schema.md)
- [Control protocol](../assets/protocol_assets/system/graph_population/v001/graph_population_control_protocol.md)
- [Protocol manifest](../assets/protocol_assets/system/graph_population/v001/manifest.json)
- [Generate-bundle prompt](../assets/protocol_assets/system/graph_population/v001/prompts/generate_bundle.md)
- [Execute-bundle prompt](../assets/protocol_assets/system/graph_population/v001/prompts/execute_bundle.md)

The protocol schema is the compiler/bundle generator. It handles `MAKE-GRAPH`
and `GENERATE-BUNDLE`.

The control protocol is the executor. It handles `EXECUTE-BUNDLE` for an
already generated bundle.

## Generated Bundle Contract

Generated graph-population bundles belong under:

```text
assets/protocol_assets/bundles/<domain_slug>/<protocol_id>/
```

Generated bundle contents typically include:

```text
manifest.json
graph_population_protocol.md
control_loop_plan.md
loop_specs/
candidate_graphs/
runs/<run_id>/cursor.json
runs/<run_id>/execution_log.md
runs/<run_id>/reports/
  graph_intent_contract.md
source_batches/
batch_packets/
tool_outputs/
```

Generated bundles are ignored by git by default. The only tracked file in the
generated-bundle root should be:

```text
assets/protocol_assets/bundles/.gitkeep
```

## Python Package Surface

Package:

```text
src/ortelius/
```

Stable top-level imports:

```python
from ortelius import GraphBundle, load_graph_bundle, validate_graph_bundle
```

Materializers:

```python
from ortelius.materialize.networkx import (
    to_networkx_fiber_graph,
    to_networkx_type_graph,
)
from ortelius.materialize.pyg import validate_pyg_readiness, to_pyg_fiber_graph
from ortelius.materialize.dgl import validate_dgl_readiness, to_dgl_fiber_graph
```

Protocol checks:

```python
from ortelius.protocol_assets import (
    validate_protocol_bundle,
    validate_system_protocol_assets,
)
```

## CLI Examples

Validate the v001 system protocol assets:

```bash
uv run ortelius protocol validate-system --system-root assets/protocol_assets/system/graph_population/v001
```

Validate and inspect the minimal generated-bundle fixture:

```bash
uv run ortelius protocol validate-bundle --protocol-root tests/fixtures/protocol_assets/minimal_generated_bundle
uv run ortelius protocol inspect-bundle --protocol-root tests/fixtures/protocol_assets/minimal_generated_bundle
```

Validate and inspect the generic graph fixture:

```bash
uv run ortelius validate --graph-root tests/fixtures/graph_assets/minimal_generic/graphs --type-graph-id tg --fiber-graph-id fg --mode bootstrap
uv run ortelius inspect --graph-root tests/fixtures/graph_assets/minimal_generic/graphs --type-graph-id tg --fiber-graph-id fg
```

Run materialization smokes:

```bash
uv run ortelius materialize networkx --graph-root tests/fixtures/graph_assets/minimal_generic/graphs --type-graph-id tg --fiber-graph-id fg
uv run ortelius materialize pyg --graph-root tests/fixtures/graph_assets/minimal_generic/graphs --type-graph-id tg --fiber-graph-id fg
uv run ortelius materialize dgl --graph-root tests/fixtures/graph_assets/minimal_generic/graphs --type-graph-id tg --fiber-graph-id fg
```

## Stable Links

- [README](../README.md)
- [Protocol schema](../assets/protocol_assets/system/graph_population/v001/graph_population_protocol_schema.md)
- [Control protocol](../assets/protocol_assets/system/graph_population/v001/graph_population_control_protocol.md)
- [CLI implementation](../src/ortelius/cli.py)
- [Generic graph fixture](../tests/fixtures/graph_assets/minimal_generic/graphs/)
- [Generic type graph nodes](../tests/fixtures/graph_assets/minimal_generic/graphs/tg/nodes.json)
- [Generic type graph edges](../tests/fixtures/graph_assets/minimal_generic/graphs/tg/edges.json)
- [Generic fiber graph nodes](../tests/fixtures/graph_assets/minimal_generic/graphs/fg/nodes.json)
- [Generic fiber graph edges](../tests/fixtures/graph_assets/minimal_generic/graphs/fg/edges.json)

## Release Facts

- Package name: `ortelius`
- Current version: `0.1.0`
- Python: `>=3.12`
- License: MIT
- Protocol version: `v001`
- Main CLI: `ortelius`
- Main prompt: `MAKE-GRAPH`

## LLM Handling Notes

When assisting with Ortelius:

- Treat the protocol docs as operational documents, not background prose.
- Treat generated bundle files as run authority once a bundle exists.
- Do not invent hidden helper scripts as the workflow driver.
- Do not infer graph intent silently for broad domains unless the prompt explicitly authorizes infer-and-proceed.
- Do not claim the Python package performs autonomous crawling.
- Do not commit generated domain bundles by default.
- Keep examples domain-neutral unless the user explicitly requests a domain.

<p align="center">
  <img src="assets/images/logo.jpg" alt="Ortelius" width="100%">
</p>

# Ortelius

[![CI](https://github.com/TYLERSFOSTER/Ortelius/actions/workflows/ci.yml/badge.svg)](https://github.com/TYLERSFOSTER/Ortelius/actions/workflows/ci.yml)
[![Version](https://img.shields.io/badge/version-0.1.0-blue)](pyproject.toml)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Protocol](https://img.shields.io/badge/graph_population_protocol-v001-purple)](assets/protocol_assets/system/graph_population/v001/manifest.json)

Ortelius is a Codex-facing toolkit for building, validating, and materializing
source-grounded typed/fibered graph JSON.

You point Codex + Ortelius at a domain, tell it to make a graph database / knowledge graph of that domain, and Codex, guided by Ortelius, does it.

## What This Is

Ortelius has two public layers:

- operational protocol assets that tell Codex how to compile and execute a
  graph-population workflow;
- a Python graph substrate for typed/fibered graph JSON.

In short: Ortelius provides Codex-facing graph-population protocols for typed/fibered graph JSON,
plus the validation and materialization tools needed to keep that JSON usable.

The protocol assets are Markdown/JSON control surfaces for Codex. Codex reads
them, creates a generated graph-population bundle, follows the bundle's loop
specs, updates cursor/log state, and writes candidate graph JSON.

A first Ortelius prompt to Codex looks like this:

```text
MAKE-GRAPH

Use assets/protocol_assets/system/graph_population/v001/graph_population_protocol_schema.md
as the graph-build request compilation schema.

Make graph on domain: <domain>, with <N> node types and <M> instances of each
type, and then <E> edge types and <K> instances of each.
```

That minimal prompt is supposed to be enough. If the domain is broad or
multi-model and no graph intent is supplied, Ortelius instructs Codex to pause
before source probing or bundle generation, ask bounded alignment questions or
propose candidate graph lenses, and wait for confirmation.

You can optionally accelerate that first intent step with a lens, examples,
exclusions, or competency questions, but the system owns the detection step.

Generated bundles are local runtime artifacts. They are ignored by git by
default.

### Two Scales Of Control

Ortelius uses Codex at two scales of control: globally, as a policy-driven
interpreter for the workflow; locally, as a source-grounded semantic synthesis
primitive at the leaves of that workflow.

Globally, Codex is not a mechanically enforced CPU, but the protocol documents
constrain and cue its behavior because Codex chooses its next action by reading
and following the protocol. The protocol schema acts as an executable
metaprogram: Codex reads it, then generates the workflow manifest, loop specs,
cursor/log scaffold, batch packets, and control-loop plan. The control protocol
then acts as the interpreter contract: Codex reads the generated workflow
program, advances the externalized program counter, executes the next legal
bounded action, validates, logs, and resumes.

Locally, at the leaves of the workflow, Codex is used as the semantic engine.
The system calls on Codex to perform source-grounded semantic synthesis: to
identify meaningful types, discover fields, distinguish primitive relationships
from query-derived edges, and decide what the evidence justifies writing.

The central design trick in Ortelius is keeping these two roles separated. Ortelius makes Codex rigid where it should be rigid and creative where it should be creative.

The Python package `src/ortelius` within Ortelius supports the above workflow by loading graph JSON, validating graph invariants, inspecting graph counts, and materializing graph structure for NetworkX, PyG, and DGL readiness.

Ortelius v0.1.0 does not itself call Codex, crawl the web, persist to a graph
database, train graph ML models, or guarantee graph quality. It provides the
public substrate and protocol surface that a Codex session can use to build and
validate candidate graph data.

## Stable Links

- [LLM index](llms.txt)
- [Full LLM context](docs/llm_context.md)
- [Protocol schema](assets/protocol_assets/system/graph_population/v001/graph_population_protocol_schema.md)
- [Control protocol](assets/protocol_assets/system/graph_population/v001/graph_population_control_protocol.md)
- [CLI examples](#cli)
- [Generic graph JSON fixture](tests/fixtures/graph_assets/minimal_generic/graphs/)

## Graph Model

Ortelius expects a pair of graph IDs:

```text
<fiber_graph_id> -> <type_graph_id>
```

The type graph defines admissible node types and edge types. Type records also
define fields expected on concrete records.

The fiber graph contains concrete nodes and concrete edges. Every fiber node has
a `type_id` pointing to a type node. Every fiber edge has a `type_id` pointing to
a type edge.

For every fiber edge:

```text
edge = fiber_edges[e]
edge_type = type_edges[edge.type_id]
source_node = fiber_nodes[edge.source_id]
target_node = fiber_nodes[edge.target_id]

source_node.type_id == edge_type.source_type_id
target_node.type_id == edge_type.target_type_id
```

That projection invariant is the center of the system.

## Install

This project uses `uv`.

```bash
uv sync
```

Run the test suite:

```bash
uv run pytest
uv run ruff check .
git diff --check
```

## Repository Layout

```text
assets/
  images/
    logo.jpg
  protocol_assets/
    system/graph_population/v001/
      manifest.json
      graph_population_protocol_schema.md
      graph_population_control_protocol.md
      prompts/
    bundles/
      .gitkeep

src/ortelius/
  graph_io.py
  model.py
  validate.py
  protocol_assets.py
  cli.py
  materialize/

tests/
  fixtures/graph_assets/minimal_generic/
  fixtures/protocol_assets/minimal_generated_bundle/
```

## Using Ortelius With Codex

The main public workflow is to ask Codex to use the system protocol docs. The
quick-start prompt appears above; use this guided form when you want Codex to
show more state as it works.

Guided invocation:

```text
MAKE-GRAPH

Use assets/protocol_assets/system/graph_population/v001/graph_population_protocol_schema.md
as the graph-build request compilation schema.

interaction_level: guided
diagnostic_verbosity: normal

Make graph on domain: <domain>, with <N> node types and <M> instances of each
type, and then <E> edge types and <K> instances of each.
```

Codex should create a generated bundle first, including a graph-intent
contract for ordinary `MAKE-GRAPH`, then execute bounded source-grounded graph
actions through that bundle. The generated bundle, not
model memory, is the run authority.

Generated bundles belong under:

```text
assets/protocol_assets/bundles/<domain_slug>/<protocol_id>/
```

That path is ignored by git except for `.gitkeep`.

## System Protocol Assets

The two main protocol documents are:

```text
assets/protocol_assets/system/graph_population/v001/graph_population_protocol_schema.md
assets/protocol_assets/system/graph_population/v001/graph_population_control_protocol.md
```

The protocol schema compiles a graph-building request into a generated bundle.
The control protocol walks an existing generated bundle by reading its manifest,
loop specs, graph JSON, cursor, and execution log.

Validate the system protocol assets:

```bash
uv run ortelius protocol validate-system --system-root assets/protocol_assets/system/graph_population/v001
```

Validate and inspect the minimal generated-bundle fixture:

```bash
uv run ortelius protocol validate-bundle --protocol-root tests/fixtures/protocol_assets/minimal_generated_bundle
uv run ortelius protocol inspect-bundle --protocol-root tests/fixtures/protocol_assets/minimal_generated_bundle
```

## Python API

Stable top-level imports:

```python
from ortelius import GraphBundle, load_graph_bundle, validate_graph_bundle
```

Materializer imports:

```python
from ortelius.materialize.networkx import (
    to_networkx_fiber_graph,
    to_networkx_type_graph,
)
from ortelius.materialize.pyg import validate_pyg_readiness, to_pyg_fiber_graph
from ortelius.materialize.dgl import validate_dgl_readiness, to_dgl_fiber_graph
```

Protocol asset checks:

```python
from ortelius.protocol_assets import (
    validate_protocol_bundle,
    validate_system_protocol_assets,
)
```

## CLI

Validate and inspect graph JSON:

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

Available commands:

```text
ortelius validate
ortelius inspect
ortelius materialize networkx
ortelius materialize pyg
ortelius materialize dgl
ortelius protocol validate-system
ortelius protocol validate-bundle
ortelius protocol inspect-bundle
```

## DGL

DGL is optional. Try installing it only if your platform has a compatible wheel:

```bash
uv add dgl
```

Ortelius keeps DGL readiness and missing-dependency behavior tested without
requiring DGL as a default dependency.

## Generated Bundle Policy

Generated graph-population bundles are not release assets by default. Keep them
local unless you deliberately promote a generated bundle into a fixture or public
example.

The tracked generated-bundle placeholder is:

```text
assets/protocol_assets/bundles/.gitkeep
```

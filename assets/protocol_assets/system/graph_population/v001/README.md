# Graph Population System Protocols v001

This directory contains hand-authored, domain-agnostic system protocols for
graph population.

Runtime prompts should point to this directory.

## Files

- `manifest.json`: machine-readable index for this protocol version.
- `graph_population_protocol_schema.md`: `GENERATE-BUNDLE` protocol-generation
  schema.
- `graph_population_control_protocol.md`: `EXECUTE-BUNDLE` control protocol.
- `prompts/generate_bundle.md`: prompt template for creating a generated
  bundle.
- `prompts/execute_bundle.md`: prompt template for running a generated bundle.

## Boundary

These files are not a generated domain bundle. They are the stable system
protocols that generated bundles reference.

For ordinary `MAKE-GRAPH`, generated bundles must include explicit Markdown
graph-intent, source-landscape, source-family, source-adapter-frontier, joint-population,
endpoint-reservation, batch-packet, and semantic-acceptance artifacts. Python
and graph tooling may validate, inspect, materialize, and test graph JSON, but
must not become the hidden workflow runtime that selects sources, types,
relations, records, or accepted semantic targets.

Generated bundles should live under:

```text
assets/protocol_assets/bundles/<domain_slug>/<protocol_id>/
```

## Non-Goals

This directory does not contain populated graph facts, live crawl results, or a
hard Python interpreter that calls Codex/OpenAI APIs.

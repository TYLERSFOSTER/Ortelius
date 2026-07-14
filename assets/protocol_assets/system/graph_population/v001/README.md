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

Generated bundles should live under:

```text
assets/protocol_assets/bundles/<domain_slug>/<protocol_id>/
```

## Non-Goals

This directory does not contain populated graph facts, live crawl results, or a
hard Python interpreter that calls Codex/OpenAI APIs.

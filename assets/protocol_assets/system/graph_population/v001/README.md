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
graph-intent, semantic-plan-authority, source-event-ledger, source-landscape,
source-family, source-adapter-frontier, type-candidate, type-field,
edge-candidate, edge-family-diversity, edge-field, domain-membership-boundary,
source-evidence-accounting, label-quality, joint-population,
endpoint-reservation, batch-packet, semantic-sample, and semantic-acceptance
artifacts. Python and graph tooling may validate, inspect, materialize, and
test graph JSON, but must not become the hidden workflow runtime that selects
sources, types, relations, records, or accepted semantic targets.

Generated bundles should live under:

```text
assets/protocol_assets/bundles/<domain_slug>/<protocol_id>/
```

## Non-Goals

This directory does not contain populated graph facts, live crawl results, or a
hard Python interpreter that calls Codex/OpenAI APIs.

## Post-run correction gates

For ordinary `MAKE-GRAPH`, v001 now treats semantic completion as stricter than
structural JSON validity. A generated bundle must materialize graph intent
before source probing, express source reconnaissance through Markdown batch
packets, audit any generated mechanical code, separate candidate records from
accepted target-counting records, pass row-backed field, relation-family,
domain membership, source evidence, label quality, and semantic sample audits,
and reconcile accepted counts before claiming completion.

If semantic acceptance is incomplete, Codex should report that the graph is not
complete before reporting raw counts or structural validation.

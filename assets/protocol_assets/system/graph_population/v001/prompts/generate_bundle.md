# Generate Bundle Prompt Template

```text
GENERATE-BUNDLE

Use assets/protocol_assets/system/graph_population/v001/graph_population_protocol_schema.md
as the protocol-generation schema.

interaction_level: <expert|guided|onboarding>
diagnostic_verbosity: <terse|normal|full>
domain_label: <domain label>
domain_slug: <domain slug>
protocol_id: <protocol id>
protocol_root: assets/protocol_assets/bundles/<domain_slug>/<protocol_id>
type_graph_id: <type graph id>
fiber_graph_id: <fiber graph id>
candidate_graph_root: assets/protocol_assets/bundles/<domain_slug>/<protocol_id>/candidate_graphs
source_policy: <source policy>
run_contract_id: <run contract id>

Create a domain-specific graph-population protocol bundle. Do not populate graph
facts. Do not crawl live sources unless explicitly authorized as part of protocol
design. Create the domain protocol document, required loop specs, initialized
graph JSON files, manifest, cursor, and execution log placeholders.

The generated bundle must be compatible with:

assets/protocol_assets/system/graph_population/v001/graph_population_control_protocol.md

The generated bundle must use declared graph IDs and must not assume any
domain-specific graph names.
```

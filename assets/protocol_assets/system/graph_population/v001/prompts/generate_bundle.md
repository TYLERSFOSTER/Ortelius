# Generate Bundle Prompt Template

```text
GENERATE-BUNDLE

Use assets/protocol_assets/system/graph_population/v001/graph_population_protocol_schema.md
as the protocol-generation schema.

interaction_level: <expert|guided|onboarding>
diagnostic_verbosity: <terse|normal|full>
domain_label: <domain label>
domain_slug: <domain slug>
domain_lens: <optional modeling lens>
positive_type_examples:
  - <optional>
positive_relation_examples:
  - <optional>
positive_instance_examples:
  - <optional>
negative_scope:
  - <optional>
competency_questions:
  - <optional>
intent_confirmation_policy: <user_supplied_confirmed|infer_and_confirm|infer_and_proceed_explicitly_authorized|needs_human_confirmation>
protocol_id: <protocol id>
protocol_root: assets/protocol_assets/bundles/<domain_slug>/<protocol_id>
type_graph_id: <type graph id>
fiber_graph_id: <fiber graph id>
candidate_graph_root: assets/protocol_assets/bundles/<domain_slug>/<protocol_id>/candidate_graphs
source_policy: <source policy>
run_contract_id: <run contract id>

Create a domain-specific graph-population protocol bundle, including graph-intent
alignment surfaces and graph_intent_contract.md. Do not populate graph facts. Do not crawl live sources unless explicitly authorized as part of protocol
design. Create the domain protocol document, required loop specs, initialized
graph JSON files, manifest, cursor, and execution log placeholders.

The generated bundle must be compatible with:

assets/protocol_assets/system/graph_population/v001/graph_population_control_protocol.md

The generated bundle must use declared graph IDs and must not assume any
domain-specific graph names.

Post-confirmation order for `MAKE-GRAPH`: after graph intent is confirmed or explicitly authorized, Codex must materialize `graph_intent_contract.md`, `semantic_plan_authority_report.md`, `source_probe_event_ledger.md`, `control_loop_plan.md`, cursor/log state, and the source reconnaissance plan before any source probe. Source reconnaissance must be expressed in Markdown batch packets before execution. Generated helper code may only perform declared mechanical work and requires `generated_code_runtime_audit.md`; it must not decide semantic graph content. Accepted target counts mean accepted semantic records, not raw JSON records.

Generated bundles must initialize source-evidenced semantic report surfaces:
`type_candidate_review.md`, `type_field_discovery_report.md`,
`edge_candidate_review.md`, `edge_family_diversity_report.md`,
`edge_field_discovery_report.md`, `domain_membership_boundary_report.md`,
`source_evidence_accounting_report.md`, `label_quality_report.md`,
`semantic_sample_audit.md`, and `semantic_acceptance_report.md`. These are
Markdown control surfaces, not mirrors of hidden generated code.

Front-door note for `MAKE-GRAPH`: a minimal prompt with only domain + target
counts is valid and sufficient. If graph intent is missing and the domain is
broad or multi-model, Codex must run GraphIntentAlignment.Domain.ResolveIntent,
ask bounded alignment questions or propose candidate lenses, and stop before
source probing or bundle generation. Missing graph intent is the trigger, not a
reason to ask for a better prompt.
```

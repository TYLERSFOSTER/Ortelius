# Type Field Discovery

## Loop Identity

loop_id: type_field_discovery
graph_level: type_graph
manifest_order_index: 4
ordered_after: type_node_discovery
ordered_before: type_edge_discovery

## Inputs

input_files: candidate_graphs/tg/nodes.json
required_manifest_fields: graphs.type_graph_id
required_graph_files: candidate_graphs/tg/nodes.json

## Iterator

iterator_name: type_nodes
iterator_source: candidate_graphs/tg/nodes.json
target_count: 0
completion_count: 0

## Current Item Shape

current_item_fields: type_node_id, field_key
cursor_fields: active_iteration.current_type_node_id

## Action Template

action_id_template: type_field_discovery.<type_node_id>
action_prompt_template: Add declared fields for one type node when evidence exists.
allowed_subloops: field_check
attempt_budget: 1

## Allowed Writes

output_files: candidate_graphs/tg/nodes.json
write_rule: update type_fields only for current type node
max_records_written_per_action: 1

## Source Boundaries

allowed_source_types: generated protocol declared sources
allowed_source_locations: generated protocol declared locations
disallowed_sources: undeclared sources
max_sources_checked: 0
evidence_threshold: fixture has no type nodes

## Evidence Required

record_evidence_required: field rationale
field_evidence_required: value_kind, cardinality, source_policy
unsupported_claim_rule: do not invent fields

## Validation Required

validation_command: uv run ortelius validate --graph-root tests/fixtures/protocol_assets/minimal_generated_bundle/candidate_graphs --type-graph-id tg --fiber-graph-id fg --mode bootstrap
validation_checklist: type_fields are well formed
validation_unavailable_rule: stop

## Completion Rule

action_completion_rule: current type node fields checked
loop_completion_rule: all type nodes checked

## Semantic Acceptance Gate

candidate_counting_rule: fixture candidates do not count toward MAKE-GRAPH targets unless explicitly accepted
accepted_counting_rule: fixture accepted records require source-backed semantic evidence
target_progress_rule: fixture target progress is logged separately from structural validation
semantic_gate: fixture semantic gate documented for protocol validation
source_backing_rule: fixture source policy controls accepted records
field_completion_rule: fixture missing values follow declared missing-value policy
duplicate_or_multitype_policy: fixture duplicates do not count without explicit policy
seed_contract_status_rule: seed contracts do not satisfy MAKE-GRAPH semantic gates

## Recovery Policy

recoverable_failure_classes: fixture semantic shortfall, source timeout, sparse result, missing field depth
recovery_ladder: retry_or_log_fixture_limitation
recovery_attempt_budget: 1
resume_condition: fixture recovery succeeds or limitation is logged
exhaustion_condition: fixture recovery budget exhausted
proxy_substitution_forbidden: true

## Batch Execution

batch_execution_meaning: single_fixture_batch_not_generated_code_loop
batch_plan_path: runs/run_001/source_batch_plan.md
batch_packet_path: runs/run_001/batch_packets/fixture_batch.md
batch_size: fixture_small
checkpoint_rule: update cursor and execution log after fixture action

## Stop Conditions

stop_conditions: malformed type_fields, source boundary missing
failure_report_fields: failure_kind, record_id

## Handoff

handoff_to_next_loop: type_edge_discovery
cursor_update_rule: set active_loop_id to type_edge_discovery

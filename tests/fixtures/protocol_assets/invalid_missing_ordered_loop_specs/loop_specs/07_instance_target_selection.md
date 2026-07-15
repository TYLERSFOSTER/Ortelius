# Instance Target Selection

## Loop Identity

loop_id: instance_target_selection
graph_level: fiber_graph
manifest_order_index: 7
ordered_after: type_graph_review
ordered_before: instance_discovery

## Inputs

input_files: candidate_graphs/tg/nodes.json
required_manifest_fields: graphs.fiber_graph_id
required_graph_files: candidate_graphs/tg/nodes.json

## Iterator

iterator_name: type_nodes
iterator_source: candidate_graphs/tg/nodes.json
target_count: 0
completion_count: 0

## Current Item Shape

current_item_fields: type_node_id, target_count
cursor_fields: active_iteration.current_type_node_id

## Action Template

action_id_template: instance_target_selection.<type_node_id>
action_prompt_template: Choose instance target count for one type node.
allowed_subloops: none
attempt_budget: 1

## Allowed Writes

output_files: graph_population_protocol.md, runs/run_001/execution_log.md
write_rule: record target counts only
max_records_written_per_action: 0

## Source Boundaries

allowed_source_types: generated protocol declared sources
allowed_source_locations: generated protocol declared locations
disallowed_sources: undeclared sources
max_sources_checked: 0
evidence_threshold: fixture has no type nodes

## Evidence Required

record_evidence_required: target count rationale
field_evidence_required: none
unsupported_claim_rule: do not invent instances

## Validation Required

validation_command: uv run ortelius protocol validate-bundle --protocol-root tests/fixtures/protocol_assets/minimal_generated_bundle
validation_checklist: target counts are declared before instance discovery
validation_unavailable_rule: stop

## Completion Rule

action_completion_rule: current type target selected or no type exists
loop_completion_rule: all type nodes have targets

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

stop_conditions: missing target count, project_owner_decision_required
failure_report_fields: failure_kind, next_required_input

## Handoff

handoff_to_next_loop: instance_discovery
cursor_update_rule: set active_loop_id to instance_discovery

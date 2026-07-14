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

## Stop Conditions

stop_conditions: missing target count, project_owner_decision_required
failure_report_fields: failure_kind, next_required_input

## Handoff

handoff_to_next_loop: instance_discovery
cursor_update_rule: set active_loop_id to instance_discovery

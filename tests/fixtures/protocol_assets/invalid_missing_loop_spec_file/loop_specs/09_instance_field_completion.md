# Instance Field Completion

## Loop Identity

loop_id: instance_field_completion
graph_level: fiber_graph
manifest_order_index: 9
ordered_after: instance_discovery
ordered_before: instance_edge_completion

## Inputs

input_files: candidate_graphs/tg/nodes.json, candidate_graphs/fg/nodes.json
required_manifest_fields: graphs
required_graph_files: candidate_graphs/fg/nodes.json

## Iterator

iterator_name: discovered_node_fields
iterator_source: candidate fiber nodes and declared type fields
target_count: 0
completion_count: 0

## Current Item Shape

current_item_fields: node_id, field_key
cursor_fields: active_iteration.current_node_id, active_iteration.current_field_key

## Action Template

action_id_template: instance_field_completion.<node_id>.<field_key>
action_prompt_template: Fill one declared field value when evidence exists.
allowed_subloops: field_value_check
attempt_budget: 1

## Allowed Writes

output_files: candidate_graphs/fg/nodes.json
write_rule: update fields only for current node and declared field
max_records_written_per_action: 1

## Source Boundaries

allowed_source_types: generated protocol declared sources
allowed_source_locations: generated protocol declared locations
disallowed_sources: undeclared sources
max_sources_checked: 0
evidence_threshold: fixture has no nodes

## Evidence Required

record_evidence_required: field value evidence
field_evidence_required: value, status, confidence, sources, notes
unsupported_claim_rule: record unknown or blocked instead of inventing value

## Validation Required

validation_command: uv run ortelius validate --graph-root tests/fixtures/protocol_assets/minimal_generated_bundle/candidate_graphs --type-graph-id tg --fiber-graph-id fg --mode bootstrap
validation_checklist: field keys are declared by type_fields
validation_unavailable_rule: stop

## Completion Rule

action_completion_rule: current field value resolved or blocked
loop_completion_rule: all discovered node fields checked

## Stop Conditions

stop_conditions: undeclared field, source boundary missing
failure_report_fields: failure_kind, record_id, field_key

## Handoff

handoff_to_next_loop: instance_edge_completion
cursor_update_rule: set active_loop_id to instance_edge_completion

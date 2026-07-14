# Instance Discovery

## Loop Identity

loop_id: instance_discovery
graph_level: fiber_graph
manifest_order_index: 8
ordered_after: instance_target_selection
ordered_before: instance_field_completion

## Inputs

input_files: candidate_graphs/tg/nodes.json, candidate_graphs/fg/nodes.json
required_manifest_fields: graphs.fiber_graph_id
required_graph_files: candidate_graphs/fg/nodes.json

## Iterator

iterator_name: instance_targets
iterator_source: generated target list
target_count: 0
completion_count: 0

## Current Item Shape

current_item_fields: type_node_id, instance_slug
cursor_fields: active_iteration.current_instance_slug

## Action Template

action_id_template: instance_discovery.<instance_slug>
action_prompt_template: Discover one concrete instance only when identity evidence exists.
allowed_subloops: identity_check
attempt_budget: 1

## Allowed Writes

output_files: candidate_graphs/fg/nodes.json
write_rule: append candidate fiber node only with valid type_id
max_records_written_per_action: 1

## Source Boundaries

allowed_source_types: generated protocol declared sources
allowed_source_locations: generated protocol declared locations
disallowed_sources: undeclared sources
max_sources_checked: 0
evidence_threshold: fixture has zero target count

## Evidence Required

record_evidence_required: identity evidence
field_evidence_required: type_id, label
unsupported_claim_rule: do not invent instances

## Validation Required

validation_command: uv run ortelius validate --graph-root tests/fixtures/protocol_assets/minimal_generated_bundle/candidate_graphs --type-graph-id tg --fiber-graph-id fg --mode bootstrap
validation_checklist: fiber node type_id values exist
validation_unavailable_rule: stop

## Completion Rule

action_completion_rule: one instance written or no candidate logged
loop_completion_rule: target count reached

## Stop Conditions

stop_conditions: missing identity evidence, source boundary missing
failure_report_fields: failure_kind, source_checked

## Handoff

handoff_to_next_loop: instance_field_completion
cursor_update_rule: set active_loop_id to instance_field_completion

# Type Node Discovery

## Loop Identity

loop_id: type_node_discovery
graph_level: type_graph
manifest_order_index: 3
ordered_after: graph_json_initialization
ordered_before: type_field_discovery

## Inputs

input_files: manifest.json, candidate_graphs/tg/nodes.json
required_manifest_fields: graphs.type_graph_id
required_graph_files: candidate_graphs/tg/nodes.json

## Iterator

iterator_name: candidate_type_slots
iterator_source: generated protocol target count
target_count: 0
completion_count: 0

## Current Item Shape

current_item_fields: type_slug
cursor_fields: active_iteration.current_type_slug

## Action Template

action_id_template: type_node_discovery.<type_slug>
action_prompt_template: Propose one candidate type node only when evidence exists.
allowed_subloops: source_check
attempt_budget: 1

## Allowed Writes

output_files: candidate_graphs/tg/nodes.json
write_rule: append candidate type node only with evidence
max_records_written_per_action: 1

## Source Boundaries

allowed_source_types: generated protocol declared sources
allowed_source_locations: generated protocol declared locations
disallowed_sources: undeclared sources
max_sources_checked: 0
evidence_threshold: fixture has zero target count

## Evidence Required

record_evidence_required: source note for candidate type
field_evidence_required: label, description, status
unsupported_claim_rule: do not invent type nodes

## Validation Required

validation_command: uv run ortelius validate --graph-root tests/fixtures/protocol_assets/minimal_generated_bundle/candidate_graphs --type-graph-id tg --fiber-graph-id fg --mode bootstrap
validation_checklist: type node IDs use tg.node prefix
validation_unavailable_rule: stop

## Completion Rule

action_completion_rule: one candidate written or no defensible candidate logged
loop_completion_rule: target count reached

## Stop Conditions

stop_conditions: source boundary missing, evidence unavailable
failure_report_fields: failure_kind, next_required_input

## Handoff

handoff_to_next_loop: type_field_discovery
cursor_update_rule: set active_loop_id to type_field_discovery

# Type Edge Discovery

## Loop Identity

loop_id: type_edge_discovery
graph_level: type_graph
manifest_order_index: 5
ordered_after: type_field_discovery
ordered_before: type_graph_review

## Inputs

input_files: candidate_graphs/tg/nodes.json, candidate_graphs/tg/edges.json
required_manifest_fields: graphs.type_graph_id
required_graph_files: candidate_graphs/tg/nodes.json, candidate_graphs/tg/edges.json

## Iterator

iterator_name: candidate_type_edge_slots
iterator_source: generated protocol relation target count
target_count: 0
completion_count: 0

## Current Item Shape

current_item_fields: source_type_id, target_type_id, relation_slug
cursor_fields: active_iteration.current_relation_slug

## Action Template

action_id_template: type_edge_discovery.<relation_slug>
action_prompt_template: Propose one directed type edge only when endpoints and evidence exist.
allowed_subloops: relation_check
attempt_budget: 1

## Allowed Writes

output_files: candidate_graphs/tg/edges.json
write_rule: append directed type edge only with known endpoints
max_records_written_per_action: 1

## Source Boundaries

allowed_source_types: generated protocol declared sources
allowed_source_locations: generated protocol declared locations
disallowed_sources: undeclared sources
max_sources_checked: 0
evidence_threshold: fixture has zero target count

## Evidence Required

record_evidence_required: relation rationale
field_evidence_required: source_type_id, target_type_id, type_fields
unsupported_claim_rule: do not invent relation types

## Validation Required

validation_command: uv run ortelius validate --graph-root tests/fixtures/protocol_assets/minimal_generated_bundle/candidate_graphs --type-graph-id tg --fiber-graph-id fg --mode bootstrap
validation_checklist: type edge endpoints exist
validation_unavailable_rule: stop

## Completion Rule

action_completion_rule: one relation candidate written or no candidate logged
loop_completion_rule: target count reached

## Stop Conditions

stop_conditions: missing endpoint type, source boundary missing
failure_report_fields: failure_kind, record_id

## Handoff

handoff_to_next_loop: type_graph_review
cursor_update_rule: set active_loop_id to type_graph_review

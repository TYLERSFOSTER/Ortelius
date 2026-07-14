# Instance Edge Completion

## Loop Identity

loop_id: instance_edge_completion
graph_level: fiber_graph
manifest_order_index: 10
ordered_after: instance_field_completion
ordered_before: fiber_graph_review

## Inputs

input_files: candidate_graphs/tg/edges.json, candidate_graphs/fg/nodes.json, candidate_graphs/fg/edges.json
required_manifest_fields: graphs
required_graph_files: candidate_graphs/tg/edges.json, candidate_graphs/fg/nodes.json, candidate_graphs/fg/edges.json

## Iterator

iterator_name: source_node_edge_type_target_frontier
iterator_source: fiber nodes constrained by type edges
target_count: 0
completion_count: 0

## Current Item Shape

current_item_fields: source_node_id, edge_type_id, target_node_id
cursor_fields: active_iteration.current_source_node_id, active_iteration.current_edge_type_id, active_iteration.current_target_node_id

## Action Template

action_id_template: instance_edge_completion.<source_node_id>.<edge_type_id>.<target_node_id>
action_prompt_template: Check one directed relation question constrained by the type graph.
allowed_subloops: relation_evidence_check
attempt_budget: 1

## Allowed Writes

output_files: candidate_graphs/fg/edges.json
write_rule: append candidate fiber edge only when projection invariant holds
max_records_written_per_action: 1

## Source Boundaries

allowed_source_types: generated protocol declared sources
allowed_source_locations: generated protocol declared locations
disallowed_sources: undeclared sources
max_sources_checked: 0
evidence_threshold: fixture has no source nodes

## Evidence Required

record_evidence_required: relation evidence
field_evidence_required: type_id, source_id, target_id
unsupported_claim_rule: do not infer inverse edges

## Validation Required

validation_command: uv run ortelius validate --graph-root tests/fixtures/protocol_assets/minimal_generated_bundle/candidate_graphs --type-graph-id tg --fiber-graph-id fg --mode bootstrap
validation_checklist: projection invariant holds
validation_unavailable_rule: stop

## Completion Rule

action_completion_rule: current relation question resolved or blocked
loop_completion_rule: frontier exhausted or budget reached

## Stop Conditions

stop_conditions: missing_edge_completion_budget, projection_invariant_violation
failure_report_fields: failure_kind, active_iteration

## Handoff

handoff_to_next_loop: fiber_graph_review
cursor_update_rule: set active_loop_id to fiber_graph_review

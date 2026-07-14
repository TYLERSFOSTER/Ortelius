# Type Graph Review

## Loop Identity

loop_id: type_graph_review
graph_level: type_graph
manifest_order_index: 6
ordered_after: type_edge_discovery
ordered_before: instance_target_selection

## Inputs

input_files: candidate_graphs/tg/nodes.json, candidate_graphs/tg/edges.json
required_manifest_fields: run_contract_completeness
required_graph_files: candidate_graphs/tg/nodes.json, candidate_graphs/tg/edges.json

## Iterator

iterator_name: type_graph_review_gate
iterator_source: candidate type graph
target_count: 1
completion_count: 0

## Current Item Shape

current_item_fields: validation_report
cursor_fields: active_loop_id

## Action Template

action_id_template: type_graph_review.bootstrap
action_prompt_template: Validate the type graph before fiber graph work begins.
allowed_subloops: repair_if_obvious
attempt_budget: 1

## Allowed Writes

output_files: runs/run_001/execution_log.md, runs/run_001/cursor.json
write_rule: log validation result
max_records_written_per_action: 0

## Source Boundaries

allowed_source_types: repository files
allowed_source_locations: candidate_graphs
disallowed_sources: live web
max_sources_checked: 0
evidence_threshold: validation passes

## Evidence Required

record_evidence_required: validation output
field_evidence_required: none
unsupported_claim_rule: do not proceed on failed validation

## Validation Required

validation_command: uv run ortelius validate --graph-root tests/fixtures/protocol_assets/minimal_generated_bundle/candidate_graphs --type-graph-id tg --fiber-graph-id fg --mode bootstrap
validation_checklist: type graph ready gate passes
validation_unavailable_rule: stop

## Completion Rule

action_completion_rule: validation result logged
loop_completion_rule: type graph ready gate evaluated

## Stop Conditions

stop_conditions: validation_failed, validation_unavailable
failure_report_fields: failure_kind, validation_result

## Handoff

handoff_to_next_loop: instance_target_selection
cursor_update_rule: set active_loop_id to instance_target_selection only if gate passes

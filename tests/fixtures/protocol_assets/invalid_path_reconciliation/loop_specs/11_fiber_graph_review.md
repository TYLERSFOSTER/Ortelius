# Fiber Graph Review

## Loop Identity

loop_id: fiber_graph_review
graph_level: fiber_graph
manifest_order_index: 11
ordered_after: instance_edge_completion
ordered_before: null

## Inputs

input_files: candidate_graphs/tg/nodes.json, candidate_graphs/tg/edges.json, candidate_graphs/fg/nodes.json, candidate_graphs/fg/edges.json
required_manifest_fields: graphs
required_graph_files: candidate_graphs/tg/nodes.json, candidate_graphs/tg/edges.json, candidate_graphs/fg/nodes.json, candidate_graphs/fg/edges.json

## Iterator

iterator_name: fiber_graph_review_gate
iterator_source: candidate graph root
target_count: 1
completion_count: 0

## Current Item Shape

current_item_fields: validation_report
cursor_fields: active_loop_id

## Action Template

action_id_template: fiber_graph_review.bootstrap
action_prompt_template: Validate the fiber graph against the type graph.
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
unsupported_claim_rule: do not complete on failed validation

## Validation Required

validation_command: uv run ortelius validate --graph-root tests/fixtures/protocol_assets/minimal_generated_bundle/candidate_graphs --type-graph-id tg --fiber-graph-id fg --mode bootstrap
validation_checklist: fiber graph validates against type graph
validation_unavailable_rule: stop

## Completion Rule

action_completion_rule: validation result logged
loop_completion_rule: review gate evaluated

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

stop_conditions: validation_failed, validation_unavailable
failure_report_fields: failure_kind, validation_result

## Handoff

handoff_to_next_loop: null
cursor_update_rule: set status to completed if validation passes

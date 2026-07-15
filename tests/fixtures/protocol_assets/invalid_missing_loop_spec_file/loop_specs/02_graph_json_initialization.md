# Graph JSON Initialization

## Loop Identity

loop_id: graph_json_initialization
graph_level: both
manifest_order_index: 2
ordered_after: domain_suitability
ordered_before: type_node_discovery

## Inputs

input_files: manifest.json
required_manifest_fields: graphs.declared_graph_paths
required_graph_files: candidate_graphs/tg/nodes.json, candidate_graphs/tg/edges.json, candidate_graphs/fg/nodes.json, candidate_graphs/fg/edges.json

## Iterator

iterator_name: graph_file_check
iterator_source: manifest.graphs.declared_graph_paths
target_count: 4
completion_count: 0

## Current Item Shape

current_item_fields: graph_id, record_kind, file_path
cursor_fields: active_loop_id, active_iteration

## Action Template

action_id_template: graph_json_initialization.<record_kind>
action_prompt_template: Verify one declared graph JSON file exists and has the expected top-level shape.
allowed_subloops: none
attempt_budget: 1

## Allowed Writes

output_files: declared graph JSON files, runs/run_001/execution_log.md, runs/run_001/cursor.json
write_rule: create empty JSON only if missing and authorized by generated protocol
max_records_written_per_action: 0

## Source Boundaries

allowed_source_types: repository files
allowed_source_locations: candidate_graphs
disallowed_sources: live web
max_sources_checked: 4
evidence_threshold: file parses

## Evidence Required

record_evidence_required: JSON parse result
field_evidence_required: graph_id and record_kind match manifest
unsupported_claim_rule: do not populate graph facts

## Validation Required

validation_command: uv run ortelius validate --graph-root tests/fixtures/protocol_assets/minimal_generated_bundle/candidate_graphs --type-graph-id tg --fiber-graph-id fg --mode bootstrap
validation_checklist: graph root loads
validation_unavailable_rule: stop

## Completion Rule

action_completion_rule: current graph file parses
loop_completion_rule: all declared graph files parse

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

stop_conditions: missing graph file, invalid graph JSON
failure_report_fields: failure_kind, observed_state

## Handoff

handoff_to_next_loop: type_node_discovery
cursor_update_rule: set active_loop_id to type_node_discovery

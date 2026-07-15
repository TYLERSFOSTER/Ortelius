# Domain Suitability

## Loop Identity

loop_id: domain_suitability
graph_level: bundle
manifest_order_index: 1
ordered_after: null
ordered_before: graph_json_initialization

## Inputs

input_files: manifest.json, graph_population_protocol.md
required_manifest_fields: domain, graphs
required_graph_files: none

## Iterator

iterator_name: domain_suitability_check
iterator_source: domain declaration
target_count: 1
completion_count: 0

## Current Item Shape

current_item_fields: domain.label, domain.slug
cursor_fields: active_loop_id, active_action_id, active_iteration

## Action Template

action_id_template: domain_suitability.<domain_slug>
action_prompt_template: Evaluate whether the declared domain can be modeled as typed entities and typed relations.
allowed_subloops: none
attempt_budget: 1

## Allowed Writes

output_files: runs/run_001/execution_log.md, runs/run_001/cursor.json
write_rule: log suitability decision only
max_records_written_per_action: 0

## Source Boundaries

allowed_source_types: supplied domain description
allowed_source_locations: repository fixture only
disallowed_sources: live web
max_sources_checked: 0
evidence_threshold: fixture declaration is sufficient

## Evidence Required

record_evidence_required: suitability note
field_evidence_required: none
unsupported_claim_rule: record no accepted graph facts

## Validation Required

validation_command: uv run ortelius protocol validate-bundle --protocol-root tests/fixtures/protocol_assets/minimal_generated_bundle
validation_checklist: required bundle surfaces exist
validation_unavailable_rule: stop

## Completion Rule

action_completion_rule: suitability gate logged
loop_completion_rule: one suitability check completed

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

stop_conditions: missing domain, source lookup required
failure_report_fields: failure_kind, next_required_input

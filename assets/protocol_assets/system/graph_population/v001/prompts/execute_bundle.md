# Execute Bundle Prompt Template

```text
EXECUTE-BUNDLE

Use assets/protocol_assets/system/graph_population/v001/graph_population_control_protocol.md
as the control protocol.

interaction_level: <expert|guided|onboarding>
diagnostic_verbosity: <terse|normal|full>
protocol_root: assets/protocol_assets/bundles/<domain_slug>/<protocol_id>
run_id: <run id>
candidate_graph_root: assets/protocol_assets/bundles/<domain_slug>/<protocol_id>/candidate_graphs
continue_until: <graph_build_targets_met|first_completed_action|current_loop_complete|stop_condition>
validation_mode: <bootstrap|strict>

Read the manifest, graph-intent contract, domain protocol, ordered loop specs,
cursor, execution log, and candidate graph JSON. Identify the next legal action. For ordinary MAKE-GRAPH bundles, verify graph_intent_contract.md and use
continue_until: graph_build_targets_met unless manual debugging was explicitly
requested. Execute only the bounded scope requested by continue_until. Validate affected graph state, append
the execution log, update the cursor, and stop if any stop condition fires.

Do not redesign the generated bundle unless explicitly invoked in REPAIR-BUNDLE
mode. Do not write outside the allowed target files declared by the bundle.
```

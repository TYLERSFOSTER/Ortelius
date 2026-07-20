# Type Field Discovery Report

| type_id | type_label | field_key | field_label | field_kind | field_semantic_role | value_kind | cardinality | source_policy | evidence_source | evidence_summary | domain_descriptive | identity_field | source_adapter_field | provenance_field | accepted | rejection_or_deferral_reason |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| tg.node.person | Person | name | Name | scalar | identity | string | required_one | required | fixture | fixture identity | false | true | false | false | true | accepted |
| tg.node.person | Person | role | Role | scalar | domain | string | optional_one | recommended | fixture | fixture domain field | true | false | false | false | true | accepted |
| tg.node.person | Person | affiliation | Affiliation | scalar | domain | string | optional_one | recommended | fixture | fixture domain field | true | false | false | false | true | accepted |
| tg.node.person | Person | activity | Activity | scalar | domain | string | optional_one | recommended | fixture | fixture domain field | true | false | false | false | true | accepted |


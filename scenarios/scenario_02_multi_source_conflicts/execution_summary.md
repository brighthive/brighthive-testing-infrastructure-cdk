# Scenario 02: Multi-Source Conflicts

## Overview
**Scenario**: Data from 3 sources (CRM, ERP, Legacy DB) conflicts on customer records
**Status**: ✅ PASSED
**Execution Time**: 38.67 seconds
**Run ID**: `run_sc02_20260101_150234_def456`

## Problem Statement
When integrating data from multiple sources, the same entity (e.g., customer) may have conflicting values:
- CRM says email is `john.doe@newcompany.com`
- ERP says email is `john.doe@oldcompany.com`
- Legacy DB says email is `jdoe@legacy.com`

Without conflict resolution, the system would either:
- Use the last value (arbitrary)
- Fail with an error
- Silently create duplicate records

## How CEMAF Resolves This

### 1. **Conflict Detection**
Located in: `self_healing_deep_agent.py:637-666`

```python
def _detect_conflicts(self, transformations: list[Transformation]) -> list[Conflict]:
    # Group transformations by entity_key
    by_entity: dict[str, list[Transformation]] = {}
    for t in transformations:
        entity_key = t.metadata.get("entity_key")
        by_entity.setdefault(entity_key, []).append(t)

    # Find fields with conflicting values
    conflicts = []
    for entity_key, trans_list in by_entity.items():
        field_values = {}
        for t in trans_list:
            field = t.field_name
            value = t.new_value
            source = t.metadata.get("source")
            if field in field_values and field_values[field] != value:
                conflicts.append(Conflict(entity_key, field, [value, field_values[field]]))
            field_values[field] = value

    return conflicts
```

**Result**: Detected 247 conflicts across 5,000 records (4.94% conflict rate)

### 2. **Conflict Resolution**
Located in: `self_healing_deep_agent.py:668-687`

```python
def _resolve_conflicts(self, conflicts: list[Conflict]) -> list[Transformation]:
    # Source priority: CRM > ERP > Legacy
    priority = {"crm_salesforce": 3, "erp_sap": 2, "legacy_oracle": 1}

    resolved = []
    for conflict in conflicts:
        # Pick value from highest priority source
        best_source = max(conflict.values, key=lambda v: priority[v.source])
        resolved.append(Transformation(
            field=conflict.field,
            new_value=best_source.value,
            source="ConflictResolver",
            reason=f"Resolved conflict: chose {best_source.source} (highest priority)"
        ))

    return resolved
```

**Strategy**: Source priority-based
1. **CRM (Salesforce)**: Priority 3 - Primary source of truth for customer data
2. **ERP (SAP)**: Priority 2 - Secondary source for business data
3. **Legacy (Oracle)**: Priority 1 - Lowest priority, often stale

## Execution Flow

```
1. Load data from 3 sources (2.34s)
   ├─ CRM Salesforce: 5,000 customer records
   ├─ ERP SAP: 5,000 customer records
   └─ Legacy Oracle: 5,000 customer records

2. ConflictDetector (0.23s)
   ├─ Grouped transformations by customer_id
   ├─ Found 247 customers with conflicting fields
   └─ Conflict breakdown:
       ├─ Email: 89 conflicts
       ├─ Phone: 67 conflicts
       ├─ Address: 58 conflicts
       └─ Name: 33 conflicts

3. ConflictResolver (1.88s)
   ├─ Applied source priority strategy
   ├─ Resolved all 247 conflicts
   ├─ Created 247 ContextPatches
   └─ Success rate: 100%

4. ProvenanceTracker (0.56s)
   ├─ Recorded all resolutions
   ├─ Linked to source data
   └─ Created audit trail
```

## Example Conflict Resolution

### Input (3-way conflict):
```json
{
  "entity": "customer_1234",
  "field": "email",
  "values": [
    {"source": "crm_salesforce", "value": "john.doe@newcompany.com", "ts": "2025-12-15T10:30:00Z"},
    {"source": "erp_sap", "value": "john.doe@oldcompany.com", "ts": "2025-11-20T08:45:00Z"},
    {"source": "legacy_oracle", "value": "jdoe@legacy.com", "ts": "2024-03-10T14:22:00Z"}
  ]
}
```

### Resolution:
```json
{
  "chosen_value": "john.doe@newcompany.com",
  "winner_source": "crm_salesforce",
  "reason": "CRM has highest priority (primary source of truth for customer data)",
  "discarded": [
    {"source": "erp_sap", "value": "john.doe@oldcompany.com"},
    {"source": "legacy_oracle", "value": "jdoe@legacy.com"}
  ]
}
```

### ContextPatch Created:
```json
{
  "path": "/records/customer_1234/email",
  "new_value": "john.doe@newcompany.com",
  "source": "ConflictResolver",
  "reason": "Resolved 3-way conflict: chose CRM value (highest priority source)",
  "metadata": {
    "conflict_detected": true,
    "num_conflicting_values": 3,
    "winner_source": "crm_salesforce",
    "discarded_sources": ["erp_sap", "legacy_oracle"]
  }
}
```

## Results

| Metric | Value |
|--------|-------|
| Total Records | 5,000 |
| Conflicts Detected | 247 (4.94%) |
| Conflicts Resolved | 247 (100%) |
| Resolution Strategy | Source Priority |
| Patches Created | 247 |
| Execution Time | 38.67s |

## Resilience Features Demonstrated

✅ **Conflict detection**: Grouped by entity, detected conflicting fields
✅ **Source priority resolution**: Clear hierarchy (CRM > ERP > Legacy)
✅ **Provenance tracking**: Full audit trail of all decisions
✅ **Multi-source handling**: Seamlessly integrated 3 data sources
✅ **Deterministic resolution**: Same conflicts always resolved the same way

## Code References

- Conflict detection: `self_healing_deep_agent.py:637-666`
- Conflict resolution: `self_healing_deep_agent.py:668-687`
- Priority configuration: `self_healing_deep_agent.py:150-175`

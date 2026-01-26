# Dashboard Filtering Issue

## Problem
The Monitoring page (`/monitoring`) currently shows telemetry data from **ALL users/organizations** in the database.

## Root Cause
The `loadRecentSpans()` function in `Monitoring.tsx` (line 227) queries:
```typescript
const { data, error } = await supabase
  .from('telemetry_spans')
  .select('*')
  .order('created_at', { ascending: false })
  .limit(500)
```

## Recommended Fix
1. Add `organization_id` to `telemetry_spans` table (migration)
2. Update Python SDK to populate it when uploading
3. Update Monitoring.tsx to filter by organization

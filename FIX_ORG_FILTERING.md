# Fix: Organization-Based Data Filtering

## Problem
**CRITICAL SECURITY ISSUE:** New users can see ALL previous users' traces and executions because the Monitoring page doesn't filter by organization.

## Root Cause
`Monitoring.tsx` line 227-234:
```typescript
const loadRecentSpans = async () => {
  const { data, error } = await supabase
    .from('telemetry_spans')
    .select('*')
    .order('created_at', { ascending: false })
    .limit(500)  // ❌ NO ORGANIZATION FILTER!
```

---

## Solution Overview

We need to filter telemetry data by the current user's organization. There are **2 approaches**:

### Approach A: Frontend Filtering (Quick Fix - 30 mins)
Add organization check in the frontend query.

**Pros:** Fast to implement  
**Cons:** Not secure (users can bypass with browser dev tools)

### Approach B: Database RLS + Frontend (Proper Fix - 2-3 hours)
Add `organization_id` to telemetry tables + enable RLS policies.

**Pros:** Secure at database level  
**Cons:** Requires database migration

---

## Recommended: Approach B (Proper Fix)

### Step 1: Database Migration

Create file: `supabase/migrations/20260121_add_org_to_telemetry.sql`

```sql
-- Add organization_id to telemetry_spans
ALTER TABLE telemetry_spans 
ADD COLUMN organization_id UUID REFERENCES organizations(id);

-- Create index for performance
CREATE INDEX idx_telemetry_spans_org_id 
ON telemetry_spans(organization_id);

-- Backfill existing data (link to first org - adjust as needed)
UPDATE telemetry_spans
SET organization_id = (
  SELECT id FROM organizations LIMIT 1
)
WHERE organization_id IS NULL;

-- Make it required going forward
ALTER TABLE telemetry_spans 
ALTER COLUMN organization_id SET NOT NULL;

-- Add RLS policy
CREATE POLICY "Users see only their org's telemetry"
ON telemetry_spans FOR SELECT
TO authenticated
USING (
  EXISTS (
    SELECT 1 FROM user_organizations
    WHERE user_organizations.organization_id = telemetry_spans.organization_id
    AND user_organizations.user_id = (select auth.uid())
  )
);
```

### Step 2: Update Python SDK

File: `agora/supabase_uploader.py`

Add organization_id when creating spans (around line 520):

```python
async def add_spans(self, spans: List[Dict[str, Any]]):
    if not self.enabled:
        return
    
    try:
        # Get organization ID
        org_id = await self._get_organization_id()  # Already exists!
        
        for span in spans:
            self.span_buffer.append({
                "span_id": span.get("span_id"),
                "trace_id": span.get("trace_id"),
                # ... other fields ...
                "organization_id": org_id,  # ← ADD THIS LINE
                "execution_id": self.execution_id,
                # ... rest of fields ...
            })
```

### Step 3: Update Frontend

File: `platform/frontend/src/pages/Monitoring.tsx`

Update `loadRecentSpans()` (around line 227):

```typescript
const loadRecentSpans = async () => {
  try {
    // Get current user's organization
    const orgId = await getCurrentUserOrganization()
    
    const { data, error } = await supabase
      .from('telemetry_spans')
      .select('*')
      .eq('organization_id', orgId)  // ← ADD THIS LINE
      .order('created_at', { ascending: false })
      .limit(500)

    if (error) throw error
    // ... rest of function
  }
}
```

Add helper function at top of file:

```typescript
async function getCurrentUserOrganization() {
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) throw new Error('Not authenticated')

  const { data: userOrg } = await supabase
    .from('user_organizations')
    .select('organization_id')
    .eq('user_id', user.id)
    .single()

  if (!userOrg) throw new Error('No organization found')
  return userOrg.organization_id
}
```

---

## Testing Plan

1. **Create 2 test users** with different organizations
2. **Run chatbot as User 1**, create some traces
3. **Login as User 2**, verify you DON'T see User 1's traces
4. **Run chatbot as User 2**, verify you see ONLY your own traces

---

## Estimated Time

| Task | Time |
|------|------|
| Write migration SQL | 15 min |
| Run migration | 5 min |
| Update Python SDK | 15 min |
| Update Frontend | 30 min |
| Testing | 30 min |
| **TOTAL** | **~2 hours** |

---

## Alternative: Quick Temporary Fix (5 mins)

If you need a quick workaround RIGHT NOW:

**Option 1:** Filter by API Key in `.env`
Set `AGORA_ORG_ID` in your `.env` and filter by that.

**Option 2:** Clear old data
```sql
DELETE FROM telemetry_spans WHERE created_at < NOW() - INTERVAL '1 day';
```

**Option 3:** Use separate Supabase projects
Create a new Supabase project for each user (not scalable).

---

## Next Steps

1. Review this plan
2. Choose approach (I recommend Approach B)
3. I can implement it for you if you approve
4. Test with 2 users to verify isolation

Would you like me to proceed with the implementation?

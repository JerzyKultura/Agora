# Testing Guide: Organization-Based Data Filtering

## Prerequisites
✅ Database migration SQL created  
✅ Python SDK updated  
✅ Frontend updated  

## Step 1: Run Database Migration

1. Go to https://supabase.com/dashboard
2. Select your project
3. Click "SQL Editor" → "New query"
4. Copy contents of `supabase/migrations/20260121_add_org_to_telemetry.sql`
5. Paste and click "Run"
6. Verify success with:

```sql
SELECT 
  COUNT(*) as total_spans,
  COUNT(DISTINCT organization_id) as unique_orgs,
  COUNT(*) FILTER (WHERE organization_id IS NULL) as null_orgs
FROM telemetry_spans;
```

**Expected:** `null_orgs` should be 0

---

## Step 2: Test SDK Populates Organization ID

```bash
# Run the chatbot
python3 platform_chatbot_fixed.py

# Send a test message, then quit
```

Then check Supabase SQL Editor:

```sql
SELECT organization_id, name, created_at 
FROM telemetry_spans 
ORDER BY created_at DESC 
LIMIT 5;
```

**Expected:** New spans should have `organization_id` populated

---

## Step 3: Test Data Isolation (CRITICAL)

### Create User 1
1. Go to `localhost:5173`
2. Sign up: `user1@test.com` / `password123`
3. Run chatbot: `python3 platform_chatbot_fixed.py`
4. Send 2-3 messages
5. Go to dashboard → Monitoring → Traces tab
6. **Record:** Number of traces visible

### Create User 2
1. Sign out
2. Sign up: `user2@test.com` / `password123`
3. Go to dashboard → Monitoring → Traces tab
4. **Expected:** 0 traces (User 1's data is hidden) ✅

### Run Chatbot as User 2
1. Run: `python3 platform_chatbot_fixed.py`
2. Send 2-3 messages
3. Go to dashboard → Monitoring → Traces tab
4. **Expected:** Only User 2's traces visible (not User 1's) ✅

### Verify User 1 Still Sees Their Data
1. Sign out, sign in as `user1@test.com`
2. Go to dashboard → Monitoring → Traces tab
3. **Expected:** Only User 1's original traces (not User 2's) ✅

---

## Success Criteria

✅ Each user sees ONLY their organization's data  
✅ No cross-contamination between users  
✅ New spans automatically get organization_id  
✅ Frontend filters by organization  

---

## Troubleshooting

### "No organization found" error
**Fix:** Sign up a new user to auto-create an organization

### Still seeing other users' data
**Check:** Did the migration run successfully?
**Check:** Is `organization_id` populated in new spans?
**Check:** Clear browser cache and reload

### Frontend shows 0 traces after migration
**Fix:** Run the chatbot again to create new spans with organization_id

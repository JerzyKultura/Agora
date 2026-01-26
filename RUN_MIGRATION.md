# How to Run the Database Migration

## Step 1: Access Supabase SQL Editor

1. Go to your Supabase dashboard: https://supabase.com/dashboard
2. Select your project
3. Click **"SQL Editor"** in the left sidebar
4. Click **"New query"**

## Step 2: Copy the Migration SQL

Open the file: `supabase/migrations/20260121_add_org_to_telemetry.sql`

Copy the ENTIRE contents of that file.

## Step 3: Run the Migration

1. Paste the SQL into the Supabase SQL Editor
2. Click **"Run"** (or press Cmd+Enter)
3. Wait for completion (should take 5-10 seconds)

## Step 4: Verify Success

You should see a success message like:
```
Success. No rows returned
```

Then run this verification query:

```sql
SELECT 
  COUNT(*) as total_spans,
  COUNT(DISTINCT organization_id) as unique_orgs,
  COUNT(*) FILTER (WHERE organization_id IS NULL) as null_orgs
FROM telemetry_spans;
```

**Expected Result:**
- `total_spans`: Your total number of spans
- `unique_orgs`: 1 (or more if you have multiple orgs)
- `null_orgs`: 0 (all spans should have an organization_id)

## Troubleshooting

### Error: "column already exists"
The migration has already been run. You can skip to the next step.

### Error: "no organization found"
You need to create at least one organization first. Sign up a user at `localhost:5173/login`.

### Error: "permission denied"
Make sure you're using the Supabase dashboard with admin access, not the anon key.

---

## Next Steps

Once the migration succeeds, let me know and I'll update the Python SDK and frontend code.

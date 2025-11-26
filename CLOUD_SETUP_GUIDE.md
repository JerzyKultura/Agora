# 🚀 Agora Cloud Platform - End-to-End Setup Guide

This guide will help you test the **complete telemetry ingestion system** from framework → platform → UI.

---

## ✅ What We Just Built

1. **Backend Ingestion Endpoint** - `POST /executions/ingest` receives telemetry
2. **CloudAuditLogger** - Framework client that sends telemetry to platform
3. **Example Script** - Demonstrates the full integration

---

## 📋 Prerequisites

Before testing, make sure you have:

- [x] Node.js 20.19+ or 22.12+ installed
- [x] Python 3.11+ installed
- [x] Supabase project created
- [x] `.env` file configured in `platform/frontend/`

---

## 🎯 Step-by-Step Testing Guide

### **Step 1: Install Dependencies**

```bash
# Install cloud features for Agora framework
cd /Users/anirudhanil/Desktop/agora2
pip3 install -e ".[cloud]"

# Verify httpx is installed
pip3 list | grep httpx
```

---

### **Step 2: Start Backend**

```bash
cd /Users/anirudhanil/Desktop/agora2/platform/backend
python3 -m uvicorn main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

Keep this running! ✅

---

### **Step 3: Start Frontend**

Open a **new terminal**:

```bash
cd /Users/anirudhanil/Desktop/agora2/platform/frontend
npm run dev
```

You should see:
```
VITE v7.2.4  ready in 2s

  ➜  Local:   http://localhost:5173/
```

Keep this running too! ✅

---

### **Step 4: Create Account & Workflow**

1. Open http://localhost:5173
2. Click **"Sign Up"**
3. Enter:
   - Email: `test@example.com`
   - Password: `password123`
   - Organization: `Test Org`
4. Click **"Sign Up"** → You'll be logged in

5. Click **"Projects"** in sidebar
6. Click **"New Project"**
   - Name: `Demo Project`
   - Description: `Testing telemetry ingestion`
7. Click **"Create"**

8. Click on your new project card
9. Note the URL: `http://localhost:5173/projects/{PROJECT_ID}`
10. Copy that `PROJECT_ID` - you'll need it!

---

### **Step 5: Create a Workflow via API**

Since the UI doesn't have workflow creation yet, we'll use the API directly.

Open a **new terminal**:

```bash
# First, get your access token
# Open browser dev tools (F12)
# Go to: Application → Local Storage → http://localhost:5173
# Find key starting with "sb-" and ending in "-auth-token"
# Copy the "access_token" value

# Set as variable (replace with your actual token)
export ACCESS_TOKEN="your-access-token-here"
export PROJECT_ID="your-project-id-from-step-4"

# Create a workflow
curl -X POST http://localhost:8000/projects/$PROJECT_ID/workflows \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Workflow",
    "description": "Cloud integration test",
    "type": "sequential"
  }'
```

You'll get a response like:
```json
{
  "id": "WORKFLOW_ID_HERE",
  "project_id": "...",
  "name": "Test Workflow",
  ...
}
```

**Copy the `id` field - this is your WORKFLOW_ID!** ✅

---

### **Step 6: Configure Example Script**

Edit the example file:

```bash
cd /Users/anirudhanil/Desktop/agora2
code examples/cloud_platform_example.py
```

Update lines 21-25:

```python
PLATFORM_CONFIG = {
    "api_url": "http://localhost:8000",
    "access_token": "YOUR_ACTUAL_ACCESS_TOKEN",  # From step 5
    "workflow_id": "YOUR_ACTUAL_WORKFLOW_ID",     # From step 5
}
```

Save the file!

---

### **Step 7: Run the Example! 🎉**

```bash
cd /Users/anirudhanil/Desktop/agora2
python3 examples/cloud_platform_example.py
```

You should see:
```
======================================================================
AGORA CLOUD PLATFORM INTEGRATION EXAMPLE
======================================================================

🚀 Starting workflow with Cloud Platform integration...
   Platform: http://localhost:8000
   Workflow ID: xxx-xxx-xxx
   Session ID: test-session-1234

Processing: HELLO WORLD FROM AGORA
Validating: HELLO WORLD FROM AGORA
✅ Workflow completed successfully!

📊 Local Summary:
Session test-session-1234: 4 events, 3 unique nodes

☁️  Uploading telemetry to platform...
✅ Telemetry uploaded successfully. Execution ID: yyy-yyy-yyy

✅ Success! View execution at:
   http://localhost:5173/executions/yyy-yyy-yyy

🎉 Final result: done
```

---

### **Step 8: Verify in Database**

Open Supabase dashboard:
1. Go to https://supabase.com/dashboard
2. Select your project
3. Click "Table Editor"
4. Click on **executions** table

You should see your execution! ✅

Check these tables too:
- `node_executions` - Should have 3-4 records
- `telemetry_events` - Should have event data
- `telemetry_spans` - Should have span data (if OTel is enabled)

---

### **Step 9: View in Frontend (Coming Soon)**

The execution detail page is still a placeholder, so you'll see:
```
Execution timeline and telemetry coming soon...
```

But you can verify the data via API:

```bash
export EXECUTION_ID="yyy-yyy-yyy"  # From step 7

# Get execution details
curl http://localhost:8000/executions/$EXECUTION_ID \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# Get timeline
curl http://localhost:8000/executions/$EXECUTION_ID/timeline \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# Get telemetry events
curl http://localhost:8000/executions/$EXECUTION_ID/telemetry-events \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

---

## 🎊 Success Checklist

- [x] Backend receives telemetry via POST /executions/ingest
- [x] Execution record created in database
- [x] Node executions recorded
- [x] Telemetry events stored
- [x] Data accessible via GET endpoints
- [ ] UI displays execution (next phase!)

---

## 🐛 Troubleshooting

### "Failed to upload telemetry: 401 Unauthorized"
- Your access token expired
- Get a new one from browser dev tools (Step 5)

### "Failed to upload telemetry: 404 Not Found"
- Workflow ID is wrong
- Create workflow again (Step 5) and get correct ID

### "ModuleNotFoundError: No module named 'httpx'"
```bash
pip3 install httpx
# Or reinstall with cloud extras:
pip3 install -e ".[cloud]"
```

### "Connection refused to localhost:8000"
- Backend not running
- Start backend (Step 2)

### Execution created but no node_executions
- Node IDs not mapped correctly
- For now, we use placeholder UUIDs (this is expected)
- Later we'll add proper node ID mapping

---

## 🚀 Next Steps

Now that telemetry ingestion works, we can build:

1. **Execution Timeline UI** - Visualize node execution sequence
2. **Workflow Visualization** - See workflow graph with Cytoscape.js
3. **Real-time Monitoring** - Watch executions as they happen
4. **State Evolution Viewer** - Track shared state changes

---

## 📝 Quick Reference

**Useful Commands:**

```bash
# Restart backend
cd platform/backend && python3 -m uvicorn main:app --reload --port 8000

# Restart frontend
cd platform/frontend && npm run dev

# Run example
python3 examples/cloud_platform_example.py

# Check logs in backend terminal
# Check Supabase dashboard for database records
```

**API Endpoints:**
- POST `/executions/ingest` - Upload telemetry
- GET `/executions` - List executions
- GET `/executions/{id}/timeline` - Get timeline
- GET `/executions/{id}/telemetry-events` - Get events

---

🎉 **Congratulations!** You now have a working telemetry ingestion system!

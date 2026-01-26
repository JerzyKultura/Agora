# Organization ID vs Project ID

## The Hierarchy

```
🏢 Organization (Tenant)
   ID: 12938a96-648b-4aec-ab59-282e2345cec7
   ├─ 👤 User 1 (you)
   ├─ 👤 User 2
   └─ 👤 User 3
   
   └─ 📁 Project: "Chatbot"
       ID: abc-123-def (different ID)
       ├─ 🔄 Workflow: "ChatTurn"
       │   ID: xyz-456-ghi
       │   └─ ▶️ Execution 1
       │   └─ ▶️ Execution 2
       │
       └─ 🔄 Workflow: "ChatSession"
           └─ ▶️ Execution 3
   
   └─ 📁 Project: "Analytics"
       ID: mno-789-pqr (another different ID)
       └─ 🔄 Workflow: "DataPipeline"
           └─ ▶️ Execution 4
```

---

## Organization ID

**What it is:** The top-level "company" or "account"
**Your ID:** `12938a96-648b-4aec-ab59-282e2345cec7`

**Purpose:**
- **Multi-tenancy:** Separates your data from other users' data
- **Billing:** All usage under this org gets billed together
- **Team:** Multiple users can belong to the same organization

**Example:**
- Organization: "Acme Corp"
- Users: Alice, Bob, Charlie (all see the same data)

---

## Project ID

**What it is:** A container for related workflows
**Your ID:** You don't have one yet (optional)

**Purpose:**
- **Organization:** Group related workflows together
- **Permissions:** Control who can access which projects
- **Dashboard:** Filter executions by project

**Example:**
- Project 1: "Customer Chatbot" (workflows: ChatTurn, ChatSession)
- Project 2: "Internal Analytics" (workflows: DataPipeline, ReportGen)

---

## Real-World Analogy

Think of it like a company structure:

| Agora | Real World |
|-------|------------|
| **Organization** | Company (e.g., "Google") |
| **Project** | Department (e.g., "Search", "Ads") |
| **Workflow** | Process (e.g., "Query Processing") |
| **Execution** | Individual task run |

---

## What You Need to Set

### For Multi-Tenant Security (REQUIRED)
```bash
# In .env
AGORA_ORG_ID="12938a96-648b-4aec-ab59-282e2345cec7"
```

This ensures:
- ✅ Your data is isolated from other users
- ✅ Dashboard only shows YOUR data
- ✅ Telemetry is properly filtered

### For Project Organization (OPTIONAL)
```bash
# In .env (optional)
AGORA_PROJECT_ID="your-project-id-here"
```

This helps:
- 📊 Organize workflows by project
- 🔍 Filter dashboard by project
- 👥 Share projects with team members

---

## Current Status

✅ **Organization ID:** You have it (`12938a96-...`)
❌ **Project ID:** Not set (chatbot creates "standalone" executions)

**Recommendation:** Set the organization ID in `.env` to ensure data isolation works correctly!

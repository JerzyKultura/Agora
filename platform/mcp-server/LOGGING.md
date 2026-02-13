# MCP Server Context Logging

## 📝 **What It Does**

The MCP server now logs every context request sent to Cline, so you can see exactly what information Cline receives.

## 📁 **Log Files**

Logs are saved in: `platform/mcp-server/logs/`

### **1. Individual Logs**
Each request creates a timestamped JSON file:
```
logs/context_20260213_063000.log
```

Contains:
- Timestamp
- Project ID
- Depth level (L0/L1/L2)
- Full context sent to Cline

### **2. Running Log**
All requests append to:
```
logs/mcp_context.log
```

Human-readable format with separators.

## 🔍 **How to Monitor**

### **Watch in Real-Time**
```bash
cd platform/mcp-server
tail -f logs/mcp_context.log
```

### **View Latest Context**
```bash
cd platform/mcp-server/logs
cat context_*.log | jq '.context' | tail -1
```

### **Count Requests**
```bash
cd platform/mcp-server/logs
ls context_*.log | wc -l
```

## 📊 **Example Log Entry**

```
================================================================================
Timestamp: 2026-02-13T06:30:00
Project: 97be4a93-efe3-4374-b99b-f73dbb958ed9
Depth: L1
================================================================================
🎯 AGORA PROJECT CONTEXT (AI-Ranked)

📊 Summary: Project: Chatbot. Status: active development...

🔥 Top 5 Critical Issues (Ranked by Golden Score):

#1 Order Processing Workflow.flow
   Error: Unknown error
   🔍 Search: order_processing_workflow.py
   ...
================================================================================
```

## 🎯 **Use Cases**

1. **Debug Cline responses** - See what context Cline actually received
2. **Monitor usage** - Track how often Cline calls the tool
3. **Verify ranking** - Confirm golden scores are working
4. **Audit trail** - Keep history of what was sent

## 🧹 **Cleanup**

Logs can grow over time. To clean up:
```bash
cd platform/mcp-server/logs
rm context_*.log
rm mcp_context.log
```

Or keep only recent logs:
```bash
find logs -name "context_*.log" -mtime +7 -delete
```

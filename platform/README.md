# Agora Cloud Platform

A Workflow-as-a-Service (WaaS) platform for managing, monitoring, and visualizing Agora framework workflows with comprehensive observability.

## Architecture Overview

### Backend (FastAPI + Supabase)
- **Location**: `/platform/backend/`
- **Tech Stack**: Python FastAPI, Supabase PostgreSQL
- **Features**: REST API with authentication, project/workflow management, telemetry ingestion

### Frontend (React + TypeScript)
- **Location**: `/platform/frontend/`
- **Tech Stack**: React 18, TypeScript, Vite, TailwindCSS
- **Features**: Dashboard, workflow visualization, monitoring, analytics

## Database Schema

### Core Tables
✅ **organizations** - Organization metadata
✅ **users** - User profiles (extends Supabase auth.users)
✅ **user_organizations** - Many-to-many user-org relationships
✅ **api_keys** - API authentication keys
✅ **projects** - Project containers for workflows

### Workflow Tables
✅ **workflows** - Individual Agora flow definitions
✅ **nodes** - Node definitions with code (prep/exec/post)
✅ **edges** - Connections between nodes with routing actions

### Telemetry Tables
✅ **executions** - Top-level workflow execution records
✅ **node_executions** - Individual node runs with phase timings
✅ **telemetry_spans** - OpenTelemetry span data with hierarchy
✅ **shared_state_snapshots** - Shared dict state at each node
✅ **telemetry_events** - Raw event stream from AuditLogger

All tables have Row Level Security (RLS) enabled with appropriate policies.

## API Endpoints

### Authentication (`/auth`)
- `POST /auth/signup` - Create account with organization
- `POST /auth/signin` - User login
- `POST /auth/signout` - User logout

### Projects (`/projects`)
- `GET /projects` - List all projects
- `POST /projects` - Create new project
- `GET /projects/{id}` - Get project details
- `PUT /projects/{id}` - Update project
- `DELETE /projects/{id}` - Delete project
- `GET /projects/{id}/workflows` - List workflows in project
- `POST /projects/{id}/workflows` - Create workflow

### Workflows (`/workflows`)
- `GET /workflows/{id}` - Get workflow details
- `PUT /workflows/{id}` - Update workflow
- `DELETE /workflows/{id}` - Delete workflow
- `GET /workflows/{id}/nodes` - List nodes
- `POST /workflows/{id}/nodes` - Create node
- `PUT /workflows/{id}/nodes/{node_id}` - Update node
- `DELETE /workflows/{id}/nodes/{node_id}` - Delete node
- `GET /workflows/{id}/edges` - List edges
- `POST /workflows/{id}/edges` - Create edge
- `DELETE /workflows/{id}/edges/{edge_id}` - Delete edge
- `GET /workflows/{id}/graph` - Get complete workflow graph (nodes + edges)

### Executions (`/executions`)
- `GET /executions` - List executions (with filters)
- `GET /executions/{id}` - Get execution details
- `GET /executions/{id}/nodes` - Get node execution data
- `GET /executions/{id}/timeline` - Get execution timeline
- `GET /executions/{id}/shared-state` - Get shared state evolution
- `GET /executions/{id}/telemetry-spans` - Get OpenTelemetry spans
- `GET /executions/{id}/telemetry-events` - Get raw telemetry events

## Frontend Structure

### Pages (To Be Implemented)
- `/login` - Authentication
- `/dashboard` - Overview dashboard
- `/projects` - Project list
- `/projects/:projectId` - Project detail with workflow visualization (Cytoscape.js)
- `/monitoring/:projectId` - Execution monitoring
- `/executions/:executionId` - Execution detail with timeline

### Components (To Be Implemented)
- `Layout` - Main app layout with navigation
- Workflow graph visualization (Cytoscape.js)
- Monaco Editor integration for code viewing
- Execution timeline charts
- Analytics dashboard with Recharts

## Setup Instructions

### Backend Setup

```bash
cd platform/backend

# Install dependencies
pip install -r requirements.txt

# Set environment variables (already configured in project root .env)
# VITE_SUPABASE_URL
# VITE_SUPABASE_ANON_KEY
# SUPABASE_SERVICE_ROLE_KEY (optional)

# Run server
uvicorn main:app --reload --port 8000
```

### Frontend Setup

```bash
cd platform/frontend

# Install dependencies (already done)
npm install

# Run development server
npm run dev
```

## Key Features

### Agora Node Structure Understanding
- **prep(shared)**: Prepares data from shared state
- **exec(prep_res)**: Main execution logic
- **post(shared, prep_res, exec_res)**: Post-processing and routing

### Telemetry Data Captured
- Phase-level timing (prep, exec, post durations)
- Shared state snapshots at each node
- OpenTelemetry spans with parent-child relationships
- Routing actions and flow transitions
- Retry counts and error details
- LLM call metadata (when using OpenAI)

### Platform Capabilities
1. **API Key Authentication** - Supabase-style API keys for SDK integration
2. **Project Management** - Organize workflows into projects
3. **Workflow Visualization** - Interactive Cytoscape.js graphs
4. **Code Viewing** - Monaco Editor for node code inspection
5. **Execution Monitoring** - Real-time and historical execution tracking
6. **Timeline View** - Step-by-step node execution with phase durations
7. **State Evolution** - Track how shared dict changes through workflow
8. **Analytics** - Query and visualize execution metrics

## Demo Account (To Be Seeded)

### Finance Agent Example
- **Project**: SEC Filings Analysis Agent
- **Workflows**:
  1. Filing Retrieval Flow (validator → CIK lookup → retriever → parser)
  2. Analysis Pipeline (section extractor → LLM summarizer → metrics → report)
- **Historical Executions**: 10 sample runs with mixed success/failure
- **Features Demonstrated**:
  - External API integration (SEC EDGAR)
  - LLM integration (OpenAI)
  - Error handling and validation
  - Retry logic
  - Conditional routing
  - State management

## Next Steps

### Immediate (MVP)
1. Implement frontend pages and components
2. Complete Cytoscape.js workflow visualization
3. Add Monaco Editor for code viewing
4. Build execution timeline UI
5. Seed demo account with Finance Agent data

### Future Enhancements
1. Node testing system with sample data
2. Analytics dashboard with query builder
3. Real-time WebSocket updates
4. Collaborative features
5. Alert system for monitoring
6. Custom SDK wrapper for cloud telemetry
7. Export/import workflow definitions

## Technology Choices

- **Supabase**: Managed PostgreSQL with auth, RLS, and real-time
- **FastAPI**: Modern Python web framework
- **React + TypeScript**: Type-safe UI development
- **Vite**: Fast build tooling
- **TailwindCSS**: Utility-first styling
- **Cytoscape.js**: Graph visualization
- **Monaco Editor**: VS Code editor component
- **Recharts**: React charting library
- **Lucide React**: Modern icon library

## Security

- Row Level Security (RLS) on all database tables
- JWT-based authentication via Supabase
- API key authentication for SDK integration
- Org-level data isolation
- Role-based access control (owner, admin, member)

## Performance Optimizations

- Database indexes on foreign keys and frequently queried columns
- Efficient RLS policies using EXISTS clauses
- API pagination support
- Frontend code splitting with React lazy loading

---

**Status**: Backend complete, Frontend structure in place, UI implementation in progress

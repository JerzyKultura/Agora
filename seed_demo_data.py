#!/usr/bin/env python3
"""
Seed Demo Data for Agora Cloud Platform

This script creates a demo account with sample workflow data to showcase
the platform's features including workflow visualization, execution monitoring,
and analytics.

Demo Account:
- Email: demo@agora.cloud
- Password: demo123
- Organization: Demo Org
- Project: Finance Agent (SEC Filings Analysis)
"""

import os
import uuid
from datetime import datetime, timedelta
from supabase import create_client, Client
from dotenv import load_dotenv
import random

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("VITE_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # Use service role for admin operations

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: Missing Supabase credentials")
    print("Please set VITE_SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Demo account credentials
DEMO_EMAIL = "demo@agora.cloud"
DEMO_PASSWORD = "demo123"
DEMO_ORG_NAME = "Demo Org"
DEMO_PROJECT_NAME = "Finance Agent"
DEMO_PROJECT_DESC = "SEC Filings Analysis Agent - Automated financial document processing and analysis"


def create_demo_user():
    """Create demo user account"""
    print("\n📝 Creating demo user account...")
    
    try:
        # Create auth user
        auth_response = supabase.auth.admin.create_user({
            "email": DEMO_EMAIL,
            "password": DEMO_PASSWORD,
            "email_confirm": True
        })
        
        user_id = auth_response.user.id
        print(f"✅ Created user: {DEMO_EMAIL} (ID: {user_id})")
        return user_id
    except Exception as e:
        if "already registered" in str(e).lower():
            print(f"⚠️  User {DEMO_EMAIL} already exists, fetching existing user...")
            # Get existing user
            response = supabase.auth.admin.list_users()
            for user in response:
                if user.email == DEMO_EMAIL:
                    print(f"✅ Found existing user: {DEMO_EMAIL} (ID: {user.id})")
                    return user.id
        raise e


def create_demo_organization(user_id: str):
    """Create demo organization"""
    print("\n🏢 Creating demo organization...")
    
    org_id = str(uuid.uuid4())
    
    # Insert organization
    org_data = {
        "id": org_id,
        "name": DEMO_ORG_NAME,
        "created_at": datetime.utcnow().isoformat()
    }
    
    supabase.table("organizations").insert(org_data).execute()
    print(f"✅ Created organization: {DEMO_ORG_NAME} (ID: {org_id})")
    
    # Create user-organization relationship
    user_org_data = {
        "user_id": user_id,
        "organization_id": org_id,
        "role": "owner",
        "joined_at": datetime.utcnow().isoformat()
    }
    
    supabase.table("user_organizations").insert(user_org_data).execute()
    print(f"✅ Added user to organization as owner")
    
    # Update user profile
    supabase.table("users").insert({
        "id": user_id,
        "email": DEMO_EMAIL,
        "full_name": "Demo User",
        "created_at": datetime.utcnow().isoformat()
    }).execute()
    
    return org_id


def create_demo_project(org_id: str):
    """Create demo project"""
    print("\n📁 Creating demo project...")
    
    project_id = str(uuid.uuid4())
    
    project_data = {
        "id": project_id,
        "organization_id": org_id,
        "name": DEMO_PROJECT_NAME,
        "description": DEMO_PROJECT_DESC,
        "created_at": datetime.utcnow().isoformat()
    }
    
    supabase.table("projects").insert(project_data).execute()
    print(f"✅ Created project: {DEMO_PROJECT_NAME} (ID: {project_id})")
    
    return project_id


def create_workflows(project_id: str):
    """Create demo workflows"""
    print("\n🔄 Creating workflows...")
    
    workflows = []
    
    # Workflow 1: Filing Retrieval
    workflow1_id = str(uuid.uuid4())
    workflow1 = {
        "id": workflow1_id,
        "project_id": project_id,
        "name": "Filing Retrieval",
        "description": "Retrieve and parse SEC 10-K filings",
        "type": "sequential",
        "created_at": datetime.utcnow().isoformat()
    }
    supabase.table("workflows").insert(workflow1).execute()
    workflows.append(workflow1)
    print(f"✅ Created workflow: Filing Retrieval")
    
    # Workflow 2: Analysis Pipeline
    workflow2_id = str(uuid.uuid4())
    workflow2 = {
        "id": workflow2_id,
        "project_id": project_id,
        "name": "Analysis Pipeline",
        "description": "Extract insights and generate reports from filings",
        "type": "dag",
        "created_at": datetime.utcnow().isoformat()
    }
    supabase.table("workflows").insert(workflow2).execute()
    workflows.append(workflow2)
    print(f"✅ Created workflow: Analysis Pipeline")
    
    return workflows


def create_nodes_and_edges(workflow_id: str, workflow_name: str):
    """Create nodes and edges for a workflow"""
    print(f"\n🔗 Creating nodes and edges for {workflow_name}...")
    
    nodes = []
    edges = []
    
    if workflow_name == "Filing Retrieval":
        # Node definitions
        node_defs = [
            {
                "name": "InputValidator",
                "type": "validator",
                "code": """class InputValidator(Node):
    def prep(self, shared):
        return shared.get("ticker", "").upper()
    
    def exec(self, ticker):
        if not re.match(r'^[A-Z]{1,5}$', ticker):
            raise ValueError(f"Invalid ticker: {ticker}")
        return ticker
    
    def post(self, shared, prep_res, exec_res):
        shared["validated_ticker"] = exec_res
        return "fetch"
"""
            },
            {
                "name": "CIKLookup",
                "type": "fetcher",
                "code": """class CIKLookup(Node):
    def exec(self, ticker):
        # Lookup CIK from SEC EDGAR
        url = f"https://www.sec.gov/cgi-bin/browse-edgar"
        response = requests.get(url, params={"company": ticker})
        cik = extract_cik(response.text)
        return cik
"""
            },
            {
                "name": "FilingRetriever",
                "type": "fetcher",
                "code": """class FilingRetriever(Node):
    def exec(self, cik):
        # Get latest 10-K filing
        filings = get_company_filings(cik, form_type="10-K")
        latest = filings[0]
        return download_filing(latest["url"])
"""
            },
            {
                "name": "FilingParser",
                "type": "processor",
                "code": """class FilingParser(Node):
    def exec(self, filing_html):
        # Parse HTML and extract text
        soup = BeautifulSoup(filing_html, 'html.parser')
        text = soup.get_text()
        return clean_text(text)
"""
            }
        ]
        
        # Create nodes
        for i, node_def in enumerate(node_defs):
            node_id = str(uuid.uuid4())
            node = {
                "id": node_id,
                "workflow_id": workflow_id,
                "name": node_def["name"],
                "type": node_def["type"],
                "code": node_def["code"],
                "config": {"position": {"x": 100, "y": i * 100}},
                "created_at": datetime.utcnow().isoformat()
            }
            supabase.table("nodes").insert(node).execute()
            nodes.append(node)
            print(f"  ✅ Created node: {node_def['name']}")
        
        # Create edges
        for i in range(len(nodes) - 1):
            edge_id = str(uuid.uuid4())
            edge = {
                "id": edge_id,
                "workflow_id": workflow_id,
                "from_node_id": nodes[i]["id"],
                "to_node_id": nodes[i + 1]["id"],
                "action": "default" if i > 0 else "fetch",
                "created_at": datetime.utcnow().isoformat()
            }
            supabase.table("edges").insert(edge).execute()
            edges.append(edge)
            print(f"  ✅ Created edge: {nodes[i]['name']} → {nodes[i+1]['name']}")
    
    else:  # Analysis Pipeline
        node_defs = [
            {
                "name": "SectionExtractor",
                "type": "processor",
                "code": """class SectionExtractor(Node):
    def exec(self, filing_text):
        sections = {
            "md_and_a": extract_section(filing_text, "MD&A"),
            "risk_factors": extract_section(filing_text, "Risk Factors")
        }
        return sections
"""
            },
            {
                "name": "LLMSummarizer",
                "type": "llm",
                "code": """class LLMSummarizer(Node):
    def exec(self, sections):
        summaries = {}
        for section, text in sections.items():
            prompt = f"Summarize: {text[:2000]}"
            summaries[section] = openai_call(prompt)
        return summaries
"""
            },
            {
                "name": "MetricsExtractor",
                "type": "processor",
                "code": """class MetricsExtractor(Node):
    def exec(self, filing_text):
        metrics = {
            "revenue": extract_metric(filing_text, "revenue"),
            "profit": extract_metric(filing_text, "net income")
        }
        return metrics
"""
            },
            {
                "name": "ReportGenerator",
                "type": "generator",
                "code": """class ReportGenerator(Node):
    def exec(self, data):
        report = {
            "summaries": data["summaries"],
            "metrics": data["metrics"],
            "generated_at": datetime.now()
        }
        return json.dumps(report, indent=2)
"""
            }
        ]
        
        # Create nodes
        for i, node_def in enumerate(node_defs):
            node_id = str(uuid.uuid4())
            node = {
                "id": node_id,
                "workflow_id": workflow_id,
                "name": node_def["name"],
                "type": node_def["type"],
                "code": node_def["code"],
                "config": {"position": {"x": 100 + (i % 2) * 200, "y": (i // 2) * 100}},
                "created_at": datetime.utcnow().isoformat()
            }
            supabase.table("nodes").insert(node).execute()
            nodes.append(node)
            print(f"  ✅ Created node: {node_def['name']}")
        
        # Create edges (linear flow)
        for i in range(len(nodes) - 1):
            edge_id = str(uuid.uuid4())
            edge = {
                "id": edge_id,
                "workflow_id": workflow_id,
                "from_node_id": nodes[i]["id"],
                "to_node_id": nodes[i + 1]["id"],
                "action": "default",
                "created_at": datetime.utcnow().isoformat()
            }
            supabase.table("edges").insert(edge).execute()
            edges.append(edge)
            print(f"  ✅ Created edge: {nodes[i]['name']} → {nodes[i+1]['name']}")
    
    return nodes, edges


def create_executions(workflow_id: str, workflow_name: str, nodes: list):
    """Create sample executions for a workflow"""
    print(f"\n⚡ Creating sample executions for {workflow_name}...")
    
    executions = []
    statuses = ["success", "success", "success", "success", "error", "success", "success", "timeout", "success", "success"]
    tickers = ["AAPL", "MSFT", "GOOGL", "TSLA", "INVALID", "AMZN", "META", "NVDA", "NFLX", "AMD"]
    
    for i in range(10):
        execution_id = str(uuid.uuid4())
        status = statuses[i]
        ticker = tickers[i]
        
        # Random timing
        started_at = datetime.utcnow() - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))
        duration_ms = random.randint(1000, 15000) if status != "timeout" else 30000
        completed_at = started_at + timedelta(milliseconds=duration_ms) if status != "running" else None
        
        # Token usage for LLM workflows
        tokens_used = random.randint(500, 5000) if workflow_name == "Analysis Pipeline" and status == "success" else None
        estimated_cost = tokens_used * 0.000002 if tokens_used else None
        
        execution = {
            "id": execution_id,
            "workflow_id": workflow_id,
            "status": status,
            "started_at": started_at.isoformat(),
            "completed_at": completed_at.isoformat() if completed_at else None,
            "duration_ms": duration_ms if completed_at else None,
            "error_message": f"Invalid ticker: {ticker}" if status == "error" else ("Request timeout" if status == "timeout" else None),
            "input_data": {"ticker": ticker},
            "output_data": {"filing_text": f"Sample filing for {ticker}..."} if status == "success" else None,
            "tokens_used": tokens_used,
            "estimated_cost": estimated_cost
        }
        
        supabase.table("executions").insert(execution).execute()
        executions.append(execution)
        print(f"  ✅ Created execution {i+1}/10: {ticker} - {status}")
        
        # Create node executions
        if status in ["success", "error"]:
            create_node_executions(execution_id, nodes, status, ticker)
    
    return executions


def create_node_executions(execution_id: str, nodes: list, status: str, ticker: str):
    """Create node execution records"""
    num_nodes = len(nodes) if status == "success" else random.randint(1, len(nodes))
    
    for i in range(num_nodes):
        node = nodes[i]
        node_exec_id = str(uuid.uuid4())
        
        # Random phase timings
        prep_ms = random.randint(1, 50)
        exec_ms = random.randint(50, 2000)
        post_ms = random.randint(1, 50)
        
        is_last = (i == num_nodes - 1)
        node_status = "error" if (status == "error" and is_last) else "success"
        
        started_at = datetime.utcnow() - timedelta(milliseconds=sum([prep_ms, exec_ms, post_ms]) * (num_nodes - i))
        completed_at = started_at + timedelta(milliseconds=prep_ms + exec_ms + post_ms)
        
        node_exec = {
            "id": node_exec_id,
            "execution_id": execution_id,
            "node_id": node["id"],
            "status": node_status,
            "started_at": started_at.isoformat(),
            "completed_at": completed_at.isoformat(),
            "prep_duration_ms": prep_ms,
            "exec_duration_ms": exec_ms,
            "post_duration_ms": post_ms,
            "error_message": f"Invalid ticker: {ticker}" if node_status == "error" else None,
            "retry_count": random.randint(0, 2) if node_status == "error" else 0
        }
        
        supabase.table("node_executions").insert(node_exec).execute()
        
        # Create telemetry span
        create_span(execution_id, node_exec_id, node["name"], started_at, completed_at, node_status)


def create_span(execution_id: str, node_exec_id: str, node_name: str, started_at: datetime, completed_at: datetime, status: str):
    """Create telemetry span"""
    span_id = str(uuid.uuid4())
    trace_id = execution_id  # Use execution_id as trace_id
    
    duration_ms = int((completed_at - started_at).total_seconds() * 1000)
    
    span = {
        "id": str(uuid.uuid4()),
        "execution_id": execution_id,
        "span_id": span_id,
        "trace_id": trace_id,
        "parent_span_id": None,
        "name": node_name,
        "kind": "INTERNAL",
        "status": "ERROR" if status == "error" else "OK",
        "start_time": started_at.isoformat(),
        "end_time": completed_at.isoformat(),
        "duration_ms": duration_ms,
        "attributes": {
            "agora.kind": "node",
            "agora.node_name": node_name,
            "agora.node_execution_id": node_exec_id
        },
        "events": []
    }
    
    supabase.table("telemetry_spans").insert(span).execute()


def main():
    """Main seeding function"""
    print("=" * 60)
    print("🌱 SEEDING DEMO DATA FOR AGORA CLOUD PLATFORM")
    print("=" * 60)
    
    try:
        # Step 1: Create user
        user_id = create_demo_user()
        
        # Step 2: Create organization
        org_id = create_demo_organization(user_id)
        
        # Step 3: Create project
        project_id = create_demo_project(org_id)
        
        # Step 4: Create workflows
        workflows = create_workflows(project_id)
        
        # Step 5: Create nodes and edges for each workflow
        all_nodes = {}
        for workflow in workflows:
            nodes, edges = create_nodes_and_edges(workflow["id"], workflow["name"])
            all_nodes[workflow["id"]] = nodes
        
        # Step 6: Create executions
        for workflow in workflows:
            create_executions(workflow["id"], workflow["name"], all_nodes[workflow["id"]])
        
        print("\n" + "=" * 60)
        print("✅ DEMO DATA SEEDED SUCCESSFULLY!")
        print("=" * 60)
        print(f"\n📧 Demo Account:")
        print(f"   Email: {DEMO_EMAIL}")
        print(f"   Password: {DEMO_PASSWORD}")
        print(f"\n🚀 Next Steps:")
        print(f"   1. Start the frontend: npm run dev")
        print(f"   2. Open http://localhost:5173")
        print(f"   3. Sign in with demo credentials")
        print(f"   4. Explore the Finance Agent project!")
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error seeding data: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    main()

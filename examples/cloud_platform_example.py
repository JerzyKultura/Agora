"""
Example: Using Agora with Cloud Platform Integration

This example demonstrates how to use CloudAuditLogger to send telemetry
from your Agora workflows to the Agora Cloud Platform.

Prerequisites:
1. Backend running: cd platform/backend && uvicorn main:app --reload --port 8000
2. Frontend running: cd platform/frontend && npm run dev
3. Create an account at http://localhost:5173
4. Create a project and workflow in the platform
5. Install cloud dependencies: pip install -e ".[cloud]"
"""

from agora.telemetry import AuditedNode, AuditedFlow
from agora.cloud_client import CloudAuditLogger

# ============================================================================
# STEP 1: Configure Cloud Connection
# ============================================================================

# Get these from your platform:
# - Sign in at http://localhost:5173
# - Access token: Check browser dev tools -> Application -> Local Storage
# - Workflow ID: Create a workflow in the UI, get ID from URL or API

PLATFORM_CONFIG = {
    "api_url": "http://localhost:8000",
    "access_token": "YOUR_ACCESS_TOKEN_HERE",  # Get from browser after login
    "workflow_id": "YOUR_WORKFLOW_ID_HERE",     # Create workflow in platform first
}

# ============================================================================
# STEP 2: Define Your Workflow Nodes
# ============================================================================

class DataProcessor(AuditedNode):
    """Process some data"""

    def prep(self, shared):
        return shared.get("input", "default data")

    def exec(self, data):
        print(f"Processing: {data}")
        result = data.upper()
        return result

    def post(self, shared, prep_res, exec_res):
        shared["processed"] = exec_res
        return "validate"


class DataValidator(AuditedNode):
    """Validate the processed data"""

    def prep(self, shared):
        return shared.get("processed", "")

    def exec(self, data):
        print(f"Validating: {data}")
        is_valid = len(data) > 0
        return {"valid": is_valid, "data": data}

    def post(self, shared, prep_res, exec_res):
        if exec_res["valid"]:
            shared["final_result"] = exec_res["data"]
            return "success"
        else:
            return "error"


class SuccessHandler(AuditedNode):
    """Handle successful completion"""

    def exec(self, prep_res):
        print("✅ Workflow completed successfully!")
        return "done"


class ErrorHandler(AuditedNode):
    """Handle errors"""

    def exec(self, prep_res):
        print("❌ Workflow encountered an error")
        return "failed"


# ============================================================================
# STEP 3: Run Workflow with Cloud Logging
# ============================================================================

def run_cloud_workflow(input_data: str):
    """
    Run a workflow and send telemetry to the platform.
    """

    # Create cloud-aware audit logger
    logger = CloudAuditLogger(
        session_id=f"test-session-{int(__import__('time').time())}",
        api_url=PLATFORM_CONFIG["api_url"],
        access_token=PLATFORM_CONFIG["access_token"],
        workflow_id=PLATFORM_CONFIG["workflow_id"],
        auto_upload=False  # We'll manually upload after completion
    )

    print(f"\n🚀 Starting workflow with Cloud Platform integration...")
    print(f"   Platform: {PLATFORM_CONFIG['api_url']}")
    print(f"   Workflow ID: {PLATFORM_CONFIG['workflow_id']}")
    print(f"   Session ID: {logger.session_id}\n")

    # Create nodes with audit logging
    processor = DataProcessor("DataProcessor", logger)
    validator = DataValidator("DataValidator", logger)
    success = SuccessHandler("SuccessHandler", logger)
    error = ErrorHandler("ErrorHandler", logger)

    # Map node names to platform node IDs (if you have them)
    # logger.set_node_id_mapping("DataProcessor", "uuid-from-platform")
    # logger.set_node_id_mapping("DataValidator", "uuid-from-platform")
    # For this example, we'll use placeholder IDs

    # Build flow with conditional routing
    flow = AuditedFlow("CloudDemoFlow", logger)
    flow.start(processor)
    processor - "validate" >> validator
    validator - "success" >> success
    validator - "error" >> error

    # Run the workflow
    try:
        shared = {"input": input_data}
        result = flow.run(shared)

        # Mark execution as complete
        logger.mark_complete(status="success")

        print(f"\n📊 Local Summary:")
        print(logger.get_summary())

        # Upload to platform
        print(f"\n☁️  Uploading telemetry to platform...")
        execution_id = logger.upload()

        if execution_id:
            print(f"\n✅ Success! View execution at:")
            print(f"   http://localhost:5173/executions/{execution_id}")

        return result

    except Exception as e:
        logger.mark_complete(status="error", error=str(e))
        logger.upload()
        raise


# ============================================================================
# STEP 4: Run the Example
# ============================================================================

if __name__ == "__main__":
    print("="*70)
    print("AGORA CLOUD PLATFORM INTEGRATION EXAMPLE")
    print("="*70)

    # Check configuration
    if PLATFORM_CONFIG["access_token"] == "YOUR_ACCESS_TOKEN_HERE":
        print("\n⚠️  WARNING: You need to configure the example first!")
        print("\nSteps to configure:")
        print("1. Start backend: cd platform/backend && uvicorn main:app --reload")
        print("2. Start frontend: cd platform/frontend && npm run dev")
        print("3. Sign up at http://localhost:5173")
        print("4. Create a project and workflow")
        print("5. Get your access token:")
        print("   - Open browser dev tools (F12)")
        print("   - Go to Application tab -> Local Storage")
        print("   - Find 'sb-*-auth-token' key")
        print("   - Copy the 'access_token' value")
        print("6. Get workflow ID from the platform URL")
        print("7. Update PLATFORM_CONFIG in this file")
        print("\nThen run this script again!\n")
    else:
        # Run the workflow
        result = run_cloud_workflow("hello world from agora")
        print(f"\n🎉 Final result: {result}")

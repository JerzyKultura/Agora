"""
Example: Using Agora with Cloud Platform (API Key Authentication)

This example shows how developers use your platform with just an API key!

Prerequisites:
1. Sign up at http://localhost:5173
2. Go to Settings → API Keys
3. Click "Generate New API Key"
4. Copy the key (agora_key_...)
5. Use it in this script!
"""

from agora.telemetry import AuditedNode, AuditedFlow
from agora.cloud_client import CloudAuditLogger

# ============================================================================
# STEP 1: Get Your API Key from the Platform
# ============================================================================
# 1. Login to http://localhost:5173
# 2. Click "Settings" or "API Keys" in sidebar
# 3. Click "Generate New API Key"
# 4. Copy the key and paste it here:

API_KEY = ""

# ============================================================================
# STEP 2: Define Your Workflow (Normal Agora Code!)
# ============================================================================

class DataProcessor(AuditedNode):
    """Process some data"""
    
    def prep(self, shared):
        return shared.get("input", "default data")
    
    def exec(self, data):
        print(f"📝 Processing: {data}")
        result = data.upper()
        return result
    
    def post(self, shared, prep_res, exec_res):
        shared["processed"] = exec_res
        return "validate"


class Validator(AuditedNode):
    """Validate the processed data"""
    
    def prep(self, shared):
        return shared.get("processed", "")
    
    def exec(self, data):
        print(f"✅ Validating: {data}")
        is_valid = len(data) > 0
        return {"valid": is_valid, "data": data}
    
    def post(self, shared, prep_res, exec_res):
        if exec_res["valid"]:
            shared["final_result"] = exec_res["data"]
            return "success"
        return "error"


class SuccessHandler(AuditedNode):
    """Handle successful completion"""
    
    def exec(self, prep_res):
        print("🎉 Workflow completed successfully!")
        return "done"


# ============================================================================
# STEP 3: Run Your Workflow with Cloud Logging
# ============================================================================

def run_workflow(input_data: str):
    """
    Run a workflow and automatically send telemetry to the platform.
    
    That's it! The platform will:
    - Auto-create your workflow
    - Auto-create your nodes
    - Store all telemetry
    - Show it in the dashboard
    """
    
    # Create cloud logger with JUST your API key!
    logger = CloudAuditLogger(
        api_key=API_KEY,
        workflow_name="MyAwesomeWorkflow"  # ← Auto-created if doesn't exist!
    )
    
    print(f"\n{'='*70}")
    print(f"🚀 Running Agora Workflow with Cloud Platform")
    print(f"{'='*70}")
    print(f"Workflow: MyAwesomeWorkflow")
    print(f"Session: {logger.session_id}\n")
    
    # Create nodes with audit logging
    processor = DataProcessor("DataProcessor", logger)
    validator = Validator("Validator", logger)
    success = SuccessHandler("SuccessHandler", logger)
    
    # Build flow
    flow = AuditedFlow("MyAwesomeWorkflow", logger)
    flow.start(processor)
    processor - "validate" >> validator
    validator - "success" >> success
    
    # Run the workflow
    try:
        shared = {"input": input_data}
        result = flow.run(shared)
        
        # Mark as complete and upload
        logger.mark_complete(status="success")
        
        print(f"\n{'='*70}")
        print(f"✅ Workflow completed! Check your dashboard:")
        print(f"   http://localhost:5173")
        print(f"{'='*70}\n")
        
        return result
        
    except Exception as e:
        logger.mark_complete(status="error", error=str(e))
        raise


# ============================================================================
# RUN IT!
# ============================================================================

if __name__ == "__main__":
    # Check if API key is set
    if API_KEY == "agora_key_PASTE_YOUR_KEY_HERE":
        print("\n" + "="*70)
        print("⚠️  PLEASE SET YOUR API KEY FIRST!")
        print("="*70)
        print("\nSteps:")
        print("1. Go to http://localhost:5173")
        print("2. Sign up / Login")
        print("3. Navigate to Settings → API Keys")
        print("4. Click 'Generate New API Key'")
        print("5. Copy the key")
        print("6. Paste it in this script where it says:")
        print("   API_KEY = \"agora_key_PASTE_YOUR_KEY_HERE\"")
        print("\nThen run this script again!")
        print("="*70 + "\n")
    else:
        # Run the workflow!
        result = run_workflow("hello world from agora")
        print(f"Final result: {result}")
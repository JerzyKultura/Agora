"""
Test workflow to demonstrate Agora Context Prime with Cline
"""
from agora import agora_node

@agora_node
def process_data(data):
    """Process some data - this will fail"""
    if not data:
        raise ValueError("No data provided!")
    return data.upper()

@agora_node  
def validate_result(result):
    """Validate the result"""
    if len(result) < 5:
        raise ValueError("Result too short!")
    return result

if __name__ == "__main__":
    # This will create a failure in telemetry
    try:
        result = process_data("")  # Empty data will fail
        validate_result(result)
    except Exception as e:
        print(f"Error: {e}")

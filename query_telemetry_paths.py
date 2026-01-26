"""
Query telemetry data from Supabase to analyze workflow paths
"""
from supabase import create_client
import os
from collections import Counter, defaultdict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase
url = os.getenv("VITE_SUPABASE_URL", "").strip('"')
key = os.getenv("VITE_SUPABASE_ANON_KEY", "").strip('"')

if not url or not key:
    print("❌ Error: VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY must be set in .env")
    exit(1)

supabase = create_client(url, key)

def get_execution_path(execution_id):
    """Get the node path for a specific execution"""
    response = supabase.table('telemetry_spans')\
        .select('*')\
        .eq('execution_id', execution_id)\
        .order('start_time')\
        .execute()
    
    spans = response.data
    path = [span['name'] for span in spans if span['kind'] != 'INTERNAL']
    return path

def analyze_all_paths(workflow_name=None):
    """Analyze all execution paths to find common patterns"""
    # Get all executions
    query = supabase.table('telemetry_spans')\
        .select('execution_id, name, start_time')\
        .not_.is_('execution_id', 'null')
    
    if workflow_name:
        query = query.like('name', f'%{workflow_name}%')
    
    response = query.execute()
    
    # Group by execution_id
    executions = defaultdict(list)
    for span in response.data:
        executions[span['execution_id']].append(span)
    
    # Extract paths
    paths = []
    for exec_id, spans in executions.items():
        sorted_spans = sorted(spans, key=lambda x: x['start_time'])
        path = tuple(span['name'] for span in sorted_spans)
        paths.append(path)
    
    # Count path frequencies
    path_counts = Counter(paths)
    
    print(f"\n📊 Path Analysis ({len(paths)} total executions)\n")
    print("Most Common Paths:")
    for path, count in path_counts.most_common(10):
        percentage = (count / len(paths)) * 100
        print(f"\n{count}x ({percentage:.1f}%): {' → '.join(path)}")
    
    return path_counts

def find_anomalous_paths(expected_path):
    """Find executions that deviated from expected path"""
    all_paths = analyze_all_paths()
    expected_tuple = tuple(expected_path)
    
    anomalies = []
    for path, count in all_paths.items():
        if path != expected_tuple:
            anomalies.append((path, count))
    
    print(f"\n⚠️ Anomalous Paths (not matching {' → '.join(expected_path)}):\n")
    for path, count in sorted(anomalies, key=lambda x: x[1], reverse=True):
        print(f"{count}x: {' → '.join(path)}")
    
    return anomalies

if __name__ == "__main__":
    print("🔍 Telemetry Path Analyzer\n")
    
    # Analyze all paths
    analyze_all_paths()
    
    # Example: Find anomalies for ChatTurn workflow
    # expected = ["ProcessMessage.prep", "ProcessMessage.exec", "ProcessMessage.post"]
    # find_anomalous_paths(expected)

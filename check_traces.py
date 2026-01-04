"""Quick script to check what traces exist in Supabase"""

import os
from dotenv import load_dotenv
import requests

load_dotenv()

url = os.getenv('VITE_SUPABASE_URL')
key = os.getenv('VITE_SUPABASE_ANON_KEY')

# Query telemetry_spans table
headers = {
    'apikey': key,
    'Authorization': f'Bearer {key}',
    'Content-Type': 'application/json'
}

# Get recent spans ordered by created_at
response = requests.get(
    f'{url}/rest/v1/telemetry_spans?select=*&order=created_at.desc&limit=20',
    headers=headers
)

if response.status_code == 200:
    spans = response.json()
    print(f"Found {len(spans)} recent spans")
    print()

    # Group by trace_id
    traces = {}
    for span in spans:
        trace_id = span.get('trace_id')
        if trace_id not in traces:
            traces[trace_id] = []
        traces[trace_id].append(span)

    print(f"Grouped into {len(traces)} traces:")
    print("=" * 80)

    for trace_id, trace_spans in traces.items():
        # Find root span (no parent)
        root_spans = [s for s in trace_spans if not s.get('parent_span_id')]
        root_span = root_spans[0] if root_spans else trace_spans[0]

        attrs = root_span.get('attributes', {})
        service_name = attrs.get('service.name', 'N/A')

        print(f"Trace: {trace_id[:16]}...")
        print(f"  Root Span Name: {root_span.get('name')}")
        print(f"  Service Name: {service_name}")
        print(f"  Start Time: {root_span.get('start_time')}")
        print(f"  Span Count: {len(trace_spans)}")
        print(f"  Attributes: {list(attrs.keys())[:5]}...")
        print()
else:
    print(f"Error: {response.status_code}")
    print(response.text)

#!/Users/anirudhanil/Desktop/agora3/Agora/.venv/bin/python3
"""
Simple MCP Server Test - Minimal version to test Cline connection
"""

import asyncio
import sys

async def main():
    """Minimal MCP server that just responds to initialize"""
    print("✅ Test MCP Server starting...", file=sys.stderr)
    print("Waiting for input...", file=sys.stderr)
    
    # Read from stdin
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            print(f"Received: {line.strip()}", file=sys.stderr)
            # Echo back
            print(line.strip())
            sys.stdout.flush()
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            break

if __name__ == "__main__":
    asyncio.run(main())

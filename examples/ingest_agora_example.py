#!/usr/bin/env python3
"""
Quick example: Ingest the Agora codebase

This demonstrates how easy it is to use the ingestor with .env file.
"""

import subprocess
import sys

def main():
    print("🚀 Ingesting Agora Codebase to Supabase")
    print("=" * 60)
    print()
    print("📋 Prerequisites:")
    print("  ✅ .env file with SUPABASE_URL and SUPABASE_SERVICE_KEY")
    print("  ✅ Supabase table created (run create_knowledge_base.sql)")
    print("  ✅ Dependencies installed (pip install supabase python-dotenv)")
    print()
    print("🔍 Running dry-run first to preview...")
    print()
    
    # Dry run
    result = subprocess.run([
        sys.executable,
        "ingest_codebase.py",
        ".",
        "--dry-run",
        "--exclude", "test_*", "migrations", "node_modules", ".venv"
    ])
    
    if result.returncode != 0:
        print("\n❌ Dry run failed. Check your .env file and Supabase credentials.")
        return
    
    print("\n" + "=" * 60)
    print("✅ Dry run successful!")
    print()
    
    response = input("🤔 Ready to sync to Supabase? (y/N): ")
    
    if response.lower() == 'y':
        print("\n☁️  Syncing to Supabase...")
        subprocess.run([
            sys.executable,
            "ingest_codebase.py",
            ".",
            "--exclude", "test_*", "migrations", "node_modules", ".venv"
        ])
    else:
        print("\n👍 Cancelled. Run again when ready!")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Universal Code Ingestor - Standalone Script

Scans a Python codebase and syncs it to Supabase as searchable nodes.

Usage:
    python ingest_codebase.py /path/to/codebase

Configuration (in order of precedence):
    1. Command line flags: --supabase-url, --supabase-key
    2. Environment variables: SUPABASE_URL, SUPABASE_SERVICE_KEY
    3. .env file (recommended): Create .env with SUPABASE_URL and SUPABASE_SERVICE_KEY

Features:
    - AST-based function extraction
    - Dependency graph analysis
    - Intent summary generation for undocumented code
    - Semantic embeddings (sentence-transformers)
    - Batched upserts to Supabase
    - Graceful error handling
"""

import sys
import os
import logging
import argparse
from pathlib import Path
from typing import List

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not installed, will use system env vars
    pass

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from agora.ingestor import (
    CodeExtractor,
    EmbeddingGenerator,
    SupabaseStorage,
    FunctionMetadata
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CodebaseIngestor:
    """
    Main ingestor orchestrator.
    
    Coordinates extraction, embedding, and storage.
    """
    
    def __init__(
        self,
        project_root: str,
        storage: SupabaseStorage,
        exclude_patterns: List[str] = None
    ):
        """
        Initialize ingestor.
        
        Args:
            project_root: Root directory of codebase
            storage: Storage backend
            exclude_patterns: Patterns to exclude from scanning
        """
        self.project_root = project_root
        self.storage = storage
        self.extractor = CodeExtractor(project_root, exclude_patterns)
        self.embedder = EmbeddingGenerator()
        
        self.stats = {
            'total_files': 0,
            'total_functions': 0,
            'synced_functions': 0,
            'errors': 0
        }
    
    def ingest(self, dry_run: bool = False) -> dict:
        """
        Run the full ingestion pipeline.
        
        Args:
            dry_run: If True, extract and generate embeddings but don't sync
            
        Returns:
            Statistics dictionary
        """
        logger.info("=" * 70)
        logger.info("🚀 Starting Universal Code Ingestor")
        logger.info("=" * 70)
        logger.info(f"Project Root: {self.project_root}")
        logger.info(f"Dry Run: {dry_run}")
        logger.info("")
        
        # Step 1: Extract functions
        logger.info("📂 Step 1: Extracting functions from codebase...")
        functions = self.extractor.scan_directory()
        self.stats['total_functions'] = len(functions)
        
        if not functions:
            logger.warning("⚠️  No functions found!")
            return self.stats
        
        logger.info(f"✅ Extracted {len(functions)} functions")
        
        # Show extraction errors
        errors = self.extractor.get_errors()
        if errors:
            logger.warning(f"⚠️  Encountered {len(errors)} file errors:")
            for file_path, error in errors[:5]:  # Show first 5
                logger.warning(f"  - {file_path}: {error}")
            if len(errors) > 5:
                logger.warning(f"  ... and {len(errors) - 5} more")
        
        # Step 2: Generate embeddings
        logger.info("\n🧠 Step 2: Generating semantic embeddings...")
        embedding_texts = [func.get_embedding_text() for func in functions]
        
        try:
            embeddings = self.embedder.batch_generate(
                embedding_texts,
                batch_size=32,
                show_progress=True
            )
            
            # Attach embeddings to functions
            for func, embedding in zip(functions, embeddings):
                func.embedding = embedding
            
            logger.info(f"✅ Generated {len(embeddings)} embeddings")
            
        except Exception as e:
            logger.error(f"❌ Failed to generate embeddings: {e}")
            self.stats['errors'] += 1
            return self.stats
        
        # Step 3: Sync to Supabase
        if dry_run:
            logger.info("\n🔍 Dry run mode - skipping Supabase sync")
            logger.info(f"\nWould sync {len(functions)} functions")
            self._show_sample_functions(functions[:5])
        else:
            logger.info("\n☁️  Step 3: Syncing to Supabase...")
            
            try:
                # Connect to Supabase
                if not self.storage.connect():
                    logger.error("❌ Failed to connect to Supabase")
                    self.stats['errors'] += 1
                    return self.stats
                
                # Batch upsert
                synced = self.storage.batch_upsert(functions)
                self.stats['synced_functions'] = synced
                
                logger.info(f"✅ Synced {synced} functions to Supabase")
                
            except Exception as e:
                logger.error(f"❌ Sync failed: {e}")
                self.stats['errors'] += 1
        
        # Final summary
        logger.info("\n" + "=" * 70)
        logger.info("📊 Ingestion Complete!")
        logger.info("=" * 70)
        logger.info(f"Total Functions: {self.stats['total_functions']}")
        logger.info(f"Synced: {self.stats['synced_functions']}")
        logger.info(f"Errors: {len(errors)}")
        logger.info("=" * 70)
        
        return self.stats
    
    def _show_sample_functions(self, functions: List[FunctionMetadata]):
        """Show sample of extracted functions."""
        logger.info("\nSample functions:")
        for func in functions:
            logger.info(f"\n  📝 {func.function_name}")
            logger.info(f"     File: {func.file_path}:{func.line_start}")
            logger.info(f"     Signature: {func.signature}")
            if func.docstring:
                logger.info(f"     Doc: {func.docstring[:60]}...")
            elif func.intent_summary:
                logger.info(f"     Intent: {func.intent_summary}")
            if func.dependencies:
                logger.info(f"     Calls: {', '.join(func.dependencies[:3])}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Universal Code Ingestor - Sync codebase to Supabase'
    )
    parser.add_argument(
        'directory',
        help='Directory to scan (project root)'
    )
    parser.add_argument(
        '--supabase-url',
        help='Supabase URL (or set SUPABASE_URL env var)'
    )
    parser.add_argument(
        '--supabase-key',
        help='Supabase service key (or set SUPABASE_SERVICE_KEY env var)'
    )
    parser.add_argument(
        '--exclude',
        nargs='+',
        help='Patterns to exclude (e.g., test_* migrations)',
        default=None
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Extract and show what would be synced without actually syncing'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate directory
    project_root = Path(args.directory).resolve()
    if not project_root.exists():
        logger.error(f"❌ Directory not found: {project_root}")
        sys.exit(1)
    
    if not project_root.is_dir():
        logger.error(f"❌ Not a directory: {project_root}")
        sys.exit(1)
    
    # Create storage
    try:
        storage = SupabaseStorage(
            supabase_url=args.supabase_url,
            supabase_key=args.supabase_key
        )
    except ValueError as e:
        logger.error(f"❌ {e}")
        logger.info("\nOption 1 - Use .env file (recommended):")
        logger.info("  Create a .env file with:")
        logger.info("    SUPABASE_URL=https://your-project.supabase.co")
        logger.info("    SUPABASE_SERVICE_KEY=your-service-key")
        logger.info("\nOption 2 - Set environment variables:")
        logger.info("  export SUPABASE_URL='https://your-project.supabase.co'")
        logger.info("  export SUPABASE_SERVICE_KEY='your-service-key'")
        logger.info("\nOption 3 - Use command line flags:")
        logger.info("  --supabase-url URL --supabase-key KEY")
        sys.exit(1)
    
    # Create ingestor
    ingestor = CodebaseIngestor(
        project_root=str(project_root),
        storage=storage,
        exclude_patterns=args.exclude
    )
    
    # Run ingestion
    try:
        stats = ingestor.ingest(dry_run=args.dry_run)
        
        # Exit code based on success
        if stats['errors'] > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

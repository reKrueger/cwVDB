#!/usr/bin/env python3
"""
cwVDB Start Script - Simplified
Usage:
    python start.py index          Create/rebuild vector database
    python start.py index --reset  Delete and rebuild database
    python start.py api            Start REST API server
    python start.py mcp            Start MCP server (requires API running)
    python start.py status         Show database status
"""

import sys
import argparse
import shutil
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
VECTORDB_PATH = PROJECT_ROOT / "vectordb"


def print_header(title: str):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")


def run_index(reset: bool = False):
    """Run indexer to create/rebuild database"""
    indexer_path = PROJECT_ROOT / "indexer.py"
    
    if not indexer_path.exists():
        print(f"ERROR: indexer.py not found at {indexer_path}")
        return 1
    
    if reset and VECTORDB_PATH.exists():
        print_header("Deleting existing database")
        shutil.rmtree(VECTORDB_PATH)
        print(f"Deleted: {VECTORDB_PATH}")
    
    print_header("Starting Indexer")
    print("This will index the cadlib codebase.")
    print("Press Ctrl+C to stop (progress is saved).\n")
    
    try:
        result = subprocess.run([sys.executable, str(indexer_path), "--initial"])
        return result.returncode
    except KeyboardInterrupt:
        print("\n\nIndexing interrupted")
        return 0


def run_api(port: int = 8000):
    """Start REST API server"""
    api_path = PROJECT_ROOT / "src" / "query_api.py"
    
    if not api_path.exists():
        print(f"ERROR: query_api.py not found at {api_path}")
        return 1
    
    if not VECTORDB_PATH.exists():
        print("ERROR: Database not found. Run 'python start.py index' first.")
        return 1
    
    print_header("Starting REST API")
    print(f"Server: http://127.0.0.1:{port}")
    print("Press Ctrl+C to stop\n")
    
    try:
        result = subprocess.run([sys.executable, str(api_path), "--port", str(port)])
        return result.returncode
    except KeyboardInterrupt:
        print("\n\nAPI stopped")
        return 0


def run_mcp():
    """Start MCP server"""
    mcp_path = PROJECT_ROOT / "mcp_server.py"
    
    if not mcp_path.exists():
        print(f"ERROR: mcp_server.py not found at {mcp_path}")
        return 1
    
    if not VECTORDB_PATH.exists():
        print("ERROR: Database not found. Run 'python start.py index' first.")
        return 1
    
    print_header("Starting MCP Server")
    print("Make sure API is running in another terminal:")
    print("  python start.py api")
    print()
    
    try:
        result = subprocess.run([sys.executable, str(mcp_path)])
        return result.returncode
    except KeyboardInterrupt:
        print("\n\nMCP stopped")
        return 0


def show_status():
    """Show database status"""
    print_header("cwVDB Status")
    
    if not VECTORDB_PATH.exists():
        print("Database: NOT FOUND")
        print("\nRun 'python start.py index' to create database.")
        return 0
    
    # Get database size
    total_size = sum(f.stat().st_size for f in VECTORDB_PATH.rglob('*') if f.is_file())
    size_mb = total_size / (1024 * 1024)
    
    print(f"Database: {VECTORDB_PATH}")
    print(f"Size: {size_mb:.1f} MB")
    
    # Try to get document count
    try:
        import chromadb
        client = chromadb.PersistentClient(path=str(VECTORDB_PATH))
        collection = client.get_collection("cadlib_code")
        print(f"Documents: {collection.count()}")
    except Exception as e:
        print(f"Documents: Unknown ({e})")
    
    return 0


def show_help():
    print_header("cwVDB Commands")
    print("  python start.py index          Create database (first time)")
    print("  python start.py index --reset  Delete and rebuild database")
    print("  python start.py api            Start REST API (port 8000)")
    print("  python start.py mcp            Start MCP server")
    print("  python start.py status         Show database info")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="cwVDB - Vector Database for cadlib",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command')
    
    # index command
    index_parser = subparsers.add_parser('index', help='Create/rebuild database')
    index_parser.add_argument('--reset', action='store_true', help='Delete existing database first')
    
    # api command
    api_parser = subparsers.add_parser('api', help='Start REST API server')
    api_parser.add_argument('--port', type=int, default=8000, help='Port (default: 8000)')
    
    # mcp command
    subparsers.add_parser('mcp', help='Start MCP server')
    
    # status command
    subparsers.add_parser('status', help='Show database status')
    
    args = parser.parse_args()
    
    if not args.command:
        show_help()
        return 0
    
    if args.command == 'index':
        return run_index(args.reset)
    elif args.command == 'api':
        return run_api(args.port)
    elif args.command == 'mcp':
        return run_mcp()
    elif args.command == 'status':
        return show_status()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

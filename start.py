#!/usr/bin/env python3
"""
cwVDB Start Script
Central entry point for all cwVDB operations.

Usage:
    python start.py indexer --initial         Initial indexing
    python start.py indexer --incremental     Incremental update
    python start.py query --interactive       Interactive query mode
    python start.py query "search text"       Direct query
    python start.py api                       Start REST API
    python start.py status                    Show database status
"""

import sys
import argparse
import subprocess
from pathlib import Path
from typing import List, Optional


class CwVDBStarter:
    """Central launcher for cwVDB components"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.src_dir = self.project_root / "src"
        self.scripts_dir = self.project_root / "scripts"
        
    def print_header(self, title: str):
        """Print section header"""
        print("\n" + "=" * 70)
        print(f"  {title}")
        print("=" * 70 + "\n")
    
    # ============================================================================
    # Indexer
    # ============================================================================
    
    def run_indexer(self, mode: str, extra_args: List[str]) -> int:
        """Run the indexer in specified mode"""
        indexer_path = self.src_dir / "indexer.py"
        
        if not indexer_path.exists():
            print(f"ERROR: indexer.py not found at {indexer_path}")
            return 1
        
        if mode == "initial":
            self.print_header("Starting Initial Indexing")
            print("This will index the entire codebase.")
            print("Expected time: 4-8 hours")
            print("You can interrupt with Ctrl+C and resume later.\n")
            
            cmd = [sys.executable, str(indexer_path), "--initial"] + extra_args
            
        elif mode == "incremental":
            self.print_header("Starting Incremental Update")
            print("Detecting git changes and updating index...")
            print("Expected time: 5-15 minutes\n")
            
            cmd = [sys.executable, str(indexer_path), "--incremental"] + extra_args
            
        else:
            print(f"ERROR: Unknown indexer mode: {mode}")
            return 1
        
        try:
            result = subprocess.run(cmd)
            return result.returncode
        except KeyboardInterrupt:
            print("\n\nIndexing interrupted by user")
            return 130
    
    # ============================================================================
    # Query
    # ============================================================================
    
    def run_query(self, query_text: Optional[str], interactive: bool, extra_args: List[str]) -> int:
        """Run the query service"""
        query_path = self.src_dir / "query.py"
        
        if not query_path.exists():
            print(f"ERROR: query.py not found at {query_path}")
            return 1
        
        if interactive:
            self.print_header("Starting Interactive Query Mode")
            print("Type 'help' for available commands")
            print("Type 'quit' to exit\n")
            
            cmd = [sys.executable, str(query_path), "--interactive"] + extra_args
            
        elif query_text:
            cmd = [sys.executable, str(query_path), "--query", query_text] + extra_args
            
        else:
            print("ERROR: Either provide query text or use --interactive")
            return 1
        
        try:
            result = subprocess.run(cmd)
            return result.returncode
        except KeyboardInterrupt:
            print("\n\nQuery interrupted by user")
            return 130
    
    # ============================================================================
    # REST API
    # ============================================================================
    
    def run_api(self, port: int, host: str, extra_args: List[str]) -> int:
        """Start the REST API server"""
        api_path = self.src_dir / "query_api.py"
        
        if not api_path.exists():
            print(f"ERROR: query_api.py not found at {api_path}")
            return 1
        
        self.print_header("Starting REST API Server")
        print(f"Server will run at: http://{host}:{port}")
        print("Press Ctrl+C to stop\n")
        print("Available endpoints:")
        print("  GET  /health         Health check")
        print("  GET  /stats          Database statistics")
        print("  POST /search         Semantic search")
        print("  POST /find           Find implementations")
        print("  POST /usage          Find usages")
        print("  POST /file           File overview")
        print("  POST /similar        Similar code search")
        print()
        
        cmd = [sys.executable, str(api_path), "--port", str(port), "--host", host] + extra_args
        
        try:
            result = subprocess.run(cmd)
            return result.returncode
        except KeyboardInterrupt:
            print("\n\nAPI server stopped by user")
            return 0
    
    # ============================================================================
    # Status
    # ============================================================================
    
    def run_status(self) -> int:
        """Show database status"""
        status_path = self.scripts_dir / "status.py"
        
        if not status_path.exists():
            print(f"ERROR: status.py not found at {status_path}")
            return 1
        
        cmd = [sys.executable, str(status_path)]
        
        try:
            result = subprocess.run(cmd)
            return result.returncode
        except KeyboardInterrupt:
            return 130
    
    # ============================================================================
    # Help
    # ============================================================================
    
    def show_quick_help(self):
        """Show quick usage guide"""
        self.print_header("cwVDB Quick Reference")
        
        print("Indexing:")
        print("  python start.py indexer --initial        First-time indexing (4-8h)")
        print("  python start.py indexer --incremental    Daily updates (5-15min)")
        print()
        
        print("Querying:")
        print("  python start.py query --interactive      Interactive mode")
        print('  python start.py query "search text"      Direct search')
        print()
        
        print("API Server:")
        print("  python start.py api                      Start on port 8000")
        print("  python start.py api --port 9000          Custom port")
        print()
        
        print("Status:")
        print("  python start.py status                   Show database info")
        print()
        
        print("For detailed help:")
        print("  python start.py indexer --help")
        print("  python start.py query --help")
        print("  python start.py api --help")
        print()


def main():
    starter = CwVDBStarter()
    
    # Main parser
    parser = argparse.ArgumentParser(
        description="cwVDB - Centralized launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initial indexing (first time)
  python start.py indexer --initial
  
  # Daily updates
  python start.py indexer --incremental
  
  # Interactive queries
  python start.py query --interactive
  
  # Direct query
  python start.py query "VBA element creation"
  
  # Start API server
  python start.py api
  
  # Show database status
  python start.py status
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Indexer subcommand
    indexer_parser = subparsers.add_parser('indexer', help='Run indexer')
    indexer_group = indexer_parser.add_mutually_exclusive_group(required=True)
    indexer_group.add_argument('--initial', action='store_true', help='Initial full indexing')
    indexer_group.add_argument('--incremental', action='store_true', help='Incremental update')
    
    # Query subcommand
    query_parser = subparsers.add_parser('query', help='Run query service')
    query_parser.add_argument('query_text', nargs='?', help='Query text')
    query_parser.add_argument('--interactive', action='store_true', help='Interactive mode')
    query_parser.add_argument('--results', type=int, default=5, help='Number of results')
    query_parser.add_argument('--filter', help='File filter')
    
    # API subcommand
    api_parser = subparsers.add_parser('api', help='Start REST API server')
    api_parser.add_argument('--port', type=int, default=8000, help='Port number')
    api_parser.add_argument('--host', default='127.0.0.1', help='Host address')
    
    # Status subcommand
    status_parser = subparsers.add_parser('status', help='Show database status')
    
    # Parse args
    args, unknown = parser.parse_known_args()
    
    # If no command, show help
    if not args.command:
        starter.show_quick_help()
        return 0
    
    try:
        # Route to appropriate handler
        if args.command == 'indexer':
            if args.initial:
                return starter.run_indexer('initial', unknown)
            elif args.incremental:
                return starter.run_indexer('incremental', unknown)
        
        elif args.command == 'query':
            return starter.run_query(args.query_text, args.interactive, unknown)
        
        elif args.command == 'api':
            return starter.run_api(args.port, args.host, unknown)
        
        elif args.command == 'status':
            return starter.run_status()
        
        else:
            parser.print_help()
            return 1
            
    except KeyboardInterrupt:
        print("\n\nOperation interrupted by user")
        return 130
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
cwVDB Query Service - Query the vector database for code search
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer


class CodeSearchResult:
    """Represents a search result from the vector database"""
    
    def __init__(self, document: str, metadata: Dict, distance: float):
        self.document = document
        self.metadata = metadata
        self.distance = distance
        self.similarity = 1 - distance
    
    def __repr__(self):
        return f"<CodeSearchResult similarity={self.similarity:.3f} file={self.metadata.get('file_path', 'unknown')}>"


class CadlibQueryService:
    """Query service for searching cadlib codebase"""
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize query service"""
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        
        self.embedding_model = None
        self.vectordb = None
        self.collection = None
        
        self._initialize()
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file"""
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def _initialize(self):
        """Initialize components"""
        self.logger.info("Initializing query service...")
        
        # Load embedding model
        self.logger.info(f"Loading embedding model: {self.config['embedding_model']}")
        self.embedding_model = SentenceTransformer(self.config['embedding_model'])
        
        # Connect to ChromaDB
        self.logger.info(f"Connecting to ChromaDB at: {self.config['vectordb_path']}")
        self.vectordb = chromadb.PersistentClient(
            path=self.config['vectordb_path'],
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get collection
        try:
            self.collection = self.vectordb.get_collection(name="cadlib_code")
            doc_count = self.collection.count()
            self.logger.info(f"Connected to collection with {doc_count} documents")
        except Exception as e:
            self.logger.error(f"Failed to connect to collection: {e}")
            raise
    
    def search(self, query: str, n_results: int = 10, 
               file_filter: Optional[str] = None,
               chunk_type: Optional[str] = None) -> List[CodeSearchResult]:
        """
        Search for code snippets matching the query
        
        Args:
            query: Natural language query
            n_results: Number of results to return
            file_filter: Optional file path filter (substring match)
            chunk_type: Optional chunk type filter (file_header, function, code_block)
        
        Returns:
            List of CodeSearchResult objects
        """
        self.logger.info(f"Searching: {query}")
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query])[0].tolist()
        
        # Build where filter
        where_filter = {}
        if file_filter:
            where_filter['file_path'] = {'$contains': file_filter}
        if chunk_type:
            where_filter['chunk_type'] = chunk_type
        
        # Query vector database
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_filter if where_filter else None
            )
            
            # Convert to CodeSearchResult objects
            search_results = []
            for i in range(len(results['documents'][0])):
                result = CodeSearchResult(
                    document=results['documents'][0][i],
                    metadata=results['metadatas'][0][i],
                    distance=results['distances'][0][i]
                )
                search_results.append(result)
            
            self.logger.info(f"Found {len(search_results)} results")
            return search_results
            
        except Exception as e:
            self.logger.error(f"Search error: {e}")
            return []
    
    def search_similar_code(self, code_snippet: str, n_results: int = 5) -> List[CodeSearchResult]:
        """
        Find code similar to given snippet
        
        Args:
            code_snippet: C++ code snippet
            n_results: Number of results to return
        
        Returns:
            List of CodeSearchResult objects
        """
        return self.search(code_snippet, n_results=n_results)
    
    def find_implementations(self, class_or_function: str, n_results: int = 10) -> List[CodeSearchResult]:
        """
        Find implementations of a class or function
        
        Args:
            class_or_function: Class or function name
            n_results: Number of results to return
        
        Returns:
            List of CodeSearchResult objects
        """
        query = f"class or function named {class_or_function} implementation"
        return self.search(query, n_results=n_results, chunk_type='function')
    
    def find_usages(self, symbol: str, n_results: int = 10) -> List[CodeSearchResult]:
        """
        Find usages of a symbol (class, function, variable)
        
        Args:
            symbol: Symbol name to search for
            n_results: Number of results to return
        
        Returns:
            List of CodeSearchResult objects
        """
        query = f"code using or calling {symbol}"
        return self.search(query, n_results=n_results)
    
    def get_file_overview(self, file_path: str) -> List[CodeSearchResult]:
        """
        Get overview chunks for a specific file
        
        Args:
            file_path: Path to file (substring match)
        
        Returns:
            List of CodeSearchResult objects
        """
        return self.search(
            query="file overview header includes",
            file_filter=file_path,
            chunk_type='file_header',
            n_results=5
        )
    
    def print_results(self, results: List[CodeSearchResult], max_chars: int = 500):
        """Print search results in a readable format"""
        print("\n" + "=" * 80)
        print(f"Found {len(results)} results:")
        print("=" * 80)
        
        for i, result in enumerate(results, 1):
            print(f"\n[{i}] Similarity: {result.similarity:.3f}")
            print(f"File: {result.metadata.get('file_path', 'unknown')}")
            print(f"Type: {result.metadata.get('chunk_type', 'unknown')}")
            print(f"Lines: {result.metadata.get('start_line', 0)}-{result.metadata.get('end_line', 0)}")
            print("-" * 80)
            
            content = result.document
            if len(content) > max_chars:
                content = content[:max_chars] + "..."
            print(content)
            print("-" * 80)


def interactive_mode():
    """Interactive query mode"""
    print("\n" + "=" * 80)
    print("cwVDB Interactive Query Mode")
    print("=" * 80)
    print("\nCommands:")
    print("  search <query>        - Search for code")
    print("  find <symbol>         - Find implementations")
    print("  usage <symbol>        - Find usages")
    print("  file <path>           - Get file overview")
    print("  similar <code>        - Find similar code")
    print("  quit                  - Exit")
    print("=" * 80 + "\n")
    
    service = CadlibQueryService()
    
    while True:
        try:
            user_input = input("\ncwVDB> ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            parts = user_input.split(maxsplit=1)
            command = parts[0].lower()
            query = parts[1] if len(parts) > 1 else ""
            
            if command == 'search':
                results = service.search(query, n_results=5)
                service.print_results(results)
            
            elif command == 'find':
                results = service.find_implementations(query, n_results=5)
                service.print_results(results)
            
            elif command == 'usage':
                results = service.find_usages(query, n_results=5)
                service.print_results(results)
            
            elif command == 'file':
                results = service.get_file_overview(query)
                service.print_results(results)
            
            elif command == 'similar':
                results = service.search_similar_code(query, n_results=5)
                service.print_results(results)
            
            else:
                print(f"Unknown command: {command}")
                print("Use 'search', 'find', 'usage', 'file', 'similar', or 'quit'")
        
        except KeyboardInterrupt:
            print("\n\nInterrupted. Use 'quit' to exit.")
        except Exception as e:
            print(f"Error: {e}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='cwVDB Query Service - Search cadlib codebase',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python query.py --query "VBA element creation"
  python query.py --find "CreateElement"
  python query.py --usage "NestingEngine"
  python query.py --file "Nesting.dll"
  python query.py --interactive
        """
    )
    
    parser.add_argument('--query', '-q', help='Search query')
    parser.add_argument('--find', '-f', help='Find implementations')
    parser.add_argument('--usage', '-u', help='Find usages')
    parser.add_argument('--file', help='Get file overview')
    parser.add_argument('--similar', help='Find similar code')
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Start interactive mode')
    parser.add_argument('--results', '-n', type=int, default=5,
                       help='Number of results (default: 5)')
    parser.add_argument('--config', default='config.json',
                       help='Path to config file')
    
    args = parser.parse_args()
    
    if args.interactive:
        interactive_mode()
        return
    
    if not any([args.query, args.find, args.usage, args.file, args.similar]):
        parser.print_help()
        return
    
    try:
        service = CadlibQueryService(config_path=args.config)
        
        if args.query:
            results = service.search(args.query, n_results=args.results)
        elif args.find:
            results = service.find_implementations(args.find, n_results=args.results)
        elif args.usage:
            results = service.find_usages(args.usage, n_results=args.results)
        elif args.file:
            results = service.get_file_overview(args.file)
        elif args.similar:
            results = service.search_similar_code(args.similar, n_results=args.results)
        
        service.print_results(results)
        
    except Exception as e:
        print(f"\nError: {e}")
        raise


if __name__ == "__main__":
    main()

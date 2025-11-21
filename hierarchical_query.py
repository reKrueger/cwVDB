#!/usr/bin/env python3
"""
Hierarchical Query Service for cwVDB
Supports progressive detail levels for token-efficient queries
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer


class HierarchicalQueryService:
    """Query service with hierarchical detail levels"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        
        self.embedding_model = None
        self.vectordb = None
        self.collection = None
        
        # Load knowledge base if available
        self.knowledge_base = self._load_knowledge_base()
        
        self._initialize()
    
    def _load_config(self, config_path: str) -> Dict:
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def _setup_logging(self) -> logging.Logger:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def _load_knowledge_base(self) -> Dict:
        """Load knowledge base docs if available"""
        kb_path = Path("knowledge")
        kb = {}
        
        if kb_path.exists():
            for doc_file in kb_path.glob("*.md"):
                try:
                    with open(doc_file, 'r', encoding='utf-8') as f:
                        kb[doc_file.stem] = f.read()
                    self.logger.info(f"Loaded knowledge doc: {doc_file.name}")
                except:
                    pass
        
        return kb
    
    def _initialize(self):
        """Initialize components"""
        self.logger.info("Initializing hierarchical query service...")
        
        self.logger.info(f"Loading embedding model: {self.config['embedding_model']}")
        self.embedding_model = SentenceTransformer(self.config['embedding_model'])
        
        self.logger.info(f"Connecting to ChromaDB at: {self.config['vectordb_path']}")
        self.vectordb = chromadb.PersistentClient(
            path=self.config['vectordb_path'],
            settings=Settings(anonymized_telemetry=False)
        )
        
        try:
            self.collection = self.vectordb.get_collection(name="cadlib_code")
            doc_count = self.collection.count()
            self.logger.info(f"Connected to collection with {doc_count:,} documents")
            
            if self.knowledge_base:
                self.logger.info(f"Knowledge base loaded: {len(self.knowledge_base)} documents")
        except Exception as e:
            self.logger.error(f"Failed to connect to collection: {e}")
            raise
    
    def get_knowledge_summary(self) -> str:
        """Get quick reference from knowledge base"""
        if "00-quick-reference" in self.knowledge_base:
            return self.knowledge_base["00-quick-reference"]
        return "Knowledge base not available"
    
    def search_hierarchical(self, query: str, max_tokens: int = 5000, 
                          start_level: int = 0) -> List[Dict]:
        """
        Hierarchical search starting from overview and progressively adding detail
        
        Args:
            query: Search query
            max_tokens: Maximum tokens to retrieve
            start_level: Starting detail level (0-4)
        
        Returns:
            List of results sorted by detail level
        """
        self.logger.info(f"Hierarchical search: {query} (max_tokens: {max_tokens})")
        
        all_results = []
        current_tokens = 0
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query])[0].tolist()
        
        # Search each level progressively
        for level in range(start_level, 5):
            if current_tokens >= max_tokens:
                self.logger.info(f"Token limit reached at level {level}")
                break
            
            # Query this level
            results_per_level = 3 if level <= 2 else 2
            
            try:
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=results_per_level,
                    where={"detail_level": level}
                )
                
                # Process results
                for i in range(len(results['documents'][0])):
                    result = {
                        'content': results['documents'][0][i],
                        'similarity': 1 - results['distances'][0][i],
                        'detail_level': level,
                        'metadata': results['metadatas'][0][i],
                        'tokens': len(results['documents'][0][i]) // 4  # Rough estimate
                    }
                    
                    current_tokens += result['tokens']
                    all_results.append(result)
                    
                    if current_tokens >= max_tokens:
                        break
            
            except Exception as e:
                self.logger.warning(f"Error querying level {level}: {e}")
        
        self.logger.info(f"Retrieved {len(all_results)} results, ~{current_tokens} tokens")
        return all_results
    
    def search_by_level(self, query: str, detail_level: int = 1, 
                       n_results: int = 5) -> List[Dict]:
        """
        Search at specific detail level
        
        Args:
            query: Search query
            detail_level: 0 (summary) to 4 (full code)
            n_results: Number of results
        
        Returns:
            List of results
        """
        self.logger.info(f"Level {detail_level} search: {query}")
        
        query_embedding = self.embedding_model.encode([query])[0].tolist()
        
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where={"detail_level": detail_level}
            )
            
            search_results = []
            for i in range(len(results['documents'][0])):
                result = {
                    'content': results['documents'][0][i],
                    'similarity': 1 - results['distances'][0][i],
                    'detail_level': detail_level,
                    'metadata': results['metadatas'][0][i]
                }
                search_results.append(result)
            
            return search_results
        
        except Exception as e:
            self.logger.error(f"Search error: {e}")
            return []
    
    def find_implementations(self, symbol: str, detail_level: int = 3) -> List[Dict]:
        """
        Find implementations at specified detail level
        
        Args:
            symbol: Function or class name
            detail_level: 3 (preview) or 4 (full)
        """
        query = f"implementation of {symbol}"
        return self.search_by_level(query, detail_level=detail_level, n_results=5)
    
    def get_file_overview(self, file_path: str) -> List[Dict]:
        """Get file overview (Level 0 and 1)"""
        results = []
        
        # Level 0 - summary
        level0 = self.collection.get(
            where={
                "detail_level": 0,
                "file_path": {"$contains": file_path}
            },
            include=['metadatas', 'documents']
        )
        
        if level0['documents']:
            results.append({
                'content': level0['documents'][0],
                'detail_level': 0,
                'metadata': level0['metadatas'][0]
            })
        
        # Level 1 - overview
        level1 = self.collection.get(
            where={
                "detail_level": 1,
                "file_path": {"$contains": file_path}
            },
            include=['metadatas', 'documents']
        )
        
        if level1['documents']:
            results.append({
                'content': level1['documents'][0],
                'detail_level': 1,
                'metadata': level1['metadatas'][0]
            })
        
        return results
    
    def print_results(self, results: List[Dict], show_content: bool = True):
        """Print search results"""
        print("\n" + "=" * 80)
        print(f"Found {len(results)} results")
        print("=" * 80)
        
        for i, result in enumerate(results, 1):
            level = result.get('detail_level', 'N/A')
            similarity = result.get('similarity', 0)
            metadata = result.get('metadata', {})
            
            level_names = {
                0: "Summary",
                1: "Overview",
                2: "Class Summary",
                3: "Function Preview",
                4: "Full Code"
            }
            
            print(f"\n[{i}] Level {level} ({level_names.get(level, 'Unknown')})")
            if similarity:
                print(f"Similarity: {similarity:.3f}")
            print(f"File: {metadata.get('file_path', 'Unknown')}")
            print(f"Type: {metadata.get('chunk_type', 'Unknown')}")
            print("-" * 80)
            
            if show_content:
                content = result.get('content', '')
                if len(content) > 800:
                    content = content[:800] + "\n... (truncated)"
                print(content)
            
            print("-" * 80)


def interactive_mode():
    """Interactive query mode"""
    print("\n" + "=" * 80)
    print("cwVDB Hierarchical Query Mode")
    print("=" * 80)
    print("\nCommands:")
    print("  search <query>           - Hierarchical search (all levels)")
    print("  level <0-4> <query>      - Search specific level")
    print("  find <symbol>            - Find implementation")
    print("  file <path>              - Get file overview")
    print("  kb                       - Show knowledge base summary")
    print("  quit                     - Exit")
    print("=" * 80 + "\n")
    
    service = HierarchicalQueryService()
    
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
                results = service.search_hierarchical(query, max_tokens=5000)
                service.print_results(results)
            
            elif command == 'level':
                level_query = query.split(maxsplit=1)
                if len(level_query) == 2:
                    level = int(level_query[0])
                    q = level_query[1]
                    results = service.search_by_level(q, detail_level=level, n_results=5)
                    service.print_results(results)
                else:
                    print("Usage: level <0-4> <query>")
            
            elif command == 'find':
                results = service.find_implementations(query, detail_level=3)
                service.print_results(results)
            
            elif command == 'file':
                results = service.get_file_overview(query)
                service.print_results(results, show_content=True)
            
            elif command == 'kb':
                summary = service.get_knowledge_summary()
                print("\n" + "=" * 80)
                print("Knowledge Base Summary")
                print("=" * 80)
                print(summary)
            
            else:
                print(f"Unknown command: {command}")
                print("Use 'search', 'level', 'find', 'file', 'kb', or 'quit'")
        
        except KeyboardInterrupt:
            print("\n\nInterrupted. Use 'quit' to exit.")
        except Exception as e:
            print(f"Error: {e}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Hierarchical Query Service for cwVDB'
    )
    
    parser.add_argument('--query', '-q', help='Search query (hierarchical)')
    parser.add_argument('--level', '-l', type=int, choices=range(5), 
                       help='Specific detail level (0-4)')
    parser.add_argument('--find', '-f', help='Find implementation')
    parser.add_argument('--file', help='Get file overview')
    parser.add_argument('--kb', action='store_true', help='Show knowledge base')
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Start interactive mode')
    parser.add_argument('--max-tokens', type=int, default=5000,
                       help='Max tokens for hierarchical search')
    
    args = parser.parse_args()
    
    if args.interactive:
        interactive_mode()
        return
    
    try:
        service = HierarchicalQueryService()
        
        if args.kb:
            summary = service.get_knowledge_summary()
            print(summary)
        
        elif args.query:
            if args.level is not None:
                results = service.search_by_level(args.query, detail_level=args.level)
            else:
                results = service.search_hierarchical(args.query, max_tokens=args.max_tokens)
            service.print_results(results)
        
        elif args.find:
            results = service.find_implementations(args.find)
            service.print_results(results)
        
        elif args.file:
            results = service.get_file_overview(args.file)
            service.print_results(results)
        
        else:
            parser.print_help()
    
    except Exception as e:
        print(f"\nError: {e}")
        raise


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
cwVDB Indexer - Vector Database Indexer for cadlib codebase
Scans C++ source code, creates embeddings, and stores in ChromaDB
"""

import json
import logging
import pickle
import re
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import git


@dataclass
class CodeChunk:
    """Represents a chunk of code with metadata"""
    id: str
    file_path: str
    content: str
    chunk_type: str
    start_line: int
    end_line: int
    metadata: Dict
    embedding: Optional[List[float]] = None


class CppParser:
    """Simple C++ parser to extract code structures"""
    
    # Regex patterns for C++ code elements
    CLASS_PATTERN = re.compile(
        r'(?:class|struct)\s+(\w+)(?:\s*:\s*(?:public|private|protected)\s+[\w:,\s]+)?\s*\{',
        re.MULTILINE
    )
    
    FUNCTION_PATTERN = re.compile(
        r'(?:[\w:]+\s+)?(?:[\w:]+\s+)?(\w+)\s*\([^)]*\)\s*(?:const)?\s*(?:override)?\s*\{',
        re.MULTILINE
    )
    
    NAMESPACE_PATTERN = re.compile(
        r'namespace\s+(\w+)\s*\{',
        re.MULTILINE
    )
    
    INCLUDE_PATTERN = re.compile(
        r'#include\s+[<"]([^>"]+)[>"]',
        re.MULTILINE
    )
    
    @staticmethod
    def extract_metadata(file_path: Path, content: str) -> Dict:
        """Extract metadata from C++ file"""
        metadata = {
            'classes': [],
            'functions': [],
            'namespaces': [],
            'includes': [],
            'file_size': len(content),
            'line_count': content.count('\n')
        }
        
        metadata['classes'] = [m.group(1) for m in CppParser.CLASS_PATTERN.finditer(content)]
        metadata['namespaces'] = [m.group(1) for m in CppParser.NAMESPACE_PATTERN.finditer(content)]
        metadata['includes'] = [m.group(1) for m in CppParser.INCLUDE_PATTERN.finditer(content)]
        
        return metadata
    
    @staticmethod
    def create_chunks(file_path: Path, content: str, chunk_size: int, chunk_overlap: int) -> List[Dict]:
        """Create semantic chunks from file content"""
        chunks = []
        lines = content.split('\n')
        
        # Chunk 1: File-level chunk with metadata
        file_hash = hashlib.md5(content.encode()).hexdigest()
        metadata = CppParser.extract_metadata(file_path, content)
        
        # Create file-level overview chunk
        header_lines = []
        for i, line in enumerate(lines[:50]):
            if line.strip().startswith('//') or line.strip().startswith('/*') or line.strip().startswith('*'):
                header_lines.append(line)
            elif line.strip().startswith('#include'):
                header_lines.append(line)
        
        if header_lines:
            chunks.append({
                'id': f"{file_hash}_header",
                'file_path': str(file_path),
                'content': '\n'.join(header_lines[:20]),
                'chunk_type': 'file_header',
                'start_line': 0,
                'end_line': min(20, len(header_lines)),
                'metadata': metadata
            })
        
        # Chunk 2: Function-level chunks
        for match in CppParser.FUNCTION_PATTERN.finditer(content):
            func_name = match.group(1)
            start_pos = match.start()
            
            start_line = content[:start_pos].count('\n')
            
            brace_count = 1
            pos = match.end()
            while pos < len(content) and brace_count > 0:
                if content[pos] == '{':
                    brace_count += 1
                elif content[pos] == '}':
                    brace_count -= 1
                pos += 1
            
            end_line = content[:pos].count('\n')
            func_content = content[start_pos:pos]
            
            if len(func_content.strip()) > 50:
                chunk_id = hashlib.md5(f"{file_path}_{func_name}_{start_line}".encode()).hexdigest()
                chunks.append({
                    'id': chunk_id,
                    'file_path': str(file_path),
                    'content': func_content,
                    'chunk_type': 'function',
                    'start_line': start_line,
                    'end_line': end_line,
                    'metadata': {
                        'function_name': func_name,
                        **metadata
                    }
                })
        
        # Chunk 3: Sliding window chunks for remaining content
        current_pos = 0
        chunk_idx = 0
        
        while current_pos < len(lines):
            chunk_lines = lines[current_pos:current_pos + chunk_size]
            chunk_content = '\n'.join(chunk_lines)
            
            if len(chunk_content.strip()) > 50:
                chunk_id = hashlib.md5(f"{file_path}_chunk_{chunk_idx}".encode()).hexdigest()
                chunks.append({
                    'id': chunk_id,
                    'file_path': str(file_path),
                    'content': chunk_content,
                    'chunk_type': 'code_block',
                    'start_line': current_pos,
                    'end_line': current_pos + len(chunk_lines),
                    'metadata': metadata
                })
            
            current_pos += chunk_size - chunk_overlap
            chunk_idx += 1
        
        return chunks


class FileScanner:
    """Scans directories for C++ files with smart filtering"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.source_path = Path(config['source_path'])
        self.exclude_dirs = set(config['exclude_dirs'])
        self.exclude_patterns = config['exclude_patterns']
        self.file_extensions = set(config['file_extensions'])
        self.min_file_size = config['min_file_size']
        self.max_file_size = config['max_file_size']
    
    def should_exclude_file(self, file_path: Path) -> bool:
        """Check if file should be excluded"""
        # Check file extension
        if file_path.suffix not in self.file_extensions:
            return True
        
        # Check exclude patterns
        for pattern in self.exclude_patterns:
            if file_path.match(pattern):
                return True
        
        # Check file size
        try:
            file_size = file_path.stat().st_size
            if file_size < self.min_file_size or file_size > self.max_file_size:
                return True
        except:
            return True
        
        return False
    
    def should_exclude_dir(self, dir_path: Path) -> bool:
        """Check if directory should be excluded"""
        dir_name = dir_path.name
        return dir_name in self.exclude_dirs
    
    def scan(self) -> List[Path]:
        """Scan source directory and return list of valid C++ files"""
        files = []
        
        for item in self.source_path.rglob('*'):
            if item.is_file():
                # Check if any parent directory is excluded
                should_skip = False
                for parent in item.parents:
                    if self.should_exclude_dir(parent):
                        should_skip = True
                        break
                
                if not should_skip and not self.should_exclude_file(item):
                    files.append(item)
        
        return files


class CheckpointManager:
    """Manages checkpoints for long-running indexing"""
    
    def __init__(self, checkpoint_path: Path):
        self.checkpoint_path = checkpoint_path
        self.checkpoint_path.mkdir(exist_ok=True)
    
    def save_checkpoint(self, state: Dict, checkpoint_name: str = "latest"):
        """Save checkpoint state"""
        checkpoint_file = self.checkpoint_path / f"{checkpoint_name}.pkl"
        with open(checkpoint_file, 'wb') as f:
            pickle.dump(state, f)
    
    def load_checkpoint(self, checkpoint_name: str = "latest") -> Optional[Dict]:
        """Load checkpoint state"""
        checkpoint_file = self.checkpoint_path / f"{checkpoint_name}.pkl"
        if checkpoint_file.exists():
            with open(checkpoint_file, 'rb') as f:
                return pickle.load(f)
        return None
    
    def checkpoint_exists(self, checkpoint_name: str = "latest") -> bool:
        """Check if checkpoint exists"""
        checkpoint_file = self.checkpoint_path / f"{checkpoint_name}.pkl"
        return checkpoint_file.exists()


class CadlibIndexer:
    """Main indexer class for vectorizing cadlib source code"""
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize indexer with configuration"""
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        
        self.file_scanner = FileScanner(self.config)
        self.checkpoint_manager = CheckpointManager(Path(self.config['checkpoint_path']))
        
        self.embedding_model = None
        self.vectordb = None
        self.collection = None
        self.git_repo = None
        
        self.logger.info("Indexer initialized")
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file"""
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging to file and console"""
        log_dir = Path(self.config['logs_path'])
        log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"indexer_{timestamp}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)
    
    def initialize_components(self):
        """Initialize embedding model and vector database"""
        self.logger.info("Initializing components...")
        
        # Initialize embedding model
        self.logger.info(f"Loading embedding model: {self.config['embedding_model']}")
        self.embedding_model = SentenceTransformer(self.config['embedding_model'])
        
        # Initialize ChromaDB
        self.logger.info(f"Initializing ChromaDB at: {self.config['vectordb_path']}")
        self.vectordb = chromadb.PersistentClient(
            path=self.config['vectordb_path'],
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        try:
            self.collection = self.vectordb.get_or_create_collection(
                name="cadlib_code",
                metadata={"description": "cadlib codebase vector embeddings"}
            )
            self.logger.info(f"Collection ready. Current document count: {self.collection.count()}")
        except Exception as e:
            self.logger.error(f"Failed to initialize collection: {e}")
            raise
        
        # Initialize git repo
        try:
            self.git_repo = git.Repo(self.config['source_path'])
            self.logger.info("Git repository detected")
        except:
            self.logger.warning("No git repository found - incremental updates disabled")
            self.git_repo = None
    
    def scan_files(self) -> List[Path]:
        """Scan source directory for C++ files"""
        self.logger.info("Scanning source directory...")
        files = self.file_scanner.scan()
        self.logger.info(f"Found {len(files)} valid C++ files")
        return files
    
    def process_file(self, file_path: Path) -> List[Dict]:
        """Process a single file and return chunks"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            chunks = CppParser.create_chunks(
                file_path,
                content,
                self.config['chunk_size'],
                self.config['chunk_overlap']
            )
            
            return chunks
        except Exception as e:
            self.logger.error(f"Error processing {file_path}: {e}")
            return []
    
    def generate_embeddings(self, chunks: List[Dict]) -> List[Dict]:
        """Generate vector embeddings for chunks"""
        if not chunks:
            return []
        
        contents = [chunk['content'] for chunk in chunks]
        embeddings = self.embedding_model.encode(
            contents,
            show_progress_bar=False,
            convert_to_numpy=True
        )
        
        for i, chunk in enumerate(chunks):
            chunk['embedding'] = embeddings[i].tolist()
        
        return chunks
    
    def store_in_vectordb(self, chunks: List[Dict]):
        """Store embeddings in ChromaDB"""
        if not chunks:
            return
        
        ids = [chunk['id'] for chunk in chunks]
        embeddings = [chunk['embedding'] for chunk in chunks]
        documents = [chunk['content'] for chunk in chunks]
        metadatas = [{
            'file_path': chunk['file_path'],
            'chunk_type': chunk['chunk_type'],
            'start_line': chunk['start_line'],
            'end_line': chunk['end_line']
        } for chunk in chunks]
        
        try:
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
        except Exception as e:
            self.logger.error(f"Error storing chunks in vectordb: {e}")
            raise
    
    def process_batch(self, files: List[Path]) -> int:
        """Process a batch of files"""
        total_chunks = 0
        all_chunks = []
        
        for file_path in files:
            chunks = self.process_file(file_path)
            if chunks:
                chunks = self.generate_embeddings(chunks)
                all_chunks.extend(chunks)
        
        if all_chunks:
            self.store_in_vectordb(all_chunks)
            total_chunks = len(all_chunks)
        
        return total_chunks
    
    def run_initial_index(self):
        """Run initial full indexing"""
        self.logger.info("=" * 80)
        self.logger.info("Starting initial indexing of cadlib codebase")
        self.logger.info("=" * 80)
        
        start_time = datetime.now()
        
        # Initialize components
        self.initialize_components()
        
        # Check for existing checkpoint
        checkpoint_state = None
        if self.config['enable_checkpoints'] and self.checkpoint_manager.checkpoint_exists():
            self.logger.info("Found existing checkpoint")
            response = input("Resume from checkpoint? (y/n): ")
            if response.lower() == 'y':
                checkpoint_state = self.checkpoint_manager.load_checkpoint()
                self.logger.info(f"Resuming from file {checkpoint_state['processed_files']}")
        
        # Scan files
        files = self.scan_files()
        total_files = len(files)
        
        # Resume from checkpoint if available
        start_idx = 0
        total_chunks = 0
        if checkpoint_state:
            start_idx = checkpoint_state['processed_files']
            total_chunks = checkpoint_state['total_chunks']
            files = files[start_idx:]
        
        # Process files in batches
        batch_size = self.config['batch_size']
        checkpoint_interval = self.config['checkpoint_interval']
        
        with tqdm(total=total_files, initial=start_idx, desc="Indexing files") as pbar:
            for i in range(0, len(files), batch_size):
                batch = files[i:i + batch_size]
                chunks_processed = self.process_batch(batch)
                total_chunks += chunks_processed
                pbar.update(len(batch))
                
                # Save checkpoint
                if self.config['enable_checkpoints'] and (i // batch_size) % checkpoint_interval == 0:
                    checkpoint = {
                        'processed_files': start_idx + i + len(batch),
                        'total_chunks': total_chunks,
                        'timestamp': datetime.now().isoformat()
                    }
                    self.checkpoint_manager.save_checkpoint(checkpoint)
                    self.logger.info(f"Checkpoint saved at file {checkpoint['processed_files']}")
        
        # Final statistics
        end_time = datetime.now()
        duration = end_time - start_time
        
        self.logger.info("=" * 80)
        self.logger.info("Indexing completed!")
        self.logger.info(f"Files processed: {total_files}")
        self.logger.info(f"Chunks created: {total_chunks}")
        self.logger.info(f"Total documents in DB: {self.collection.count()}")
        self.logger.info(f"Duration: {duration}")
        self.logger.info("=" * 80)
    
    def run_incremental_update(self):
        """Run incremental update based on git changes"""
        self.logger.info("=" * 80)
        self.logger.info("Starting incremental update")
        self.logger.info("=" * 80)
        
        if not self.git_repo:
            self.logger.error("Git repository not found - incremental updates not available")
            return
        
        start_time = datetime.now()
        
        # Initialize components
        self.initialize_components()
        
        # Get changed files since last commit
        try:
            changed_files = []
            
            # Get unstaged changes
            diff_unstaged = self.git_repo.index.diff(None)
            for diff in diff_unstaged:
                file_path = Path(self.config['source_path']) / diff.a_path
                if file_path.exists() and not self.file_scanner.should_exclude_file(file_path):
                    changed_files.append(file_path)
            
            # Get staged changes
            diff_staged = self.git_repo.index.diff('HEAD')
            for diff in diff_staged:
                file_path = Path(self.config['source_path']) / diff.a_path
                if file_path.exists() and not self.file_scanner.should_exclude_file(file_path):
                    changed_files.append(file_path)
            
            changed_files = list(set(changed_files))
            
            self.logger.info(f"Found {len(changed_files)} changed files")
            
            if not changed_files:
                self.logger.info("No changes detected")
                return
            
            # Process changed files
            total_chunks = 0
            for file_path in tqdm(changed_files, desc="Updating files"):
                # Remove old chunks for this file
                try:
                    self.collection.delete(
                        where={"file_path": str(file_path)}
                    )
                except:
                    pass
                
                # Process and add new chunks
                chunks = self.process_file(file_path)
                if chunks:
                    chunks = self.generate_embeddings(chunks)
                    self.store_in_vectordb(chunks)
                    total_chunks += len(chunks)
            
            # Final statistics
            end_time = datetime.now()
            duration = end_time - start_time
            
            self.logger.info("=" * 80)
            self.logger.info("Incremental update completed!")
            self.logger.info(f"Files updated: {len(changed_files)}")
            self.logger.info(f"Chunks updated: {total_chunks}")
            self.logger.info(f"Total documents in DB: {self.collection.count()}")
            self.logger.info(f"Duration: {duration}")
            self.logger.info("=" * 80)
            
        except Exception as e:
            self.logger.error(f"Error during incremental update: {e}")
            raise


def generate_documentation(config_path: str, limit: int = 100, skip_existing: bool = True):
    """Generate documentation after indexing"""
    try:
        from generate_docs import CDocumentationGenerator
        print("\n" + "=" * 80)
        print("DOCUMENTATION GENERATION")
        print("=" * 80)
        generator = CDocumentationGenerator(config_path)
        generator.generateAllDocs(limit, skip_existing)
    except ImportError as e:
        print(f"\nWarning: Could not import generate_docs: {e}")
    except Exception as e:
        print(f"\nWarning: Documentation generation failed: {e}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='cwVDB Indexer - Vector Database Indexer for cadlib',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python indexer.py --initial                    Run initial full index
  python indexer.py --incremental                Run incremental update
  python indexer.py --initial --generate-docs    Index and generate docs
  python indexer.py --generate-docs --limit 50   Only generate docs
  python indexer.py --initial --config custom.json
        """
    )
    
    parser.add_argument('--initial', action='store_true', 
                       help='Run initial full index')
    parser.add_argument('--incremental', action='store_true',
                       help='Run incremental update (git-based)')
    parser.add_argument('--generate-docs', action='store_true',
                       help='Generate documentation after indexing')
    parser.add_argument('--docs-limit', type=int, default=100,
                       help='Limit number of docs to generate (default: 100)')
    parser.add_argument('--force-docs', action='store_true',
                       help='Regenerate existing docs (default: skip existing)')
    parser.add_argument('--config', default='config.json',
                       help='Path to config file (default: config.json)')
    
    args = parser.parse_args()
    
    # If only --generate-docs, just generate docs
    if args.generate_docs and not args.initial and not args.incremental:
        generate_documentation(args.config, args.docs_limit, not args.force_docs)
        return
    
    if not args.initial and not args.incremental:
        parser.print_help()
        return
    
    try:
        indexer = CadlibIndexer(config_path=args.config)
        
        if args.initial:
            indexer.run_initial_index()
        elif args.incremental:
            indexer.run_incremental_update()
        
        # Generate documentation if requested
        if args.generate_docs:
            generate_documentation(args.config, args.docs_limit, not args.force_docs)
            
    except KeyboardInterrupt:
        print("\n\nIndexing interrupted by user")
    except Exception as e:
        print(f"\n\nError: {e}")
        raise


if __name__ == "__main__":
    main()

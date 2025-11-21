#!/usr/bin/env python3
"""
Hierarchical Indexer for cwVDB
Creates 5 levels of abstraction for token-efficient queries
"""

import json
import logging
import pickle
import re
import hashlib
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import git


class HierarchicalChunker:
    """Creates hierarchical chunks with 5 detail levels"""
    
    # Regex patterns
    CLASS_PATTERN = re.compile(
        r'(?:class|struct)\s+(\w+)(?:\s*:\s*(?:public|private|protected)\s+[\w:,\s]+)?\s*\{',
        re.MULTILINE
    )
    
    FUNCTION_PATTERN = re.compile(
        r'(?:[\w:]+\s+)?(?:[\w:]+\s+)?(\w+)\s*\([^)]*\)\s*(?:const)?\s*(?:override)?\s*\{',
        re.MULTILINE
    )
    
    NAMESPACE_PATTERN = re.compile(r'namespace\s+(\w+)\s*\{', re.MULTILINE)
    INCLUDE_PATTERN = re.compile(r'#include\s+[<"]([^>"]+)[>"]', re.MULTILINE)
    COMMENT_PATTERN = re.compile(r'//.*?$|/\*.*?\*/', re.MULTILINE | re.DOTALL)
    
    @staticmethod
    def extract_metadata(file_path: Path, content: str) -> Dict:
        """Extract comprehensive metadata"""
        metadata = {
            'classes': [],
            'functions': [],
            'namespaces': [],
            'includes': [],
            'file_size': len(content),
            'line_count': content.count('\n'),
            'has_main': 'int main(' in content or 'void main(' in content
        }
        
        metadata['classes'] = [m.group(1) for m in HierarchicalChunker.CLASS_PATTERN.finditer(content)]
        metadata['namespaces'] = [m.group(1) for m in HierarchicalChunker.NAMESPACE_PATTERN.finditer(content)]
        metadata['includes'] = [m.group(1) for m in HierarchicalChunker.INCLUDE_PATTERN.finditer(content)]
        metadata['functions'] = [m.group(1) for m in HierarchicalChunker.FUNCTION_PATTERN.finditer(content)][:20]
        
        return metadata
    
    @staticmethod
    def create_level0_chunk(file_path: Path, content: str, metadata: Dict) -> Optional[Dict]:
        """
        Level 0: Ultra-compact file summary (50-100 chars)
        Purpose: Quick reference, minimal tokens
        """
        classes_str = f"{len(metadata['classes'])} classes" if metadata['classes'] else "no classes"
        funcs_str = f"{len(metadata['functions'])} functions" if metadata['functions'] else "no functions"
        
        summary = f"{file_path.name}: {classes_str}, {funcs_str}"
        
        if metadata['classes']:
            summary += f" ({', '.join(metadata['classes'][:3])})"
        
        file_hash = hashlib.md5(str(file_path).encode()).hexdigest()
        
        return {
            'id': f"{file_hash}_L0",
            'file_path': str(file_path),
            'content': summary,
            'chunk_type': 'file_summary',
            'detail_level': 0,
            'start_line': 0,
            'end_line': 0,
            'metadata': {**metadata, 'detail_level': 0}
        }
    
    @staticmethod
    def create_level1_chunk(file_path: Path, content: str, metadata: Dict) -> Optional[Dict]:
        """
        Level 1: File overview with key elements (200-500 chars)
        Purpose: Understanding file purpose and main components
        """
        lines = content.split('\n')
        overview_lines = []
        
        # Extract file comments (first 10 lines)
        for line in lines[:10]:
            stripped = line.strip()
            if stripped.startswith('//') or stripped.startswith('/*') or stripped.startswith('*'):
                overview_lines.append(line)
        
        # Add includes
        overview_lines.append("\n// Includes:")
        for inc in metadata['includes'][:5]:
            overview_lines.append(f"#include <{inc}>")
        
        # Add class/namespace declarations
        if metadata['namespaces']:
            overview_lines.append(f"\n// Namespaces: {', '.join(metadata['namespaces'][:3])}")
        
        if metadata['classes']:
            overview_lines.append(f"// Classes: {', '.join(metadata['classes'][:5])}")
        
        if metadata['functions']:
            overview_lines.append(f"// Functions: {len(metadata['functions'])} total")
        
        content_overview = '\n'.join(overview_lines[:30])
        file_hash = hashlib.md5(str(file_path).encode()).hexdigest()
        
        return {
            'id': f"{file_hash}_L1",
            'file_path': str(file_path),
            'content': content_overview,
            'chunk_type': 'file_overview',
            'detail_level': 1,
            'start_line': 0,
            'end_line': 30,
            'metadata': {**metadata, 'detail_level': 1}
        }
    
    @staticmethod
    def create_level2_chunks(file_path: Path, content: str, metadata: Dict) -> List[Dict]:
        """
        Level 2: Class/namespace summaries (300-600 chars each)
        Purpose: Understanding major components
        """
        chunks = []
        
        for class_match in HierarchicalChunker.CLASS_PATTERN.finditer(content):
            class_name = class_match.group(1)
            start_pos = class_match.start()
            start_line = content[:start_pos].count('\n')
            
            # Extract class body (first 20 lines or until closing brace)
            brace_count = 1
            pos = class_match.end()
            lines_extracted = 0
            
            while pos < len(content) and brace_count > 0 and lines_extracted < 20:
                if content[pos] == '{':
                    brace_count += 1
                elif content[pos] == '}':
                    brace_count -= 1
                elif content[pos] == '\n':
                    lines_extracted += 1
                pos += 1
            
            end_line = content[:pos].count('\n')
            class_summary = content[start_pos:pos]
            
            # Extract only declarations (remove implementations)
            summary_lines = []
            for line in class_summary.split('\n')[:20]:
                if '{' in line or '}' in line or 'public:' in line or 'private:' in line or 'protected:' in line:
                    summary_lines.append(line)
                elif line.strip() and not line.strip().startswith('//'):
                    summary_lines.append(line)
            
            chunk_id = hashlib.md5(f"{file_path}_{class_name}_L2".encode()).hexdigest()
            
            chunks.append({
                'id': chunk_id,
                'file_path': str(file_path),
                'content': '\n'.join(summary_lines[:20]),
                'chunk_type': 'class_summary',
                'detail_level': 2,
                'start_line': start_line,
                'end_line': end_line,
                'metadata': {
                    **metadata,
                    'detail_level': 2,
                    'class_name': class_name
                }
            })
        
        return chunks
    
    @staticmethod
    def create_level3_chunks(file_path: Path, content: str, metadata: Dict) -> List[Dict]:
        """
        Level 3: Function signatures + brief body (400-800 chars each)
        Purpose: Understanding function behavior
        """
        chunks = []
        
        for func_match in HierarchicalChunker.FUNCTION_PATTERN.finditer(content):
            func_name = func_match.group(1)
            start_pos = func_match.start()
            start_line = content[:start_pos].count('\n')
            
            # Get function signature + first 10 lines of body
            brace_count = 1
            pos = func_match.end()
            lines_extracted = 0
            
            while pos < len(content) and lines_extracted < 15:
                if content[pos] == '{':
                    brace_count += 1
                elif content[pos] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        break
                elif content[pos] == '\n':
                    lines_extracted += 1
                pos += 1
            
            end_line = content[:pos].count('\n')
            func_preview = content[start_pos:pos]
            
            if len(func_preview.strip()) < 20:
                continue
            
            chunk_id = hashlib.md5(f"{file_path}_{func_name}_L3_{start_line}".encode()).hexdigest()
            
            chunks.append({
                'id': chunk_id,
                'file_path': str(file_path),
                'content': func_preview,
                'chunk_type': 'function_preview',
                'detail_level': 3,
                'start_line': start_line,
                'end_line': end_line,
                'metadata': {
                    **metadata,
                    'detail_level': 3,
                    'function_name': func_name
                }
            })
        
        return chunks
    
    @staticmethod
    def create_level4_chunks(file_path: Path, content: str, metadata: Dict, chunk_size: int = 50) -> List[Dict]:
        """
        Level 4: Full code implementation (1000+ chars each)
        Purpose: Detailed code analysis
        """
        chunks = []
        lines = content.split('\n')
        
        # Full function implementations
        for func_match in HierarchicalChunker.FUNCTION_PATTERN.finditer(content):
            func_name = func_match.group(1)
            start_pos = func_match.start()
            start_line = content[:start_pos].count('\n')
            
            # Get complete function
            brace_count = 1
            pos = func_match.end()
            
            while pos < len(content) and brace_count > 0:
                if content[pos] == '{':
                    brace_count += 1
                elif content[pos] == '}':
                    brace_count -= 1
                pos += 1
            
            end_line = content[:pos].count('\n')
            func_full = content[start_pos:pos]
            
            if len(func_full.strip()) < 50:
                continue
            
            chunk_id = hashlib.md5(f"{file_path}_{func_name}_L4_{start_line}".encode()).hexdigest()
            
            chunks.append({
                'id': chunk_id,
                'file_path': str(file_path),
                'content': func_full,
                'chunk_type': 'function_full',
                'detail_level': 4,
                'start_line': start_line,
                'end_line': end_line,
                'metadata': {
                    **metadata,
                    'detail_level': 4,
                    'function_name': func_name
                }
            })
        
        # Sliding window for remaining code
        current_pos = 0
        chunk_idx = 0
        
        while current_pos < len(lines):
            chunk_lines = lines[current_pos:current_pos + chunk_size]
            chunk_content = '\n'.join(chunk_lines)
            
            if len(chunk_content.strip()) > 50:
                chunk_id = hashlib.md5(f"{file_path}_L4_block_{chunk_idx}".encode()).hexdigest()
                
                chunks.append({
                    'id': chunk_id,
                    'file_path': str(file_path),
                    'content': chunk_content,
                    'chunk_type': 'code_block',
                    'detail_level': 4,
                    'start_line': current_pos,
                    'end_line': current_pos + len(chunk_lines),
                    'metadata': {**metadata, 'detail_level': 4}
                })
            
            current_pos += chunk_size - 10  # Overlap
            chunk_idx += 1
        
        return chunks
    
    @staticmethod
    def create_all_chunks(file_path: Path, content: str, chunk_size: int = 50) -> List[Dict]:
        """Create all hierarchical chunks for a file"""
        chunks = []
        
        metadata = HierarchicalChunker.extract_metadata(file_path, content)
        
        # Level 0: Ultra-compact summary
        l0 = HierarchicalChunker.create_level0_chunk(file_path, content, metadata)
        if l0:
            chunks.append(l0)
        
        # Level 1: File overview
        l1 = HierarchicalChunker.create_level1_chunk(file_path, content, metadata)
        if l1:
            chunks.append(l1)
        
        # Level 2: Class summaries
        l2_chunks = HierarchicalChunker.create_level2_chunks(file_path, content, metadata)
        chunks.extend(l2_chunks)
        
        # Level 3: Function previews
        l3_chunks = HierarchicalChunker.create_level3_chunks(file_path, content, metadata)
        chunks.extend(l3_chunks)
        
        # Level 4: Full implementation
        l4_chunks = HierarchicalChunker.create_level4_chunks(file_path, content, metadata, chunk_size)
        chunks.extend(l4_chunks)
        
        return chunks


class HierarchicalIndexer:
    """Main indexer with hierarchical chunking"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        
        self.embedding_model = None
        self.vectordb = None
        self.collection = None
        
        self.logger.info("Hierarchical Indexer initialized")
    
    def _load_config(self, config_path: str) -> Dict:
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def _setup_logging(self) -> logging.Logger:
        log_dir = Path(self.config['logs_path'])
        log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"hierarchical_indexer_{timestamp}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)
    
    def initialize(self):
        """Initialize embedding model and vector database"""
        self.logger.info("Initializing components...")
        
        self.logger.info(f"Loading embedding model: {self.config['embedding_model']}")
        self.embedding_model = SentenceTransformer(self.config['embedding_model'])
        
        self.logger.info(f"Initializing ChromaDB at: {self.config['vectordb_path']}")
        self.vectordb = chromadb.PersistentClient(
            path=self.config['vectordb_path'],
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Delete old collection if exists
        try:
            self.vectordb.delete_collection(name="cadlib_code")
            self.logger.info("Deleted old collection")
        except:
            pass
        
        # Create new collection
        self.collection = self.vectordb.create_collection(
            name="cadlib_code",
            metadata={"description": "cadlib codebase with hierarchical embeddings"}
        )
        
        self.logger.info("Collection ready for hierarchical indexing")
    
    def scan_files(self) -> List[Path]:
        """Scan source directory for files"""
        self.logger.info("Scanning source directory...")
        
        source_path = Path(self.config['source_path'])
        file_extensions = set(self.config['file_extensions'])
        exclude_dirs = set(self.config['exclude_dirs'])
        exclude_patterns = self.config['exclude_patterns']
        
        files = []
        
        for item in source_path.rglob('*'):
            if item.is_file():
                # Check extension
                if item.suffix not in file_extensions and item.name not in file_extensions:
                    continue
                
                # Check excluded directories
                skip = False
                for parent in item.parents:
                    if parent.name in exclude_dirs:
                        skip = True
                        break
                
                if skip:
                    continue
                
                # Check excluded patterns
                skip_pattern = False
                for pattern in exclude_patterns:
                    if item.match(pattern):
                        skip_pattern = True
                        break
                
                if skip_pattern:
                    continue
                
                # Check file size
                try:
                    file_size = item.stat().st_size
                    if file_size < self.config['min_file_size'] or file_size > self.config['max_file_size']:
                        continue
                except:
                    continue
                
                files.append(item)
        
        self.logger.info(f"Found {len(files)} valid files")
        return files
    
    def process_file(self, file_path: Path) -> List[Dict]:
        """Process a single file with hierarchical chunking"""
        try:
            # Read file
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except:
                with open(file_path, 'r', encoding='latin-1', errors='ignore') as f:
                    content = f.read()
            
            # Create hierarchical chunks
            chunks = HierarchicalChunker.create_all_chunks(file_path, content, self.config['chunk_size'])
            
            return chunks
        
        except Exception as e:
            self.logger.error(f"Error processing {file_path}: {e}")
            return []
    
    def generate_embeddings(self, chunks: List[Dict]) -> List[Dict]:
        """Generate embeddings for chunks"""
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
    
    def store_chunks(self, chunks: List[Dict]):
        """Store chunks in ChromaDB"""
        if not chunks:
            return
        
        ids = [chunk['id'] for chunk in chunks]
        embeddings = [chunk['embedding'] for chunk in chunks]
        documents = [chunk['content'] for chunk in chunks]
        metadatas = [{
            'file_path': chunk['file_path'],
            'chunk_type': chunk['chunk_type'],
            'detail_level': chunk['detail_level'],
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
            self.logger.error(f"Error storing chunks: {e}")
    
    def run_full_index(self):
        """Run complete hierarchical indexing"""
        self.logger.info("=" * 80)
        self.logger.info("Starting Hierarchical Indexing")
        self.logger.info("=" * 80)
        
        start_time = datetime.now()
        
        # Initialize
        self.initialize()
        
        # Scan files
        files = self.scan_files()
        
        # Process in batches
        batch_size = self.config['batch_size']
        total_chunks = 0
        
        with tqdm(total=len(files), desc="Indexing files") as pbar:
            for i in range(0, len(files), batch_size):
                batch = files[i:i + batch_size]
                
                all_chunks = []
                for file_path in batch:
                    chunks = self.process_file(file_path)
                    if chunks:
                        chunks = self.generate_embeddings(chunks)
                        all_chunks.extend(chunks)
                
                if all_chunks:
                    self.store_chunks(all_chunks)
                    total_chunks += len(all_chunks)
                
                pbar.update(len(batch))
        
        # Statistics
        end_time = datetime.now()
        duration = end_time - start_time
        
        # Count chunks by level
        level_counts = {}
        for level in range(5):
            results = self.collection.get(
                where={"detail_level": level},
                limit=1
            )
            count = self.collection.count()
            level_counts[level] = count
        
        self.logger.info("=" * 80)
        self.logger.info("Hierarchical Indexing Complete!")
        self.logger.info(f"Files processed: {len(files)}")
        self.logger.info(f"Total chunks: {total_chunks}")
        self.logger.info(f"Total documents in DB: {self.collection.count()}")
        self.logger.info(f"Duration: {duration}")
        self.logger.info("=" * 80)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Hierarchical Indexer for cwVDB')
    parser.add_argument('--config', default='config.json', help='Config file path')
    
    args = parser.parse_args()
    
    try:
        indexer = HierarchicalIndexer(config_path=args.config)
        indexer.run_full_index()
    except KeyboardInterrupt:
        print("\n\nIndexing interrupted")
    except Exception as e:
        print(f"\n\nError: {e}")
        raise


if __name__ == "__main__":
    main()

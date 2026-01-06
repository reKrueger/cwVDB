#!/usr/bin/env python3
"""
cwVDB Indexer - Vector Database Indexer for cadlib codebase
Scans C++ source code, creates embeddings, and stores in ChromaDB

Usage:
    python indexer.py --initial    Create/rebuild database
"""

import json
import logging
import pickle
import re
import hashlib
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from dataclasses import dataclass

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from tqdm import tqdm


class CppParser:
    """Simple C++ parser to extract code structures"""
    
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
    
    @staticmethod
    def extract_metadata(content: str) -> Dict:
        """Extract metadata from C++ file"""
        return {
            'classes': [m.group(1) for m in CppParser.CLASS_PATTERN.finditer(content)],
            'namespaces': [m.group(1) for m in CppParser.NAMESPACE_PATTERN.finditer(content)],
            'includes': [m.group(1) for m in CppParser.INCLUDE_PATTERN.finditer(content)],
            'file_size': len(content),
            'line_count': content.count('\n')
        }
    
    @staticmethod
    def create_chunks(file_path: Path, content: str, chunk_size: int, chunk_overlap: int) -> List[Dict]:
        """Create semantic chunks from file content"""
        chunks = []
        lines = content.split('\n')
        file_hash = hashlib.md5(content.encode()).hexdigest()
        metadata = CppParser.extract_metadata(content)
        
        # File header chunk
        header_lines = []
        for line in lines[:50]:
            if line.strip().startswith(('/', '*', '#include')):
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
        
        # Function chunks
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
                    'metadata': {'function_name': func_name, **metadata}
                })
        
        # Sliding window chunks
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
    """Scans directories for source files"""
    
    def __init__(self, config: Dict):
        self.source_path = Path(config['source_path'])
        self.exclude_dirs = set(config['exclude_dirs'])
        self.exclude_patterns = config['exclude_patterns']
        self.file_extensions = set(config['file_extensions'])
        self.min_file_size = config['min_file_size']
        self.max_file_size = config['max_file_size']
    
    def should_exclude_file(self, file_path: Path) -> bool:
        if file_path.suffix not in self.file_extensions:
            return True
        for pattern in self.exclude_patterns:
            if file_path.match(pattern):
                return True
        try:
            size = file_path.stat().st_size
            if size < self.min_file_size or size > self.max_file_size:
                return True
        except:
            return True
        return False
    
    def scan(self) -> List[Path]:
        files = []
        for item in self.source_path.rglob('*'):
            if item.is_file():
                skip = any(p.name in self.exclude_dirs for p in item.parents)
                if not skip and not self.should_exclude_file(item):
                    files.append(item)
        return files


class CadlibIndexer:
    """Main indexer class"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        self.file_scanner = FileScanner(self.config)
        self.embedding_model = None
        self.vectordb = None
        self.collection = None
    
    def _load_config(self, config_path: str) -> Dict:
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def _setup_logging(self) -> logging.Logger:
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
    
    def initialize(self):
        """Initialize embedding model and database"""
        self.logger.info(f"Loading embedding model: {self.config['embedding_model']}")
        self.embedding_model = SentenceTransformer(self.config['embedding_model'])
        
        self.logger.info(f"Initializing ChromaDB at: {self.config['vectordb_path']}")
        self.vectordb = chromadb.PersistentClient(
            path=self.config['vectordb_path'],
            settings=Settings(anonymized_telemetry=False)
        )
        
        self.collection = self.vectordb.get_or_create_collection(
            name="cadlib_code",
            metadata={"description": "cadlib codebase vector embeddings"}
        )
        self.logger.info(f"Collection ready. Documents: {self.collection.count()}")
    
    def process_file(self, file_path: Path) -> List[Dict]:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            return CppParser.create_chunks(
                file_path, content,
                self.config['chunk_size'],
                self.config['chunk_overlap']
            )
        except Exception as e:
            self.logger.error(f"Error processing {file_path}: {e}")
            return []
    
    def generate_embeddings(self, chunks: List[Dict]) -> List[Dict]:
        if not chunks:
            return []
        contents = [c['content'] for c in chunks]
        embeddings = self.embedding_model.encode(contents, show_progress_bar=False, convert_to_numpy=True)
        for i, chunk in enumerate(chunks):
            chunk['embedding'] = embeddings[i].tolist()
        return chunks
    
    def store_chunks(self, chunks: List[Dict]):
        if not chunks:
            return
        self.collection.add(
            ids=[c['id'] for c in chunks],
            embeddings=[c['embedding'] for c in chunks],
            documents=[c['content'] for c in chunks],
            metadatas=[{
                'file_path': c['file_path'],
                'chunk_type': c['chunk_type'],
                'start_line': c['start_line'],
                'end_line': c['end_line']
            } for c in chunks]
        )
    
    def run(self):
        """Run full indexing"""
        self.logger.info("=" * 60)
        self.logger.info("Starting indexing")
        self.logger.info("=" * 60)
        
        start_time = datetime.now()
        self.initialize()
        
        files = self.file_scanner.scan()
        self.logger.info(f"Found {len(files)} files")
        
        total_chunks = 0
        batch_size = self.config['batch_size']
        
        with tqdm(total=len(files), desc="Indexing") as pbar:
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
        
        duration = datetime.now() - start_time
        
        self.logger.info("=" * 60)
        self.logger.info("Indexing complete!")
        self.logger.info(f"Files: {len(files)}")
        self.logger.info(f"Chunks: {total_chunks}")
        self.logger.info(f"Total in DB: {self.collection.count()}")
        self.logger.info(f"Duration: {duration}")
        self.logger.info("=" * 60)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='cwVDB Indexer')
    parser.add_argument('--initial', action='store_true', help='Run full index')
    parser.add_argument('--config', default='config.json', help='Config file')
    
    args = parser.parse_args()
    
    if not args.initial:
        parser.print_help()
        return
    
    try:
        indexer = CadlibIndexer(config_path=args.config)
        indexer.run()
    except KeyboardInterrupt:
        print("\n\nIndexing interrupted")
    except Exception as e:
        print(f"\nError: {e}")
        raise


if __name__ == "__main__":
    main()

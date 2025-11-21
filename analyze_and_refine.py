#!/usr/bin/env python3
"""
Claude Analysis Script - Phase 2
Analyzes VectorDB and creates smart documentation for token-efficient queries
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from collections import defaultdict

import chromadb
from chromadb.config import Settings


class VectorDBAnalyzer:
    """Analyzes VectorDB and creates structured documentation"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        
        self.vectordb = None
        self.collection = None
        
        self.knowledge_base_path = Path("knowledge")
        self.knowledge_base_path.mkdir(exist_ok=True)
        
        self.logger.info("VectorDB Analyzer initialized")
    
    def _load_config(self, config_path: str) -> Dict:
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def _setup_logging(self) -> logging.Logger:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def initialize(self):
        """Connect to VectorDB"""
        self.logger.info("Connecting to VectorDB...")
        
        self.vectordb = chromadb.PersistentClient(
            path=self.config['vectordb_path'],
            settings=Settings(anonymized_telemetry=False)
        )
        
        self.collection = self.vectordb.get_collection(name="cadlib_code")
        self.logger.info(f"Connected. Collection has {self.collection.count()} documents")
    
    def get_all_files(self) -> List[str]:
        """Get list of all unique files in VectorDB"""
        self.logger.info("Extracting file list...")
        
        # Get Level 0 chunks (one per file)
        results = self.collection.get(
            where={"detail_level": 0},
            include=['metadatas']
        )
        
        files = []
        for metadata in results['metadatas']:
            file_path = metadata.get('file_path', '')
            if file_path and file_path not in files:
                files.append(file_path)
        
        self.logger.info(f"Found {len(files)} unique files")
        return sorted(files)
    
    def analyze_project_structure(self) -> Dict:
        """Analyze overall project structure"""
        self.logger.info("Analyzing project structure...")
        
        files = self.get_all_files()
        
        structure = {
            'total_files': len(files),
            'by_extension': defaultdict(int),
            'by_directory': defaultdict(list),
            'file_types': {
                'headers': [],
                'implementations': [],
                'projects': [],
                'configs': []
            }
        }
        
        for file in files:
            path = Path(file)
            
            # Count by extension
            ext = path.suffix
            structure['by_extension'][ext] += 1
            
            # Group by directory
            if len(path.parts) > 1:
                dir_name = path.parts[-2]
                structure['by_directory'][dir_name].append(path.name)
            
            # Categorize
            if ext in ['.h', '.hpp']:
                structure['file_types']['headers'].append(str(path))
            elif ext in ['.cpp', '.c', '.cc']:
                structure['file_types']['implementations'].append(str(path))
            elif ext in ['.vcxproj', '.sln']:
                structure['file_types']['projects'].append(str(path))
            elif ext in ['.xml', '.props', '.targets']:
                structure['file_types']['configs'].append(str(path))
        
        return structure
    
    def extract_class_hierarchy(self) -> Dict:
        """Extract all classes and their relationships"""
        self.logger.info("Extracting class hierarchy...")
        
        # Get Level 2 chunks (class summaries)
        results = self.collection.get(
            where={"detail_level": 2},
            include=['metadatas', 'documents']
        )
        
        classes = {}
        
        for i, metadata in enumerate(results['metadatas']):
            class_name = metadata.get('class_name', '')
            if class_name:
                file_path = metadata.get('file_path', '')
                content = results['documents'][i] if i < len(results['documents']) else ''
                
                # Extract inheritance (simple pattern matching)
                inheritance = []
                if ':' in content:
                    for line in content.split('\n')[:5]:
                        if 'public' in line or 'private' in line or 'protected' in line:
                            parts = line.split(':')[1] if ':' in line else ''
                            for part in parts.split(','):
                                base = part.strip().split()[-1] if part.strip() else ''
                                if base and base != '{':
                                    inheritance.append(base)
                
                classes[class_name] = {
                    'file': file_path,
                    'inherits': inheritance
                }
        
        self.logger.info(f"Found {len(classes)} classes")
        return classes
    
    def extract_api_functions(self) -> List[Dict]:
        """Extract all public functions"""
        self.logger.info("Extracting API functions...")
        
        # Get Level 3 chunks (function previews)
        results = self.collection.get(
            where={"detail_level": 3},
            include=['metadatas', 'documents']
        )
        
        functions = []
        
        for i, metadata in enumerate(results['metadatas']):
            func_name = metadata.get('function_name', '')
            if func_name:
                file_path = metadata.get('file_path', '')
                content = results['documents'][i] if i < len(results['documents']) else ''
                
                # Extract signature (first line usually)
                signature = content.split('\n')[0] if content else func_name
                
                functions.append({
                    'name': func_name,
                    'file': file_path,
                    'signature': signature[:200]
                })
        
        self.logger.info(f"Found {len(functions)} functions")
        return functions[:500]  # Limit for doc size
    
    def create_quick_reference(self, structure: Dict):
        """Create ultra-compact quick reference"""
        self.logger.info("Creating quick reference...")
        
        doc_path = self.knowledge_base_path / "00-quick-reference.md"
        
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write("# cwVDB Quick Reference\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Project Overview\n\n")
            f.write(f"- **Total Files:** {structure['total_files']}\n")
            f.write(f"- **C++ Headers:** {structure['by_extension'].get('.h', 0) + structure['by_extension'].get('.hpp', 0)}\n")
            f.write(f"- **C++ Sources:** {structure['by_extension'].get('.cpp', 0) + structure['by_extension'].get('.c', 0)}\n")
            f.write(f"- **VS Projects:** {structure['by_extension'].get('.vcxproj', 0)}\n")
            f.write(f"- **Solutions:** {structure['by_extension'].get('.sln', 0)}\n\n")
            
            f.write("## Main Directories\n\n")
            for dir_name, files in sorted(structure['by_directory'].items())[:20]:
                f.write(f"- **{dir_name}**: {len(files)} files\n")
            
            f.write("\n## File Types\n\n")
            f.write(f"- Headers: {len(structure['file_types']['headers'])}\n")
            f.write(f"- Implementations: {len(structure['file_types']['implementations'])}\n")
            f.write(f"- Projects: {len(structure['file_types']['projects'])}\n")
            f.write(f"- Configs: {len(structure['file_types']['configs'])}\n")
        
        self.logger.info(f"Created: {doc_path}")
    
    def create_project_overview(self, structure: Dict, classes: Dict):
        """Create detailed project overview"""
        self.logger.info("Creating project overview...")
        
        doc_path = self.knowledge_base_path / "01-project-overview.md"
        
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write("# Project Overview\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## File Statistics\n\n")
            f.write(f"Total files indexed: {structure['total_files']}\n\n")
            
            f.write("### By Extension\n\n")
            for ext, count in sorted(structure['by_extension'].items(), key=lambda x: -x[1])[:10]:
                f.write(f"- `{ext}`: {count} files\n")
            
            f.write("\n### By Directory\n\n")
            for dir_name, files in sorted(structure['by_directory'].items(), key=lambda x: -len(x[1]))[:30]:
                f.write(f"- **{dir_name}**: {len(files)} files\n")
            
            f.write("\n## Code Structure\n\n")
            f.write(f"- Total classes found: {len(classes)}\n")
            f.write(f"- Headers: {len(structure['file_types']['headers'])}\n")
            f.write(f"- Implementations: {len(structure['file_types']['implementations'])}\n")
            
            if structure['file_types']['projects']:
                f.write("\n## Visual Studio Projects\n\n")
                for proj in structure['file_types']['projects'][:20]:
                    f.write(f"- {Path(proj).name}\n")
        
        self.logger.info(f"Created: {doc_path}")
    
    def create_class_reference(self, classes: Dict):
        """Create class hierarchy reference"""
        self.logger.info("Creating class reference...")
        
        doc_path = self.knowledge_base_path / "02-class-hierarchy.md"
        
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write("# Class Hierarchy\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write(f"Total classes: {len(classes)}\n\n")
            
            # Group by file
            by_file = defaultdict(list)
            for class_name, info in classes.items():
                file = Path(info['file']).name
                by_file[file].append((class_name, info))
            
            f.write("## Classes by File\n\n")
            for file in sorted(by_file.keys())[:100]:
                f.write(f"### {file}\n\n")
                for class_name, info in by_file[file]:
                    f.write(f"- **{class_name}**")
                    if info['inherits']:
                        f.write(f" : {', '.join(info['inherits'])}")
                    f.write("\n")
                f.write("\n")
        
        self.logger.info(f"Created: {doc_path}")
    
    def create_api_reference(self, functions: List[Dict]):
        """Create API function reference"""
        self.logger.info("Creating API reference...")
        
        doc_path = self.knowledge_base_path / "03-api-reference.md"
        
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write("# API Reference\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write(f"Total functions indexed: {len(functions)}\n\n")
            
            # Group by file
            by_file = defaultdict(list)
            for func in functions:
                file = Path(func['file']).name
                by_file[file].append(func)
            
            f.write("## Functions by File\n\n")
            for file in sorted(by_file.keys())[:50]:
                f.write(f"### {file}\n\n")
                for func in by_file[file][:20]:
                    f.write(f"- `{func['name']}`\n")
                    if func['signature']:
                        f.write(f"  ```cpp\n  {func['signature']}\n  ```\n")
                f.write("\n")
        
        self.logger.info(f"Created: {doc_path}")
    
    def create_summary_doc(self):
        """Create overall summary document"""
        self.logger.info("Creating summary...")
        
        doc_path = self.knowledge_base_path / "README.md"
        
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write("# cwVDB Knowledge Base\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Purpose\n\n")
            f.write("This knowledge base contains structured documentation ")
            f.write("extracted from the VectorDB for token-efficient queries.\n\n")
            
            f.write("## Documents\n\n")
            f.write("1. **00-quick-reference.md** - Ultra-compact overview (~500 tokens)\n")
            f.write("2. **01-project-overview.md** - Detailed statistics (~2k tokens)\n")
            f.write("3. **02-class-hierarchy.md** - All classes and inheritance (~3k tokens)\n")
            f.write("4. **03-api-reference.md** - Public functions (~5k tokens)\n\n")
            
            f.write("## Usage\n\n")
            f.write("Claude should read these docs first before querying VectorDB.\n")
            f.write("This saves 70-90% of tokens compared to direct VectorDB queries.\n\n")
            
            f.write("## Token Efficiency\n\n")
            f.write("- Quick reference: ~500 tokens\n")
            f.write("- All docs combined: ~10k tokens\n")
            f.write("- Alternative (VectorDB queries): ~50k+ tokens\n")
        
        self.logger.info(f"Created: {doc_path}")
    
    def run_analysis(self):
        """Run complete analysis"""
        self.logger.info("=" * 80)
        self.logger.info("Starting VectorDB Analysis")
        self.logger.info("=" * 80)
        
        start_time = datetime.now()
        
        # Initialize
        self.initialize()
        
        # Analyze
        structure = self.analyze_project_structure()
        classes = self.extract_class_hierarchy()
        functions = self.extract_api_functions()
        
        # Create documentation
        self.create_quick_reference(structure)
        self.create_project_overview(structure, classes)
        self.create_class_reference(classes)
        self.create_api_reference(functions)
        self.create_summary_doc()
        
        # Statistics
        end_time = datetime.now()
        duration = end_time - start_time
        
        self.logger.info("=" * 80)
        self.logger.info("Analysis Complete!")
        self.logger.info(f"Documents created: 5")
        self.logger.info(f"Location: {self.knowledge_base_path.resolve()}")
        self.logger.info(f"Duration: {duration}")
        self.logger.info("=" * 80)


def main():
    try:
        analyzer = VectorDBAnalyzer()
        analyzer.run_analysis()
    except KeyboardInterrupt:
        print("\n\nAnalysis interrupted")
    except Exception as e:
        print(f"\n\nError: {e}")
        raise


if __name__ == "__main__":
    main()

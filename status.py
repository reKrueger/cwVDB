#!/usr/bin/env python3
"""
Status script to show cwVDB database statistics
"""

import json
from pathlib import Path
from datetime import datetime
import chromadb
from chromadb.config import Settings


def format_size(bytes):
    """Format bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024.0:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.2f} TB"

def get_directory_size(path):
    """Get total size of directory"""
    total = 0
    try:
        for item in Path(path).rglob('*'):
            if item.is_file():
                total += item.stat().st_size
    except:
        pass
    return total

def main():
    print("\n" + "=" * 80)
    print("cwVDB Database Status")
    print("=" * 80 + "\n")
    
    # Load config
    try:
        with open('config.json') as f:
            config = json.load(f)
    except Exception as e:
        print(f"ERROR: Cannot load config.json: {e}")
        return
    
    # Check source path
    print("[Source Path]")
    source_path = Path(config['source_path'])
    if source_path.exists():
        print(f"  Path: {source_path}")
        print(f"  Status: OK")
    else:
        print(f"  Path: {source_path}")
        print(f"  Status: NOT FOUND")
    print()
    
    # Check vector database
    print("[Vector Database]")
    vectordb_path = Path(config['vectordb_path'])
    
    if not vectordb_path.exists():
        print(f"  Status: NOT INITIALIZED")
        print(f"  Run: python indexer.py --initial")
        print()
        return
    
    try:
        client = chromadb.PersistentClient(
            path=config['vectordb_path'],
            settings=Settings(anonymized_telemetry=False)
        )
        
        collection = client.get_collection(name="cadlib_code")
        doc_count = collection.count()
        
        db_size = get_directory_size(vectordb_path)
        
        print(f"  Status: ACTIVE")
        print(f"  Location: {vectordb_path.resolve()}")
        print(f"  Documents: {doc_count:,}")
        print(f"  Size: {format_size(db_size)}")
        
    except Exception as e:
        print(f"  Status: ERROR")
        print(f"  Error: {e}")
    
    print()
    
    # Check logs
    print("[Logs]")
    logs_path = Path(config['logs_path'])
    if logs_path.exists():
        log_files = list(logs_path.glob('*.log'))
        if log_files:
            latest_log = max(log_files, key=lambda x: x.stat().st_mtime)
            modified = datetime.fromtimestamp(latest_log.stat().st_mtime)
            print(f"  Total logs: {len(log_files)}")
            print(f"  Latest: {latest_log.name}")
            print(f"  Modified: {modified.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print(f"  No logs found")
    else:
        print(f"  Directory not found")
    print()
    
    # Check checkpoints
    print("[Checkpoints]")
    checkpoint_path = Path(config['checkpoint_path'])
    if checkpoint_path.exists():
        checkpoints = list(checkpoint_path.glob('*.pkl'))
        if checkpoints:
            latest_cp = max(checkpoints, key=lambda x: x.stat().st_mtime)
            modified = datetime.fromtimestamp(latest_cp.stat().st_mtime)
            
            # Try to load checkpoint info
            try:
                import pickle
                with open(latest_cp, 'rb') as f:
                    cp_data = pickle.load(f)
                
                print(f"  Status: CHECKPOINT FOUND")
                print(f"  Files processed: {cp_data.get('processed_files', 'unknown')}")
                print(f"  Chunks created: {cp_data.get('total_chunks', 'unknown')}")
                print(f"  Timestamp: {modified.strftime('%Y-%m-%d %H:%M:%S')}")
            except:
                print(f"  Status: CHECKPOINT FOUND")
                print(f"  File: {latest_cp.name}")
        else:
            print(f"  Status: No checkpoints")
    else:
        print(f"  Directory not found")
    print()
    
    # Configuration summary
    print("[Configuration]")
    print(f"  Embedding model: {config['embedding_model']}")
    print(f"  Chunk size: {config['chunk_size']} lines")
    print(f"  Chunk overlap: {config['chunk_overlap']} lines")
    print(f"  Max workers: {config['max_workers']}")
    print(f"  Batch size: {config['batch_size']}")
    print()
    
    # File filters
    print("[File Filters]")
    print(f"  Extensions: {', '.join(config['file_extensions'])}")
    print(f"  Excluded dirs: {len(config['exclude_dirs'])} directories")
    print(f"  Excluded patterns: {len(config['exclude_patterns'])} patterns")
    print()
    
    print("=" * 80)
    
    if vectordb_path.exists():
        print("\nDatabase is ready for queries!")
        print("Try: python query.py --interactive")
    else:
        print("\nDatabase not initialized!")
        print("Run: python indexer.py --initial")
    
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()

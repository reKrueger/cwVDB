#!/usr/bin/env python3
"""
Test script to verify cwVDB installation and configuration
"""

import sys
import json
from pathlib import Path

def test_python_version():
    """Test Python version"""
    print("[1/7] Testing Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"    OK - Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"    ERROR - Python {version.major}.{version.minor} (requires 3.8+)")
        return False

def test_dependencies():
    """Test required dependencies"""
    print("[2/7] Testing dependencies...")
    required = [
        'chromadb',
        'sentence_transformers',
        'langchain',
        'git',
        'tqdm',
        'flask',
        'flask_cors'
    ]
    
    missing = []
    for module in required:
        try:
            __import__(module)
            print(f"    OK - {module}")
        except ImportError:
            print(f"    MISSING - {module}")
            missing.append(module)
    
    if missing:
        print(f"\n    ERROR - Missing: {', '.join(missing)}")
        print("    Run: pip install -r requirements.txt")
        return False
    return True

def test_config():
    """Test config.json"""
    print("[3/7] Testing config.json...")
    config_path = Path("config.json")
    
    if not config_path.exists():
        print("    ERROR - config.json not found")
        return False
    
    try:
        with open(config_path) as f:
            config = json.load(f)
        
        required_keys = [
            'source_path',
            'vectordb_path',
            'embedding_model',
            'chunk_size'
        ]
        
        for key in required_keys:
            if key not in config:
                print(f"    ERROR - Missing key: {key}")
                return False
        
        print("    OK - config.json valid")
        return True
        
    except Exception as e:
        print(f"    ERROR - {e}")
        return False

def test_source_path():
    """Test source path exists"""
    print("[4/7] Testing source path...")
    
    try:
        with open("config.json") as f:
            config = json.load(f)
        
        source_path = Path(config['source_path'])
        
        if source_path.exists():
            print(f"    OK - {source_path}")
            return True
        else:
            print(f"    WARNING - Path not found: {source_path}")
            print("    Note: Update config.json with correct path")
            return True  # Not critical for testing
            
    except Exception as e:
        print(f"    ERROR - {e}")
        return False

def test_directories():
    """Test required directories"""
    print("[5/7] Testing directories...")
    
    dirs = ['logs', 'checkpoints']
    all_ok = True
    
    for dir_name in dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"    OK - {dir_name}/")
        else:
            print(f"    Creating - {dir_name}/")
            dir_path.mkdir(exist_ok=True)
    
    return True

def test_embedding_model():
    """Test embedding model can be loaded"""
    print("[6/7] Testing embedding model...")
    
    try:
        from sentence_transformers import SentenceTransformer
        
        with open("config.json") as f:
            config = json.load(f)
        
        model_name = config['embedding_model']
        print(f"    Loading model: {model_name}")
        print("    This may take a moment on first run...")
        
        model = SentenceTransformer(model_name)
        
        test_text = "Hello world"
        embedding = model.encode([test_text])
        
        print(f"    OK - Model loaded (embedding size: {len(embedding[0])})")
        return True
        
    except Exception as e:
        print(f"    ERROR - {e}")
        return False

def test_chromadb():
    """Test ChromaDB can be initialized"""
    print("[7/7] Testing ChromaDB...")
    
    try:
        import chromadb
        from chromadb.config import Settings
        import time
        
        test_path = Path("./test_vectordb")
        
        # Clean up old test database if exists
        if test_path.exists():
            import shutil
            try:
                shutil.rmtree(test_path)
            except Exception:
                # File might be locked, use alternative path
                test_path = Path(f"./test_vectordb_{int(time.time())}")
        
        test_path.mkdir(exist_ok=True)
        
        client = chromadb.PersistentClient(
            path=str(test_path),
            settings=Settings(anonymized_telemetry=False)
        )
        
        collection = client.get_or_create_collection(name="test")
        collection.add(
            ids=["test1"],
            documents=["test document"],
            embeddings=[[0.1] * 384]
        )
        
        # Verify
        result = collection.get(ids=["test1"])
        assert len(result['documents']) == 1
        
        # Cleanup
        del collection
        del client
        time.sleep(0.5)
        
        import shutil
        try:
            shutil.rmtree(test_path)
        except Exception:
            print("    WARNING - Test database cleanup deferred (file locked)")
        
        print("    OK - ChromaDB working")
        return True
        
    except Exception as e:
        print(f"    ERROR - {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "=" * 60)
    print("cwVDB Installation Test")
    print("=" * 60 + "\n")
    
    tests = [
        test_python_version,
        test_dependencies,
        test_config,
        test_source_path,
        test_directories,
        test_embedding_model,
        test_chromadb
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"    CRITICAL ERROR - {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
        print()
    
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"SUCCESS - All tests passed ({passed}/{total})")
        print("\nYou can now run:")
        print("  python indexer.py --initial")
    else:
        print(f"FAILED - {total - passed} test(s) failed ({passed}/{total})")
        print("\nPlease fix the errors above before proceeding")
    
    print("=" * 60 + "\n")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

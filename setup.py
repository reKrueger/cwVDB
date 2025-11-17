#!/usr/bin/env python3
"""
cwVDB Setup Script
Handles installation, verification, and initialization of the vector database system.

Usage:
    python setup.py --install      Install dependencies
    python setup.py --test         Run tests only
    python setup.py --full         Full setup (install + test + init directories)
    python setup.py --help         Show this help
"""

import sys
import json
import subprocess
import argparse
from pathlib import Path
from typing import List, Tuple


class SetupManager:
    """Manages the setup and testing of cwVDB"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.results: List[Tuple[str, bool]] = []
        
    def print_header(self, title: str):
        """Print section header"""
        print("\n" + "=" * 70)
        print(f"  {title}")
        print("=" * 70 + "\n")
    
    def print_result(self, step: str, success: bool):
        """Print step result"""
        symbol = "✓" if success else "✗"
        status = "OK" if success else "FAILED"
        print(f"  {symbol} {step}: {status}")
        self.results.append((step, success))
    
    # ============================================================================
    # Installation
    # ============================================================================
    
    def install_dependencies(self) -> bool:
        """Install Python dependencies from requirements.txt"""
        self.print_header("Installing Dependencies")
        
        requirements_file = self.project_root / "requirements.txt"
        
        if not requirements_file.exists():
            print("ERROR: requirements.txt not found")
            return False
        
        try:
            print("Installing packages from requirements.txt...")
            print("This may take several minutes on first run...\n")
            
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✓ All dependencies installed successfully")
                return True
            else:
                print(f"ERROR: Installation failed")
                print(result.stderr)
                return False
                
        except Exception as e:
            print(f"ERROR: {e}")
            return False
    
    # ============================================================================
    # Directory Setup
    # ============================================================================
    
    def create_directories(self) -> bool:
        """Create required directories"""
        self.print_header("Creating Directories")
        
        dirs = [
            "logs",
            "checkpoints",
            "src",
            "tests",
            "scripts",
            "docs"
        ]
        
        all_success = True
        for dir_name in dirs:
            dir_path = self.project_root / dir_name
            try:
                dir_path.mkdir(exist_ok=True)
                print(f"  ✓ {dir_name}/")
            except Exception as e:
                print(f"  ✗ {dir_name}/ - {e}")
                all_success = False
        
        return all_success
    
    # ============================================================================
    # Testing
    # ============================================================================
    
    def test_python_version(self) -> bool:
        """Test Python version"""
        print("[1/7] Testing Python version...")
        version = sys.version_info
        if version.major >= 3 and version.minor >= 8:
            print(f"      ✓ Python {version.major}.{version.minor}.{version.micro}")
            return True
        else:
            print(f"      ✗ Python {version.major}.{version.minor} (requires 3.8+)")
            return False
    
    def test_dependencies(self) -> bool:
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
            except ImportError:
                missing.append(module)
        
        if missing:
            print(f"      ✗ Missing: {', '.join(missing)}")
            print("      Run: python setup.py --install")
            return False
        
        print(f"      ✓ All {len(required)} packages available")
        return True
    
    def test_config(self) -> bool:
        """Test config.json"""
        print("[3/7] Testing config.json...")
        config_path = self.project_root / "config.json"
        
        if not config_path.exists():
            print("      ✗ config.json not found")
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
                    print(f"      ✗ Missing key: {key}")
                    return False
            
            print("      ✓ config.json valid")
            return True
            
        except Exception as e:
            print(f"      ✗ {e}")
            return False
    
    def test_source_path(self) -> bool:
        """Test source path exists"""
        print("[4/7] Testing source path...")
        
        try:
            config_path = self.project_root / "config.json"
            with open(config_path) as f:
                config = json.load(f)
            
            source_path = Path(config['source_path'])
            
            if source_path.exists():
                print(f"      ✓ {source_path}")
                return True
            else:
                print(f"      ⚠ Path not found: {source_path}")
                print("      Note: Update config.json with correct path before indexing")
                return True  # Not critical for setup
                
        except Exception as e:
            print(f"      ✗ {e}")
            return False
    
    def test_directories(self) -> bool:
        """Test required directories"""
        print("[5/7] Testing directories...")
        
        dirs = ['logs', 'checkpoints', 'src', 'tests', 'scripts', 'docs']
        all_ok = True
        
        for dir_name in dirs:
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                pass  # OK
            else:
                print(f"      ⚠ Creating {dir_name}/")
                dir_path.mkdir(exist_ok=True)
        
        print("      ✓ All directories present")
        return True
    
    def test_embedding_model(self) -> bool:
        """Test embedding model can be loaded"""
        print("[6/7] Testing embedding model...")
        
        try:
            from sentence_transformers import SentenceTransformer
            
            config_path = self.project_root / "config.json"
            with open(config_path) as f:
                config = json.load(f)
            
            model_name = config['embedding_model']
            print(f"      Loading model: {model_name}")
            print("      This may take a moment on first run...")
            
            model = SentenceTransformer(model_name)
            
            test_text = "Hello world"
            embedding = model.encode([test_text])
            
            print(f"      ✓ Model loaded (dimension: {len(embedding[0])})")
            return True
            
        except Exception as e:
            print(f"      ✗ {e}")
            return False
    
    def test_chromadb(self) -> bool:
        """Test ChromaDB can be initialized"""
        print("[7/7] Testing ChromaDB...")
        
        try:
            import chromadb
            from chromadb.config import Settings
            import time
            import shutil
            
            test_path = self.project_root / "test_vectordb"
            
            # Clean up old test database if exists
            if test_path.exists():
                try:
                    shutil.rmtree(test_path)
                except Exception:
                    test_path = self.project_root / f"test_vectordb_{int(time.time())}"
            
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
            
            result = collection.get(ids=["test1"])
            assert len(result['documents']) == 1
            
            # Cleanup
            del collection
            del client
            time.sleep(0.5)
            
            try:
                shutil.rmtree(test_path)
            except Exception:
                pass
            
            print("      ✓ ChromaDB working")
            return True
            
        except Exception as e:
            print(f"      ✗ {e}")
            return False
    
    def run_tests(self) -> bool:
        """Run all tests"""
        self.print_header("Running Tests")
        
        tests = [
            self.test_python_version,
            self.test_dependencies,
            self.test_config,
            self.test_source_path,
            self.test_directories,
            self.test_embedding_model,
            self.test_chromadb
        ]
        
        results = []
        for test in tests:
            try:
                result = test()
                results.append(result)
            except Exception as e:
                print(f"      CRITICAL ERROR: {e}")
                results.append(False)
        
        print()
        passed = sum(results)
        total = len(results)
        
        if passed == total:
            print(f"✓ All tests passed ({passed}/{total})")
            return True
        else:
            print(f"✗ {total - passed} test(s) failed ({passed}/{total})")
            return False
    
    # ============================================================================
    # Main Setup Flow
    # ============================================================================
    
    def run_full_setup(self) -> bool:
        """Run complete setup process"""
        self.print_header("cwVDB Setup - Full Installation")
        
        # Step 1: Create directories
        if not self.create_directories():
            print("\n✗ Directory creation failed")
            return False
        
        # Step 2: Install dependencies
        if not self.install_dependencies():
            print("\n✗ Installation failed")
            return False
        
        # Step 3: Run tests
        if not self.run_tests():
            print("\n✗ Tests failed")
            return False
        
        self.print_header("Setup Complete!")
        print("✓ Installation successful")
        print("✓ All tests passed")
        print("\nNext steps:")
        print("  1. Edit config.json with your source path")
        print("  2. Run: python start.py indexer --initial")
        print("  3. Run: python start.py api")
        
        return True
    
    def show_status(self):
        """Show setup status"""
        self.print_header("cwVDB Setup Status")
        
        # Check directories
        print("Directories:")
        dirs = ['src', 'tests', 'scripts', 'docs', 'logs', 'checkpoints']
        for d in dirs:
            exists = (self.project_root / d).exists()
            symbol = "✓" if exists else "✗"
            print(f"  {symbol} {d}/")
        
        # Check config
        print("\nConfiguration:")
        config_exists = (self.project_root / "config.json").exists()
        symbol = "✓" if config_exists else "✗"
        print(f"  {symbol} config.json")
        
        # Check dependencies
        print("\nDependencies:")
        try:
            import chromadb
            print("  ✓ chromadb")
        except:
            print("  ✗ chromadb (run: python setup.py --install)")
        
        print()


def main():
    parser = argparse.ArgumentParser(
        description="cwVDB Setup Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python setup.py --install          Install dependencies only
  python setup.py --test             Run tests only
  python setup.py --full             Full setup (recommended)
  python setup.py --status           Show setup status
        """
    )
    
    parser.add_argument('--install', action='store_true', help='Install dependencies')
    parser.add_argument('--test', action='store_true', help='Run tests')
    parser.add_argument('--full', action='store_true', help='Full setup (install + test)')
    parser.add_argument('--status', action='store_true', help='Show setup status')
    
    args = parser.parse_args()
    
    manager = SetupManager()
    
    # If no arguments, show help
    if not any(vars(args).values()):
        parser.print_help()
        return 0
    
    try:
        if args.status:
            manager.show_status()
            return 0
        
        if args.full:
            success = manager.run_full_setup()
            return 0 if success else 1
        
        if args.install:
            success = manager.install_dependencies()
            return 0 if success else 1
        
        if args.test:
            success = manager.run_tests()
            return 0 if success else 1
            
    except KeyboardInterrupt:
        print("\n\nSetup interrupted by user")
        return 1
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

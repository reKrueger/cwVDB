#!/usr/bin/env python3
"""
API Test Script - Test the cwVDB REST API endpoints
"""

import requests
import json
import sys
import time


API_URL = "http://localhost:8000"


def print_section(title):
    """Print a section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def test_health():
    """Test health endpoint"""
    print_section("Testing /health endpoint")
    
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"Status: {data.get('status', 'unknown')}")
            print(f"Documents: {data.get('documents', 0):,}")
            print(f"Timestamp: {data.get('timestamp', 'unknown')}")
            return True
        else:
            print(f"ERROR: Status code {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to API server")
        print(f"Make sure the API is running on {API_URL}")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False


def test_stats():
    """Test stats endpoint"""
    print_section("Testing /stats endpoint")
    
    try:
        response = requests.get(f"{API_URL}/stats", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"Total documents: {data.get('total_documents', 0):,}")
            print(f"Collection: {data.get('collection_name', 'unknown')}")
            print(f"Model: {data.get('embedding_model', 'unknown')}")
            print(f"Metadata fields: {', '.join(data.get('sample_metadata_fields', []))}")
            return True
        else:
            print(f"ERROR: Status code {response.status_code}")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False


def test_search():
    """Test search endpoint"""
    print_section("Testing /search endpoint")
    
    test_query = "class definition with members"
    
    try:
        payload = {
            "query": test_query,
            "n_results": 3
        }
        
        print(f"Query: {test_query}")
        print("Searching...")
        
        response = requests.post(
            f"{API_URL}/search",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nFound {data.get('count', 0)} results\n")
            
            for i, result in enumerate(data.get('results', [])[:3], 1):
                print(f"[{i}] Similarity: {result['similarity']:.3f}")
                print(f"    File: {result['metadata'].get('file_path', 'unknown')}")
                print(f"    Type: {result['metadata'].get('chunk_type', 'unknown')}")
                print(f"    Lines: {result['metadata'].get('start_line', 0)}-{result['metadata'].get('end_line', 0)}")
                
                content = result['document']
                if len(content) > 200:
                    content = content[:200] + "..."
                print(f"    Preview: {content[:100]}...")
                print()
            
            return True
        else:
            print(f"ERROR: Status code {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False


def test_find():
    """Test find endpoint"""
    print_section("Testing /find endpoint")
    
    test_symbol = "CreateElement"
    
    try:
        payload = {
            "symbol": test_symbol,
            "n_results": 2
        }
        
        print(f"Symbol: {test_symbol}")
        print("Searching for implementations...")
        
        response = requests.post(
            f"{API_URL}/find",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nFound {data.get('count', 0)} implementations\n")
            
            for i, result in enumerate(data.get('results', [])[:2], 1):
                print(f"[{i}] Similarity: {result['similarity']:.3f}")
                print(f"    File: {result['metadata'].get('file_path', 'unknown')}")
                print()
            
            return True
        else:
            print(f"ERROR: Status code {response.status_code}")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False


def main():
    """Main test function"""
    print("\n" + "=" * 80)
    print("  cwVDB REST API Test Suite")
    print("=" * 80)
    print(f"\nTesting API at: {API_URL}")
    print("Make sure the API server is running (start_api.bat)")
    print()
    
    input("Press Enter to start tests...")
    
    results = []
    
    # Test health
    results.append(("Health Check", test_health()))
    time.sleep(1)
    
    # Test stats
    results.append(("Statistics", test_stats()))
    time.sleep(1)
    
    # Test search
    results.append(("Search", test_search()))
    time.sleep(1)
    
    # Test find
    results.append(("Find Implementations", test_find()))
    
    # Print summary
    print_section("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\nAll tests passed! API is working correctly.")
        return 0
    else:
        print(f"\n{total - passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

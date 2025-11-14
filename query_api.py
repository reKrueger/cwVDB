#!/usr/bin/env python3
"""
cwVDB REST API - REST API for querying the vector database
Provides endpoints for semantic code search with JSON responses
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from flask import Flask, request, jsonify
from flask_cors import CORS
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer


app = Flask(__name__)
CORS(app)

# Global variables
config = None
logger = None
embedding_model = None
vectordb = None
collection = None


def load_config(config_path: str = "config.json") -> Dict:
    """Load configuration from JSON file"""
    with open(config_path, 'r') as f:
        return json.load(f)


def setup_logging() -> logging.Logger:
    """Setup logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


def initialize_service():
    """Initialize query service components"""
    global config, logger, embedding_model, vectordb, collection
    
    logger = setup_logging()
    logger.info("Initializing cwVDB REST API...")
    
    config = load_config()
    
    # Load embedding model
    logger.info(f"Loading embedding model: {config['embedding_model']}")
    embedding_model = SentenceTransformer(config['embedding_model'])
    
    # Connect to ChromaDB
    logger.info(f"Connecting to ChromaDB at: {config['vectordb_path']}")
    vectordb = chromadb.PersistentClient(
        path=config['vectordb_path'],
        settings=Settings(anonymized_telemetry=False)
    )
    
    # Get collection
    try:
        collection = vectordb.get_collection(name="cadlib_code")
        doc_count = collection.count()
        logger.info(f"Connected to collection with {doc_count:,} documents")
    except Exception as e:
        logger.error(f"Failed to connect to collection: {e}")
        raise


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        doc_count = collection.count() if collection else 0
        return jsonify({
            'status': 'healthy',
            'documents': doc_count,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/search', methods=['POST'])
def search():
    """
    Search for code snippets
    
    Request body:
    {
        "query": "string",
        "n_results": int (optional, default: 10),
        "file_filter": "string" (optional),
        "chunk_type": "string" (optional)
    }
    
    Response:
    {
        "results": [
            {
                "document": "string",
                "similarity": float,
                "metadata": {
                    "file_path": "string",
                    "chunk_type": "string",
                    "start_line": int,
                    "end_line": int
                }
            }
        ],
        "query": "string",
        "count": int,
        "timestamp": "string"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({'error': 'Missing query parameter'}), 400
        
        query = data['query']
        n_results = data.get('n_results', 10)
        file_filter = data.get('file_filter')
        chunk_type = data.get('chunk_type')
        
        logger.info(f"Search request: {query}")
        
        # Generate query embedding
        query_embedding = embedding_model.encode([query])[0].tolist()
        
        # Build where filter
        where_filter = {}
        if file_filter:
            where_filter['file_path'] = {'$contains': file_filter}
        if chunk_type:
            where_filter['chunk_type'] = chunk_type
        
        # Query vector database
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter if where_filter else None
        )
        
        # Format results
        search_results = []
        for i in range(len(results['documents'][0])):
            result = {
                'document': results['documents'][0][i],
                'similarity': 1 - results['distances'][0][i],
                'metadata': results['metadatas'][0][i]
            }
            search_results.append(result)
        
        response = {
            'results': search_results,
            'query': query,
            'count': len(search_results),
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Found {len(search_results)} results")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/find', methods=['POST'])
def find_implementations():
    """
    Find implementations of a class or function
    
    Request body:
    {
        "symbol": "string",
        "n_results": int (optional, default: 10)
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'symbol' not in data:
            return jsonify({'error': 'Missing symbol parameter'}), 400
        
        symbol = data['symbol']
        n_results = data.get('n_results', 10)
        
        logger.info(f"Find implementations: {symbol}")
        
        query = f"class or function named {symbol} implementation"
        query_embedding = embedding_model.encode([query])[0].tolist()
        
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where={'chunk_type': 'function'}
        )
        
        search_results = []
        for i in range(len(results['documents'][0])):
            result = {
                'document': results['documents'][0][i],
                'similarity': 1 - results['distances'][0][i],
                'metadata': results['metadatas'][0][i]
            }
            search_results.append(result)
        
        response = {
            'results': search_results,
            'symbol': symbol,
            'count': len(search_results),
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Find error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/usage', methods=['POST'])
def find_usages():
    """
    Find usages of a symbol
    
    Request body:
    {
        "symbol": "string",
        "n_results": int (optional, default: 10)
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'symbol' not in data:
            return jsonify({'error': 'Missing symbol parameter'}), 400
        
        symbol = data['symbol']
        n_results = data.get('n_results', 10)
        
        logger.info(f"Find usages: {symbol}")
        
        query = f"code using or calling {symbol}"
        query_embedding = embedding_model.encode([query])[0].tolist()
        
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        search_results = []
        for i in range(len(results['documents'][0])):
            result = {
                'document': results['documents'][0][i],
                'similarity': 1 - results['distances'][0][i],
                'metadata': results['metadatas'][0][i]
            }
            search_results.append(result)
        
        response = {
            'results': search_results,
            'symbol': symbol,
            'count': len(search_results),
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Usage error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/file', methods=['POST'])
def file_overview():
    """
    Get overview of a specific file
    
    Request body:
    {
        "file_path": "string",
        "n_results": int (optional, default: 5)
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'file_path' not in data:
            return jsonify({'error': 'Missing file_path parameter'}), 400
        
        file_path = data['file_path']
        n_results = data.get('n_results', 5)
        
        logger.info(f"File overview: {file_path}")
        
        query = "file overview header includes"
        query_embedding = embedding_model.encode([query])[0].tolist()
        
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where={
                'file_path': {'$contains': file_path},
                'chunk_type': 'file_header'
            }
        )
        
        search_results = []
        for i in range(len(results['documents'][0])):
            result = {
                'document': results['documents'][0][i],
                'similarity': 1 - results['distances'][0][i],
                'metadata': results['metadatas'][0][i]
            }
            search_results.append(result)
        
        response = {
            'results': search_results,
            'file_path': file_path,
            'count': len(search_results),
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"File overview error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/similar', methods=['POST'])
def find_similar_code():
    """
    Find code similar to given snippet
    
    Request body:
    {
        "code": "string",
        "n_results": int (optional, default: 5)
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'code' not in data:
            return jsonify({'error': 'Missing code parameter'}), 400
        
        code = data['code']
        n_results = data.get('n_results', 5)
        
        logger.info(f"Find similar code: {len(code)} characters")
        
        query_embedding = embedding_model.encode([code])[0].tolist()
        
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        search_results = []
        for i in range(len(results['documents'][0])):
            result = {
                'document': results['documents'][0][i],
                'similarity': 1 - results['distances'][0][i],
                'metadata': results['metadatas'][0][i]
            }
            search_results.append(result)
        
        response = {
            'results': search_results,
            'count': len(search_results),
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Similar code error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/stats', methods=['GET'])
def database_stats():
    """Get database statistics"""
    try:
        doc_count = collection.count()
        
        # Get sample metadata to show available fields
        sample_results = collection.get(limit=1)
        sample_metadata = sample_results['metadatas'][0] if sample_results['metadatas'] else {}
        
        stats = {
            'total_documents': doc_count,
            'collection_name': 'cadlib_code',
            'embedding_model': config['embedding_model'],
            'sample_metadata_fields': list(sample_metadata.keys()),
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return jsonify({'error': str(e)}), 500


@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='cwVDB REST API - Query service for cadlib codebase',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python query_api.py --port 8000
  python query_api.py --host 0.0.0.0 --port 8000
  python query_api.py --debug

Test with curl:
  curl -X POST http://localhost:8000/search -H "Content-Type: application/json" -d '{"query": "VBA element creation"}'
  curl http://localhost:8000/health
  curl http://localhost:8000/stats
        """
    )
    
    parser.add_argument('--host', default='127.0.0.1',
                       help='Host to bind to (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=8000,
                       help='Port to bind to (default: 8000)')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug mode')
    parser.add_argument('--config', default='config.json',
                       help='Path to config file')
    
    args = parser.parse_args()
    
    try:
        # Initialize service
        initialize_service()
        
        # Print startup info
        print("\n" + "=" * 80)
        print("cwVDB REST API Starting")
        print("=" * 80)
        print(f"\nHost: {args.host}")
        print(f"Port: {args.port}")
        print(f"Debug: {args.debug}")
        print(f"\nEndpoints:")
        print(f"  GET  /health          - Health check")
        print(f"  GET  /stats           - Database statistics")
        print(f"  POST /search          - Search for code")
        print(f"  POST /find            - Find implementations")
        print(f"  POST /usage           - Find usages")
        print(f"  POST /file            - File overview")
        print(f"  POST /similar         - Find similar code")
        print(f"\nExample:")
        print(f'  curl -X POST http://{args.host}:{args.port}/search \\')
        print(f'       -H "Content-Type: application/json" \\')
        print(f'       -d \'{{"query": "VBA element creation"}}\'')
        print("\n" + "=" * 80 + "\n")
        
        # Start server
        app.run(host=args.host, port=args.port, debug=args.debug)
        
    except Exception as e:
        print(f"\nError starting API: {e}")
        raise


if __name__ == "__main__":
    main()

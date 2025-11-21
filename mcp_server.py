#!/usr/bin/env python3
"""
cwVDB MCP Server
Model Context Protocol server for cwVDB integration with Claude Desktop.
Allows Claude to directly query the vector database.
"""

import asyncio
import json
import os
from typing import Any
import requests
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent


# Configuration
API_BASE_URL = os.getenv("CWVDB_API_URL", "http://127.0.0.1:8000")
CONFIG_PATH = os.getenv("CWVDB_CONFIG", "config.json")

# Initialize MCP server
app = Server("cwvdb")


def call_api(endpoint: str, data: dict = None) -> dict:
    """Call cwVDB REST API"""
    url = f"{API_BASE_URL}{endpoint}"
    try:
        if data:
            response = requests.post(url, json=data, timeout=30)
        else:
            response = requests.get(url, timeout=30)
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "success": False}


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools for Claude"""
    return [
        Tool(
            name="search_code",
            description="Search for code semantically in the vector database. "
                       "Use this to find code related to a concept, function, or feature. "
                       "Returns the most relevant code snippets with file paths and context.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language search query (e.g., 'API functions', 'error handling', 'main class')"
                    },
                    "n_results": {
                        "type": "integer",
                        "description": "Number of results to return (default: 5, max: 20)",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="find_implementation",
            description="Find the implementation of a specific function, class, or symbol. "
                       "Use this when you need to see how something is defined or implemented.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Symbol name (function, class, variable, etc.)"
                    },
                    "n_results": {
                        "type": "integer",
                        "description": "Number of results (default: 5)",
                        "default": 5
                    }
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="find_usages",
            description="Find all places where a symbol (function, class, variable) is used. "
                       "Useful for understanding dependencies and impact analysis.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Symbol to find usages of"
                    },
                    "n_results": {
                        "type": "integer",
                        "description": "Number of results (default: 10)",
                        "default": 10
                    }
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="get_file_overview",
            description="Get a complete overview of a specific file including all classes, "
                       "functions, and important code sections.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Relative or partial file path (e.g., 'main.cpp' or 'src/api/Manager.cpp')"
                    }
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="get_statistics",
            description="Get statistics about the code database (number of files, chunks, etc.)",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls from Claude"""
    
    try:
        if name == "search_code":
            query = arguments["query"]
            n_results = arguments.get("n_results", 5)
            
            result = call_api("/search", {
                "query": query,
                "n_results": min(n_results, 20)
            })
            
            if not result.get("error"):
                formatted = format_search_results(result["results"])
                return [TextContent(
                    type="text",
                    text=f"Found {result.get('count', 0)} results for '{query}':\n\n{formatted}"
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"Error searching: {result.get('error', 'Unknown error')}"
                )]
        
        elif name == "find_implementation":
            symbol = arguments["symbol"]
            n_results = arguments.get("n_results", 5)
            
            result = call_api("/find", {
                "symbol": symbol,
                "n_results": n_results
            })
            
            if not result.get("error"):
                formatted = format_search_results(result["results"])
                return [TextContent(
                    type="text",
                    text=f"Found {result.get('count', 0)} implementations of '{symbol}':\n\n{formatted}"
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"Error finding implementation: {result.get('error', 'Unknown error')}"
                )]
        
        elif name == "find_usages":
            symbol = arguments["symbol"]
            n_results = arguments.get("n_results", 10)
            
            result = call_api("/usage", {
                "symbol": symbol,
                "n_results": n_results
            })
            
            if not result.get("error"):
                formatted = format_search_results(result["results"])
                return [TextContent(
                    type="text",
                    text=f"Found {result.get('count', 0)} usages of '{symbol}':\n\n{formatted}"
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"Error finding usages: {result.get('error', 'Unknown error')}"
                )]
        
        elif name == "get_file_overview":
            file_path = arguments["file_path"]
            
            result = call_api("/file", {
                "file_path": file_path
            })
            
            if not result.get("error"):
                formatted = format_file_overview(result)
                return [TextContent(
                    type="text",
                    text=formatted
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"Error getting file overview: {result.get('error', 'Unknown error')}"
                )]
        
        elif name == "get_statistics":
            result = call_api("/stats")
            
            if not result.get("error"):
                formatted = f"""Database Statistics:
- Total Documents: {result.get('total_documents', 'N/A')}
- Collection Name: {result.get('collection_name', 'N/A')}
- Embedding Model: {result.get('embedding_model', 'N/A')}
- Metadata Fields: {', '.join(result.get('sample_metadata_fields', []))}
"""
                return [TextContent(
                    type="text",
                    text=formatted
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"Error getting statistics: {result.get('message', 'Unknown error')}"
                )]
        
        else:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]
    
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error executing tool '{name}': {str(e)}"
        )]


def format_search_results(results: list) -> str:
    """Format search results for Claude"""
    if not results:
        return "No results found."
    
    formatted = []
    for i, result in enumerate(results, 1):
        metadata = result.get("metadata", {})
        code = result.get("document", "")  # API returns 'document' not 'code'
        score = result.get("similarity", 0)  # API returns 'similarity' not 'score'
        
        formatted.append(f"""
{'='*80}
Result {i}/{len(results)} (Similarity: {score:.3f})
{'='*80}
File: {metadata.get('file_path', 'Unknown')}
Type: {metadata.get('chunk_type', 'Unknown')}
Lines: {metadata.get('start_line', '?')}-{metadata.get('end_line', '?')}
{'-'*80}
{code}
{'-'*80}
""")
    
    return "\n".join(formatted)


def format_file_overview(result: dict) -> str:
    """Format file overview for Claude"""
    file_path = result.get("file", "Unknown")
    chunks = result.get("chunks", [])
    
    formatted = [f"""
{'='*80}
File Overview: {file_path}
{'='*80}
Total Chunks: {len(chunks)}
"""]
    
    for i, chunk in enumerate(chunks, 1):
        metadata = chunk.get("metadata", {})
        code = chunk.get("document", "")  # API returns 'document' not 'code'
        
        formatted.append(f"""
{'-'*80}
Chunk {i}/{len(chunks)}
Type: {metadata.get('chunk_type', 'Unknown')}
Lines: {metadata.get('start_line', '?')}-{metadata.get('end_line', '?')}
{'-'*80}
{code}
""")
    
    return "\n".join(formatted)


async def main():
    """Run the MCP server"""
    # Check if API is available
    print(f"DEBUG: Checking API at {API_BASE_URL}...")
    try:
        health = call_api("/health")
        print(f"DEBUG: API Response: {health}")
        if health.get("status") == "healthy":
            print(f"SUCCESS: cwVDB API is responding!")
            print(f"DEBUG: Documents: {health.get('documents', 'unknown')}")
        else:
            print(f"WARNING: API returned unexpected status: {health.get('status')}")
            print(f"Full response: {health}")
            print("Server will continue but tools may not work...")
    except Exception as e:
        print(f"WARNING: Cannot connect to cwVDB API: {e}")
        print(f"Make sure API is running at {API_BASE_URL}")
        print("Server will continue but tools may not work...")
    
    # Run server
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())

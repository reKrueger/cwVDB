# cwVDB REST API Documentation

## Overview

The cwVDB REST API provides endpoints for semantic code search in the cadlib codebase. All endpoints return JSON responses.

**Base URL:** `http://localhost:8000`

---

## Endpoints

### 1. Health Check

**GET** `/health`

Check if the API is running and database is accessible.

**Response:**
```json
{
  "status": "healthy",
  "documents": 12345,
  "timestamp": "2025-01-15T10:30:00"
}
```

**cURL Example:**
```bash
curl http://localhost:8000/health
```

---

### 2. Database Statistics

**GET** `/stats`

Get statistics about the vector database.

**Response:**
```json
{
  "total_documents": 12345,
  "collection_name": "cadlib_code",
  "embedding_model": "all-MiniLM-L6-v2",
  "sample_metadata_fields": ["file_path", "chunk_type", "start_line", "end_line"],
  "timestamp": "2025-01-15T10:30:00"
}
```

**cURL Example:**
```bash
curl http://localhost:8000/stats
```

---

### 3. Search

**POST** `/search`

Search for code snippets using natural language queries.

**Request Body:**
```json
{
  "query": "string (required)",
  "n_results": 10 (optional, default: 10),
  "file_filter": "string (optional)",
  "chunk_type": "string (optional: file_header, function, code_block)"
}
```

**Response:**
```json
{
  "results": [
    {
      "document": "code snippet",
      "similarity": 0.85,
      "metadata": {
        "file_path": "C:\\source\\cadlib\\v_33.0\\module\\file.cpp",
        "chunk_type": "function",
        "start_line": 100,
        "end_line": 150
      }
    }
  ],
  "query": "original query",
  "count": 5,
  "timestamp": "2025-01-15T10:30:00"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "VBA element creation", "n_results": 5}'
```

**Python Example:**
```python
import requests

response = requests.post(
    "http://localhost:8000/search",
    json={
        "query": "VBA element creation",
        "n_results": 5,
        "file_filter": "VBA"  # optional
    }
)

data = response.json()
for result in data['results']:
    print(f"Similarity: {result['similarity']:.3f}")
    print(f"File: {result['metadata']['file_path']}")
    print(f"Code:\n{result['document'][:200]}...")
    print("-" * 80)
```

---

### 4. Find Implementations

**POST** `/find`

Find implementations of a specific class or function.

**Request Body:**
```json
{
  "symbol": "string (required)",
  "n_results": 10 (optional, default: 10)
}
```

**Response:**
```json
{
  "results": [
    {
      "document": "function implementation",
      "similarity": 0.90,
      "metadata": {
        "file_path": "...",
        "chunk_type": "function",
        "start_line": 50,
        "end_line": 100
      }
    }
  ],
  "symbol": "CreateElement",
  "count": 3,
  "timestamp": "2025-01-15T10:30:00"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/find \
  -H "Content-Type: application/json" \
  -d '{"symbol": "CreateElement", "n_results": 5}'
```

---

### 5. Find Usages

**POST** `/usage`

Find usages of a symbol (class, function, variable).

**Request Body:**
```json
{
  "symbol": "string (required)",
  "n_results": 10 (optional, default: 10)
}
```

**Response:**
```json
{
  "results": [
    {
      "document": "code using the symbol",
      "similarity": 0.88,
      "metadata": {
        "file_path": "...",
        "chunk_type": "code_block",
        "start_line": 200,
        "end_line": 220
      }
    }
  ],
  "symbol": "NestingEngine",
  "count": 8,
  "timestamp": "2025-01-15T10:30:00"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/usage \
  -H "Content-Type: application/json" \
  -d '{"symbol": "NestingEngine"}'
```

---

### 6. File Overview

**POST** `/file`

Get overview chunks for a specific file.

**Request Body:**
```json
{
  "file_path": "string (required, substring match)",
  "n_results": 5 (optional, default: 5)
}
```

**Response:**
```json
{
  "results": [
    {
      "document": "file header with includes",
      "similarity": 0.75,
      "metadata": {
        "file_path": "...",
        "chunk_type": "file_header",
        "start_line": 0,
        "end_line": 20
      }
    }
  ],
  "file_path": "Nesting.dll",
  "count": 2,
  "timestamp": "2025-01-15T10:30:00"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/file \
  -H "Content-Type: application/json" \
  -d '{"file_path": "Nesting.dll"}'
```

---

### 7. Find Similar Code

**POST** `/similar`

Find code similar to a given snippet.

**Request Body:**
```json
{
  "code": "string (required, C++ code snippet)",
  "n_results": 5 (optional, default: 5)
}
```

**Response:**
```json
{
  "results": [
    {
      "document": "similar code",
      "similarity": 0.92,
      "metadata": {
        "file_path": "...",
        "chunk_type": "function",
        "start_line": 300,
        "end_line": 350
      }
    }
  ],
  "count": 5,
  "timestamp": "2025-01-15T10:30:00"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/similar \
  -H "Content-Type: application/json" \
  -d '{"code": "void MyFunction() { return 42; }"}'
```

---

## Integration Examples

### Using with Claude

1. **Ask Claude a question:**
   ```
   "Wo werden VBA Elemente in cadlib erstellt?"
   ```

2. **Query the API:**
   ```bash
   curl -X POST http://localhost:8000/search \
     -H "Content-Type: application/json" \
     -d '{"query": "VBA element creation", "n_results": 3}'
   ```

3. **Share results with Claude:**
   ```
   Hier sind die relevanten Code-Stellen:
   
   [Result 1 - Similarity 0.89]
   File: C:\source\cadlib\v_33.0\vba\VBAElementFactory.cpp
   Lines: 120-180
   
   Code:
   [paste code snippet]
   ```

4. **Get Claude's analysis:**
   ```
   Claude: "Basierend auf dem Code sehe ich, dass VBA Elemente
   in der VBAElementFactory Klasse erstellt werden. Die
   CreateElement() Methode..."
   ```

---

### Python Script Example

```python
#!/usr/bin/env python3
"""
Query cadlib codebase and format for Claude
"""

import requests
import json


def query_cadlib(question):
    """Query cwVDB API"""
    response = requests.post(
        "http://localhost:8000/search",
        json={"query": question, "n_results": 3}
    )
    return response.json()


def format_for_claude(results):
    """Format results for Claude"""
    output = []
    
    for i, result in enumerate(results['results'], 1):
        output.append(f"\n[Result {i} - Similarity {result['similarity']:.2f}]")
        output.append(f"File: {result['metadata']['file_path']}")
        output.append(f"Lines: {result['metadata']['start_line']}-{result['metadata']['end_line']}")
        output.append(f"Type: {result['metadata']['chunk_type']}")
        output.append("\nCode:")
        output.append(result['document'])
        output.append("-" * 80)
    
    return "\n".join(output)


# Example usage
question = "How are VBA elements created?"
results = query_cadlib(question)
formatted = format_for_claude(results)

print("Results to share with Claude:")
print("=" * 80)
print(formatted)
```

---

### PowerShell Script Example

```powershell
# Query cwVDB API from PowerShell

function Query-Cadlib {
    param(
        [string]$Query,
        [int]$Results = 5
    )
    
    $body = @{
        query = $Query
        n_results = $Results
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod `
        -Uri "http://localhost:8000/search" `
        -Method Post `
        -Body $body `
        -ContentType "application/json"
    
    return $response
}

# Example usage
$results = Query-Cadlib -Query "VBA element creation" -Results 3

foreach ($result in $results.results) {
    Write-Host "`n[Similarity $($result.similarity)]"
    Write-Host "File: $($result.metadata.file_path)"
    Write-Host "Lines: $($result.metadata.start_line)-$($result.metadata.end_line)"
    Write-Host "`nCode Preview:"
    Write-Host $result.document.Substring(0, [Math]::Min(200, $result.document.Length))
    Write-Host ("-" * 80)
}
```

---

## Error Handling

### Standard Error Response

```json
{
  "error": "Error message description"
}
```

### HTTP Status Codes

- `200 OK` - Request successful
- `400 Bad Request` - Invalid request body or parameters
- `404 Not Found` - Endpoint not found
- `500 Internal Server Error` - Server error

### Common Errors

**Missing query parameter:**
```json
{
  "error": "Missing query parameter"
}
```

**Database not initialized:**
```json
{
  "error": "Failed to connect to collection: Collection not found"
}
```

**Connection refused:**
```
Cannot connect to API server
Make sure the API is running on http://localhost:8000
```

---

## Performance

### Response Times (Typical)

- `/health`: < 10ms
- `/stats`: < 50ms
- `/search`: 100-500ms (depends on n_results)
- `/find`: 100-500ms
- `/usage`: 100-500ms
- `/file`: 100-300ms
- `/similar`: 200-600ms

### Optimization Tips

1. **Reduce n_results** if you don't need many results
2. **Use file_filter** to narrow down search scope
3. **Use chunk_type filter** to search only specific types
4. **Keep queries concise** for better performance

---

## Security

### Default Configuration

- **Host:** `127.0.0.1` (localhost only)
- **Port:** `8000`
- **Authentication:** None (local use only)
- **CORS:** Enabled for all origins

### Production Considerations

If exposing to network:

1. **Add authentication:**
   ```python
   from flask_httpauth import HTTPBasicAuth
   auth = HTTPBasicAuth()
   
   @auth.verify_password
   def verify(username, password):
       # Verify credentials
       pass
   
   @app.route('/search', methods=['POST'])
   @auth.login_required
   def search():
       # ...
   ```

2. **Enable HTTPS**
3. **Restrict CORS origins**
4. **Add rate limiting**

---

## Troubleshooting

### API won't start

**Problem:** `Failed to connect to collection: Collection not found`

**Solution:** Run initial indexing first:
```bash
python indexer.py --initial
```

---

**Problem:** `ModuleNotFoundError: No module named 'flask'`

**Solution:** Install dependencies:
```bash
pip install -r requirements.txt
```

---

**Problem:** Port 8000 already in use

**Solution:** Use different port:
```bash
python query_api.py --port 8001
```

---

### Queries return no results

**Problem:** All queries return empty results

**Solution:** 
1. Check if database is populated: `python status.py`
2. Check if indexing completed successfully
3. Check logs in `logs/` directory

---

**Problem:** Low similarity scores

**Solution:**
- Try different query phrasing
- Use more specific queries
- Increase n_results to see more options

---

## Monitoring

### Log Files

Logs are written to console. To save logs:

```bash
python query_api.py --port 8000 > api.log 2>&1
```

### Health Monitoring Script

```python
import requests
import time

while True:
    try:
        r = requests.get("http://localhost:8000/health", timeout=5)
        if r.status_code != 200:
            print(f"ALERT: API unhealthy - Status {r.status_code}")
    except:
        print("ALERT: API not responding")
    
    time.sleep(60)  # Check every minute
```

---

## Summary

The cwVDB REST API provides a simple HTTP interface for semantic code search. All endpoints accept JSON and return JSON responses. Use the `/search` endpoint for most queries, and specialized endpoints like `/find` and `/usage` for specific use cases.

**Quick Start:**
```bash
# Start API
python query_api.py

# Test it
curl http://localhost:8000/health

# Search
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "your search query"}'
```

For more examples, see `test_api.py`.

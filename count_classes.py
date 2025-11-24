#!/usr/bin/env python3
"""Count how many classes are in the VectorDB"""

import chromadb
import re

lClient = chromadb.PersistentClient(path="./vectordb")
lCollection = lClient.get_collection("cadlib_code")

print(f"Total chunks in VectorDB: {lCollection.count()}")

# Get file_summary chunks to count classes
lResults = lCollection.get(
    limit=10000,
    include=["documents"],
    where={"chunk_type": {"$eq": "file_summary"}}
)

print(f"File summaries found: {len(lResults['documents'])}")

# Count unique class names
lClasses = set()
for lDoc in lResults['documents']:
    # Format: "ClassName.h: 1 classes, ... (ClassName)"
    lMatch = re.search(r'\(([CI][A-Z]\w+)\)', lDoc)
    if lMatch:
        lClasses.add(lMatch.group(1))

print(f"\nUnique classes found: {len(lClasses)}")
print(f"\nSample classes:")
for lClass in sorted(lClasses)[:20]:
    print(f"  - {lClass}")

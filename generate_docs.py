#!/usr/bin/env python3
"""
cwVDB Documentation Generator v5
Extended with: Usages, Related Classes, Code Examples
"""

import argparse
import json
import re
from pathlib import Path
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from collections import Counter

import chromadb


@dataclass
class SClassInfo:
    """Information about a C++ class"""
    name: str
    header_path: str = ""
    cpp_path: str = ""
    base_classes: List[str] = field(default_factory=list)
    derived_classes: List[str] = field(default_factory=list)
    methods: List[Dict] = field(default_factory=list)
    members: List[str] = field(default_factory=list)
    includes: List[str] = field(default_factory=list)
    included_by: List[str] = field(default_factory=list)  # Who includes this class
    usages: List[Dict] = field(default_factory=list)  # Where is this class used
    related_classes: List[str] = field(default_factory=list)
    namespace: str = ""
    code_example: str = ""


class CDocumentationGenerator:
    """Generates Markdown documentation from VectorDB"""
    
    def __init__(self, aConfigPath: str = "config.json"):
        self.mConfig = self._loadConfig(aConfigPath)
        self.mVectorDb = self._initVectorDb()
        self.mSourcePath = self.mConfig.get("source_path", "")
        self.mOutputPath = Path(self.mConfig.get("knowledge_output_path", "./knowledge/generated"))
        self.mOutputPath.mkdir(parents=True, exist_ok=True)
        
    def _loadConfig(self, aPath: str) -> Dict:
        with open(aPath, 'r') as lFile:
            return json.load(lFile)
    
    def _initVectorDb(self) -> chromadb.Collection:
        lDbPath = self.mConfig.get("vectordb_path", "./vectordb")
        lClient = chromadb.PersistentClient(path=lDbPath)
        return lClient.get_collection("cadlib_code")
    
    def generateClassDoc(self, aClassName: str, aVerbose: bool = True) -> Optional[str]:
        """Generate documentation for a single class"""
        if aVerbose:
            print(f"Generating documentation for: {aClassName}")
        
        lClassInfo = SClassInfo(name=aClassName)
        
        # STEP 1: Find the file paths
        if aVerbose:
            print(f"  [1/6] Finding source files...")
        self._findFilePaths(aClassName, lClassInfo)
        
        if not lClassInfo.header_path and not lClassInfo.cpp_path:
            if aVerbose:
                print(f"  ERROR: Could not find files for {aClassName}")
            return None
        
        # STEP 2: Load header chunks
        if aVerbose:
            print(f"  [2/6] Loading header file...")
        self._loadFileChunks(lClassInfo.header_path, lClassInfo, is_header=True)
        
        # STEP 3: Load cpp chunks
        if aVerbose:
            print(f"  [3/6] Loading implementation...")
        self._loadFileChunks(lClassInfo.cpp_path, lClassInfo, is_header=False)
        
        # STEP 4: Find usages (where is this class used?)
        if aVerbose:
            print(f"  [4/6] Finding usages...")
        self._findUsages(aClassName, lClassInfo)
        
        # STEP 5: Find related classes
        if aVerbose:
            print(f"  [5/6] Finding related classes...")
        self._findRelatedClasses(aClassName, lClassInfo)
        
        # STEP 6: Find code example
        if aVerbose:
            print(f"  [6/6] Finding code example...")
        self._findCodeExample(aClassName, lClassInfo)
        
        if aVerbose:
            print(f"  Result: {len(lClassInfo.methods)} methods, {len(lClassInfo.usages)} usages, {len(lClassInfo.related_classes)} related")
        
        # Generate markdown
        lMarkdown = self._generateMarkdown(lClassInfo)
        
        # Save
        lOutputFile = self.mOutputPath / f"{aClassName}.md"
        with open(lOutputFile, 'w', encoding='utf-8') as lFile:
            lFile.write(lMarkdown)
        
        if aVerbose:
            print(f"  Saved to: {lOutputFile}")
        return str(lOutputFile)
    
    def _findFilePaths(self, aClassName: str, aClassInfo: SClassInfo):
        """Find header and cpp file paths"""
        # Strategy 1: Search for exact file name
        lResults = self.mVectorDb.query(
            query_texts=[f"{aClassName}.h {aClassName}.cpp"],
            n_results=30,
            where={"chunk_type": {"$in": ["file_summary", "file_overview"]}}
        )
        
        for lMeta in lResults['metadatas'][0]:
            lPath = lMeta.get('file_path', '')
            if f"{aClassName}.h" in lPath and not aClassInfo.header_path:
                aClassInfo.header_path = lPath
            elif f"{aClassName}.cpp" in lPath and not aClassInfo.cpp_path:
                aClassInfo.cpp_path = lPath
        
        # Strategy 2: If not found, search for class definition
        if not aClassInfo.header_path and not aClassInfo.cpp_path:
            lResults2 = self.mVectorDb.query(
                query_texts=[f"class {aClassName}"],
                n_results=20,
                where={"chunk_type": {"$in": ["class_summary", "file_overview"]}}
            )
            
            for lDoc, lMeta in zip(lResults2['documents'][0], lResults2['metadatas'][0]):
                if f"class {aClassName}" in lDoc or f": {aClassName}" in lDoc:
                    lPath = lMeta.get('file_path', '')
                    if lPath.endswith('.h') and not aClassInfo.header_path:
                        aClassInfo.header_path = lPath
                    elif lPath.endswith('.cpp') and not aClassInfo.cpp_path:
                        aClassInfo.cpp_path = lPath
    
    def _loadFileChunks(self, aFilePath: str, aClassInfo: SClassInfo, is_header: bool):
        """Load all chunks from a specific file"""
        if not aFilePath:
            return
        
        try:
            lResults = self.mVectorDb.get(
                limit=200,
                include=["metadatas", "documents"],
                where={"file_path": {"$eq": aFilePath}}
            )
        except Exception as e:
            return
        
        lSeenMethods = {m['name'] for m in aClassInfo.methods}
        
        for lDoc, lMeta in zip(lResults['documents'], lResults['metadatas']):
            lChunkType = lMeta.get('chunk_type', '')
            
            if lChunkType == 'file_overview' and is_header:
                self._extractFromOverview(lDoc, aClassInfo)
            elif lChunkType == 'class_summary':
                self._extractFromClassSummary(lDoc, aClassInfo)
            elif lChunkType in ['function_full', 'function_preview']:
                self._extractMethod(lDoc, aClassInfo, lSeenMethods)
    
    def _extractFromOverview(self, aDoc: str, aClassInfo: SClassInfo):
        """Extract includes and namespace from file_overview"""
        lIncludeMatches = re.findall(r'#include\s*[<"]([^>"]+)[>"]', aDoc)
        for lInclude in lIncludeMatches:
            if lInclude not in aClassInfo.includes:
                aClassInfo.includes.append(lInclude)
        
        lNsMatch = re.search(r'Namespaces?:\s*([\w:,\s]+)', aDoc)
        if lNsMatch and not aClassInfo.namespace:
            aClassInfo.namespace = lNsMatch.group(1).strip()
    
    def _extractFromClassSummary(self, aDoc: str, aClassInfo: SClassInfo):
        """Extract base classes from class_summary"""
        lBaseMatch = re.search(
            rf'class\s+{aClassInfo.name}\s*:\s*(?:public|private|protected)\s+(\w+)',
            aDoc
        )
        if lBaseMatch:
            lBase = lBaseMatch.group(1)
            if lBase not in aClassInfo.base_classes:
                aClassInfo.base_classes.append(lBase)
        
        lMemberMatches = re.findall(r'\b(m[A-Z]\w+)\b', aDoc)
        for lMember in lMemberMatches:
            if lMember not in aClassInfo.members:
                aClassInfo.members.append(lMember)
    
    def _extractMethod(self, aDoc: str, aClassInfo: SClassInfo, aSeenMethods: Set[str]):
        """Extract method information from function chunk"""
        lSkipWords = {'if', 'for', 'while', 'switch', 'return', 'else', 'case', 'try', 'catch'}
        
        lMatch1 = re.match(r'^(\w+)\s*\([^)]*\)', aDoc.strip())
        if lMatch1:
            lMethodName = lMatch1.group(1)
            if lMethodName not in lSkipWords and lMethodName not in aSeenMethods:
                aSeenMethods.add(lMethodName)
                aClassInfo.methods.append({'name': lMethodName, 'return_type': '-'})
                return
        
        lMatch2 = re.match(r'^(\w+(?:\s*[*&<>:\w]+)?)\s+(\w+)\s*\([^)]*\)', aDoc.strip())
        if lMatch2:
            lReturnType = lMatch2.group(1).strip()
            lMethodName = lMatch2.group(2)
            if lMethodName not in lSkipWords and lMethodName not in aSeenMethods:
                aSeenMethods.add(lMethodName)
                aClassInfo.methods.append({'name': lMethodName, 'return_type': lReturnType})
    
    def _findUsages(self, aClassName: str, aClassInfo: SClassInfo):
        """Find where this class is used"""
        # Search for usages in other files
        lResults = self.mVectorDb.query(
            query_texts=[f"{aClassName} usage instance pointer reference"],
            n_results=50
        )
        
        lSeenFiles = set()
        lHeaderFile = Path(aClassInfo.header_path).name if aClassInfo.header_path else ""
        lCppFile = Path(aClassInfo.cpp_path).name if aClassInfo.cpp_path else ""
        
        for lDoc, lMeta in zip(lResults['documents'][0], lResults['metadatas'][0]):
            lPath = lMeta.get('file_path', '')
            lFileName = Path(lPath).name
            
            # Skip the class's own files
            if lFileName in [lHeaderFile, lCppFile]:
                continue
            
            # Check if class is actually mentioned
            if aClassName in lDoc:
                if lPath not in lSeenFiles:
                    lSeenFiles.add(lPath)
                    
                    # Determine usage type
                    lUsageType = "reference"
                    if f"#include" in lDoc and aClassName in lDoc:
                        lUsageType = "include"
                    elif f"{aClassName}::" in lDoc:
                        lUsageType = "method call"
                    elif f"new {aClassName}" in lDoc or f"{aClassName}(" in lDoc:
                        lUsageType = "instantiation"
                    elif f"{aClassName}*" in lDoc or f"{aClassName}&" in lDoc:
                        lUsageType = "pointer/reference"
                    
                    aClassInfo.usages.append({
                        'file': lPath.replace(self.mSourcePath + "\\", ""),
                        'type': lUsageType
                    })
        
        # Limit to most relevant
        aClassInfo.usages = aClassInfo.usages[:15]
    
    def _findRelatedClasses(self, aClassName: str, aClassInfo: SClassInfo):
        """Find classes that are related (same module, similar purpose)"""
        # Get classes from same directory
        if aClassInfo.header_path:
            lDir = str(Path(aClassInfo.header_path).parent)
            
            lResults = self.mVectorDb.query(
                query_texts=[f"class {aClassName}"],
                n_results=30,
                where={"chunk_type": {"$in": ["file_summary", "class_summary"]}}
            )
            
            lRelated = set()
            for lDoc, lMeta in zip(lResults['documents'][0], lResults['metadatas'][0]):
                lPath = lMeta.get('file_path', '')
                # Same directory = related
                if lDir in lPath:
                    lMatches = re.findall(r'\b([CI][A-Z]\w+)\b', lDoc)
                    lRelated.update(lMatches)
            
            # Remove self and base classes
            lRelated.discard(aClassName)
            for lBase in aClassInfo.base_classes:
                lRelated.discard(lBase)
            
            aClassInfo.related_classes = sorted(lRelated)[:10]
        
        # Find derived classes (classes that inherit from this one)
        lDerivedResults = self.mVectorDb.query(
            query_texts=[f"class : public {aClassName}"],
            n_results=20,
            where={"chunk_type": {"$eq": "class_summary"}}
        )
        
        for lDoc in lDerivedResults['documents'][0]:
            lMatch = re.search(rf'class\s+(\w+)\s*:\s*(?:public|private|protected)\s+{aClassName}', lDoc)
            if lMatch:
                lDerived = lMatch.group(1)
                if lDerived not in aClassInfo.derived_classes:
                    aClassInfo.derived_classes.append(lDerived)
    
    def _findCodeExample(self, aClassName: str, aClassInfo: SClassInfo):
        """Find a code example showing usage"""
        lResults = self.mVectorDb.query(
            query_texts=[f"{aClassName} example usage code"],
            n_results=20,
            where={"chunk_type": {"$in": ["function_full", "code_block"]}}
        )
        
        lHeaderFile = Path(aClassInfo.header_path).name if aClassInfo.header_path else ""
        lCppFile = Path(aClassInfo.cpp_path).name if aClassInfo.cpp_path else ""
        
        for lDoc, lMeta in zip(lResults['documents'][0], lResults['metadatas'][0]):
            lFileName = Path(lMeta.get('file_path', '')).name
            
            # Skip own files, look for usage examples
            if lFileName not in [lHeaderFile, lCppFile]:
                if aClassName in lDoc:
                    # Clean up the code example
                    lCode = lDoc.strip()
                    if len(lCode) > 100 and len(lCode) < 800:
                        aClassInfo.code_example = lCode
                        break
    
    def _generateMarkdown(self, aClassInfo: SClassInfo) -> str:
        """Generate Markdown documentation"""
        lLines = []
        
        # Header
        lLines.append(f"# {aClassInfo.name}")
        lLines.append("")
        lLines.append(f"> Auto-generated - {datetime.now().strftime('%Y-%m-%d')}")
        lLines.append("")
        
        # Quick info table
        lLines.append("## Overview")
        lLines.append("")
        lLines.append("| Property | Value |")
        lLines.append("|----------|-------|")
        
        if aClassInfo.header_path:
            lShortPath = aClassInfo.header_path.replace(self.mSourcePath + "\\", "")
            lLines.append(f"| **Header** | `{lShortPath}` |")
        if aClassInfo.cpp_path:
            lShortPath = aClassInfo.cpp_path.replace(self.mSourcePath + "\\", "")
            lLines.append(f"| **Source** | `{lShortPath}` |")
        if aClassInfo.namespace:
            lLines.append(f"| **Namespace** | `{aClassInfo.namespace}` |")
        if aClassInfo.base_classes:
            lBases = ", ".join(f"`{b}`" for b in aClassInfo.base_classes)
            lLines.append(f"| **Inherits** | {lBases} |")
        if aClassInfo.derived_classes:
            lDerived = ", ".join(f"`{d}`" for d in aClassInfo.derived_classes[:5])
            lLines.append(f"| **Derived** | {lDerived} |")
        lLines.append(f"| **Methods** | {len(aClassInfo.methods)} |")
        lLines.append(f"| **Used in** | {len(aClassInfo.usages)} files |")
        lLines.append("")
        
        # Inheritance diagram
        if aClassInfo.base_classes or aClassInfo.derived_classes:
            lLines.append("## Class Hierarchy")
            lLines.append("")
            lLines.append("```")
            for lBase in aClassInfo.base_classes:
                lLines.append(f"{lBase}")
                lLines.append(f"    |")
                lLines.append(f"    v")
            lLines.append(f"{aClassInfo.name}")
            if aClassInfo.derived_classes:
                lLines.append(f"    |")
                lLines.append(f"    v")
                lLines.append(f"[{', '.join(aClassInfo.derived_classes[:3])}]")
            lLines.append("```")
            lLines.append("")
        
        # Methods
        if aClassInfo.methods:
            lLines.append("## Methods")
            lLines.append("")
            lLines.append("| Method | Return Type |")
            lLines.append("|--------|-------------|")
            for lMethod in sorted(aClassInfo.methods, key=lambda x: x['name']):
                lLines.append(f"| `{lMethod['name']}()` | `{lMethod['return_type']}` |")
            lLines.append("")
        
        # Usages
        if aClassInfo.usages:
            lLines.append("## Usage Locations")
            lLines.append("")
            lLines.append("| File | Usage Type |")
            lLines.append("|------|------------|")
            for lUsage in aClassInfo.usages:
                lLines.append(f"| `{lUsage['file']}` | {lUsage['type']} |")
            lLines.append("")
        
        # Code example
        if aClassInfo.code_example:
            lLines.append("## Code Example")
            lLines.append("")
            lLines.append("```cpp")
            lLines.append(aClassInfo.code_example)
            lLines.append("```")
            lLines.append("")
        
        # Related classes
        if aClassInfo.related_classes:
            lLines.append("## Related Classes")
            lLines.append("")
            for lRelated in aClassInfo.related_classes:
                lLines.append(f"- [{lRelated}]({lRelated}.md)")
            lLines.append("")
        
        # Members
        if aClassInfo.members:
            lLines.append("## Member Variables")
            lLines.append("")
            for lMember in sorted(set(aClassInfo.members))[:20]:
                lLines.append(f"- `{lMember}`")
            lLines.append("")
        
        # Dependencies
        if aClassInfo.includes:
            lLines.append("## Dependencies")
            lLines.append("")
            for lInclude in sorted(aClassInfo.includes)[:15]:
                lLines.append(f"- `{lInclude}`")
            lLines.append("")
        
        # Footer
        lLines.append("---")
        lLines.append("*Generated by cwVDB Documentation Generator*")
        
        return "\n".join(lLines)
    
    def generateModuleDocs(self, aModuleName: str, aLimit: int = 20) -> List[str]:
        """Generate documentation for classes in a module"""
        print(f"Searching for classes in module: {aModuleName}")
        
        lResults = self.mVectorDb.query(
            query_texts=[f"{aModuleName}"],
            n_results=100,
            where={"chunk_type": {"$in": ["file_summary", "class_summary"]}}
        )
        
        lClassNames = set()
        for lDoc, lMeta in zip(lResults['documents'][0], lResults['metadatas'][0]):
            lPath = lMeta.get('file_path', '').lower()
            if aModuleName.lower() in lPath or aModuleName.lower() in lDoc.lower():
                lMatches = re.findall(r'\b([CI][A-Z]\w+)\b', lDoc)
                lClassNames.update(lMatches)
        
        print(f"Found {len(lClassNames)} classes, generating {min(aLimit, len(lClassNames))}")
        
        lGeneratedFiles = []
        for i, lClassName in enumerate(sorted(lClassNames)[:aLimit]):
            print(f"\n[{i+1}/{min(aLimit, len(lClassNames))}] ", end="")
            try:
                lFile = self.generateClassDoc(lClassName)
                if lFile:
                    lGeneratedFiles.append(lFile)
            except Exception as e:
                print(f"  Error: {e}")
        
        # Generate module index
        self._generateModuleIndex(aModuleName, lClassNames)
        
        return lGeneratedFiles
    
    def _generateModuleIndex(self, aModuleName: str, aClassNames: Set[str]):
        """Generate index file for module"""
        lLines = []
        lLines.append(f"# {aModuleName} Module")
        lLines.append("")
        lLines.append(f"> Auto-generated - {datetime.now().strftime('%Y-%m-%d')}")
        lLines.append("")
        lLines.append(f"**Total classes:** {len(aClassNames)}")
        lLines.append("")
        
        lInterfaces = sorted([c for c in aClassNames if c.startswith('I')])
        lClasses = sorted([c for c in aClassNames if c.startswith('C')])
        
        if lInterfaces:
            lLines.append("## Interfaces")
            lLines.append("")
            for lName in lInterfaces:
                lLines.append(f"- [{lName}]({lName}.md)")
            lLines.append("")
        
        if lClasses:
            lLines.append("## Classes")
            lLines.append("")
            for lName in lClasses:
                lLines.append(f"- [{lName}]({lName}.md)")
            lLines.append("")
        
        lOutputFile = self.mOutputPath / f"_index_{aModuleName}.md"
        with open(lOutputFile, 'w', encoding='utf-8') as lFile:
            lFile.write("\n".join(lLines))
        print(f"\nIndex saved to: {lOutputFile}")
    
    def findUndocumentedClasses(self, aLimit: int = 50) -> List[str]:
        """Find classes without documentation"""
        print("Searching for classes...")
        
        lResults = self.mVectorDb.query(
            query_texts=["class definition"],
            n_results=aLimit * 2,
            where={"chunk_type": {"$in": ["file_summary", "class_summary"]}}
        )
        
        lAllClasses = set()
        for lDoc in lResults['documents'][0]:
            lMatches = re.findall(r'\b([CI][A-Z]\w{3,})\b', lDoc)
            lAllClasses.update(lMatches)
        
        lUndocumented = []
        for lClassName in lAllClasses:
            lDocFile = self.mOutputPath / f"{lClassName}.md"
            if not lDocFile.exists():
                lUndocumented.append(lClassName)
        
        return sorted(lUndocumented)[:aLimit]
    
    def generateAllDocs(self, aLimit: int = 100, aSkipExisting: bool = True):
        """Generate docs for all classes (used by indexer)"""
        print(f"Generating documentation for all classes (limit: {aLimit}, skip_existing: {aSkipExisting})...")
        
        lResults = self.mVectorDb.query(
            query_texts=["class interface"],
            n_results=aLimit * 2,
            where={"chunk_type": {"$in": ["file_summary"]}}
        )
        
        lClassNames = set()
        for lDoc, lMeta in zip(lResults['documents'][0], lResults['metadatas'][0]):
            # Extract class names from file_summary
            # Format: "ClassName.h: 1 classes, ... (ClassName)"
            lMatch = re.search(r'\(([CI][A-Z]\w+)\)', lDoc)
            if lMatch:
                lClassNames.add(lMatch.group(1))
        
        print(f"Found {len(lClassNames)} classes")
        
        # Filter out existing if skip_existing is True
        if aSkipExisting:
            lToGenerate = []
            lSkipped = 0
            for lClassName in sorted(lClassNames)[:aLimit]:
                lDocFile = self.mOutputPath / f"{lClassName}.md"
                if lDocFile.exists():
                    lSkipped += 1
                else:
                    lToGenerate.append(lClassName)
            print(f"Skipping {lSkipped} existing docs, generating {len(lToGenerate)} new")
        else:
            lToGenerate = sorted(lClassNames)[:aLimit]
        
        lGenerated = 0
        lNotFound = 0
        for i, lClassName in enumerate(lToGenerate):
            print(f"[{i+1}/{len(lToGenerate)}] {lClassName}...", end=" ")
            try:
                lFile = self.generateClassDoc(lClassName, aVerbose=False)
                if lFile:
                    lGenerated += 1
                    print("OK")
                else:
                    lNotFound += 1
                    print("NOT FOUND (no .h/.cpp)")
            except Exception as e:
                print(f"ERROR: {e}")
        
        print(f"\nGenerated {lGenerated} new documentation files")
        if lNotFound > 0:
            print(f"Could not find source files for {lNotFound} classes")
        return lGenerated


def main():
    lParser = argparse.ArgumentParser(description='Generate documentation from VectorDB')
    lParser.add_argument('--class', dest='class_name', help='Generate docs for specific class')
    lParser.add_argument('--module', help='Generate docs for module classes')
    lParser.add_argument('--all', action='store_true', help='Generate docs for all classes')
    lParser.add_argument('--find-undocumented', action='store_true', help='List undocumented classes')
    lParser.add_argument('--limit', type=int, default=50, help='Limit results')
    lParser.add_argument('--force', action='store_true', help='Regenerate existing docs (default: skip)')
    lParser.add_argument('--config', default='config.json', help='Config file')
    
    lArgs = lParser.parse_args()
    lGenerator = CDocumentationGenerator(lArgs.config)
    
    lSkipExisting = not lArgs.force
    
    if lArgs.class_name:
        lGenerator.generateClassDoc(lArgs.class_name)
    elif lArgs.module:
        lGenerator.generateModuleDocs(lArgs.module, lArgs.limit)
    elif lArgs.all:
        lGenerator.generateAllDocs(lArgs.limit, lSkipExisting)
    elif lArgs.find_undocumented:
        lUndocumented = lGenerator.findUndocumentedClasses(lArgs.limit)
        print(f"\nUndocumented classes ({len(lUndocumented)}):")
        for lName in lUndocumented:
            print(f"  - {lName}")
    else:
        lParser.print_help()


if __name__ == "__main__":
    main()

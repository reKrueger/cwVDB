# cwVDB Quick Start Guide

## Installation

1. **Run Setup Script** (Windows)
   ```bash
   setup.bat
   ```
   This will:
   - Check Python installation
   - Install all dependencies
   - Optionally create virtual environment

2. **Or Manual Installation**
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Edit `config.json` to adjust:
- `source_path`: Path to cadlib source code
- `max_workers`: Number of CPU cores to use
- `chunk_size`: Size of code chunks (default: 1000 lines)
- `exclude_dirs`: Directories to skip

## Usage

### Initial Indexing (First Time)

```bash
python indexer.py --initial
```

**Expected behavior:**
- Scans ~60 GB of C++ code
- Creates ~3-5 GB vector database
- Takes 4-8 hours on average hardware
- Progress bar shows current status
- Checkpoints saved every 100 files

**Resume from checkpoint:**
If interrupted, just run again:
```bash
python indexer.py --initial
```
You'll be asked if you want to resume from checkpoint.

### Incremental Updates (Daily)

After initial indexing, use incremental updates for git changes:

```bash
python indexer.py --incremental
```

**Expected behavior:**
- Detects git changes
- Only re-indexes modified files
- Takes 5-15 minutes
- Updates existing chunks

### Querying the Database

#### Interactive Mode (Recommended)
```bash
python query.py --interactive
```

Commands:
- `search <query>` - Natural language search
- `find <symbol>` - Find implementations
- `usage <symbol>` - Find usages
- `file <path>` - Get file overview
- `quit` - Exit

#### Command Line Mode
```bash
# Search for code
python query.py --query "VBA element creation"

# Find function implementations
python query.py --find "CreateElement"

# Find symbol usages
python query.py --usage "NestingEngine"

# Get file overview
python query.py --file "Nesting.dll"

# Adjust number of results
python query.py --query "export functions" --results 10
```

## Example Queries

### Finding Code
```bash
python query.py --query "Wo werden VBA Elemente erstellt?"
python query.py --query "How are DLLs exported?"
python query.py --query "String manipulation utilities"
```

### Finding Functions
```bash
python query.py --find "CreateRoof"
python query.py --find "ExportToXML"
python query.py --find "CalculateVolume"
```

### Finding Usages
```bash
python query.py --usage "CwAPI"
python query.py --usage "Logger"
python query.py --usage "DatabaseConnection"
```

### File Overview
```bash
python query.py --file "Geometry.dll"
python query.py --file "ElementController"
python query.py --file "MainWindow.cpp"
```

## Integration with Claude

Use this workflow:

1. **Ask Claude a question about cadlib:**
   ```
   "Wo werden VBA Elemente in cadlib erstellt?"
   ```

2. **Search the vector database:**
   ```bash
   python query.py --query "VBA element creation"
   ```

3. **Share results with Claude:**
   Copy relevant code snippets and ask Claude to analyze them

4. **Generate documentation/diagrams:**
   ```
   "Erstelle UML Diagramm basierend auf diesem Code"
   ```

## Performance Tips

### Hardware Recommendations
- **CPU**: 6+ cores (for parallel processing)
- **RAM**: 16+ GB (32 GB recommended)
- **Storage**: SSD strongly recommended
- **Disk Space**: 10+ GB free (for vectordb + checkpoints)

### Speed Optimization
1. **Adjust max_workers** in config.json:
   - More cores = faster indexing
   - Recommended: Number of CPU cores - 1
   - Default: 6

2. **Adjust batch_size**:
   - Larger batches = faster but more memory
   - Default: 100 files per batch

3. **Use incremental updates**:
   - After initial index, always use `--incremental`
   - Much faster than re-indexing

### Memory Optimization
If running out of memory:
1. Reduce `max_workers` to 2-4
2. Reduce `batch_size` to 50
3. Reduce `chunk_size` to 500

## Troubleshooting

### "ChromaDB collection not found"
- Run initial indexing first: `python indexer.py --initial`

### "Out of memory"
- Reduce `max_workers` in config.json
- Reduce `batch_size`
- Close other applications

### "No git repository found"
- Git is only needed for incremental updates
- Initial indexing works without git
- Incremental updates disabled without git

### Slow indexing
- Check if running on HDD (use SSD)
- Reduce `max_workers` if CPU overheating
- Check if antivirus is scanning files

### Wrong search results
- Verify source path in config.json
- Re-run initial indexing if source changed
- Check if files are excluded in config

## Advanced Usage

### Custom Configuration
```bash
python indexer.py --initial --config custom_config.json
python query.py --query "test" --config custom_config.json
```

### Checkpoint Management
Checkpoints stored in `./checkpoints/`
- `latest.pkl` - Most recent checkpoint
- Deleted automatically after successful completion

### Logging
Logs stored in `./logs/`
- Format: `indexer_YYYYMMDD_HHMMSS.log`
- Contains detailed progress and errors

### Database Location
Vector database stored in `./vectordb/`
- Persistent storage (survives restarts)
- Can be backed up/copied
- Size: ~3-5 GB after initial index

## Next Steps

1. **Initial Index**: Run `python indexer.py --initial`
2. **Test Query**: Run `python query.py --interactive`
3. **Daily Updates**: Schedule `python indexer.py --incremental`
4. **Integrate with Claude**: Use for semantic code search

## Support

For issues or questions:
- Check logs in `./logs/`
- Review config.json settings
- Verify source path exists
- Ensure all dependencies installed

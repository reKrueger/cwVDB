# cwVDB - Quick Reference Card

## ⚡ Schnellstart

```bash
# 1. Setup (einmalig, 5 Minuten)
cd C:\Github\cwVDB
setup.bat

# 2. Test Installation
python test_setup.py

# 3. Initial Indexing (4-8 Stunden, über Nacht)
python indexer.py --initial

# 4. REST API starten
start_api.bat

# 5. API testen
python test_api.py
```

---

## 🔍 Suchen - 3 Wege

### CLI Interface
```bash
# Interactive
python query.py --interactive

# Direct
python query.py --query "VBA element creation"
python query.py --find "CreateElement"
python query.py --usage "NestingEngine"
```

### REST API (empfohlen)
```bash
# Search
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "VBA element creation", "n_results": 5}'

# Find Implementation
curl -X POST http://localhost:8000/find \
  -H "Content-Type: application/json" \
  -d '{"symbol": "CreateElement"}'

# Find Usage
curl -X POST http://localhost:8000/usage \
  -H "Content-Type: application/json" \
  -d '{"symbol": "NestingEngine"}'
```

### Python Script
```python
import requests

response = requests.post(
    "http://localhost:8000/search",
    json={"query": "VBA element creation", "n_results": 5}
)

for result in response.json()['results']:
    print(f"File: {result['metadata']['file_path']}")
    print(f"Code: {result['document'][:200]}...")
```

---

## 🤖 Claude Integration

### Workflow

1. **API starten:**
   ```bash
   start_api.bat
   ```

2. **Claude fragen:**
   ```
   "Wo werden VBA Elemente in cadlib erstellt?"
   ```

3. **Code holen:**
   ```bash
   curl -X POST http://localhost:8000/search \
     -H "Content-Type: application/json" \
     -d '{"query": "VBA element creation"}' > results.json
   ```

4. **An Claude geben:**
   ```
   Hier sind die relevanten Code-Stellen:
   [Paste results.json content]
   
   Bitte analysiere diese und erstelle ein UML Diagramm.
   ```

---

## 🔄 Updates

### Manuell
```bash
# Incremental (5-15 Minuten)
python indexer.py --incremental

# Status checken
python status.py
```

### Automatisch (Task Scheduler)
```powershell
# Einmalig einrichten (PowerShell als Admin)
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" `
  -Argument "-ExecutionPolicy Bypass -File C:\Github\cwVDB\run_incremental_update.ps1"
$trigger = New-ScheduledTaskTrigger -Daily -At 6:00AM
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries
$task = New-ScheduledTask -Action $action -Trigger $trigger -Settings $settings
Register-ScheduledTask -TaskName "cwVDB Incremental Update" -InputObject $task
```

---

## 📊 Status & Monitoring

```bash
# Database Status
python status.py

# Logs anzeigen
type logs\indexer_*.log
type logs\incremental_update_*.log

# API Health Check
curl http://localhost:8000/health

# Database Statistics
curl http://localhost:8000/stats
```

---

## 🛠️ Troubleshooting

### Problem: Collection not found
```bash
# Solution: Initial indexing ausführen
python indexer.py --initial
```

### Problem: Port 8000 already in use
```bash
# Solution: Anderen Port verwenden
python query_api.py --port 8001
```

### Problem: Out of memory
```json
// Solution: config.json anpassen
{
  "max_workers": 2,  // Reduzieren
  "batch_size": 50   // Reduzieren
}
```

### Problem: Keine Suchergebnisse
```bash
# 1. Status prüfen
python status.py

# 2. Logs checken
type logs\indexer_*.log

# 3. Ggf. neu indexieren
python indexer.py --initial
```

---

## 📝 REST API Endpoints

| Endpoint | Method | Beschreibung |
|----------|--------|--------------|
| `/health` | GET | Health Check |
| `/stats` | GET | Database Statistics |
| `/search` | POST | Semantic Search |
| `/find` | POST | Find Implementations |
| `/usage` | POST | Find Usages |
| `/file` | POST | File Overview |
| `/similar` | POST | Find Similar Code |

---

## 🎯 Häufige Queries

```bash
# VBA Funktionen finden
{"query": "VBA element creation"}

# Nesting Algorithmen
{"query": "nesting algorithm implementation"}

# COM Interfaces
{"query": "COM interface definition"}

# Export Funktionen
{"query": "file export functions"}

# Element Factory
{"query": "element factory creation methods"}
```

---

## 📁 Wichtige Dateien

| Datei | Zweck |
|-------|-------|
| `indexer.py` | Vektorisierung |
| `query.py` | CLI Suche |
| `query_api.py` | REST API |
| `status.py` | Status Check |
| `config.json` | Konfiguration |
| `STATUS.md` | Vollständiger Status |
| `API_DOCUMENTATION.md` | API Docs |

---

## ⚙️ Config Quick Tweaks

```json
{
  // Performance
  "max_workers": 6,        // CPU Cores
  "batch_size": 100,       // Files per batch
  
  // Filtering
  "min_file_size": 100,    // Bytes
  "max_file_size": 1048576, // 1 MB
  
  // Chunking
  "chunk_size": 1000,      // Lines
  "chunk_overlap": 200,    // Lines
  
  // Checkpoints
  "checkpoint_interval": 100 // Files
}
```

---

## 📚 Dokumentation

- **README.md** - Projekt Übersicht
- **QUICKSTART.md** - Schnellstart
- **STATUS.md** - Aktueller Status (KOMPLETT!)
- **API_DOCUMENTATION.md** - REST API Vollständige Docs
- **TASK_SCHEDULER_SETUP.md** - Windows Automation
- **IMPLEMENTATION.md** - Technische Details

---

## 💡 Pro Tips

1. **Initial Indexing über Nacht laufen lassen**
2. **REST API für Claude verwenden (nicht CLI)**
3. **Task Scheduler einrichten für automatische Updates**
4. **Logs regelmäßig checken**
5. **Backup von vectordb/ anlegen**

---

## 🎉 One-Liner für alles

```bash
# Setup → Test → Index → API → Test API
setup.bat && python test_setup.py && python indexer.py --initial && start_api.bat && python test_api.py
```

---

**Projekt Status:** ✅ PRODUCTION READY  
**Version:** Phase 5 Complete  
**Datum:** 2025-11-14

Viel Erfolg! 🚀

# MCP Integration für cwVDB - Interaktives Code-Lexikon

## 🎯 Was ist das Ziel?

**VORHER (aktuell):**
```
Du → cwVDB Query Tool → Ergebnisse → Du kopierst → Claude analysiert
```

**NACHHER (mit MCP):**
```
Du fragst Claude direkt: "Welche API Funktionen gibt es?"
    ↓
Claude ruft automatisch cwVDB ab
    ↓
Claude bekommt Code-Stellen
    ↓  
Claude gibt dir detaillierte Analyse - ALLES AUTOMATISCH!
```

---

## 📚 Was ist MCP?

**Model Context Protocol (MCP)** = Standard von Anthropic, damit Claude auf lokale Tools zugreifen kann.

**Vorteile:**
- ✅ Du fragst Claude direkt in natürlicher Sprache
- ✅ Claude sucht automatisch in deiner Vector DB
- ✅ Claude analysiert den Code sofort
- ✅ Interaktives Lexikon - wie ein Code-Experte der alles weiß!

---

## 🏗️ Architektur

```
Claude Desktop
    ↓ (MCP Protocol)
cwVDB MCP Server (Python)
    ↓ (REST API)
cwVDB Query API (localhost:8000)
    ↓
Vector Database (ChromaDB)
```

---

## 📋 Voraussetzungen

- ✅ cwVDB bereits installiert und indexiert (hast du!)
- ✅ Claude Desktop installiert
- ✅ Python 3.10+ (hast du!)
- ✅ Node.js/npm ODER Python MCP SDK

---

## 🚀 Installation - Schritt für Schritt

### Schritt 1: MCP Server für cwVDB erstellen

Ich erstelle dir einen fertigen MCP Server in Python.

**Datei:** `mcp_server.py` (wird automatisch erstellt)

### Schritt 2: MCP SDK installieren

```bash
# Im cwVDB Verzeichnis
pip install mcp
```

### Schritt 3: REST API dauerhaft laufen lassen

Die MCP Server braucht die REST API:

```bash
# Terminal 1: REST API starten
python start.py api --port 8000
```

**Oder als Windows Service einrichten** (siehe unten)

### Schritt 4: MCP Server testen

```bash
# Terminal 2: MCP Server starten
python mcp_server.py
```

### Schritt 5: Claude Desktop konfigurieren

Datei: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "cwvdb": {
      "command": "python",
      "args": [
        "C:\\Github\\cwVDB\\mcp_server.py"
      ]
    }
  }
}
```

### Schritt 6: Claude Desktop neu starten

**WICHTIG:** Komplett schließen und neu öffnen!

---

## 🎮 Verwendung

### Beispiel-Fragen an Claude (nach MCP Integration):

```
"Welche API Funktionen gibt es in meinem IOP Projekt?"

"Zeige mir die Implementierung der CMainWindow Klasse"

"Wo wird der Logger verwendet?"

"Finde alle Fehlerbehandlungs-Routinen"

"Erkläre mir wie die Datei main.cpp funktioniert"

"Welche Klassen gibt es und was machen sie?"
```

**Claude antwortet automatisch mit:**
1. Suche in Vector DB
2. Relevante Code-Stellen
3. Detaillierte Analyse
4. Erklärungen und Zusammenhänge

---

## 🔧 MCP Server Code

Der MCP Server hat folgende Tools:

### 1. `search_code`
```python
search_code(query: str, n_results: int = 5)
# Semantische Code-Suche
```

### 2. `find_implementation`
```python
find_implementation(symbol: str)
# Finde Implementierungen einer Funktion/Klasse
```

### 3. `find_usages`
```python
find_usages(symbol: str)
# Finde alle Verwendungen
```

### 4. `get_file_overview`
```python
get_file_overview(file_path: str)
# Vollständige Datei-Übersicht
```

### 5. `get_statistics`
```python
get_statistics()
# DB Statistiken
```

---

## 📊 Workflow-Beispiel

### Ohne MCP (aktuell):
```
Du: "Welche API Funktionen gibt es?"
→ Du öffnest Terminal
→ python start.py query "API functions"
→ Du kopierst Ergebnisse
→ Du fragst Claude in neuem Chat
→ Du pastest Code
→ Claude analysiert

= 5-6 Schritte, mehrere Fenster
```

### Mit MCP:
```
Du: "Welche API Funktionen gibt es?"
→ Claude ruft automatisch search_code("API functions")
→ Claude bekommt Ergebnisse
→ Claude analysiert sofort
→ Claude antwortet: "Ich habe 5 API-Funktionen gefunden:
    1. InitAPI() in api/Manager.cpp - Initialisiert...
    2. RegisterCallback() in api/Events.cpp - ..."

= 1 Schritt, alles automatisch!
```

---

## 🛠️ Fortgeschrittene Konfiguration

### Option A: REST API als Windows Service

Damit die API immer läuft (kein separates Terminal nötig):

**Mit NSSM (Non-Sucking Service Manager):**

```powershell
# NSSM installieren (einmalig)
choco install nssm

# Service erstellen
nssm install cwVDB_API "C:\Github\cwVDB\env\Scripts\python.exe" "C:\Github\cwVDB\start.py api"
nssm set cwVDB_API AppDirectory "C:\Github\cwVDB"
nssm start cwVDB_API
```

### Option B: Autostart mit Windows

**startup_api.bat:**
```batch
@echo off
start /min python C:\Github\cwVDB\start.py api
```

In Autostart-Ordner kopieren:
```
%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\
```

---

## 🐛 Troubleshooting

### Problem: "MCP Server not responding"
**Lösung:**
1. Prüfe ob REST API läuft: `curl http://localhost:8000/health`
2. Prüfe MCP Server Logs
3. Claude Desktop neu starten

### Problem: "No results found"
**Lösung:**
1. DB Status prüfen: `run_status.bat`
2. Neu indexieren falls nötig: `run_test_indexing.bat`

### Problem: "Connection refused"
**Lösung:**
- REST API läuft nicht: `python start.py api`
- Port belegt: `python start.py api --port 8001`

---

## 📈 Performance-Tipps

### Schnellere Antworten:
```json
{
  "max_workers": 8,      // Mehr CPU
  "chunk_size": 800,     // Kleinere Chunks
  "n_results": 3         // Weniger Ergebnisse
}
```

### Bessere Qualität:
```json
{
  "embedding_model": "all-mpnet-base-v2",  // Besseres Model
  "n_results": 10                          // Mehr Ergebnisse
}
```

---

## 🎯 Best Practices

### Gute Fragen an Claude:

✅ **Spezifisch:**
```
"Zeige mir alle Funktionen die mit Dateien arbeiten"
"Wo wird die Klasse CLogger initialisiert?"
```

❌ **Zu allgemein:**
```
"Zeig mir alles"
"Was macht der Code?"
```

### Claude nutzt automatisch die besten Tools:

```
Frage: "Welche Klassen gibt es?"
→ Claude ruft: search_code("class definitions")

Frage: "Wo wird Logger verwendet?"  
→ Claude ruft: find_usages("Logger")

Frage: "Zeig mir main.cpp"
→ Claude ruft: get_file_overview("main.cpp")
```

---

## 🚀 Erweiterte Features (optional)

### Multi-Projekt Support:

```json
{
  "mcpServers": {
    "cwvdb-iop": {
      "command": "python",
      "args": ["C:\\Github\\cwVDB\\mcp_server.py"],
      "env": {
        "CWVDB_CONFIG": "config_iop.json"
      }
    },
    "cwvdb-cadlib": {
      "command": "python",
      "args": ["C:\\Github\\cwVDB\\mcp_server.py"],
      "env": {
        "CWVDB_CONFIG": "config_cadlib.json"
      }
    }
  }
}
```

### Custom Tools hinzufügen:

Editiere `mcp_server.py` und füge neue Tools hinzu:

```python
@server.tool()
async def analyze_dependencies(file_path: str):
    """Analyze dependencies of a file"""
    # Custom logic here
    pass
```

---

## 📚 Weitere Ressourcen

- **MCP Dokumentation:** https://modelcontextprotocol.io
- **Anthropic MCP Guide:** https://docs.anthropic.com/mcp
- **cwVDB GitHub:** (dein Projekt)

---

## ✅ Zusammenfassung

Nach der MCP Integration kannst du:

1. **Claude direkt fragen:**
   - "Welche API Funktionen gibt es?"
   - "Erkläre mir die Hauptklassen"
   - "Wo wird Error Handling gemacht?"

2. **Claude sucht automatisch** in deiner Vector DB

3. **Claude analysiert** den gefundenen Code

4. **Du bekommst** detaillierte, kontextuelle Antworten

**= Interaktives Code-Lexikon! 🎉**

---

## 🎬 Nächste Schritte

1. Ich erstelle dir den `mcp_server.py` Code
2. Du installierst die MCP SDK: `pip install mcp`
3. Du konfigurierst Claude Desktop
4. Du stellst mir Fragen über deinen Code!

**Bereit? Sag Bescheid und ich erstelle den MCP Server Code!** 🚀

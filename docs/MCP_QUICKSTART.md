# MCP Integration - Quick Start

## 🚀 Installation (5 Minuten)

### Schritt 1: MCP SDK installieren
```bash
pip install mcp requests
```

**Oder einfach:**
```bash
setup_mcp.bat
```

### Schritt 2: REST API starten
```bash
python start.py api
```
→ Läuft auf http://localhost:8000

### Schritt 3: Claude Desktop konfigurieren

Datei öffnen: `%APPDATA%\Claude\claude_desktop_config.json`

Hinzufügen:
```json
{
  "mcpServers": {
    "cwvdb": {
      "command": "python",
      "args": ["C:\\Github\\cwVDB\\mcp_server.py"]
    }
  }
}
```

**WICHTIG:** Passe den Pfad an deine Installation an!

### Schritt 4: Claude Desktop NEU STARTEN

Komplett schließen und wieder öffnen!

---

## ✅ Testen

In Claude Desktop fragen:

```
"Welche Dateien sind in der Vector DB?"
```

```
"Suche nach API Funktionen"
```

```
"Zeige mir die main.cpp Datei"
```

Claude sollte automatisch die Tools nutzen und antworten!

---

## 🔧 Troubleshooting

### Problem: "Tool not available"
- REST API läuft nicht → `python start.py api`
- MCP Server nicht in Config → Claude Desktop Config prüfen
- Claude Desktop nicht neu gestartet

### Problem: "Connection refused"
- API Port belegt → `python start.py api --port 8001`
- Dann MCP Config anpassen: `CWVDB_API_URL=http://localhost:8001`

### Problem: "No results found"
- Datenbank leer → `run_test_indexing.bat` ausführen
- Status prüfen → `run_status.bat`

---

## 📚 Vollständige Dokumentation

Siehe: `docs/MCP_INTEGRATION.md`

---

## 🎯 Beispiel-Workflow

**Du:**
> "Welche API Funktionen gibt es in meinem Projekt?"

**Claude:**
> *[Ruft automatisch search_code("API functions") auf]*
> 
> Ich habe 5 API-Funktionen in deinem Projekt gefunden:
> 
> 1. **InitAPI()** in `src/api/Manager.cpp`
>    - Initialisiert das API-System
>    - Code: `void InitAPI() { ... }`
> 
> 2. **RegisterCallback()** in `src/api/Events.cpp`
>    - Registriert Event-Callbacks
>    - ...
> 
> [Detaillierte Analyse folgt...]

**= Interaktives Code-Lexikon! 🎉**

# Hierarchical System - User Guide

## Overview

Das hierarchische System erstellt 5 verschiedene Detail-Ebenen für token-effiziente Queries:

- **Level 0**: Ultra-kompakte Datei-Zusammenfassung (50-100 Zeichen)
- **Level 1**: Datei-Übersicht mit Hauptelementen (200-500 Zeichen)
- **Level 2**: Klassen-Zusammenfassungen (300-600 Zeichen)
- **Level 3**: Funktions-Signaturen + kurzer Body (400-800 Zeichen)
- **Level 4**: Vollständiger Code (1000+ Zeichen)

## Quick Start

### 1. Kompletten Rebuild durchführen

```batch
rebuild_complete.bat
```

Dies wird:
- Alte VectorDB löschen
- Hierarchische Indexierung durchführen
- Smart-Dokumentation generieren
- Knowledge Base erstellen

**Dauer:** 4-8 Stunden (abhängig von Codebase-Größe)

### 2. System testen

```batch
test_hierarchical.bat
```

Führt verschiedene Test-Queries durch alle Ebenen aus.

### 3. Interaktiv nutzen

```batch
python hierarchical_query.py --interactive
```

## Usage Examples

### Hierarchische Suche (empfohlen)

```bash
# Sucht progressiv von Level 0 bis 4
python hierarchical_query.py --query "VBA element creation"
```

**Token-Verbrauch:** ~2000-5000 tokens (vs. 10000+ bei normaler Suche)

### Suche auf spezifischem Level

```bash
# Level 0 - Nur Datei-Summaries (minimal tokens)
python hierarchical_query.py --level 0 --query "nesting"

# Level 1 - Datei-Übersichten
python hierarchical_query.py --level 1 --query "API functions"

# Level 2 - Klassen-Details
python hierarchical_query.py --level 2 --query "Manager classes"

# Level 3 - Funktions-Previews
python hierarchical_query.py --level 3 --query "initialization"

# Level 4 - Vollständiger Code
python hierarchical_query.py --level 4 --query "error handling"
```

### Implementation finden

```bash
# Findet Implementation auf Level 3 (preview)
python hierarchical_query.py --find "CreateElement"
```

### Datei-Übersicht

```bash
# Zeigt Level 0 + 1 für eine Datei
python hierarchical_query.py --file "Manager.cpp"
```

### Knowledge Base anzeigen

```bash
# Zeigt kompakte Projekt-Übersicht
python hierarchical_query.py --kb
```

## Token-Vergleich

### Beispiel-Frage: "Wie funktioniert das Nesting-System?"

#### Alte Methode (normale VectorDB):
```
Query → 10 Code-Chunks à 1000 Zeilen
= 10,000 Tokens
```

#### Neue Methode (hierarchisch):
```
1. Lese quick-reference.md (bereits geladen)
   = 0 Tokens (schon im Kontext)

2. Falls nicht ausreichend:
   Level 0 Query → 2 File-Summaries
   = 200 Tokens

3. Falls mehr Details nötig:
   Level 2 Query → 3 Class-Summaries
   = 1,000 Tokens

Total: 1,200 Tokens (88% Einsparung!)
```

## Knowledge Base

Nach dem Rebuild wird automatisch eine Knowledge Base erstellt:

```
knowledge/
├── README.md                    - Übersicht
├── 00-quick-reference.md        - Ultra-kompakt (~500 tokens)
├── 01-project-overview.md       - Detailliert (~2k tokens)
├── 02-class-hierarchy.md        - Alle Klassen (~3k tokens)
└── 03-api-reference.md          - API-Funktionen (~5k tokens)
```

**Verwendung durch Claude:**
1. Claude liest `00-quick-reference.md` (500 tokens)
2. Bei einfachen Fragen → Antwort direkt aus Knowledge Base
3. Bei komplexen Fragen → Hierarchische VectorDB-Query
4. **Ergebnis:** 70-90% Token-Einsparung

## Interactive Mode Commands

```
cwVDB> search <query>           # Hierarchische Suche
cwVDB> level <0-4> <query>      # Spezifischer Level
cwVDB> find <symbol>            # Implementation finden
cwVDB> file <path>              # Datei-Übersicht
cwVDB> kb                       # Knowledge Base anzeigen
cwVDB> quit                     # Beenden
```

## Best Practices

### 1. Start mit Knowledge Base
```bash
# Erst kompakte Übersicht lesen
python hierarchical_query.py --kb
```

### 2. Hierarchisch von oben nach unten
```bash
# Erst Level 0/1 für Übersicht
python hierarchical_query.py --level 0 --query "your topic"

# Dann bei Bedarf tiefer gehen
python hierarchical_query.py --level 3 --query "your topic"
```

### 3. Token-Budget setzen
```bash
# Max 2000 tokens (sehr sparsam)
python hierarchical_query.py --query "topic" --max-tokens 2000

# Max 5000 tokens (standard)
python hierarchical_query.py --query "topic" --max-tokens 5000
```

## Wann welchen Level verwenden?

| Frage | Level | Beispiel |
|-------|-------|----------|
| "Welche Projekte gibt es?" | 0 | File summaries |
| "Was macht Modul X?" | 1 | File overviews |
| "Welche Klassen hat X?" | 2 | Class summaries |
| "Wie funktioniert Funktion Y?" | 3 | Function previews |
| "Zeig mir den Code von Z" | 4 | Full implementation |
| "Generelle Übersicht" | Hierarchisch | Progressive detail |

## Integration mit Claude

### MCP-Integration

Die MCP-Tools wurden automatisch erweitert:

```python
# Neues Tool: search_code_hierarchical
{
  "query": "your question",
  "detail_level": "overview",  # overview, summary, detail, code
  "max_tokens": 5000
}
```

### Manuelle Verwendung

```
User: "Erkläre mir das Nesting-System"

Claude:
1. Liest knowledge/00-quick-reference.md (500 tokens)
2. Antwortet mit Übersicht
3. Bei Bedarf: Hierarchical query für Details (1500 tokens)

Total: 2000 tokens (vs. 10000+ vorher)
```

## Maintenance

### Bei Code-Änderungen

```batch
# Kompletter Rebuild (empfohlen bei großen Änderungen)
rebuild_complete.bat

# Oder: Inkrementelles Update (für kleinere Änderungen)
# TODO: Noch nicht implementiert
```

### Knowledge Base aktualisieren

```batch
# Nur Dokumentation neu generieren
python analyze_and_refine.py
```

## Troubleshooting

### Problem: "Collection not found"
**Lösung:** Rebuild durchführen
```batch
rebuild_complete.bat
```

### Problem: "Knowledge base not available"
**Lösung:** Analyse-Script ausführen
```batch
python analyze_and_refine.py
```

### Problem: "Out of memory"
**Lösung:** Reduziere `batch_size` in `config.json`
```json
{
  "batch_size": 50  // Statt 100
}
```

## Performance-Tipps

1. **Nutze Knowledge Base für Übersichten** → 0 extra tokens
2. **Starte mit Level 0/1** → Nur 200-500 tokens
3. **Gehe nur bei Bedarf zu Level 4** → Spart 80-90% tokens
4. **Setze Token-Limits** → Verhindert übermäßige Nutzung

## Token-Savings Beispiele

| Szenario | Alte Methode | Neue Methode | Einsparung |
|----------|--------------|--------------|------------|
| Projekt-Übersicht | 5000 tokens | 500 tokens | 90% |
| Klasse finden | 3000 tokens | 800 tokens | 73% |
| Funktion verstehen | 4000 tokens | 1200 tokens | 70% |
| Code-Details | 10000 tokens | 3000 tokens | 70% |

**Durchschnittliche Einsparung: 70-90%**

## Support

Bei Problemen:
1. Logs prüfen: `logs/hierarchical_indexer_*.log`
2. Status checken: `python start.py status`
3. Rebuild durchführen: `rebuild_complete.bat`

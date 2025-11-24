# cwVDB Documentation Generator

Automatische Dokumentations-Generierung aus dem C++ Source Code.

## Uebersicht

```
                    VectorDB (ChromaDB)
                           |
                           v
              +------------------------+
              |  generate_docs.py      |   Basic: Regex-basiert
              +------------------------+
                           |
                           v
              +------------------------+
              |  generate_docs_ai.py   |   Advanced: Claude API
              +------------------------+
                           |
                           v
                  knowledge/generated/
                     ClassName.md
```

## Verwendung

### Basic Generator (ohne API)

```batch
REM Einzelne Klasse dokumentieren
generate_docs.bat --class CCwTsiModel

REM Modul dokumentieren
generate_docs.bat --module tsi

REM Undokumentierte Klassen finden
generate_docs.bat --find-undocumented
```

### AI Generator (mit Claude API)

```batch
REM API Key setzen
set ANTHROPIC_API_KEY=sk-ant-...

REM Einzelne Klasse mit AI dokumentieren
python generate_docs_ai.py --class CCwTsiModel

REM Modul mit Limit
python generate_docs_ai.py --module tsi --limit 10
```

## Output

Die generierten Dateien landen in `knowledge/generated/`:

```
knowledge/
    generated/
        CCwTsiModel.md
        CCwTsiShopDrawings.md
        ITsiCollection.md
        _index_tsi.md
```

## Struktur der generierten Dokumentation

```markdown
# ClassName

> Auto-generated documentation - 2025-11-24

## Quick Info

| Property | Value |
|----------|-------|
| **File** | `path/to/file.h` |
| **Namespace** | `cadwork::tsi` |
| **Base Classes** | `IBaseClass` |

## Methods

| Method | Return Type | Modifiers |
|--------|-------------|-----------|
| `methodName()` | `void` | virtual |

## Dependencies

- `Header1.h`
- `Header2.h`

## Usage Examples

```cpp
// Example code
```

## Related Classes

- `RelatedClass1`
- `RelatedClass2`
```

## Workflow: Komplette Modul-Dokumentation

1. **Starte mit undokumentierten Klassen:**
   ```batch
   generate_docs.bat --find-undocumented
   ```

2. **Generiere Basic-Docs fuer Modul:**
   ```batch
   generate_docs.bat --module tsi
   ```

3. **Verfeinere wichtige Klassen mit AI:**
   ```batch
   python generate_docs_ai.py --class ICwN2dTsiCollectionManager
   python generate_docs_ai.py --class CCwTsiModel
   ```

4. **Pruefe und editiere manuell falls noetig**

## Erweiterung

### Eigene Dokumentations-Templates

Editiere `DOCUMENTATION_PROMPT` in `generate_docs_ai.py`:

```python
DOCUMENTATION_PROMPT = """
Dein custom prompt hier...
"""
```

### Weitere Module dokumentieren

```batch
REM Beispiele fuer andere Module
generate_docs.bat --module fgm
generate_docs.bat --module ceo
generate_docs.bat --module bim
```

## Requirements

- Python 3.8+
- chromadb
- anthropic (fuer AI-Generator)

```batch
pip install chromadb anthropic
```

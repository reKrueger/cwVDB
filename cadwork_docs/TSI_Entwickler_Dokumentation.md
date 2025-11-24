# TSI Klassen - Entwicklerdokumentation

> **TSI** = **T**echnical **S**hop-drawing **I**nterface
> 
> Verwaltet die Verbindung zwischen 3D-Elementen und deren 2D-Werkstattplaenen.

---

## Inhaltsverzeichnis

- [1. Systemuebersicht](#1-systemuebersicht)
  - [1.1 Was ist TSI?](#11-was-ist-tsi)
  - [1.2 Unterschied 2D-Manager vs 3D-Manager](#12-unterschied-2d-manager-vs-3d-manager)
- [2. Die Collection Manager im Detail](#2-die-collection-manager-im-detail)
  - [2.1 Wo werden die Manager erstellt?](#21-wo-werden-die-manager-erstellt)
  - [2.2 Was wird benoetigt?](#22-was-wird-benoetigt)
  - [2.3 Die internen Komponenten](#23-die-internen-komponenten)
  - [2.4 ICwN2dTsiCollectionManager - Vollstaendige Referenz](#24-icwn2dtsicollectionmanager---vollstaendige-referenz)
  - [2.5 ICw3dTsiCollectionManager - Vollstaendige Referenz](#25-icw3dtsicollectionmanager---vollstaendige-referenz)
- [3. Die TSI-Hierarchie](#3-die-tsi-hierarchie)
- [4. Wichtige Enums](#4-wichtige-enums)
- [5. Die Signale im Detail](#5-die-signale-im-detail)
- [6. Praxisbeispiel: TSI Collection erstellen](#6-praxisbeispiel-tsi-collection-erstellen)
- [7. Kernklassen-Referenz](#7-kernklassen-referenz)
- [8. Haeufige Anwendungsfaelle](#8-haeufige-anwendungsfaelle)

---

# 1. Systemuebersicht

## 1.1 Was ist TSI?

Das TSI-System ist das Rueckgrat der Werkstattplan-Funktionalitaet in cadwork. Es loest folgende Probleme:

| Problem | TSI-Loesung |
|---------|-----------|
| Wie weiss ich, welche 2D-Linien zu welchem 3D-Element gehoeren? | `ITsiBoundElement` verknuepft 3D-ID mit 2D-Element-IDs |
| Wie organisiere ich mehrere Ansichten eines Elements? | Hierarchie: Collection -> Page -> View -> BoundElement |
| Wie erkenne ich, ob ein Plan veraltet ist? | `EShopDrawingState` (UpToDate, Expired, Modified...) |
| Wie reagiere ich auf Aenderungen? | Signal-System (getNotifyOnAddDrawing, get3dModifySignal...) |

---

## 1.2 Unterschied 2D-Manager vs 3D-Manager

Es gibt **zwei verschiedene Manager-Typen** fuer unterschiedliche Einsatzzwecke:

```
                    ICw3dDocument
                         |
         +---------------+---------------+
         |                               |
         v                               v
  ICwN2dTsiCollectionManager     ICw3dTsiCollectionManager
  (CCwN2dTsiCollectionManager)   (CCw3dTsiCollectionManager)
         |                               |
         v                               v
   Plan Connector 2D              Bridge 3D / Connector 3D
   PlanStudio                     Nur Ansicht, kein Editing
   Layouts
   Volles 2D-Element-Management
```

### Schnellvergleich

| Aspekt | 2D-Manager (ICwN2dTsiCollectionManager) | 3D-Manager (ICw3dTsiCollectionManager) |
|--------|----------------------------------------|---------------------------------------|
| **Zugriff** | `aDocument.getN2dTsiCollectionManager()` | `aDocument.get3dTsiCollectionManager()` |
| **Implementierung** | `CCwN2dTsiCollectionManager` | `CCw3dTsiCollectionManager` |
| **2D-Element-Verwaltung** | Ja (add/remove) | Nein |
| **Undo/Redo** | Ja | Nein |
| **Plug-System** | Ja | Nein |
| **Persistenz** | Vollstaendig (load/save) | Nur Pods |
| **Cache-System** | Ja | Nein |
| **TreeView-State** | Nein | Ja |
| **Typischer Einsatz** | Wenn 2D-Elemente bearbeitet werden | Wenn nur Uebersicht benoetigt wird |

---

# 2. Die Collection Manager im Detail

## 2.1 Wo werden die Manager erstellt?

Die Manager werden im **Konstruktor von `CCdwk3dDocument`** erstellt. Das passiert automatisch beim Oeffnen eines 3D-Dokuments.

```cpp
// Aus CCdwk3dDocument.cpp - Konstruktor
CCdwk3dDocument::CCdwk3dDocument(const CCwQtString& aFilePath)
{
    // ... andere Initialisierungen ...
    
    // Hier werden beide TSI-Manager erstellt:
    mN2dTsiManager = cadwork::tsi::createTsiCollectionManager2d(*this);
    m3dTsiManager = cadwork::tsi::createTsiCollectionManager3d(*this);
    
    // ... weitere Initialisierungen ...
}
```

### Zugriff auf die Manager

```cpp
// 2D-Manager holen (fuer PlanStudio, Plan Connector, etc.)
ICwN2dTsiCollectionManager& l2dManager = aDocument.getN2dTsiCollectionManager();

// 3D-Manager holen (fuer Bridge 3D, etc.)
ICw3dTsiCollectionManager& l3dManager = aDocument.get3dTsiCollectionManager();
```

---

## 2.2 Was wird benoetigt?

Beide Manager benoetigen dieselben Basis-Komponenten, die in `STsiManagerAddition` zusammengefasst sind:

```cpp
// Aus cadwork_tsi_utils.h
namespace cadwork::tsi
{
    struct STsiManagerAddition
    {
        std::unique_ptr<CCwTsiShopDrawings> mTsiShopDrawing;  // Neuberechnung
        std::unique_ptr<CCwTsiModel> mTsiModel;               // Datenhaltung
        std::unique_ptr<CCwTsiManagerSignals> mTsiSignals;    // Signale
    };
}
```

### Factory-Funktion fuer 2D-Manager

```cpp
// Aus cadwork_tsi_utils.cpp
std::unique_ptr<ICwN2dTsiCollectionManager> 
cadwork::tsi::createTsiCollectionManager2d(ICw3dDocument& a3dDocument)
{
    STsiManagerAddition lAddition{
        std::make_unique<CCwTsiShopDrawings>(a3dDocument),
        std::make_unique<CCwTsiModel>(a3dDocument),
        std::make_unique<CCwTsiManagerSignals>(),
    };
    
    return std::make_unique<CCwN2dTsiCollectionManager>(
        a3dDocument, 
        lAddition, 
        std::make_unique<cadwork::tsi::CCwN2dTsiDBProvider>(a3dDocument)
    );
}
```

### Factory-Funktion fuer 3D-Manager

```cpp
std::unique_ptr<ICw3dTsiCollectionManager> 
cadwork::tsi::createTsiCollectionManager3d(ICw3dDocument& a3dDocument)
{
    STsiManagerAddition lAddition{
        std::make_unique<CCwTsiShopDrawings>(a3dDocument),
        std::make_unique<CCwTsiModel>(a3dDocument),
        std::make_unique<CCwTsiManagerSignals>(),
    };
    
    return std::make_unique<CCw3dTsiCollectionManager>(
        a3dDocument, 
        lAddition, 
        std::make_unique<cadwork::tsi::CCw3dTsiDBProvider>(a3dDocument)
    );
}
```

---

## 2.3 Die internen Komponenten

Beide Manager bestehen intern aus denselben Kernkomponenten:

```
+----------------------------------+
|     TsiCollectionManager         |
+----------------------------------+
|                                  |
|  +---------------------------+   |
|  |    CCwTsiShopDrawings     |   |   Neuberechnung von Werkstattplaenen
|  +---------------------------+   |
|                                  |
|  +---------------------------+   |
|  |       CCwTsiModel         |   |   Datenhaltung (ValidMap, InvalidMap)
|  +---------------------------+   |
|                                  |
|  +---------------------------+   |
|  |   CCwTsiManagerSignals    |   |   Signal-System fuer Events
|  +---------------------------+   |
|                                  |
|  +---------------------------+   |
|  |     ITsiDBProvider        |   |   Persistenz (Laden/Speichern)
|  +---------------------------+   |
|                                  |
+----------------------------------+
```

### CCwTsiShopDrawings - Neuberechnung

Diese Klasse ist verantwortlich fuer das **Neuberechnen** von Shop-Drawings.

| Methode | Beschreibung |
|---------|-------------|
| `recreateSelectedShopDrawingsTdo()` | TDO-Zeichnungen neu berechnen |
| `recreateSelectedShopDrawingsEsz()` | ESZ-Zeichnungen neu berechnen |
| `recreateSelectedShopDrawingsWall()` | Wandplaene neu berechnen |
| `recreateSelectedShopDrawingsExportSolid()` | ExportSolid-Zeichnungen neu berechnen |
| `recreateSelectedShopDrawingsContainer()` | Container-Zeichnungen neu berechnen |
| `recreateSelectedShopDrawingsNesting()` | Nesting-Zeichnungen neu berechnen |

### CCwTsiModel - Datenhaltung

Diese Klasse verwaltet **alle Collections** intern. Sie haelt zwei Maps:

| Map | Beschreibung |
|-----|-------------|
| `mValidMap` | Aktive Collections (GUID -> Collection) |
| `mInvalidMap` | Geloeschte/ungueltige Collections (fuer Undo) |

Wichtige Methoden:

| Methode | Beschreibung |
|---------|-------------|
| `insert()` | Neue Collection hinzufuegen |
| `remove()` | Collection entfernen (in InvalidMap verschieben) |
| `findTsiCollectionByGuid()` | Collection ueber GUID finden |
| `findTsiCollectionByMasterId()` | Collection ueber 3D-Master-ID finden |
| `getN2dArray()` | Alle Collections eines Typs holen |
| `changesIn3DModelArea()` | 3D-Aenderungen verarbeiten |
| `appendTsiCache()` / `getFromTsiCache()` | Cache-Verwaltung |

### CCwTsiManagerSignals - Signal-System

Diese Klasse haelt alle Signale:

```cpp
class CCwTsiManagerSignals
{
private:
    CCwSignal<> mNotifyOnAddDrawing;              // Zeichnung hinzugefuegt
    CCwSignal<int> mCollectionCacheSignal;        // Cache-Status (Progress)
    CCwSignal<> mRefreshConnectorData;            // Daten aktualisiert
    CCwSignal<> mNotifyOnAddDrawingLayout;        // Layout hinzugefuegt
    CCwSignal<CCwVector<CCwQtGuid>> m3dModifySignal;  // 3D geaendert
    CCwSignal<CCwVector<CCwQtGuid>> m3dElementDeletedSignal; // 3D geloescht
};
```

### ITsiDBProvider - Persistenz

Zwei Spezialisierungen:

| Klasse | Verwendung |
|--------|-----------|
| `CCwN2dTsiDBProvider` | Fuer 2D-Manager (PlanStudio-Datenbank) |
| `CCw3dTsiDBProvider` | Fuer 3D-Manager (Bridge-Datenbank) |

---

## 2.4 ICwN2dTsiCollectionManager - Vollstaendige Referenz

Der 2D-Manager bietet das **vollstaendige Feature-Set** fuer die Arbeit mit Shop-Drawings.

### Collection-Verwaltung

| Methode | Beschreibung |
|---------|-------------|
| `insertCollection(unique_ptr<ITsiCollection>)` | Neue Collection einfuegen |
| `removeCollectionNoUpdate(CCwQtGuid)` | Collection entfernen (ohne UI-Update) |
| `removeCollectionNoUpdatePermanently(CCwQtGuid)` | Collection permanent loeschen |
| `recoverCollection(CCwQtGuid)` | Geloeschte Collection wiederherstellen |

### Suche

| Methode | Beschreibung |
|---------|-------------|
| `findTsiCollection(CCwQtGuid)` | Finde Collection ueber GUID |
| `findTsiCollection(TCwDbId)` | Finde Collection ueber 3D-Master-ID |
| `findTsiCollection(IElementDrawing2d&)` | Finde Collection ueber 2D-Element |
| `findTsiCollection(PodCollectionMasterLink)` | Finde Collection ueber Master-Link |
| `findTsiBoundElement(TDbIdD2d)` | Finde BoundElement ueber 2D-Element-ID |
| `find3dElementMasterFromGuid(CCwQtGuid)` | Finde 3D-Master-Element |

### 2D-Element-Verwaltung (NUR im 2D-Manager!)

| Methode | Beschreibung |
|---------|-------------|
| `add2dElementsNoUpdate(CCwQtGuid, TDbIdD2dVector)` | 2D-Elemente hinzufuegen |
| `remove2dElementsNoUpdate(CCwQtGuid, TDbIdD2dVector)` | 2D-Elemente entfernen |
| `remove2dIdFromTsiNoUpdate(TDbIdD2d, CCwQtGuid)` | Einzelnes 2D-Element entfernen |
| `remove2dElementsNoUpdatePermanently(TDbIdD2dVector)` | 2D-Elemente permanent loeschen |
| `pullUser2dElements(CCwQtGuid, TDbIdD2dVector&)` | User-2D-Elemente extrahieren |
| `get2dElementDbIdsFromTsiGuid(CCwQtGuid)` | Alle 2D-IDs einer Collection holen |

### Undo/Redo (NUR im 2D-Manager!)

| Methode | Beschreibung |
|---------|-------------|
| `getTsiCollectionState(TDbIdD2dVector, CCwQtGuid)` | Aktuellen State speichern |
| `setTsiCollectionStateNoUpdate(CCwVector<TsiCollectionState>&)` | State wiederherstellen |
| `removeElementsFromTsiNoUpdate(CCwVector<TsiCollectionState>)` | Elemente entfernen (mit State) |
| `elementIsPushedToUndo(CCwQtGuid, TCwDbId)` | Element in Undo-Stack |
| `elementIsPopedFromUndo(CCwQtGuid, TCwDbId)` | Element aus Undo-Stack |

### Plug-Verwaltung (NUR im 2D-Manager!)

| Methode | Beschreibung |
|---------|-------------|
| `moveToPlug(bool, IFgmPlug*, IElementDrawing2d&, IContextMove&)` | Element in Plug verschieben |
| `updateAllFgmPlugs()` | Alle Plugs aktualisieren |
| `updateVisibilityFgmPlugs()` | Plug-Sichtbarkeit aktualisieren |

### Neuberechnung

| Methode | Beschreibung |
|---------|-------------|
| `recreateSelectedShopDrawingsTdo(ETdoOutputMode, ITsiCollection&)` | TDO neu berechnen |
| `recreateSelectedShopDrawingsEsz(TElementVector&)` | ESZ neu berechnen |
| `recreateSelectedShopDrawingsWall(TElementVector&)` | Wand neu berechnen |
| `recreateSelectedShopDrawingsExportSolid(...)` | ExportSolid neu berechnen |
| `recreateSelectedShopDrawingsContainer(...)` | Container neu berechnen |
| `recreateSelectedShopDrawingsNesting(...)` | Nesting neu berechnen |

### Status und Abfragen

| Methode | Beschreibung |
|---------|-------------|
| `setTsiCollectionExpired(CCwQtGuid)` | Collection als veraltet markieren |
| `setSelectionReturns(ESelectionReturns)` | Selektionsmodus setzen |
| `getN2dArray(CCwVector<ITsiCollection*>&, EShopDrawingType, ETsiMapType)` | Collections nach Typ holen |
| `getVisibilityGuids(CCwVector<CCwQtGuid>&)` | Sichtbare GUIDs holen |
| `isShopDrawingCalculate()` | Ist Berechnung aktiv? |
| `blockAutoSave() / setBlockAutoSave(bool)` | AutoSave blockieren |

### Persistenz

| Methode | Beschreibung |
|---------|-------------|
| `load(bool readFromDatabase)` | Daten laden |
| `save(int aDbHandle)` | Daten speichern |
| `writePlugData(int aDbHandle)` | Plug-Daten speichern |

### Signale

| Methode | Beschreibung |
|---------|-------------|
| `getNotifyOnAddDrawing()` | Signal: Zeichnung hinzugefuegt |
| `getNotifyOnAddDrawingLayout()` | Signal: Layout hinzugefuegt |
| `getRefreshDataSignal()` | Signal: Daten aktualisiert |
| `get3dModifySignal()` | Signal: 3D-Elemente geaendert |
| `getCollectionCacheSignal()` | Signal: Cache-Status |

### Cache (NUR im 2D-Manager!)

| Methode | Beschreibung |
|---------|-------------|
| `appendShopdrawingCache(unique_ptr<ITsiCache>)` | Cache hinzufuegen |
| `getFromShopdrawingCache()` | Cache holen |
| `proofShopdrawingCache()` | Cache pruefen |

---

## 2.5 ICw3dTsiCollectionManager - Vollstaendige Referenz

Der 3D-Manager bietet ein **reduziertes Interface** fuer die reine Ansicht.

### Collection-Verwaltung

| Methode | Beschreibung |
|---------|-------------|
| `insertCollection(unique_ptr<ITsiCollection>)` | Neue Collection einfuegen |

### Suche

| Methode | Beschreibung |
|---------|-------------|
| `findTsiCollection(CCwQtGuid)` | Finde Collection ueber GUID |
| `findTsiCollection(TCwDbId)` | Finde Collection ueber 3D-Master-ID |
| `findTsiCollection(PodCollectionMasterLink)` | Finde Collection ueber Master-Link |
| `find3dElementMasterFromGuid(CCwQtGuid)` | Finde 3D-Master-Element |

### Neuberechnung

Dieselben Methoden wie beim 2D-Manager.

### Status und Abfragen

| Methode | Beschreibung |
|---------|-------------|
| `setTsiCollectionExpired(CCwQtGuid)` | Collection als veraltet markieren |
| `getN2dArray(CCwVector<ITsiCollection*>&, EShopDrawingType, ETsiMapType)` | Collections nach Typ holen |
| `getPlanWall(TCwDbId)` | Wandplan holen |
| `isShopDrawingCalculate()` | Ist Berechnung aktiv? |

### TreeView-State (NUR im 3D-Manager!)

| Methode | Beschreibung |
|---------|-------------|
| `getCurrentTreeViewState()` | Aktuellen TreeView-Zustand holen |
| `setCurrentTreeViewState(PodTreeViewState&)` | TreeView-Zustand setzen |

### Pod-basierte Kommunikation (NUR im 3D-Manager!)

| Methode | Beschreibung |
|---------|-------------|
| `getCollectionPod(CCwQtGuid)` | Collection als Pod holen |
| `getCurrentCollectionPods(CCwVector<PodCollection>&)` | Alle Collections als Pods |
| `readCollectionPods(CCwVector<PodCollection>&)` | Pods einlesen |

### Signale

| Methode | Beschreibung |
|---------|-------------|
| `getNotifyOnAddDrawing()` | Signal: Zeichnung hinzugefuegt |
| `getRefreshDataSignal()` | Signal: Daten aktualisiert |
| `get3dModifySignal()` | Signal: 3D-Elemente geaendert |

---

## Was managed welcher Manager?

### 2D-Manager (ICwN2dTsiCollectionManager) managed:

```
+-- Collections (ITsiCollection)
|   +-- Pages (ITsiPage)
|   |   +-- Views (ITsiView)
|   |   |   +-- BoundElements (ITsiBoundElement)
|   |   |       +-- 2D-Element-IDs (direkte Verwaltung!)
|   |   +-- DrawFrame
|   +-- Metadaten (Name, GUID, State, etc.)
|
+-- 2D-Elemente direkt
|   +-- Hinzufuegen zu Collections
|   +-- Entfernen aus Collections
|   +-- Verschieben zwischen Plugs
|
+-- Undo/Redo States
|   +-- Collection-Zustaende speichern
|   +-- Collection-Zustaende wiederherstellen
|
+-- Plugs (IFgmPlug)
|   +-- Plug-Aktualisierung
|   +-- Plug-Sichtbarkeit
|
+-- Cache (ITsiCache)
|   +-- Temporaere Collections vor Insert
|
+-- Persistenz
    +-- Laden aus Datenbank
    +-- Speichern in Datenbank
```

### 3D-Manager (ICw3dTsiCollectionManager) managed:

```
+-- Collections (ITsiCollection) - Nur Lesen
|   +-- Keine direkte 2D-Element-Manipulation
|
+-- TreeView-State
|   +-- Welche Nodes sind expandiert?
|   +-- Welche sind selektiert?
|
+-- Pod-Kommunikation
    +-- Serialisierung fuer Bridge 3D
    +-- Deserialisierung von Bridge 3D
```

---

# 3. Die TSI-Hierarchie

```
+-----------------------------------------------------------------------+
|                      ITsiCollection                                    |
|  +---------------------------------------------------------------+    |
|  | Metadaten: GUID, Name, Typ, Zustand, Master-3D-Element        |    |
|  +---------------------------------------------------------------+    |
|                                                                        |
|  +---------------------------------------------------------------+    |
|  |                     ITsiPage (Seite)                           |    |
|  |  +---------------------------------------------------------+   |   |
|  |  | Seiten-Metadaten: ID, Name, Groesse, Nummer             |   |   |
|  |  +---------------------------------------------------------+   |   |
|  |                                                                |   |
|  |  +---------------------------------------------------------+   |   |
|  |  |                  ITsiView (Ansicht)                      |   |   |
|  |  |  +---------------------------------------------------+   |   |   |
|  |  |  | View-Metadaten: Kamera, Skalierung                |   |   |   |
|  |  |  +---------------------------------------------------+   |   |   |
|  |  |                                                          |   |   |
|  |  |  +---------------------------------------------------+   |   |   |
|  |  |  |         ITsiBoundElement                           |   |   |   |
|  |  |  |  - 3D-Element-ID (Master)                         |   |   |   |
|  |  |  |  - Liste von 2D-Element-IDs                       |   |   |   |
|  |  |  |  - Komponenten-IDs                                |   |   |   |
|  |  |  +---------------------------------------------------+   |   |   |
|  |  +---------------------------------------------------------+   |   |
|  +---------------------------------------------------------------+    |
+-----------------------------------------------------------------------+
```

### Beziehungen in Tabellenform

| Ebene | Klasse | Enthaelt | Anzahl |
|-------|--------|---------|--------|
| 1 | `ITsiCollection` | Pages | 1..n |
| 2 | `ITsiPage` | Views + optional DrawFrame | 1..n |
| 3 | `ITsiView` | BoundElements | 0..n |
| 4 | `ITsiBoundElement` | 2D-Element-IDs | 1..n |

---

# 4. Wichtige Enums

### EShopDrawingType - Was fuer ein Plan ist es?

| Wert | Bedeutung | Verwendung |
|------|-----------|------------|
| `PieceByPiece = 10` | Einzelteilzeichnung | TDO/ESZ Export |
| `ExportSolid = 30` | ExportSolid-Zeichnung | CEO Export |
| `Container = 40` | Container-Zeichnung | Container-Export |
| `Wall = 50` | Wandzeichnung | Wandplan-Export |
| `Nesting = 70` | Nesting-Zeichnung | Nesting-Export |
| `FreeLayout = 100` | Freies Layout | Plan Connector |
| `Layout = 110` | Layout-Datei | Layout-Import |

### EShopDrawingState - Wie aktuell ist der Plan?

| Wert | Farbe | Bedeutung |
|------|-------|-----------|
| `UpToDate = 1` | Gruen | Plan ist aktuell |
| `Expired = 2` | Rot | 3D-Element wurde geaendert |
| `Empty = 3` | Transparent | Keine 2D-Elemente |
| `MasterDeleted = 4` | - | 3D-Master geloescht |
| `Modified = 6` | - | In 2D bearbeitet |
| `Pending = 9` | Gelb | Noch nicht berechnet |
| `Shell` | - | Nur Huelle, keine 2D-Elemente |

### ESelectionReturns - Was soll bei Selektion zurueckgegeben werden?

| Wert | Rueckgabe |
|------|----------|
| `BoundElement` | Nur das gebundene Element |
| `View` | Alle Elemente der Ansicht |
| `Page` | Alle Elemente der Seite |
| `Collection` | Alle Elemente der Collection |
| `Drawframe` | Nur der Zeichnungsrahmen |

### ETsiMapType - Welche Map abfragen?

| Wert | Beschreibung |
|------|-------------|
| `CommonMap` | Normale, aktive Collections |
| `InvalidMap` | Geloeschte Collections (fuer Undo) |

### EEnvironment - Welche Umgebung?

| Wert | Beschreibung |
|------|-------------|
| `Connector2D` | Plan Connector 2D (PlanStudio) |
| `Connector3D` | Bridge 3D |
| `ConnectorLayout` | Layout-Modus |

---

# 5. Die Signale im Detail

Das TSI-System verwendet ein **Signal-Slot-System** fuer die Kommunikation zwischen Komponenten. Die Signale werden ueber `CCwSignal<>` implementiert.

### Signal-Uebersicht

| Signal | Parameter | Wann gefeuert? | Typischer Empfaenger |
|--------|-----------|---------------|---------------------|
| `getNotifyOnAddDrawing()` | - | Neue Zeichnung hinzugefuegt | UI-Liste aktualisieren |
| `getNotifyOnAddDrawingLayout()` | - | Neues Layout hinzugefuegt | Layout-Liste aktualisieren |
| `getRefreshDataSignal()` | - | Daten wurden aktualisiert | Komplette UI neu laden |
| `get3dModifySignal()` | `CCwVector<CCwQtGuid>` | 3D-Elemente wurden geaendert | Plaene als "Expired" markieren |
| `getCollectionCacheSignal()` | `int` | Cache-Status geaendert | Progress-Anzeige |

### Praktisches Beispiel: Signal verbinden

```cpp
void initializeUI(ICw3dDocument& aDocument)
{
    auto& lManager = aDocument.getN2dTsiCollectionManager();
    
    // Signal: Wenn neue Zeichnung hinzugefuegt wird
    lManager.getNotifyOnAddDrawing().connect([this]() 
    {
        // UI-Liste neu laden
        refreshDrawingList();
    });
    
    // Signal: Wenn 3D-Elemente geaendert wurden
    lManager.get3dModifySignal().connect([this](CCwVector<CCwQtGuid>& aModifiedGuids) 
    {
        // Betroffene Plaene als "veraltet" markieren
        for (const CCwQtGuid& lGuid : aModifiedGuids)
        {
            markAsExpired(lGuid);
        }
    });
    
    // Signal: Daten komplett aktualisiert
    lManager.getRefreshDataSignal().connect([this]() 
    {
        // Alles neu laden
        reloadEverything();
    });
}
```

---

# 6. Praxisbeispiel: TSI Collection erstellen

## Der komplette Workflow

```
+------------------+
| 1. Controller    |  PodExport konfigurieren, Controller erstellen
|    erstellen     |
+--------+---------+
         v
+------------------+
| 2. Cache         |  Cache ist der temporaere Arbeitsbereich
|    erstellen     |
+--------+---------+
         v
+------------------+
| 3. Collection    |  Collection im Cache anlegen
|    erstellen     |
+--------+---------+
         v
+------------------+
| 4. Struktur      |  Pages, Views, BoundElements erstellen
|    aufbauen      |  2D-Objekte analysieren und zuordnen
+--------+---------+
         v
+------------------+
| 5. Transfer      |  Cache an Manager uebergeben
|    zum Manager   |
+------------------+
```

## Reales Beispiel aus dem TDO-Export

```cpp
void exportWithTsi(const ITdoExportController& aController, 
                   std::unique_ptr<C2dcObjectBase>&& aObject2dc)
{
    // SCHRITT 1: Controller holen
    ITsiController* lTsiController = aController.getTsiController();
    
    // SCHRITT 2: Cache erstellen
    auto lCache = lTsiController->createCache(lTsiController->getShopdrawingType());

    // SCHRITT 3: Collection im Cache erstellen
    ITsiCollection* lCollection = lCache->createCollection();

    // SCHRITT 4: 2D-Objekte analysieren und TSI-Struktur aufbauen
    std::unique_ptr<ITsi2dcObjAnalysis> lAnalysis = lCache->createObjAnalysis(*aObject2dc);
    lAnalysis->startAnalysis(lCollection->getDrawingType());
    lCache->buildTsi(*lAnalysis, *aObject2dc->getFactoryGlyph());

    // SCHRITT 5: Cache uebergeben
    lCache->setObj2dc(std::move(aObject2dc));
    lTsiController->appendShopdrawingCache(std::move(lCache));
}
```

---

# 7. Kernklassen-Referenz

| Klasse | Wichtigste Methoden |
|--------|---------------------|
| **ICwN2dTsiCollectionManager** | `findTsiCollection()`, `insertCollection()`, `findTsiBoundElement()`, `add2dElementsNoUpdate()` |
| **ICw3dTsiCollectionManager** | `findTsiCollection()`, `insertCollection()`, `getCollectionPod()` |
| **ITsiCollection** | `getAllPages()`, `findBoundElementBy2dId()`, `createPage()`, `createView()` |
| **ITsiPage** | `getAllViews()`, `getDrawFrame()`, `setPageSize()` |
| **ITsiView** | `getAllBoundElements()`, `setScale()`, `setCamera()` |
| **ITsiBoundElement** | `get3dId()`, `getAll2dElementIds()`, `append2dId()` |
| **ITsiController** | `createCache()`, `transfer()`, `getShopdrawingType()` |
| **ITsiCache** | `createCollection()`, `buildTsi()`, `createObjAnalysis()` |

### Factory-Funktionen (cadwork_tsi_utils.h)

```cpp
namespace cadwork::tsi
{
    // Manager erstellen (normalerweise automatisch durch Document)
    std::unique_ptr<ICwN2dTsiCollectionManager> createTsiCollectionManager2d(ICw3dDocument&);
    std::unique_ptr<ICwN2dTsiCollectionManager> createTsiCollectionManager2dLayout(ICw3dDocument&);
    std::unique_ptr<ICw3dTsiCollectionManager> createTsiCollectionManager3d(ICw3dDocument&);
    
    // Controller erstellen
    std::unique_ptr<ITsiController> createController(ICw3dDocument&, PodExport);
    std::unique_ptr<ITsiController> createExportController(ICw3dDocument&, PodExport);
    std::unique_ptr<ITsiController> createTsiControllerIfSelected(EShopDrawingType);
    
    // Utility-Funktionen
    void moveTsiCollection(const CVector2d&, const ITsiCollection&);
    void moveTsiPage(const CVector2d&, const ITsiPage&);
    
    // Registrierung (fuer Plan Connector)
    void registerFromWall(ICw3dDocument&, EEnvironment);
    void registerFromExportSolid(ICw3dDocument&, EEnvironment);
    void registerFromContainer(ICw3dDocument&, EEnvironment);
    void registerFromNesting(ICwGuiDocumentView&, EEnvironment);
}
```

---

# 8. Haeufige Anwendungsfaelle

### Fall 1: Finde alle 2D-Elemente eines 3D-Elements

```cpp
TDbIdD2dVector find2dElementsOf3dElement(ICw3dDocument& aDoc, TCwDbId a3dId)
{
    auto& lManager = aDoc.getN2dTsiCollectionManager();
    const ITsiCollection* lColl = lManager.findTsiCollection(a3dId);
    
    if (!lColl) return {};
    
    return lColl->getAll2dIds();
}
```

### Fall 2: Pruefe ob ein Plan veraltet ist

```cpp
bool isDrawingExpired(ICw3dDocument& aDoc, const CCwQtGuid& aGuid)
{
    auto& lManager = aDoc.getN2dTsiCollectionManager();
    const ITsiCollection* lColl = lManager.findTsiCollection(aGuid);
    
    if (!lColl) return true;
    
    return lColl->getState() == EShopDrawingState::Expired;
}
```

### Fall 3: Alle Collections eines Typs holen

```cpp
void printAllWallPlans(ICw3dDocument& aDoc)
{
    auto& lManager = aDoc.getN2dTsiCollectionManager();
    CCwVector<const ITsiCollection*> lCollections;
    
    lManager.getN2dArray(lCollections, 
                         EShopDrawingType::Wall, 
                         cadwork::tsi::ETsiMapType::CommonMap);
    
    for (const ITsiCollection* lColl : lCollections)
    {
        // ... verarbeiten
    }
}
```

### Fall 4: Speichere TSI-Zustand fuer Undo

```cpp
CCwVector<TsiCollectionState> saveForUndo(ICw3dDocument& aDoc, 
                                           const TDbIdD2dVector& a2dIds)
{
    auto& lManager = aDoc.getN2dTsiCollectionManager();
    return lManager.getTsiCollectionState(a2dIds, CCwQtGuid());
}

void restoreFromUndo(ICw3dDocument& aDoc, 
                     CCwVector<TsiCollectionState>& aStates)
{
    auto& lManager = aDoc.getN2dTsiCollectionManager();
    lManager.setTsiCollectionStateNoUpdate(aStates);
}
```

### Fall 5: Shell-Collections registrieren (fuer Plan Connector)

```cpp
void registerShells(ICw3dDocument& aDoc)
{
    // Registriert alle Elemente als "Shell" (ohne 2D-Inhalt)
    // fuer spaetere Berechnung im Plan Connector
    
    cadwork::tsi::registerFromWall(aDoc, cadwork::tsi::EEnvironment::Connector2D);
    cadwork::tsi::registerFromExportSolid(aDoc, cadwork::tsi::EEnvironment::Connector2D);
    cadwork::tsi::registerFromContainer(aDoc, cadwork::tsi::EEnvironment::Connector2D);
}
```

---

## Zusammenfassung

| Konzept | Merke dir |
|---------|----------|
| **2D-Manager** | Volle Kontrolle: 2D-Elemente, Undo, Plugs, Persistenz |
| **3D-Manager** | Nur Lesen: TreeView-State, Pod-Kommunikation |
| **Erstellung** | Automatisch im CCdwk3dDocument-Konstruktor |
| **Komponenten** | CCwTsiShopDrawings + CCwTsiModel + CCwTsiManagerSignals + DBProvider |
| **Hierarchie** | Collection > Page > View > BoundElement |
| **Signale** | Verbinde dich mit Signalen um auf Aenderungen zu reagieren |

---

*Dokumentation Version 3.0 - cadwork 34.0*

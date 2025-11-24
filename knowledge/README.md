# cwVDB Knowledge Base

Generated: 2025-11-21 22:53:27
Updated: 2025-11-24

## Purpose

This knowledge base contains structured documentation extracted from the VectorDB for token-efficient queries.

## Documents

1. **00-quick-reference.md** - Ultra-compact overview (~500 tokens)
2. **01-project-overview.md** - Detailed statistics (~2k tokens)
3. **02-class-hierarchy.md** - All classes and inheritance (~3k tokens)
4. **03-api-reference.md** - Public functions (~5k tokens)
5. **04-tsi-classes.md** - TSI System documentation (~3k tokens) **NEW**

## Usage

Claude should read these docs first before querying VectorDB.
This saves 70-90% of tokens compared to direct VectorDB queries.

## Token Efficiency

- Quick reference: ~500 tokens
- All docs combined: ~13k tokens
- Alternative (VectorDB queries): ~50k+ tokens

## TSI Documentation (04-tsi-classes.md)

The TSI (Technical Shop-drawing Interface) documentation covers:
- ICwN2dTsiCollectionManager vs ICw3dTsiCollectionManager
- Where managers are created (CCdwk3dDocument)
- Internal components (CCwTsiShopDrawings, CCwTsiModel, CCwTsiManagerSignals)
- TSI Hierarchy (Collection > Page > View > BoundElement)
- Important enums (EShopDrawingType, EShopDrawingState)
- Signals and their usage
- Factory functions in cadwork_tsi_utils.h

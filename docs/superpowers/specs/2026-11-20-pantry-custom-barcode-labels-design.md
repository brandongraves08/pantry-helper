# Pantry Helper Custom Barcode Labels — Design

**Status:** Proposed for implementation in the existing Pantry Helper app; Brandon selected that target (“Do 1”) and asked to build the recommended Code 128 label flow.

## Intent

Let household members label repackaged pantry foods with a locally generated barcode, then scan that label later to resolve the saved item without relying on Open Food Facts. The immediate use case is a home-packed white-rice package.

## Design

Add a small custom-label flow to the existing Barcode Scanner page. It accepts an item name, package description, and package count; creates or finds the Pantry Helper inventory item, records the stock change and an internal barcode mapping, and displays a printable Code 128 label. The internal code is generated server-side with a Pantry Helper-specific prefix, so it cannot be mistaken for a retail UPC/EAN. The existing scan endpoint already checks its local barcode cache before external lookup, so future scans resolve locally. A label shows the item, package description, code, and generated date.

Use the existing SQLAlchemy models and database: `InventoryItem`, `InventoryState`, `InventoryEvent`, and `BarcodeLookup`. No table migration or Offline Prepper data integration is needed. Use an established client-side Code 128 SVG generator for print rendering; the API owns code generation and persistence. Protect the new write endpoint through the existing API auth middleware.

## Approaches

1. **Internal Code 128 (recommended/selected):** standard linear barcode for package labels; fits the existing camera scanner and local cache path.
2. **QR code:** easier to embed structured data, but not the user's requested barcode style and less convenient on small pantry labels.
3. **Fake UPC/EAN entered manually:** rejected because codes could collide with retail identifiers and trigger misleading external catalog lookups.

## Constraints and non-goals

- Keep all writes in Pantry Helper's existing inventory database; do not merge, migrate, or modify Offline Prepper stores.
- Preserve existing external-product barcode behavior.
- Creating a label adds the specified package count to inventory; scanning a label only looks up the linked item and must not silently change stock.
- Do not create a real rice inventory record during implementation or deployment; Brandon will enter the exact package description in the UI.
- Do not add bulk label printing, label-sheet templates, barcode editing/deletion, cloud services, or new database tables.
- Keep the existing UI language and make the new form, error, and print states usable at phone and desktop sizes.

## Acceptance

- Creating a label returns and stores a unique internal Code 128 value linked to the inventory item, records the stock change, and exposes the label date.
- Scanning that value returns the local product data without calling Open Food Facts; no stock is changed by the lookup.
- The page previews and prints the Code 128 graphic with readable item/package text and date.
- Invalid input and API failures are visible; writes remain behind existing Bearer auth.
- Automated tests, frontend build, and actual desktop/mobile UI inspection pass; README and feature screenshots are updated.

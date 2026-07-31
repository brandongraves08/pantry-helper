# 🥫 Pantry Inventory - Feature Guide

## Overview

The Pantry Helper inventory section allows you to:
- **View** all items currently in your pantry with detailed information
- **Manually Add** items to your inventory
- **Update Counts** for existing items (adjust, add, or set specific amounts)
- **Search & Filter** items by name or brand
- **Delete** items from inventory
- **Track** confidence levels and last seen dates

## Features

### 1. Inventory Display

The inventory table shows all items with the following information:

| Column | Description |
|--------|-------------|
| **Item** | Item name (canonical name) |
| **Brand** | Brand name (if available) |
| **Count** | Number of units in stock (red if ≤1) |
| **Confidence** | How confident the system is about the item (0-100%) |
| **Last Seen** | Date when item was last detected or updated |
| **Status** | Tags indicating special states (Low Stock, Expiring, Manual) |
| **Action** | Delete button to remove items |

### 2. Search & Filtering

- **Search Box**: Filter items by name or brand in real-time
- **Sort Options**:
  - Sort by Name (A-Z)
  - Sort by Count (highest first)
  - Sort by Confidence (most confident first)
  - Sort by Recent (most recently updated first)

### 3. Manual Item Management

#### Adding New Items

1. Go to the **"✏️ Add / Update Item"** panel on the right
2. Enter the **Item Name** (e.g., "peanut butter")
3. Optional: Add **Brand** and **Package Type** (box, can, jar, bag, bottle)
4. Select **Operation** mode:
   - **Set Count**: Replace the count with a new value
   - **Add**: Increment existing count by this amount
   - **Subtract**: Decrement existing count by this amount
5. Enter the **Amount**
6. Optional: Add **Notes** (e.g., expiry date, location)
7. Click **"Update Inventory"**

#### Auto-Suggestions

When you start typing an item name:
- Existing items matching your search appear as suggestions
- Click a suggestion to auto-fill brand and package type
- Helps maintain consistency for recurring items

#### Operation Modes Explained

**Set Count**
```
Current: peanut butter (2)
Operation: Set Count to 4
Result: peanut butter (4)
```

**Add**
```
Current: pasta (5)
Operation: Add 3
Result: pasta (8)
```

**Subtract**
```
Current: rice (4)
Operation: Subtract 1
Result: rice (3)
```

### 4. Status Indicators

- **Low Stock** (Red Badge): Item count ≤ 1
- **Expiring** (Orange Badge): Item expiring within 3 days
- **Manual** (Purple Badge): Item added manually (not from image analysis)

### 5. Confidence Levels

Confidence indicators show how certain the system is:

| Color | Confidence | Meaning |
|-------|-----------|---------|
| 🟢 Green | 80-100% | High confidence |
| 🟡 Yellow | 50-79% | Medium confidence |
| 🔴 Red | 0-49% | Low confidence |

Manual entries always have **100% confidence** since you entered them directly.

## Usage Examples

### Example 1: Add Your First Item

1. Item Name: `pasta`
2. Brand: `Barilla`
3. Package Type: `box`
4. Operation: `Set Count`
5. Amount: `3`
6. Notes: `Pantry shelf - top`
7. Result: Shows pasta (3x) with 100% confidence

### Example 2: Restock an Item

1. Click on suggestion: `peanut butter` (shows current: 2)
2. Operation: `Add`
3. Amount: `2`
4. Notes: `Restocked from store`
5. Result: peanut butter increases from 2 → 4

### Example 3: Track Low Stock

1. When rice count reaches 1, it shows:
   - Red count badge: `1`
   - Low Stock status indicator
   - Alert in dashboard stats

### Example 4: Remove an Item

1. Click the 🗑️ (trash icon) in the Action column
2. Confirm the deletion
3. Item is removed from inventory

## Search Tips

- **Partial Search**: Type "pea" to find "peanut butter"
- **Brand Search**: Type "Barilla" to find all Barilla products
- **Sort After Search**: Apply sorting to filtered results
- **Case Insensitive**: "PASTA" finds "pasta"

## Integration with Image Analysis

The inventory system works with the image upload feature:

1. **Upload Image**: Pantry Helper analyzes the image with Gemini Vision
2. **Automatic Detection**: Found items appear automatically with vision confidence
3. **Manual Override**: Use the Add/Update panel to adjust AI-detected counts
4. **Hybrid Approach**: Mix AI detection with manual corrections

## API Endpoints

If you're integrating with external tools:

### Get Inventory
```bash
curl http://localhost:8000/v1/inventory
```

### Manual Update
```bash
curl -X POST http://localhost:8000/v1/inventory/override \
  -H "Content-Type: application/json" \
  -d '{
    "item_name": "peanut butter",
    "count_estimate": 2,
    "notes": "restocked"
  }'
```

### Get Inventory History
```bash
curl http://localhost:8000/v1/inventory/history?days=7
```

## Best Practices

1. **Be Consistent**: Use the same item names for better tracking
2. **Add Brands**: Helps distinguish between similar items
3. **Use Notes**: Record expiry dates, locations, or special info
4. **Regular Updates**: Scan your pantry weekly to keep inventory current
5. **Low Stock Alerts**: Monitor the dashboard for items running low
6. **Search First**: Before adding a new item, search to avoid duplicates

## Common Tasks

### Task: Do a Full Pantry Inventory

1. Open the Add/Update panel
2. For each item on your shelf:
   - Enter the item name
   - Set count to the actual number
   - Add any notes (expiry date, location)
   - Click Update Inventory
3. Use sort-by-name to verify all items are entered
4. Take a screenshot for your records

### Task: Weekly Restock Update

1. Go through your pantry
2. For items you bought:
   - Search for the item
   - Click suggestion if available
   - Select "Add" operation
   - Enter quantity purchased
   - Click Update
3. For items you used:
   - Use "Subtract" operation
   - Enter quantity used

### Task: Move Items (Different Locations)

Use notes to track locations:
- "Added from kitchen shelf (top)"
- "Moved to pantry (left door)"
- "Location: Freezer"

## Troubleshooting

### Items Not Appearing
- Check confidence level (must be > 0 for manual items)
- Verify you clicked "Update Inventory"
- Try refreshing with the Refresh button

### Search Not Working
- Ensure you're typing the correct name/brand
- Try partial matches
- Check if item is marked as stale (confidence = 0)

### Count Seems Wrong
- Use "Set Count" to manually correct to actual value
- Check recent history to see what happened
- Add a note explaining the adjustment

## Future Features (Planned)

- 📱 Mobile app for quick updates
- 📊 Usage patterns and statistics
- 🛒 Shopping list generator (low stock alerts)
- 📸 Barcode scanning
- 🕐 Expiry date reminders
- 📍 Location tracking for multiple pantries
- 📈 Consumption rate predictions

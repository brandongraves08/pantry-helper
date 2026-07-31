#!/bin/bash
# Populate test inventory items via API

API_URL="http://localhost:8000"

echo "🥫 Populating test inventory items..."

# Test data
test_items=(
  "peanut butter:2:JIF:jar"
  "pasta:5:Barilla:box"
  "canned tomatoes:3:Hunt's:can"
  "olive oil:1:Bertolli:bottle"
  "rice:4:Uncle Ben's:bag"
  "cereal:1:Cheerios:box"
  "pasta sauce:2:Rao's:jar"
  "chicken broth:3:Swanson:can"
  "crackers:2:Goldfish:box"
  "chips:1:Lay's:bag"
)

for item in "${test_items[@]}"; do
  IFS=':' read -r name count brand package_type <<< "$item"
  
  echo -n "  Adding $name... "
  
  response=$(curl -s -X POST "$API_URL/v1/inventory/override" \
    -H "Content-Type: application/json" \
    -d "{
      \"item_name\": \"$name\",
      \"count_estimate\": $count,
      \"notes\": \"Test item - brand: $brand, type: $package_type\"
    }")
  
  if echo "$response" | grep -q "success"; then
    echo "✓"
  else
    echo "✗"
  fi
done

echo ""
echo "✓ Test inventory populated!"
echo ""
echo "Verify at: http://localhost:3000"
echo "API: http://localhost:8000/docs"

import { useEffect, useState, useRef } from 'react';
import { Barcode, Package, Plus, Link, Search, Check, X, Camera, AlertCircle, Loader, Smartphone } from 'lucide-react';
import * as api from '../api/client';
import CameraScanner from '../components/CameraScanner';

export default function BarcodeScan() {
  const [barcodeInput, setBarcodeInput] = useState('');
  const [scanning, setScanning] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [addCount, setAddCount] = useState(1);
  const [addPar, setAddPar] = useState(0);
  const [adding, setAdding] = useState(false);
  const [addSuccess, setAddSuccess] = useState(null);
  const [linkTarget, setLinkTarget] = useState('');
  const [linking, setLinking] = useState(false);
  const [showCamera, setShowCamera] = useState(false);
  const inputRef = useRef(null);

  // Auto-focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleScan = async () => {
    const barcode = barcodeInput.trim();
    if (!barcode) return;

    setScanning(true);
    setError(null);
    setResult(null);
    setAddSuccess(null);

    try {
      const data = await api.lookupBarcode(barcode);
      setResult(data);
      if (!data.found) {
        setError('Barcode not found in database');
      }
      if (data.already_in_inventory) {
        setAddSuccess(`Already tracked as "${data.existing_item_name}"`);
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Lookup failed');
    } finally {
      setScanning(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      handleScan();
    }
  };

  const handleAddToInventory = async () => {
    if (!result || !result.product_name) return;
    setAdding(true);
    setError(null);
    try {
      await api.addBarcodeToInventory({
        barcode: result.barcode,
        product_name: result.product_name,
        brand: result.brand || null,
        category: result.category || null,
        package_type: result.package_type || null,
        quantity_estimate: addCount,
        par_level: addPar || null,
      });
      setAddSuccess(`Added ${addCount}x ${result.product_name} to inventory`);
      setAddCount(1);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to add to inventory');
    } finally {
      setAdding(false);
    }
  };

  const handleLinkToItem = async () => {
    if (!result || !linkTarget.trim()) return;
    setLinking(true);
    setError(null);
    try {
      await api.linkBarcodeToItem(result.barcode, linkTarget.trim());
      setAddSuccess(`Linked barcode to "${linkTarget.trim()}"`);
      setLinkTarget('');
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to link barcode');
    } finally {
      setLinking(false);
    }
  };

  const handleClear = () => {
    setBarcodeInput('');
    setResult(null);
    setError(null);
    setAddSuccess(null);
    setAddCount(1);
    setAddPar(0);
    setLinkTarget('');
    inputRef.current?.focus();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl sm:text-2xl font-bold text-gray-900">Barcode Scanner</h2>
      </div>

      {/* Scan Input */}
      <div className="bg-white p-4 sm:p-6 rounded-xl border shadow-sm">
        <div className="flex items-center gap-4 mb-4">
          <div className="p-3 bg-blue-100 rounded-lg">
            <Barcode size={24} className="text-blue-600" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">Scan a Barcode</h3>
            <p className="text-sm text-gray-500">
              Type a barcode or use your camera to scan one
            </p>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Barcode size={20} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              ref={inputRef}
              type="text"
              placeholder="Enter barcode number..."
              value={barcodeInput}
              onChange={(e) => setBarcodeInput(e.target.value)}
              onKeyDown={handleKeyDown}
              className="w-full pl-10 pr-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-lg"
            />
          </div>
          <div className="flex gap-2 sm:gap-3">
            <button
              onClick={handleScan}
              disabled={scanning || !barcodeInput.trim()}
              className="flex items-center gap-2 px-4 sm:px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium flex-1 sm:flex-none justify-center"
            >
              {scanning ? (
                <><Loader size={20} className="animate-spin" /> Scanning...</>
              ) : (
                <><Search size={20} /> Look Up</>
              )}
            </button>
            <button
              onClick={() => setShowCamera(true)}
              className="flex items-center gap-2 px-3 sm:px-4 py-3 bg-white border-2 border-blue-500 text-blue-600 rounded-lg hover:bg-blue-50 font-medium flex-1 sm:flex-none justify-center"
            >
              <Camera size={20} />
              <span className="hidden sm:inline">Scan with Camera</span>
              <span className="sm:hidden">Camera</span>
            </button>
            {result && (
              <button onClick={handleClear} className="px-4 py-3 border rounded-lg hover:bg-gray-50 text-gray-600">
                <X size={20} />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-3 p-4 bg-red-50 border border-red-200 rounded-lg">
          <AlertCircle size={20} className="text-red-500" />
          <p className="text-red-700 text-sm">{error}</p>
        </div>
      )}

      {/* Result Card */}
      {result && result.found && (
        <div className="bg-white rounded-xl border shadow-sm overflow-hidden">
          {/* Product Header */}
          <div className="p-4 sm:p-6 border-b bg-gradient-to-r from-blue-50 to-white">
            <div className="flex flex-col sm:flex-row items-start gap-4 sm:gap-6">
              {result.image_url && (
                <img
                  src={result.image_url}
                  alt={result.product_name || 'Product'}
                  className="w-24 h-24 object-contain bg-white rounded-lg border"
                  onError={(e) => { e.target.style.display = 'none' }}
                />
              )}
              <div className="flex-1 min-w-0">
                <h3 className="text-xl font-bold text-gray-900">
                  {result.product_name || 'Unknown Product'}
                </h3>
                {result.brand && (
                  <p className="text-gray-600 mt-1">
                    <span className="font-medium">Brand:</span> {result.brand}
                  </p>
                )}
                {result.category && (
                  <p className="text-sm text-gray-500 mt-1">
                    <span className="font-medium">Category:</span> {result.category}
                  </p>
                )}
                {(result.quantity || result.package_type) && (
                  <div className="flex gap-2 mt-2">
                    {result.package_type && (
                      <span className="px-2 py-0.5 text-xs font-medium bg-gray-100 rounded">{result.package_type}</span>
                    )}
                    {result.quantity && (
                      <span className="px-2 py-0.5 text-xs font-medium bg-gray-100 rounded">{result.quantity}</span>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="p-4 sm:p-6 space-y-6">
            {/* Nutrition */}
            {result.nutrition && (
              <div>
                <h4 className="font-semibold text-gray-700 mb-2">Nutrition (per 100g)</h4>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {result.nutrition.energy_kcal != null && (
                    <NutritionBadge label="Calories" value={`${Math.round(result.nutrition.energy_kcal)} kcal`} />
                  )}
                  {result.nutrition.protein_g != null && (
                    <NutritionBadge label="Protein" value={`${result.nutrition.protein_g}g`} />
                  )}
                  {result.nutrition.carbs_g != null && (
                    <NutritionBadge label="Carbs" value={`${result.nutrition.carbs_g}g`} />
                  )}
                  {result.nutrition.fat_g != null && (
                    <NutritionBadge label="Fat" value={`${result.nutrition.fat_g}g`} />
                  )}
                </div>
              </div>
            )}

            {/* Allergens */}
            {result.allergens && result.allergens.length > 0 && (
              <div>
                <h4 className="font-semibold text-gray-700 mb-2">Allergens</h4>
                <div className="flex flex-wrap gap-2">
                  {result.allergens.map((allergen, i) => (
                    <span key={i} className="px-3 py-1 text-xs font-medium bg-red-50 text-red-700 rounded-full border border-red-200">
                      {allergen.replace(/_/g, ' ')}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Ingredients */}
            {result.ingredients_text && (
              <div>
                <h4 className="font-semibold text-gray-700 mb-1">Ingredients</h4>
                <p className="text-sm text-gray-600 line-clamp-2">{result.ingredients_text}</p>
              </div>
            )}

            {/* Success message */}
            {addSuccess && (
              <div className="flex items-center gap-2 p-3 bg-green-50 border border-green-200 rounded-lg">
                <Check size={16} className="text-green-600" />
                <p className="text-green-700 text-sm">{addSuccess}</p>
              </div>
            )}

            {/* Action buttons */}
            <div className="border-t pt-4 space-y-4">
              {/* Add to Inventory */}
              <div className="flex flex-wrap items-center gap-3">
                <div className="flex items-center gap-2">
                  <label className="text-sm font-medium text-gray-700">Count:</label>
                  <input
                    type="number"
                    min={1}
                    value={addCount}
                    onChange={(e) => setAddCount(Math.max(1, parseInt(e.target.value) || 1))}
                    className="w-20 px-3 py-2 border rounded-lg text-center"
                  />
                </div>
                <div className="flex items-center gap-2">
                  <label className="text-sm font-medium text-gray-700">Par:</label>
                  <input
                    type="number"
                    min={0}
                    value={addPar}
                    onChange={(e) => setAddPar(Math.max(0, parseInt(e.target.value) || 0))}
                    className="w-20 px-3 py-2 border rounded-lg text-center"
                  />
                </div>
                <button
                  onClick={handleAddToInventory}
                  disabled={adding || !result.product_name}
                  className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                >
                  {adding ? <Loader size={16} className="animate-spin" /> : <Plus size={16} />}
                  Add to Inventory
                </button>
              </div>

              {/* Link to existing item */}
              <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 border-t pt-3">
                <div className="relative flex-1 max-w-xs">
                  <Link size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Link to existing item name..."
                    value={linkTarget}
                    onChange={(e) => setLinkTarget(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <button
                  onClick={handleLinkToItem}
                  disabled={linking || !linkTarget.trim()}
                  className="flex items-center gap-2 px-4 py-2 border rounded-lg hover:bg-gray-50 disabled:opacity-50 text-sm"
                >
                  {linking ? <Loader size={16} className="animate-spin" /> : <Link size={16} />}
                  Link
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Not found */}
      {result && !result.found && !error && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4 sm:p-6 text-center">
          <Barcode size={48} className="mx-auto text-yellow-400 mb-3" />
          <h3 className="font-semibold text-yellow-800">Barcode Not Found</h3>
          <p className="text-sm text-yellow-600 mt-1">
            No product data found for barcode <strong>{barcodeInput}</strong>
          </p>
          <p className="text-sm text-yellow-500 mt-2">
            You can still enter the product name manually and add it to inventory.
          </p>
        </div>
      )}

      {/* Camera Scanner Modal */}
      {showCamera && (
        <CameraScanner
          onDetected={(code) => {
            setBarcodeInput(code);
            setShowCamera(false);
            // Auto-lookup after a brief delay to let state settle
            setTimeout(() => {
              setBarcodeInput(code);
              setScanning(true);
              api.lookupBarcode(code).then(data => {
                setResult(data);
                if (!data.found) setError('Barcode not found in database');
                if (data.already_in_inventory) setAddSuccess(`Already tracked as "${data.existing_item_name}"`);
              }).catch(err => {
                setError(err.response?.data?.detail || err.message || 'Lookup failed');
              }).finally(() => setScanning(false));
            }, 100);
          }}
          onClose={() => setShowCamera(false)}
        />
      )}

      {/* Quick tips card - collapsed on mobile when not scanning */}
      {!result && (
        <div className="bg-gray-50 border rounded-xl p-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Tips</h4>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs text-gray-500">
            <div className="p-3 bg-white rounded border flex items-start gap-2">
              <Smartphone size={16} className="mt-0.5 text-blue-500 shrink-0" />
              <div>
                <span className="font-medium text-gray-700">Phone</span>
                <p>Tap "Scan with Camera" and point at the barcode</p>
              </div>
            </div>
            <div className="p-3 bg-white rounded border flex items-start gap-2">
              <Barcode size={16} className="mt-0.5 text-gray-500 shrink-0" />
              <div>
                <span className="font-medium text-gray-700">Manual</span>
                <p>Type the barcode number (UPC-A, EAN-13, or EAN-8)</p>
              </div>
            </div>
            <div className="p-3 bg-white rounded border flex items-start gap-2">
              <Package size={16} className="mt-0.5 text-green-500 shrink-0" />
              <div>
                <span className="font-medium text-gray-700">Add it</span>
                <p>Once scanned, add it straight to inventory</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function NutritionBadge({ label, value }) {
  return (
    <div className="bg-gray-50 rounded-lg p-3 border">
      <p className="text-xs text-gray-500">{label}</p>
      <p className="text-lg font-semibold text-gray-800">{value}</p>
    </div>
  );
}

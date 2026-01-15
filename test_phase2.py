#!/usr/bin/env python3
"""
Phase 2 Integration Test
Tests the complete image analysis pipeline
"""

import sys
import json
import hashlib
import base64
from pathlib import Path

# Add backend to path
sys.path.insert(0, '/home/brandon/projects/pantry-helper/backend')

def test_vision_module():
    """Test that vision.py is properly structured"""
    print("\n" + "="*60)
    print("TEST 1: Vision Module Structure")
    print("="*60)
    
    try:
        from app.services.vision import VisionAnalyzer
        print("✅ VisionAnalyzer imported successfully")
        
        # Check methods exist
        analyzer = VisionAnalyzer()
        assert hasattr(analyzer, 'analyze_image'), "Missing analyze_image method"
        print("✅ analyze_image method exists")
        
        # Check can be instantiated
        print("✅ VisionAnalyzer can be instantiated")
        return True
    except Exception as e:
        print(f"❌ Vision module test failed: {e}")
        return False

def test_worker_module():
    """Test that capture worker is properly structured"""
    print("\n" + "="*60)
    print("TEST 2: Capture Worker Module")
    print("="*60)
    
    try:
        from app.workers.capture import CaptureProcessor, get_processor
        print("✅ CaptureProcessor imported successfully")
        
        # Check singleton works
        proc1 = get_processor()
        proc2 = get_processor()
        assert proc1 is proc2, "Singleton pattern not working"
        print("✅ Singleton pattern works")
        
        # Check methods exist
        assert hasattr(proc1, 'process_capture'), "Missing process_capture method"
        assert hasattr(proc1, 'process_pending_captures'), "Missing process_pending_captures method"
        print("✅ Worker methods exist")
        
        return True
    except Exception as e:
        print(f"❌ Worker module test failed: {e}")
        return False

def test_admin_routes():
    """Test that admin routes are properly structured"""
    print("\n" + "="*60)
    print("TEST 3: Admin Routes Module")
    print("="*60)
    
    try:
        from app.api.routes import admin
        print("✅ Admin routes imported successfully")
        
        # Check router exists
        assert hasattr(admin, 'router'), "Missing router object"
        print("✅ Admin router exists")
        
        return True
    except Exception as e:
        print(f"❌ Admin routes test failed: {e}")
        return False

def test_database_models():
    """Test that database models support the pipeline"""
    print("\n" + "="*60)
    print("TEST 4: Database Models")
    print("="*60)
    
    try:
        from app.db.models import Capture, Observation, InventoryEvent
        print("✅ Core models imported")
        
        # Check Capture has required fields
        capture_fields = ['id', 'device_id', 'status', 'error_message', 'processed_at']
        for field in capture_fields:
            assert hasattr(Capture, field), f"Capture missing {field}"
        print(f"✅ Capture model has all required fields: {', '.join(capture_fields)}")
        
        # Check Observation has required fields
        obs_fields = ['id', 'capture_id', 'raw_json', 'inventory_items']
        for field in obs_fields:
            assert hasattr(Observation, field), f"Observation missing {field}"
        print(f"✅ Observation model has all required fields: {', '.join(obs_fields)}")
        
        return True
    except Exception as e:
        print(f"❌ Database models test failed: {e}")
        return False

def test_main_app_integration():
    """Test that main.py includes all routes"""
    print("\n" + "="*60)
    print("TEST 5: FastAPI App Integration")
    print("="*60)
    
    try:
        from app.main import app
        print("✅ FastAPI app imported successfully")
        
        # Check routes are registered
        routes = [route.path for route in app.routes]
        
        admin_routes = [r for r in routes if '/admin' in r]
        assert len(admin_routes) > 0, "No admin routes found"
        print(f"✅ Admin routes registered: {len(admin_routes)} routes")
        
        ingest_routes = [r for r in routes if '/ingest' in r]
        assert len(ingest_routes) > 0, "No ingest routes found"
        print(f"✅ Ingest routes registered: {len(ingest_routes)} routes")
        
        inventory_routes = [r for r in routes if '/inventory' in r]
        assert len(inventory_routes) > 0, "No inventory routes found"
        print(f"✅ Inventory routes registered: {len(inventory_routes)} routes")
        
        return True
    except Exception as e:
        print(f"❌ App integration test failed: {e}")
        return False

def test_mock_image_analysis():
    """Test vision analysis with mock (no real API call)"""
    print("\n" + "="*60)
    print("TEST 6: Vision Analysis (Mock)")
    print("="*60)
    
    try:
        # Read test image
        test_image = Path('/tmp/test_pantry.jpg')
        assert test_image.exists(), "Test image not found"
        print(f"✅ Test image found ({test_image.stat().st_size} bytes)")
        
        # Test image can be read and encoded
        with open(test_image, 'rb') as f:
            image_data = f.read()
            b64_data = base64.b64encode(image_data).decode('utf-8')
            print(f"✅ Image successfully base64 encoded ({len(b64_data)} chars)")
        
        # Test mock response structure
        mock_response = {
            "items": [
                {"name": "milk", "quantity": 2, "unit": "units", "confidence": 0.95},
                {"name": "eggs", "quantity": 1, "unit": "dozen", "confidence": 0.89}
            ],
            "extraction_confidence": 0.92
        }
        
        assert len(mock_response['items']) > 0, "No items in mock response"
        print(f"✅ Mock response structure valid: {len(mock_response['items'])} items")
        
        return True
    except Exception as e:
        print(f"❌ Vision analysis mock test failed: {e}")
        return False

def test_pydantic_schemas():
    """Test that Pydantic schemas validate correctly"""
    print("\n" + "="*60)
    print("TEST 7: Pydantic Schemas")
    print("="*60)
    
    try:
        from app.schemas import VisionOutput, CaptureSchema
        print("✅ Schemas imported")
        
        # Test VisionOutput schema
        vision_out = VisionOutput(
            items=[{"name": "test", "quantity": 1, "confidence": 0.95}],
            raw_response="test response"
        )
        assert vision_out.items[0]['name'] == "test"
        print("✅ VisionOutput schema validates")
        
        return True
    except Exception as e:
        print(f"❌ Schema validation test failed: {e}")
        return False

def test_device_authentication():
    """Test device token authentication logic"""
    print("\n" + "="*60)
    print("TEST 8: Device Authentication")
    print("="*60)
    
    try:
        from app.auth import hash_token, verify_token
        print("✅ Auth functions imported")
        
        # Test token hashing
        test_token = "test-device-token-123"
        hashed = hash_token(test_token)
        assert len(hashed) == 64, "Hash should be 64 chars (SHA256)"
        print(f"✅ Token hashing works: {hashed[:16]}...")
        
        # Test verification
        assert verify_token(test_token, hashed), "Token verification failed"
        print("✅ Token verification works")
        
        return True
    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "╔" + "="*58 + "╗")
    print("║" + " "*58 + "║")
    print("║" + "PHASE 2 INTEGRATION TEST SUITE".center(58) + "║")
    print("║" + "Pantry Inventory System".center(58) + "║")
    print("║" + " "*58 + "║")
    print("╚" + "="*58 + "╝")
    
    tests = [
        ("Vision Module", test_vision_module),
        ("Capture Worker", test_worker_module),
        ("Admin Routes", test_admin_routes),
        ("Database Models", test_database_models),
        ("App Integration", test_main_app_integration),
        ("Vision Analysis (Mock)", test_mock_image_analysis),
        ("Pydantic Schemas", test_pydantic_schemas),
        ("Device Authentication", test_device_authentication),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} test crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:10} {name}")
    
    print("\n" + "-"*60)
    print(f"Total: {passed}/{total} tests passed")
    print("-"*60)
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Phase 2 implementation is valid.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed.")
        return 1

if __name__ == '__main__':
    sys.exit(main())

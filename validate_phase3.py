#!/usr/bin/env python3
"""Phase 3 validation - checks all components are properly integrated."""

import ast
import sys
from pathlib import Path


def validate_config_settings():
    """Validate config.py has all Phase 3 settings."""
    config_path = Path("backend/app/config.py")
    with open(config_path) as f:
        content = f.read()
    
    required_settings = [
        "RATE_LIMIT_ENABLED",
        "RATE_LIMIT_REQUESTS",
        "RATE_LIMIT_PERIOD",
        "REDIS_URL",
        "CELERY_BROKER_URL",
        "CELERY_RESULT_BACKEND",
        "JOB_TIMEOUT",
        "MAX_RETRIES",
    ]
    
    for setting in required_settings:
        if setting not in content:
            print(f"❌ Missing setting: {setting}")
            return False
    
    print("✅ Configuration complete")
    return True


def validate_celery_tasks():
    """Validate celery_app.py has all required tasks."""
    celery_path = Path("backend/app/workers/celery_app.py")
    
    if not celery_path.exists():
        print("❌ celery_app.py not found")
        return False
    
    with open(celery_path) as f:
        tree = ast.parse(f.read())
    
    task_names = [
        "process_image_capture",
        "process_pending_captures",
        "cleanup_old_captures",
    ]
    
    found_tasks = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            found_tasks.append(node.name)
    
    for task in task_names:
        if task not in found_tasks:
            print(f"❌ Missing task: {task}")
            return False
    
    print("✅ Celery tasks implemented")
    return True


def validate_rate_limit_middleware():
    """Validate rate_limit.py has all components."""
    middleware_path = Path("backend/app/middleware/rate_limit.py")
    
    if not middleware_path.exists():
        print("❌ rate_limit.py not found")
        return False
    
    with open(middleware_path) as f:
        content = f.read()
    
    required_classes = [
        "RateLimitStore",
        "RateLimitMiddleware",
        "AdaptiveRateLimit",
    ]
    
    for cls in required_classes:
        if f"class {cls}" not in content:
            print(f"❌ Missing class: {cls}")
            return False
    
    print("✅ Rate limit middleware implemented")
    return True


def validate_admin_routes():
    """Validate admin.py has job queue integration."""
    admin_path = Path("backend/app/api/routes/admin.py")
    
    with open(admin_path) as f:
        content = f.read()
    
    required_imports = [
        "from app.workers.celery_app import",
        "process_image_capture",
        "process_pending_captures",
        "celery_app",
    ]
    
    for imp in required_imports:
        if imp not in content:
            print(f"❌ Missing import: {imp}")
            return False
    
    required_endpoints = [
        "process_capture",
        "process_pending",
        "get_task_status",
        "cancel_task",
        "get_queue_info",
    ]
    
    for endpoint in required_endpoints:
        if f"def {endpoint}" not in content:
            print(f"❌ Missing endpoint: {endpoint}")
            return False
    
    print("✅ Admin routes updated with job queue")
    return True


def validate_main_integration():
    """Validate main.py includes rate limit middleware."""
    main_path = Path("backend/app/main.py")
    
    with open(main_path) as f:
        content = f.read()
    
    if "from app.middleware.rate_limit import RateLimitMiddleware" not in content:
        print("❌ RateLimitMiddleware not imported in main.py")
        return False
    
    if "app.add_middleware(RateLimitMiddleware)" not in content:
        print("❌ RateLimitMiddleware not added to app")
        return False
    
    print("✅ Main app integrated with rate limiting")
    return True


def validate_tests():
    """Validate test files exist."""
    test_files = [
        "backend/tests/test_phase3.py",
        "backend/tests/test_e2e.py",
    ]
    
    for test_file in test_files:
        if not Path(test_file).exists():
            print(f"❌ Test file not found: {test_file}")
            return False
    
    # Check test counts
    phase3_path = Path("backend/tests/test_phase3.py")
    with open(phase3_path) as f:
        content = f.read()
    
    test_methods = content.count("def test_")
    if test_methods < 15:
        print(f"❌ Phase 3 tests incomplete (found {test_methods}, need >= 15)")
        return False
    
    e2e_path = Path("backend/tests/test_e2e.py")
    with open(e2e_path) as f:
        content = f.read()
    
    e2e_tests = content.count("def test_")
    if e2e_tests < 8:
        print(f"❌ E2E tests incomplete (found {e2e_tests}, need >= 8)")
        return False
    
    print(f"✅ Tests implemented ({test_methods} Phase 3 + {e2e_tests} E2E)")
    return True


def validate_documentation():
    """Validate documentation files."""
    doc_path = Path("PHASE_3_COMPLETE.md")
    
    if not doc_path.exists():
        print("❌ PHASE_3_COMPLETE.md not found")
        return False
    
    with open(doc_path) as f:
        content = f.read()
    
    required_sections = [
        "Job Queue",
        "Rate Limiting",
        "Configuration",
        "Testing",
        "Deployment",
        "Usage Examples",
    ]
    
    for section in required_sections:
        if section not in content:
            print(f"❌ Missing documentation section: {section}")
            return False
    
    print("✅ Documentation complete")
    return True


def main():
    """Run all validations."""
    print("\n" + "="*60)
    print("PHASE 3 VALIDATION")
    print("="*60 + "\n")
    
    validations = [
        ("Configuration", validate_config_settings),
        ("Celery Tasks", validate_celery_tasks),
        ("Rate Limit Middleware", validate_rate_limit_middleware),
        ("Admin Routes", validate_admin_routes),
        ("Main Integration", validate_main_integration),
        ("Tests", validate_tests),
        ("Documentation", validate_documentation),
    ]
    
    results = []
    for name, validator in validations:
        print(f"\n📋 Checking {name}...")
        try:
            result = validator()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Error: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    if passed == total:
        print(f"✅ ALL VALIDATIONS PASSED ({passed}/{total})")
        print("="*60 + "\n")
        return 0
    else:
        print(f"❌ SOME VALIDATIONS FAILED ({passed}/{total})")
        print("="*60 + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())

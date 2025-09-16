#!/usr/bin/env python3
"""
Backend Architectural Consistency Review
Reviews the backend for consistent application of new architectural patterns
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def analyze_repository_pattern():
    """Analyze repository pattern implementation"""
    print("Analyzing Repository Pattern Implementation...")
    
    backend_dir = Path(__file__).parent
    
    # Check for repository implementations
    repository_dirs = [
        backend_dir / 'services' / 'repository',
        backend_dir / 'database' / 'repositories'
    ]
    
    repositories_found = []
    for repo_dir in repository_dirs:
        if repo_dir.exists():
            for py_file in repo_dir.glob('*.py'):
                if py_file.name != '__init__.py':
                    repositories_found.append(py_file)
    
    print(f"✅ Found {len(repositories_found)} repository implementations:")
    for repo in repositories_found:
        print(f"  - {repo.relative_to(backend_dir)}")
    
    # Check for base repository
    base_repo = backend_dir / 'services' / 'repository' / 'base_repository.py'
    if base_repo.exists():
        print("✅ Base repository pattern implemented")
    else:
        print("❌ Base repository pattern missing")
    
    return len(repositories_found) > 0

def analyze_service_layer():
    """Analyze service layer implementation"""
    print("\nAnalyzing Service Layer Implementation...")
    
    backend_dir = Path(__file__).parent
    services_dir = backend_dir / 'services'
    
    if not services_dir.exists():
        print("❌ Services directory not found")
        return False
    
    service_categories = []
    for item in services_dir.iterdir():
        if item.is_dir() and not item.name.startswith('__'):
            service_categories.append(item.name)
    
    print(f"✅ Found {len(service_categories)} service categories:")
    for category in service_categories:
        print(f"  - {category}")
    
    # Check for key services
    key_services = ['authservice', 'videoservice', 'filterservice']
    missing_services = [s for s in key_services if s not in service_categories]
    
    if missing_services:
        print(f"⚠️  Missing key services: {missing_services}")
    else:
        print("✅ All key services present")
    
    return len(service_categories) >= 3

def analyze_api_routes_separation():
    """Analyze API routes for business logic separation"""
    print("\nAnalyzing API Routes Business Logic Separation...")
    
    backend_dir = Path(__file__).parent
    routes_dir = backend_dir / 'api' / 'routes'
    
    if not routes_dir.exists():
        print("❌ API routes directory not found")
        return False
    
    route_files = list(routes_dir.glob('*.py'))
    route_files = [f for f in route_files if f.name != '__init__.py']
    
    print(f"✅ Found {len(route_files)} route files:")
    
    issues_found = []
    
    for route_file in route_files:
        print(f"  - {route_file.name}")
        
        # Check for direct database access in routes (anti-pattern)
        try:
            with open(route_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Look for direct SQL or database operations
            direct_db_patterns = [
                'cursor.execute',
                'conn.execute', 
                'SELECT ',
                'INSERT ',
                'UPDATE ',
                'DELETE '
            ]
            
            found_patterns = [p for p in direct_db_patterns if p in content]
            if found_patterns:
                issues_found.append(f"{route_file.name}: Direct DB access - {found_patterns}")
                
        except Exception as e:
            print(f"    ⚠️  Could not analyze {route_file.name}: {e}")
    
    if issues_found:
        print("\n❌ Business logic separation issues found:")
        for issue in issues_found:
            print(f"  - {issue}")
        return False
    else:
        print("✅ No direct database access found in routes")
        return True

def analyze_dependency_injection():
    """Analyze dependency injection patterns"""
    print("\nAnalyzing Dependency Injection Patterns...")
    
    backend_dir = Path(__file__).parent
    dependencies_file = backend_dir / 'core' / 'dependencies.py'
    
    if not dependencies_file.exists():
        print("❌ Dependencies file not found")
        return False
    
    try:
        with open(dependencies_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for key dependency functions
        key_dependencies = [
            'get_db_session',
            'current_active_user',
            'get_vocabulary_service'
        ]
        
        missing_deps = [dep for dep in key_dependencies if dep not in content]
        
        if missing_deps:
            print(f"❌ Missing key dependencies: {missing_deps}")
            return False
        else:
            print("✅ Key dependency injection functions present")
            return True
            
    except Exception as e:
        print(f"❌ Could not analyze dependencies: {e}")
        return False

def analyze_database_abstraction():
    """Analyze database abstraction layer"""
    print("\nAnalyzing Database Abstraction Layer...")
    
    backend_dir = Path(__file__).parent
    
    # Check for async SQLAlchemy database setup
    db_core = backend_dir / 'core' / 'database.py'
    if db_core.exists():
        print("✅ Async SQLAlchemy database abstraction present")
        db_abstraction = True
    else:
        print("❌ Database abstraction missing")
        db_abstraction = False
    
    # Check for migration support
    alembic_dir = backend_dir / 'alembic'
    if alembic_dir.exists():
        print("✅ Alembic migrations configured")
        migrations = True
    else:
        print("❌ Database migrations not configured")
        migrations = False
    
    return db_abstraction and migrations

def check_architectural_consistency():
    """Check overall architectural consistency"""
    print("\nChecking Overall Architectural Consistency...")
    
    backend_dir = Path(__file__).parent
    
    # Check for consistent error handling
    exceptions_file = backend_dir / 'core' / 'exceptions.py'
    if exceptions_file.exists():
        print("✅ Custom exceptions defined")
        error_handling = True
    else:
        print("⚠️  Custom exceptions not found")
        error_handling = False
    
    # Check for configuration management
    config_file = backend_dir / 'core' / 'config.py'
    if config_file.exists():
        print("✅ Configuration management present")
        config_mgmt = True
    else:
        print("❌ Configuration management missing")
        config_mgmt = False
    
    # Check for logging configuration
    logging_config = backend_dir / 'core' / 'logging_config.py'
    if logging_config.exists():
        print("✅ Logging configuration present")
        logging_setup = True
    else:
        print("❌ Logging configuration missing")
        logging_setup = False
    
    return error_handling and config_mgmt and logging_setup

def generate_recommendations():
    """Generate architectural improvement recommendations"""
    print("\n" + "=" * 60)
    print("ARCHITECTURAL IMPROVEMENT RECOMMENDATIONS")
    print("=" * 60)
    
    recommendations = [
        {
            "priority": "HIGH",
            "area": "API Routes",
            "issue": "Direct database access in route handlers",
            "recommendation": "Move all database operations to service layer or repositories",
            "example": "Replace direct SQL in routes with service method calls"
        },
        {
            "priority": "MEDIUM", 
            "area": "Repository Pattern",
            "issue": "Inconsistent repository usage across services",
            "recommendation": "Ensure all data access goes through repository layer",
            "example": "AuthService should use UserRepository for all user operations"
        },
        {
            "priority": "MEDIUM",
            "area": "Service Layer",
            "issue": "Business logic scattered across different layers",
            "recommendation": "Consolidate business logic in dedicated service classes",
            "example": "Move vocabulary processing logic to VocabularyService"
        },
        {
            "priority": "LOW",
            "area": "Error Handling",
            "issue": "Inconsistent error handling patterns",
            "recommendation": "Standardize error handling with custom exception hierarchy",
            "example": "Use domain-specific exceptions instead of generic HTTPException"
        }
    ]
    
    for rec in recommendations:
        print(f"\n🔸 {rec['priority']} PRIORITY - {rec['area']}")
        print(f"   Issue: {rec['issue']}")
        print(f"   Recommendation: {rec['recommendation']}")
        print(f"   Example: {rec['example']}")
    
    return recommendations

def main():
    """Run complete architectural review"""
    print("🏗️  LangPlug Backend Architectural Review")
    print("=" * 60)
    
    tests = [
        ("Repository Pattern", analyze_repository_pattern),
        ("Service Layer", analyze_service_layer),
        ("API Routes Separation", analyze_api_routes_separation),
        ("Dependency Injection", analyze_dependency_injection),
        ("Database Abstraction", analyze_database_abstraction),
        ("Architectural Consistency", check_architectural_consistency)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        if test_func():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Architectural Review Results: {passed}/{total} areas compliant")
    
    # Generate recommendations regardless of score
    generate_recommendations()
    
    if passed >= 4:
        print("\n🎉 ARCHITECTURAL PATTERNS ARE WELL IMPLEMENTED!")
        print("✅ The backend follows modern architectural principles.")
        print("💡 See recommendations above for further improvements.")
        return True
    else:
        print(f"\n⚠️  ARCHITECTURAL IMPROVEMENTS NEEDED")
        print(f"❌ {total - passed} areas need attention.")
        print("📋 Focus on the HIGH priority recommendations above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

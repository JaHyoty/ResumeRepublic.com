#!/usr/bin/env python3
"""
Test script to verify CareerPathPro setup
"""

import sys
import os

# Add backend to path
sys.path.append('backend')

def test_imports():
    """Test that all modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        from backend.app.core.config import settings
        print("✅ Configuration loaded")
        print(f"   Environment: {settings.ENVIRONMENT}")
        print(f"   Debug: {settings.DEBUG}")
    except Exception as e:
        print(f"❌ Configuration failed: {e}")
        return False
    
    try:
        from backend.app.models.user import User
        from backend.app.models.experience import Experience
        from backend.app.models.skill import Skill
        from backend.app.models.publication import Publication
        from backend.app.models.resume import ResumeVersion
        print("✅ Database models imported")
    except Exception as e:
        print(f"❌ Database models failed: {e}")
        return False
    
    try:
        from backend.app.main import app
        print("✅ FastAPI application created")
        print(f"   Title: {app.title}")
        print(f"   Version: {app.version}")
    except Exception as e:
        print(f"❌ FastAPI application failed: {e}")
        return False
    
    return True

def test_routes():
    """Test available routes"""
    print("\n🛣️  Testing routes...")
    
    try:
        from backend.app.main import app
        routes = []
        for route in app.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                routes.append(f"{route.path} ({', '.join(route.methods)})")
        
        print("✅ Available routes:")
        for route in routes:
            print(f"   - {route}")
    except Exception as e:
        print(f"❌ Route testing failed: {e}")
        return False
    
    return True

def test_frontend():
    """Test frontend structure"""
    print("\n🎨 Testing frontend structure...")
    
    frontend_files = [
        'frontend/package.json',
        'frontend/src/App.tsx',
        'frontend/src/main.tsx',
        'frontend/vite.config.ts',
        'frontend/tailwind.config.js'
    ]
    
    for file_path in frontend_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} missing")
            return False
    
    return True

def test_database_schema():
    """Test database schema file"""
    print("\n🗄️  Testing database schema...")
    
    if os.path.exists('database_schema.sql'):
        print("✅ database_schema.sql exists")
        with open('database_schema.sql', 'r') as f:
            content = f.read()
            if 'CREATE TABLE users' in content:
                print("✅ Users table definition found")
            if 'CREATE TABLE experiences' in content:
                print("✅ Experiences table definition found")
            if 'CREATE TABLE skills' in content:
                print("✅ Skills table definition found")
            return True
    else:
        print("❌ database_schema.sql missing")
        return False

def test_docker_config():
    """Test Docker configuration"""
    print("\n🐳 Testing Docker configuration...")
    
    docker_files = [
        'infrastructure/docker/docker-compose.yml',
        'backend/Dockerfile',
        'frontend/Dockerfile',
        'parsing-service/Dockerfile'
    ]
    
    for file_path in docker_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} missing")
            return False
    
    return True

def main():
    """Run all tests"""
    print("🚀 CareerPathPro Setup Test")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_routes,
        test_frontend,
        test_database_schema,
        test_docker_config
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 40)
    print(f"📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Setup is complete.")
        print("\n📋 Next steps:")
        print("1. Install PostgreSQL: sudo apt install postgresql postgresql-contrib")
        print("2. Run database setup: ./scripts/init-database.sh")
        print("3. Start backend: cd backend && uvicorn app.main:app --reload")
        print("4. Start frontend: cd frontend && npm install && npm run dev")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    main()

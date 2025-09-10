#!/usr/bin/env python3
"""
Test server startup time and implement proper monitoring
"""

import os
import sys
import time
import subprocess
import requests
from pathlib import Path
from datetime import datetime

def measure_startup_time():
    """Measure actual server startup time"""
    print("=" * 70)
    print("SERVER STARTUP TIME MEASUREMENT")
    print("=" * 70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 70)
    
    # Start the server
    print("\n1. Starting backend server...")
    start_time = time.time()
    
    # Use subprocess to start server
    backend_dir = Path(__file__).parent
    cmd = [
        str(backend_dir / "api_venv" / "Scripts" / "python.exe"),
        "main.py"
    ]
    
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    
    process = subprocess.Popen(
        cmd,
        cwd=backend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
    )
    
    print(f"   Server process started with PID: {process.pid}")
    
    # Monitor startup
    print("\n2. Monitoring startup progress...")
    
    startup_markers = [
        ("Logging configured", "Logging system initialized"),
        ("Middleware configured", "Middleware setup complete"),
        ("FastAPI application created", "FastAPI app ready"),
        ("Virtual environment active", "Virtual environment confirmed"),
        ("Database manager created", "Database connected"),
        ("Auth service created", "Authentication ready"),
        ("Vocabulary service created", "Vocabulary loaded"),
        ("Application startup complete", "Server fully started"),
    ]
    
    markers_found = []
    max_wait = 120  # 2 minutes max
    check_interval = 0.5
    elapsed = 0
    server_ready = False
    last_output = ""
    
    while elapsed < max_wait:
        # Check if process is still running
        if process.poll() is not None:
            print("\n[ERROR] Server process terminated unexpectedly!")
            stdout, stderr = process.communicate()
            print("STDOUT:", stdout[-1000:] if stdout else "None")
            print("STDERR:", stderr[-1000:] if stderr else "None")
            break
        
        # Try to read output (non-blocking would be better but complex on Windows)
        time.sleep(check_interval)
        elapsed = time.time() - start_time
        
        # Try HTTP connection
        if elapsed > 5:  # Start checking after 5 seconds
            try:
                response = requests.get("http://localhost:8000/docs", timeout=1)
                if response.status_code == 200:
                    server_ready = True
                    print(f"\n[SUCCESS] Server is responding! (after {elapsed:.1f} seconds)")
                    break
            except:
                pass
        
        # Print progress
        if int(elapsed) % 5 == 0 and int(elapsed) != int(elapsed - check_interval):
            print(f"   Waiting... {elapsed:.0f} seconds elapsed")
    
    # Results
    print("\n3. Startup Analysis:")
    print("-" * 70)
    
    if server_ready:
        print("[SUCCESS] Server started successfully")
        print(f"Total startup time: {elapsed:.1f} seconds")
        
        # Test endpoints
        print("\n4. Testing endpoints:")
        endpoints = [
            "/docs",
            "/openapi.json",
            "/auth/login",
            "/videos",
        ]
        
        for endpoint in endpoints:
            try:
                resp = requests.get(f"http://localhost:8000{endpoint}", timeout=2)
                status = "OK" if resp.status_code in [200, 401, 422] else f"Status {resp.status_code}"
                print(f"   {endpoint}: {status}")
            except Exception as e:
                print(f"   {endpoint}: Failed ({str(e)[:50]})")
        
        # Calculate recommended timeout
        recommended_timeout = max(30, elapsed * 2)
        print("\n5. Recommendations:")
        print(f"   - Actual startup time: {elapsed:.1f} seconds")
        print(f"   - Recommended timeout: {recommended_timeout:.0f} seconds")
        print("   - Status: Server is healthy and responding")
        
    else:
        print(f"[FAILED] Server did not start within {max_wait} seconds")
        print(f"Elapsed time: {elapsed:.1f} seconds")
        
        # Try to get process output
        try:
            stdout, stderr = process.communicate(timeout=1)
            print("\nLast output from server:")
            if stdout:
                print("STDOUT (last 500 chars):", stdout[-500:])
            if stderr:
                print("STDERR (last 500 chars):", stderr[-500:])
        except:
            pass
    
    # Cleanup
    print("\n6. Cleaning up...")
    try:
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/F", "/PID", str(process.pid)], capture_output=True)
        else:
            process.terminate()
            time.sleep(2)
            if process.poll() is None:
                process.kill()
    except:
        pass
    
    print("=" * 70)
    
    return elapsed if server_ready else None


def test_model_loading():
    """Test just Whisper model loading time"""
    print("\n" + "=" * 70)
    print("WHISPER MODEL LOADING TIME TEST")
    print("=" * 70)
    
    try:
        import whisper
        
        models = ["tiny", "base"]
        for model_name in models:
            print(f"\nLoading {model_name} model...")
            start = time.time()
            model = whisper.load_model(model_name)
            load_time = time.time() - start
            print(f"   {model_name} loaded in {load_time:.1f} seconds")
            del model  # Free memory
            
    except Exception as e:
        print(f"Could not test model loading: {e}")
    
    print("=" * 70)


if __name__ == "__main__":
    print("\nLangPlug Backend Startup Analysis")
    print("This will measure actual server startup time and provide recommendations.\n")
    
    # Test server startup
    startup_time = measure_startup_time()
    
    # Test model loading separately
    test_model_loading()
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    if startup_time:
        print(f"✓ Server startup successful: {startup_time:.1f} seconds")
        print(f"✓ Recommended timeout for tests: {max(30, startup_time * 2):.0f} seconds")
        print("\nThe server is NOT hanging - it just needs proper startup time.")
        print("Previous tests were timing out too quickly (5 second timeout).")
    else:
        print("✗ Server startup failed or took too long")
        print("Check the logs above for details")
    
    print("=" * 70)
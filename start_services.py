import subprocess
import time
import sys
import os
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# Ensure project root is in Python path
PROJECT_ROOT = Path(__file__).parent.absolute()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def start_service(script_path, service_name, wait_for_health=False, health_port=None):
    """Start a service and monitor it"""
    print(f"Starting {service_name}...")
    try:
        process = subprocess.Popen([sys.executable, script_path])
        print(f"✅ {service_name} started with PID {process.pid}")
        
        # Wait for health check if specified
        if wait_for_health and health_port:
            print(f"   Waiting for {service_name} to be ready...")
            for i in range(10):  # Try for 10 seconds
                try:
                    response = requests.get(f"http://localhost:{health_port}/health", timeout=2)
                    if response.status_code == 200:
                        print(f"   ✅ {service_name} is ready!")
                        break
                except:
                    time.sleep(1)
            else:
                print(f"   ⚠️  {service_name} may not be fully ready")
        
        return process
    except Exception as e:
        print(f"❌ Failed to start {service_name}: {e}")
        return None

def test_knowledge_server():
    """Test knowledge server functionality across all knowledge bases"""
    print("🔍 Testing Knowledge Server...")
    try:
        # Test health first
        response = requests.get("http://localhost:8005/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            knowledge_bases = data.get('knowledge_bases', [])
            kb_sizes = data.get('kb_sizes', {})
            print(f"   Knowledge bases loaded: {knowledge_bases}")
            print(f"   KB sizes: {kb_sizes}")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
        
        # Test queries for each knowledge base
        test_cases = [
            {
                "kb_name": "office",
                "query": "Excel crashes when opening large files",
                "expected_app": "Excel",
                "description": "Office KB - Excel crash test"
            },
            {
                "kb_name": "windows", 
                "query": "Windows 11 won't boot",
                "expected_contains": "boot",
                "description": "Windows KB - Boot issue test"
            },
            {
                "kb_name": "windows",
                "query": "Blue Screen of Death",
                "expected_contains": "BSOD",
                "description": "Windows KB - BSOD test"
            },
            {
                "kb_name": "hardware",
                "query": "Printer not responding",
                "expected_component": "Printer",
                "description": "Hardware KB - Printer issue test"
            },
            {
                "kb_name": "hardware",
                "query": "Monitor no display",
                "expected_component": "Monitor", 
                "description": "Hardware KB - Monitor issue test"
            }
        ]
        
        all_tests_passed = True
        
        for i, test_case in enumerate(test_cases):
            print(f"\n   Test {i+1}: {test_case['description']}")
            print(f"   Query: '{test_case['query']}'")
            
            try:
                search_response = requests.post(
                    f"http://localhost:8005/search/{test_case['kb_name']}",
                    json={"query": test_case['query'], "limit": 3},
                    timeout=10
                )
                
                if search_response.status_code == 200:
                    search_data = search_response.json()
                    results_count = search_data.get('count', 0)
                    results = search_data.get('results', [])
                    
                    print(f"   Results found: {results_count}")
                    
                    if results_count > 0:
                        print(f"   ✅ Search successful!")
                        
                        # Display results
                        for j, result in enumerate(results[:2]):  # Show first 2 results
                            if test_case['kb_name'] == 'office':
                                print(f"     {j+1}: {result.get('application', 'N/A')} - {result.get('issue', 'N/A')}")
                            elif test_case['kb_name'] == 'windows':
                                print(f"     {j+1}: {result.get('issue', 'N/A')} ({result.get('category', 'N/A')})")
                            elif test_case['kb_name'] == 'hardware':
                                print(f"     {j+1}: {result.get('component', 'N/A')} - {result.get('issue', 'N/A')}")
                        
                        # Validate expected results
                        first_result = results[0]
                        if 'expected_app' in test_case:
                            if first_result.get('application', '').lower() != test_case['expected_app'].lower():
                                print(f"   ⚠️  Expected application '{test_case['expected_app']}' but got '{first_result.get('application')}'")
                        elif 'expected_component' in test_case:
                            if first_result.get('component', '').lower() != test_case['expected_component'].lower():
                                print(f"   ⚠️  Expected component '{test_case['expected_component']}' but got '{first_result.get('component')}'")
                        elif 'expected_contains' in test_case:
                            result_text = str(first_result).lower()
                            if test_case['expected_contains'].lower() not in result_text:
                                print(f"   ⚠️  Expected to find '{test_case['expected_contains']}' in results")
                    else:
                        print(f"   ❌ No results found - this indicates a search issue!")
                        all_tests_passed = False
                else:
                    print(f"   ❌ Search failed: HTTP {search_response.status_code}")
                    print(f"   Response: {search_response.text[:200]}...")
                    all_tests_passed = False
                    
            except Exception as e:
                print(f"   ❌ Search test failed: {e}")
                all_tests_passed = False
        
        # Summary
        if all_tests_passed:
            print(f"\n   🎉 All knowledge base tests passed!")
            print(f"   ✅ Office KB: Working")
            print(f"   ✅ Windows KB: Working") 
            print(f"   ✅ Hardware KB: Working")
            return True
        else:
            print(f"\n   ⚠️  Some knowledge base tests failed!")
            return False
            
    except Exception as e:
        print(f"   ❌ Knowledge server test failed: {e}")
        return False

def main():
    services = [
        ("agents/windows_agent.py", "Windows Agent"),
        ("agents/office_agent.py", "Office Agent"), 
        ("agents/hardware_agent.py", "Hardware Agent"),
        ("agents/supervisor.py", "Supervisor Agent")
    ]
    
    processes = []
    
    print("🚀 Starting IT Support Multi-Agent System...")
    print("=" * 50)
    
    # Step 1: Start Knowledge Server first and wait for it to be ready
    print("Step 1: Starting Knowledge Server...")
    knowledge_process = start_service("servers/knowledge_server.py", "Knowledge Server", 
                                     wait_for_health=True, health_port=8005)
    if not knowledge_process:
        print("❌ Failed to start Knowledge Server. Aborting.")
        return
    
    processes.append(knowledge_process)
    
    # Step 2: Test knowledge server
    if not test_knowledge_server():
        print("❌ Knowledge Server is not working correctly!")
        print("   Please check the logs above for issues.")
        return
    
    print("\n" + "=" * 50)
    print("Step 2: Starting Agent Services...")
    
    # Start all agent services
    with ThreadPoolExecutor(max_workers=len(services)) as executor:
        futures = [executor.submit(start_service, script, name) for script, name in services]
        agent_processes = [future.result() for future in futures]
        processes.extend([p for p in agent_processes if p])
    
    # Wait a moment for services to start
    time.sleep(3)
    
    print("\n" + "=" * 50)
    print("Step 3: Starting Streamlit UI...")
    ui_process = subprocess.Popen([sys.executable, "-m", "streamlit", "run", "ui/app.py", "--server.port", "8501"])
    processes.append(ui_process)
    
    print(f"✅ Streamlit UI started with PID {ui_process.pid}")
    
    print("\n" + "=" * 50)
    print("🎉 All services started successfully!")
    print(f"📊 Streamlit UI: http://localhost:8501")
    print(f"🔍 Knowledge Server: http://localhost:8005/health")
    print("\n💡 Test the system with these queries:")
    print("   Office: 'Excel crashes when opening large files'")
    print("   Windows: 'Windows 11 won't boot'")  
    print("   Hardware: 'Printer not responding'")
    print("\nPress Ctrl+C to stop all services...")
    
    try:
        # Keep the main process running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping all services...")
        for process in processes:
            if process and process.poll() is None:
                process.terminate()
        print("✅ All services stopped.")

if __name__ == "__main__":
    main()
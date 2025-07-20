#!/usr/bin/env python3
"""
Test script to verify standardized JSON error responses for the API.
This script tests various error scenarios to ensure consistent error formatting.
"""

import requests
import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint
import tempfile
import os

console = Console()

API_BASE_URL = "http://127.0.0.1:8000"

def test_error_response_format(response_data, test_name):
    """Validate that error response follows the standardized schema."""
    required_fields = ['error', 'message', 'timestamp', 'request_id']
    
    # Check if all required fields are present
    missing_fields = [field for field in required_fields if field not in response_data]
    
    if missing_fields:
        return False, f"Missing fields: {missing_fields}"
    
    # Check error code format
    if not isinstance(response_data.get('error'), str):
        return False, "Error code should be a string"
    
    # Check if details is a list (if present)
    if 'details' in response_data and not isinstance(response_data['details'], list):
        return False, "Details should be a list"
    
    return True, "Valid error response format"

def run_test(test_name, test_func):
    """Run a single test and return results."""
    try:
        result = test_func()
        return {
            'name': test_name,
            'status': 'PASS' if result['success'] else 'FAIL',
            'message': result['message'],
            'response_data': result.get('response_data')
        }
    except Exception as e:
        return {
            'name': test_name,
            'status': 'ERROR',
            'message': f"Test error: {str(e)}",
            'response_data': None
        }

def test_file_too_large():
    """Test file size validation error."""
    # Create a large dummy file (simulate large file)
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
        # Write some data to simulate a file
        temp_file.write(b'dummy video content')
        temp_file_path = temp_file.name
    
    try:
        with open(temp_file_path, 'rb') as f:
            # Simulate large file by setting a fake size in headers
            files = {'file': ('large_video.mp4', f, 'video/mp4')}
            data = {
                'language': 'en',
                'src_lang': 'en',
                'tgt_lang': 'es'
            }
            
            response = requests.post(f"{API_BASE_URL}/api/process", files=files, data=data)
            
            if response.status_code in [400, 413, 422]:
                response_data = response.json()
                is_valid, validation_msg = test_error_response_format(response_data, "file_too_large")
                
                return {
                    'success': is_valid,
                    'message': f"Status: {response.status_code}, Validation: {validation_msg}",
                    'response_data': response_data
                }
            else:
                return {
                    'success': False,
                    'message': f"Expected error status, got {response.status_code}",
                    'response_data': response.json() if response.headers.get('content-type', '').startswith('application/json') else None
                }
    finally:
        os.unlink(temp_file_path)

def test_invalid_file_format():
    """Test unsupported file format error."""
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
        temp_file.write(b'This is not a video file')
        temp_file_path = temp_file.name
    
    try:
        with open(temp_file_path, 'rb') as f:
            files = {'file': ('document.txt', f, 'text/plain')}
            data = {
                'language': 'en',
                'src_lang': 'en',
                'tgt_lang': 'es'
            }
            
            response = requests.post(f"{API_BASE_URL}/api/process", files=files, data=data)
            
            if response.status_code in [400, 422]:
                response_data = response.json()
                is_valid, validation_msg = test_error_response_format(response_data, "invalid_file_format")
                
                return {
                    'success': is_valid,
                    'message': f"Status: {response.status_code}, Validation: {validation_msg}",
                    'response_data': response_data
                }
            else:
                return {
                    'success': False,
                    'message': f"Expected error status, got {response.status_code}",
                    'response_data': response.json() if response.headers.get('content-type', '').startswith('application/json') else None
                }
    finally:
        os.unlink(temp_file_path)

def test_missing_file():
    """Test missing file parameter error."""
    data = {
        'language': 'en',
        'src_lang': 'en',
        'tgt_lang': 'es'
    }
    
    response = requests.post(f"{API_BASE_URL}/api/process", data=data)
    
    if response.status_code == 422:
        response_data = response.json()
        is_valid, validation_msg = test_error_response_format(response_data, "missing_file")
        
        # Check if it's a validation error with invalid_fields
        has_invalid_fields = 'invalid_fields' in response_data
        
        return {
            'success': is_valid and has_invalid_fields,
            'message': f"Status: {response.status_code}, Validation: {validation_msg}, Has invalid_fields: {has_invalid_fields}",
            'response_data': response_data
        }
    else:
        return {
            'success': False,
            'message': f"Expected 422 status, got {response.status_code}",
            'response_data': response.json() if response.headers.get('content-type', '').startswith('application/json') else None
        }

def test_invalid_download_file_type():
    """Test invalid file type for download endpoint."""
    response = requests.get(f"{API_BASE_URL}/api/download/invalid_type", params={'video_path': '/fake/path.mp4'})
    
    if response.status_code == 400:
        response_data = response.json()
        is_valid, validation_msg = test_error_response_format(response_data, "invalid_download_file_type")
        
        return {
            'success': is_valid,
            'message': f"Status: {response.status_code}, Validation: {validation_msg}",
            'response_data': response_data
        }
    else:
        return {
            'success': False,
            'message': f"Expected 400 status, got {response.status_code}",
            'response_data': response.json() if response.headers.get('content-type', '').startswith('application/json') else None
        }

def test_file_not_found_download():
    """Test file not found error for download endpoint."""
    response = requests.get(f"{API_BASE_URL}/api/download/preview", params={'video_path': '/nonexistent/video.mp4'})
    
    if response.status_code == 404:
        response_data = response.json()
        is_valid, validation_msg = test_error_response_format(response_data, "file_not_found_download")
        
        return {
            'success': is_valid,
            'message': f"Status: {response.status_code}, Validation: {validation_msg}",
            'response_data': response_data
        }
    else:
        return {
            'success': False,
            'message': f"Expected 404 status, got {response.status_code}",
            'response_data': response.json() if response.headers.get('content-type', '').startswith('application/json') else None
        }

def test_legacy_endpoint_error():
    """Test error response from legacy endpoint."""
    invalid_request = {
        'video_file_path': '/nonexistent/video.mp4',
        'language': 'en',
        'src_lang': 'en',
        'tgt_lang': 'es'
    }
    
    response = requests.post(f"{API_BASE_URL}/api/process-legacy", json=invalid_request)
    
    if response.status_code in [400, 404, 500]:
        response_data = response.json()
        is_valid, validation_msg = test_error_response_format(response_data, "legacy_endpoint_error")
        
        return {
            'success': is_valid,
            'message': f"Status: {response.status_code}, Validation: {validation_msg}",
            'response_data': response_data
        }
    else:
        return {
            'success': False,
            'message': f"Expected error status, got {response.status_code}",
            'response_data': response.json() if response.headers.get('content-type', '').startswith('application/json') else None
        }

def main():
    """Run all error response tests."""
    console.print(Panel.fit("🧪 API Error Response Schema Tests", style="bold blue"))
    
    # Check if API is running
    try:
        health_response = requests.get(f"{API_BASE_URL}/api/upload-info", timeout=5)
        if health_response.status_code != 200:
            console.print("[red]❌ API health check failed. Make sure the API server is running.[/red]")
            return
    except requests.exceptions.RequestException:
        console.print("[red]❌ Cannot connect to API server. Make sure it's running on http://127.0.0.1:8000[/red]")
        return
    
    console.print("[green]✅ API server is running[/green]\n")
    
    # Define tests
    tests = [
        ("File Too Large", test_file_too_large),
        ("Invalid File Format", test_invalid_file_format),
        ("Missing File Parameter", test_missing_file),
        ("Invalid Download File Type", test_invalid_download_file_type),
        ("File Not Found Download", test_file_not_found_download),
        ("Legacy Endpoint Error", test_legacy_endpoint_error)
    ]
    
    # Run tests
    results = []
    for test_name, test_func in tests:
        console.print(f"Running: {test_name}...")
        result = run_test(test_name, test_func)
        results.append(result)
    
    # Display results
    console.print("\n")
    table = Table(title="Error Response Schema Test Results")
    table.add_column("Test", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Message", style="yellow")
    
    passed = 0
    for result in results:
        status_style = "green" if result['status'] == 'PASS' else "red"
        table.add_row(
            result['name'],
            f"[{status_style}]{result['status']}[/{status_style}]",
            result['message']
        )
        if result['status'] == 'PASS':
            passed += 1
    
    console.print(table)
    
    # Summary
    total = len(results)
    console.print(f"\n[bold]Summary: {passed}/{total} tests passed[/bold]")
    
    # Show sample error responses
    console.print("\n" + "="*50)
    console.print("[bold cyan]Sample Error Response Formats:[/bold cyan]")
    
    for result in results[:2]:  # Show first 2 error responses as examples
        if result['response_data']:
            console.print(f"\n[bold]{result['name']}:[/bold]")
            console.print(json.dumps(result['response_data'], indent=2))

if __name__ == "__main__":
    main()
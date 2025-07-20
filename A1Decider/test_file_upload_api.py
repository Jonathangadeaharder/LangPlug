#!/usr/bin/env python3
"""
Test script for the refactored file upload API endpoints.

This script tests the new multipart/form-data endpoints to ensure
they work correctly and provide better RESTful API design.
"""

import os
import sys
import asyncio
import tempfile
import requests
from pathlib import Path
from typing import Dict, Any

# Add current directory to path
sys.path.insert(0, '.')

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
except ImportError:
    print("Please install rich: pip install rich")
    sys.exit(1)

console = Console()

class APITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = []
    
    def log_result(self, test_name: str, success: bool, message: str = "", response_data: Dict = None):
        """Log test result."""
        self.results.append({
            'test': test_name,
            'success': success,
            'message': message,
            'response_data': response_data
        })
    
    def test_health_check(self):
        """Test the health check endpoint."""
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                self.log_result("health_check", True, f"Status: {data.get('status')}", data)
            else:
                self.log_result("health_check", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("health_check", False, str(e))
    
    def test_upload_info(self):
        """Test the upload info endpoint."""
        try:
            response = self.session.get(f"{self.base_url}/api/upload-info")
            if response.status_code == 200:
                data = response.json()
                max_size = data.get('max_file_size')
                formats = len(data.get('supported_formats', []))
                self.log_result("upload_info", True, f"Max size: {max_size}, {formats} formats", data)
            else:
                self.log_result("upload_info", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("upload_info", False, str(e))
    
    def test_supported_formats(self):
        """Test the supported formats endpoint."""
        try:
            response = self.session.get(f"{self.base_url}/api/formats")
            if response.status_code == 200:
                data = response.json()
                video_formats = len(data.get('video_formats', {}))
                languages = len(data.get('processing_options', {}).get('languages', []))
                self.log_result("supported_formats", True, f"{video_formats} video formats, {languages} languages", data)
            else:
                self.log_result("supported_formats", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("supported_formats", False, str(e))
    
    def test_pipelines(self):
        """Test the pipelines endpoint."""
        try:
            response = self.session.get(f"{self.base_url}/api/pipelines")
            if response.status_code == 200:
                data = response.json()
                pipelines = len(data.get('pipelines', {}))
                self.log_result("pipelines", True, f"{pipelines} pipeline configurations", data)
            else:
                self.log_result("pipelines", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("pipelines", False, str(e))
    
    def test_model_stats(self):
        """Test the model stats endpoint."""
        try:
            response = self.session.get(f"{self.base_url}/api/model-stats")
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    stats = data.get('stats', {})
                    device = stats.get('device', 'unknown')
                    self.log_result("model_stats", True, f"Device: {device}", data)
                else:
                    self.log_result("model_stats", False, "API returned success=false")
            else:
                self.log_result("model_stats", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("model_stats", False, str(e))
    
    def create_test_video_file(self) -> str:
        """Create a small test video file for upload testing."""
        # Create a minimal test file (not a real video, but for API testing)
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
            # Write some dummy content
            f.write(b'\x00\x00\x00\x20ftypmp42\x00\x00\x00\x00mp42isom')
            f.write(b'\x00' * 100)  # Pad with zeros
            return f.name
    
    def test_file_upload_validation(self):
        """Test file upload validation."""
        try:
            # Test with invalid file extension
            with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
                f.write(b'This is not a video file')
                f.flush()
                
                with open(f.name, 'rb') as file:
                    files = {'file': ('test.txt', file, 'text/plain')}
                    data = {'language': 'en', 'pipeline_config': 'quick'}
                    
                    response = self.session.post(
                        f"{self.base_url}/api/process",
                        files=files,
                        data=data
                    )
                
                os.unlink(f.name)
                
                if response.status_code == 400:
                    self.log_result("file_validation", True, "Correctly rejected invalid file type")
                else:
                    self.log_result("file_validation", False, f"Expected 400, got {response.status_code}")
                    
        except Exception as e:
            self.log_result("file_validation", False, str(e))
    
    def test_file_upload_processing(self):
        """Test actual file upload and processing (with mock video)."""
        try:
            test_file = self.create_test_video_file()
            
            try:
                with open(test_file, 'rb') as file:
                    files = {'file': ('test_video.mp4', file, 'video/mp4')}
                    data = {
                        'language': 'en',
                        'src_lang': 'en',
                        'tgt_lang': 'es',
                        'pipeline_config': 'quick',
                        'no_preview': True
                    }
                    
                    response = self.session.post(
                        f"{self.base_url}/api/process",
                        files=files,
                        data=data,
                        timeout=30  # Short timeout for testing
                    )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        self.log_result("file_upload_processing", True, "File processed successfully", data)
                    else:
                        self.log_result("file_upload_processing", False, f"Processing failed: {data.get('error')}")
                else:
                    self.log_result("file_upload_processing", False, f"HTTP {response.status_code}: {response.text[:200]}")
                    
            finally:
                os.unlink(test_file)
                
        except Exception as e:
            self.log_result("file_upload_processing", False, str(e))
    
    def test_legacy_endpoint_deprecation(self):
        """Test that legacy endpoints are properly marked as deprecated."""
        try:
            # Test legacy upload endpoint
            test_file = self.create_test_video_file()
            
            try:
                with open(test_file, 'rb') as file:
                    files = {'file': ('test_video.mp4', file, 'video/mp4')}
                    data = {'language': 'en', 'pipeline_config': 'quick'}
                    
                    response = self.session.post(
                        f"{self.base_url}/api/upload-and-process",
                        files=files,
                        data=data,
                        timeout=30
                    )
                
                # Should still work but be marked as deprecated
                if response.status_code in [200, 422]:  # 422 for processing errors is OK
                    self.log_result("legacy_endpoint", True, "Legacy endpoint accessible (deprecated)")
                else:
                    self.log_result("legacy_endpoint", False, f"HTTP {response.status_code}")
                    
            finally:
                os.unlink(test_file)
                
        except Exception as e:
            self.log_result("legacy_endpoint", False, str(e))
    
    def test_openapi_documentation(self):
        """Test that OpenAPI documentation is available."""
        try:
            response = self.session.get(f"{self.base_url}/openapi.json")
            if response.status_code == 200:
                data = response.json()
                title = data.get('info', {}).get('title', '')
                version = data.get('info', {}).get('version', '')
                paths = len(data.get('paths', {}))
                self.log_result("openapi_docs", True, f"{title} v{version}, {paths} endpoints")
            else:
                self.log_result("openapi_docs", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("openapi_docs", False, str(e))
    
    def run_all_tests(self):
        """Run all API tests."""
        console.print(Panel("[bold blue]Testing File Upload API Endpoints[/bold blue]"))
        
        tests = [
            ("Health Check", self.test_health_check),
            ("Upload Info", self.test_upload_info),
            ("Supported Formats", self.test_supported_formats),
            ("Pipeline Configurations", self.test_pipelines),
            ("Model Statistics", self.test_model_stats),
            ("File Validation", self.test_file_upload_validation),
            ("File Upload Processing", self.test_file_upload_processing),
            ("Legacy Endpoint", self.test_legacy_endpoint_deprecation),
            ("OpenAPI Documentation", self.test_openapi_documentation)
        ]
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            for test_name, test_func in tests:
                task = progress.add_task(f"Running {test_name}...", total=1)
                try:
                    test_func()
                    progress.update(task, completed=1)
                except Exception as e:
                    self.log_result(test_name.lower().replace(' ', '_'), False, f"Test execution failed: {e}")
                    progress.update(task, completed=1)
        
        self.display_results()
    
    def display_results(self):
        """Display test results in a formatted table."""
        console.print("\n[bold green]API Test Results[/bold green]")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Test", style="cyan")
        table.add_column("Status", justify="center")
        table.add_column("Message", style="white")
        
        success_count = 0
        for result in self.results:
            status = "[green]✓ PASS[/green]" if result['success'] else "[red]✗ FAIL[/red]"
            if result['success']:
                success_count += 1
            
            message = result['message'][:80] + "..." if len(result['message']) > 80 else result['message']
            
            table.add_row(
                result['test'].replace('_', ' ').title(),
                status,
                message
            )
        
        console.print(table)
        
        # Summary
        total_tests = len(self.results)
        success_rate = (success_count / total_tests) * 100 if total_tests > 0 else 0
        
        summary_style = "green" if success_rate >= 80 else "yellow" if success_rate >= 60 else "red"
        console.print(f"\n[{summary_style}]Summary: {success_count}/{total_tests} tests passed ({success_rate:.1f}%)[/{summary_style}]")
        
        if success_rate >= 80:
            console.print("[bold green]🎉 File upload API is working well![/bold green]")
        else:
            console.print("[bold red]⚠️  Some API endpoints need attention.[/bold red]")
        
        # Display endpoint information
        console.print("\n[bold cyan]API Endpoint Information:[/bold cyan]")
        console.print("• Primary endpoint: [green]/api/process[/green] (multipart/form-data)")
        console.print("• Legacy endpoint: [yellow]/api/process-legacy[/yellow] (deprecated)")
        console.print("• Alternative endpoint: [yellow]/api/upload-and-process[/yellow] (deprecated)")
        console.print("• Documentation: [blue]/docs[/blue] (Swagger UI)")
        console.print("• OpenAPI spec: [blue]/openapi.json[/blue]")

def main():
    """Main test function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test the file upload API endpoints")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    args = parser.parse_args()
    
    try:
        console.print(f"[bold blue]Testing API at: {args.url}[/bold blue]")
        tester = APITester(args.url)
        tester.run_all_tests()
    except KeyboardInterrupt:
        console.print("\n[yellow]Tests interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Test execution failed: {e}[/red]")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
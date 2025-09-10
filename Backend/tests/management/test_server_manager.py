"""
Unit tests for Server Manager
Tests server lifecycle management and monitoring
"""
import pytest
from unittest.mock import Mock, patch
from pathlib import Path
import tempfile
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from management.server_manager import ProfessionalServerManager
from management.config import ServerStatus


class TestProfessionalServerManager:
    """Test cases for ProfessionalServerManager"""

    @pytest.fixture
    def temp_state_file(self):
        """Create temporary state file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = Path(f.name)
        yield temp_path
        if temp_path.exists():
            temp_path.unlink()

    @pytest.fixture
    def mock_manager(self, temp_state_file):
        """Create server manager with mocked dependencies"""
        with patch('management.server_manager.PID_FILE', temp_state_file), \
             patch('management.server_manager.ProcessController'), \
             patch('management.server_manager.HealthMonitor'):
            manager = ProfessionalServerManager()
            return manager

    def test_initialization(self, mock_manager):
        """Test manager initialization"""
        assert mock_manager is not None
        assert "backend" in mock_manager.servers
        assert "frontend" in mock_manager.servers
        assert mock_manager.health_monitor is None

    def test_server_configuration(self, mock_manager):
        """Test server configuration setup"""
        backend = mock_manager.servers["backend"]
        frontend = mock_manager.servers["frontend"]
        
        assert backend.name == "backend"
        assert backend.port == 8000
        assert backend.startup_time == 15
        
        assert frontend.name == "frontend"
        assert frontend.port == 3000
        assert frontend.startup_time == 30

    def test_save_and_load_state(self, mock_manager, temp_state_file):
        """Test state persistence"""
        # Set up some state
        mock_manager.servers["backend"].pid = 12345
        mock_manager.servers["backend"].status = ServerStatus.RUNNING
        
        # Save state
        mock_manager._save_state()
        
        # Verify state file was created
        assert temp_state_file.exists()
        
        # Load state in new manager instance
        with patch('management.server_manager.PID_FILE', temp_state_file):
            new_manager = ProfessionalServerManager()
            
        # Note: In actual test, we'd need to mock ProcessController.is_process_running
        # to return False so the process isn't considered recovered

    def test_start_server_success(self, mock_manager):
        """Test successful server startup"""
        with patch.object(mock_manager.servers["backend"], 'is_port_in_use', return_value=False), \
             patch.object(mock_manager.servers["backend"], 'check_health', return_value=True), \
             patch('management.server_manager.ProcessController.start_process') as mock_start:
            
            # Mock successful process start
            mock_process = Mock()
            mock_process.pid = 12345
            mock_start.return_value = mock_process
            
            result = mock_manager.start_server("backend")
            
            assert result is True
            assert mock_manager.servers["backend"].status == ServerStatus.RUNNING
            assert mock_manager.servers["backend"].pid == 12345

    def test_start_server_port_in_use(self, mock_manager):
        """Test server startup when port is in use"""
        with patch.object(mock_manager.servers["backend"], 'is_port_in_use', return_value=True), \
             patch.object(mock_manager.servers["backend"], 'check_health', return_value=True), \
             patch('management.server_manager.ProcessController.cleanup_port') as mock_cleanup, \
             patch('management.server_manager.ProcessController.start_process') as mock_start, \
             patch('time.sleep'):  # Speed up tests
            
            mock_process = Mock()
            mock_process.pid = 12345
            mock_start.return_value = mock_process
            
            result = mock_manager.start_server("backend")
            
            mock_cleanup.assert_called_once_with(8000)
            assert result is True

    def test_start_server_health_check_failure(self, mock_manager):
        """Test server startup with health check failure"""
        with patch.object(mock_manager.servers["backend"], 'is_port_in_use', return_value=False), \
             patch.object(mock_manager.servers["backend"], 'check_health', return_value=False), \
             patch('management.server_manager.ProcessController.start_process') as mock_start, \
             patch('time.sleep'):  # Speed up tests
            
            mock_process = Mock()
            mock_process.pid = 12345
            mock_start.return_value = mock_process
            
            result = mock_manager.start_server("backend")
            
            assert result is False
            assert mock_manager.servers["backend"].status == ServerStatus.ERROR

    def test_start_unknown_server(self, mock_manager):
        """Test starting non-existent server"""
        result = mock_manager.start_server("unknown_server")
        assert result is False

    def test_stop_server_success(self, mock_manager):
        """Test successful server shutdown"""
        # Setup running server
        mock_manager.servers["backend"].pid = 12345
        mock_manager.servers["backend"].status = ServerStatus.RUNNING
        
        with patch('management.server_manager.ProcessController.kill_process_tree', return_value=True):
            result = mock_manager.stop_server("backend")
            
            assert result is True
            assert mock_manager.servers["backend"].status == ServerStatus.STOPPED
            assert mock_manager.servers["backend"].pid is None

    def test_stop_server_already_stopped(self, mock_manager):
        """Test stopping already stopped server"""
        mock_manager.servers["backend"].status = ServerStatus.STOPPED
        mock_manager.servers["backend"].pid = None
        
        result = mock_manager.stop_server("backend")
        assert result is True

    def test_start_all_servers(self, mock_manager):
        """Test starting all servers"""
        with patch.object(mock_manager, 'start_server', return_value=True) as mock_start:
            result = mock_manager.start_all()
            
            assert result is True
            assert mock_start.call_count == 2  # backend and frontend

    def test_start_all_backend_failure(self, mock_manager):
        """Test start all when backend fails"""
        def mock_start_side_effect(name):
            return name != "backend"  # backend fails, frontend succeeds
            
        with patch.object(mock_manager, 'start_server', side_effect=mock_start_side_effect):
            result = mock_manager.start_all()
            assert result is False

    def test_stop_all_servers(self, mock_manager):
        """Test stopping all servers"""
        with patch.object(mock_manager, 'stop_server', return_value=True) as mock_stop:
            result = mock_manager.stop_all()
            
            assert result is True
            assert mock_stop.call_count == 2  # backend and frontend

    def test_restart_all_servers(self, mock_manager):
        """Test restarting all servers"""
        with patch.object(mock_manager, 'stop_all', return_value=True), \
             patch.object(mock_manager, 'start_all', return_value=True), \
             patch('time.sleep'):  # Speed up tests
            
            result = mock_manager.restart_all()
            assert result is True

    def test_monitoring_lifecycle(self, mock_manager):
        """Test health monitoring start/stop"""
        # Test starting monitoring
        mock_manager.start_monitoring()
        assert mock_manager.health_monitor is not None
        
        # Test stopping monitoring
        mock_manager.stop_monitoring()
        # Health monitor should still exist but be stopped

    def test_print_status(self, mock_manager, capsys):
        """Test status printing"""
        mock_manager.print_status()
        
        captured = capsys.readouterr()
        assert "LangPlug Server Status" in captured.out
        assert "BACKEND SERVER" in captured.out
        assert "FRONTEND SERVER" in captured.out

    def test_error_handling_process_start_exception(self, mock_manager):
        """Test error handling when process start throws exception"""
        with patch.object(mock_manager.servers["backend"], 'is_port_in_use', return_value=False), \
             patch('management.server_manager.ProcessController.start_process', side_effect=Exception("Start failed")):
            
            result = mock_manager.start_server("backend")
            
            assert result is False
            assert mock_manager.servers["backend"].status == ServerStatus.ERROR

    def test_concurrent_server_operations(self, mock_manager):
        """Test concurrent server operations"""
        import threading
        
        results = []
        
        def start_server_thread(name):
            with patch.object(mock_manager.servers[name], 'is_port_in_use', return_value=False), \
                 patch.object(mock_manager.servers[name], 'check_health', return_value=True), \
                 patch('management.server_manager.ProcessController.start_process') as mock_start:
                
                mock_process = Mock()
                mock_process.pid = 12345
                mock_start.return_value = mock_process
                
                result = mock_manager.start_server(name)
                results.append(result)
        
        # Start both servers concurrently
        threads = [
            threading.Thread(target=start_server_thread, args=("backend",)),
            threading.Thread(target=start_server_thread, args=("frontend",))
        ]
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Both should succeed
        assert all(results)

    @pytest.mark.parametrize("server_name,expected_port", [
        ("backend", 8000),
        ("frontend", 3000),
    ])
    def test_server_port_configuration(self, mock_manager, server_name, expected_port):
        """Test server port configuration"""
        server = mock_manager.servers[server_name]
        assert server.port == expected_port
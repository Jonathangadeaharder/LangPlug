"""
Process control utilities for server management
"""
import os
import subprocess
import psutil
import logging
from typing import List

logger = logging.getLogger(__name__)


class ProcessController:
    """Handles low-level process operations"""

    @staticmethod
    def kill_process_tree(pid: int) -> bool:
        """Kill a process and all its children"""
        try:
            parent = psutil.Process(pid)
            logger.info(f"Killing process tree for PID {pid} ({parent.name()})")

            # Get all child processes
            children = parent.children(recursive=True)

            # Terminate children first
            for child in children:
                try:
                    logger.info(f"Terminating child process {child.pid} ({child.name()})")
                    child.terminate()
                except psutil.NoSuchProcess:
                    pass

            # Wait for children to terminate
            gone, alive = psutil.wait_procs(children, timeout=5)

            # Force kill any remaining children
            for child in alive:
                try:
                    logger.warning(f"Force killing child process {child.pid}")
                    child.kill()
                except psutil.NoSuchProcess:
                    pass

            # Finally terminate parent
            parent.terminate()
            parent.wait(timeout=5)

            logger.info(f"Successfully killed process tree for PID {pid}")
            return True

        except psutil.NoSuchProcess:
            logger.info(f"Process {pid} already terminated")
            return True
        except psutil.TimeoutExpired:
            logger.warning(f"Timeout killing process {pid}, force killing")
            try:
                parent = psutil.Process(pid)
                parent.kill()
                return True
            except psutil.NoSuchProcess:
                return True
        except Exception as e:
            logger.error(f"Failed to kill process tree {pid}: {e}")
            return False

    @staticmethod
    def cleanup_port(port: int) -> bool:
        """Kill any processes using the specified port"""
        try:
            killed_any = False
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    # Get connections for this process
                    connections = proc.connections(kind='inet')
                    for conn in connections:
                        # Check if this connection is using our port
                        if hasattr(conn, 'laddr') and conn.laddr.port == port:
                            pid = proc.info['pid']
                            name = proc.info['name']
                            logger.info(f"Killing process {name} (PID {pid}) on port {port}")
                            ProcessController.kill_process_tree(pid)
                            killed_any = True
                            break
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    # Skip processes we can't access or that have disappeared
                    continue
                except AttributeError:
                    # Some processes might not have connections
                    continue

            if not killed_any:
                logger.info(f"No processes found using port {port}")

            return True

        except Exception as e:
            logger.error(f"Error cleaning up port {port}: {e}")
            return False

    @staticmethod
    def start_process(cmd: List[str], cwd: str, env: dict = None) -> subprocess.Popen:
        """Start a process with proper error handling"""
        try:
            # Set up environment
            process_env = os.environ.copy()
            if env:
                process_env.update(env)

            # Start process
            process = subprocess.Popen(
                cmd,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=process_env,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )

            logger.info(f"Started process {' '.join(cmd)} with PID {process.pid}")
            return process

        except Exception as e:
            logger.error(f"Failed to start process {' '.join(cmd)}: {e}")
            raise

    @staticmethod
    def comprehensive_cleanup(ports: List[int] = None) -> bool:
        """Perform comprehensive cleanup of LangPlug processes and ports"""
        try:
            success = True

            # Default ports if none specified
            if ports is None:
                ports = [8000, 3000]

            logger.info("Starting comprehensive cleanup...")

            # Clean up specified ports
            for port in ports:
                if not ProcessController.cleanup_port(port):
                    success = False

            # Kill LangPlug-specific processes by name patterns
            process_patterns = [
                'run_backend.py',
                'main.py',
                'uvicorn',
                'npm run dev',
                'vite'
            ]

            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''

                    # Check if this process matches any of our patterns
                    for pattern in process_patterns:
                        if pattern in cmdline:
                            pid = proc.info['pid']
                            logger.info(f"Killing LangPlug process: {cmdline[:100]}... (PID {pid})")
                            ProcessController.kill_process_tree(pid)
                            break

                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
                except Exception as e:
                    logger.warning(f"Error checking process: {e}")
                    continue

            logger.info("Comprehensive cleanup completed")
            return success

        except Exception as e:
            logger.error(f"Error during comprehensive cleanup: {e}")
            return False

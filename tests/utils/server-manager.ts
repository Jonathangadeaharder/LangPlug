import { spawn, ChildProcess } from 'child_process';
import { promisify } from 'util';
import { setTimeout } from 'timers';
import path from 'path';
import axios from 'axios';

const wait = promisify(setTimeout);

export class ServerManager {
  private backendProcess: ChildProcess | null = null;
  private frontendProcess: ChildProcess | null = null;
  private backendReady = false;
  private frontendReady = false;

  /**
   * Start the backend server
   */
  async startBackend(): Promise<void> {
    console.log('Starting backend server...');
    
    return new Promise((resolve, reject) => {
      // Start backend server using the Windows command from AGENTS.md
      this.backendProcess = spawn('powershell.exe', [
        '-Command',
        'python E:\\Users\\Jonandrop\\IdeaProjects\\LangPlug\\Backend\\run_backend.py'
      ], {
        cwd: path.resolve(__dirname, '../../Backend'),
        stdio: ['pipe', 'pipe', 'pipe'],
        shell: true
      });

      this.backendProcess.stdout?.on('data', (data) => {
        const output = data.toString();
        console.log(`[Backend] ${output}`);
        
        // Check for server ready signal
        if (output.includes('Uvicorn running on') || output.includes('Application startup complete')) {
          this.backendReady = true;
          console.log('Backend server is ready');
          resolve();
        }
      });

      this.backendProcess.stderr?.on('data', (data) => {
        const error = data.toString();
        console.error(`[Backend Error] ${error}`);
      });

      this.backendProcess.on('error', (error) => {
        console.error('Failed to start backend server:', error);
        reject(error);
      });

      // Timeout after 60 seconds
      setTimeout(() => {
        if (!this.backendReady) {
          reject(new Error('Backend server startup timeout'));
        }
      }, 60000);
    });
  }

  /**
   * Start the frontend server
   */
  async startFrontend(): Promise<void> {
    console.log('Starting frontend server...');
    
    return new Promise((resolve, reject) => {
      // Start frontend server
      this.frontendProcess = spawn('npm', ['run', 'dev'], {
        cwd: path.resolve(__dirname, '../../Frontend'),
        stdio: ['pipe', 'pipe'],
        shell: true
      });

      this.frontendProcess.stdout?.on('data', (data) => {
        const output = data.toString();
        console.log(`[Frontend] ${output}`);
        
        // Check for server ready signal
        if (output.includes('Local:') || output.includes('http://localhost:3000')) {
          this.frontendReady = true;
          console.log('Frontend server is ready');
          resolve();
        }
      });

      this.frontendProcess.stderr?.on('data', (data) => {
        const error = data.toString();
        console.error(`[Frontend Error] ${error}`);
      });

      this.frontendProcess.on('error', (error) => {
        console.error('Failed to start frontend server:', error);
        reject(error);
      });

      // Timeout after 60 seconds
      setTimeout(() => {
        if (!this.frontendReady) {
          reject(new Error('Frontend server startup timeout'));
        }
      }, 60000);
    });
  }

  /**
   * Wait for backend to be responsive
   */
  async waitForBackend(): Promise<void> {
    const maxRetries = 30;
    const retryDelay = 2000;
    
    for (let i = 0; i < maxRetries; i++) {
      try {
        await axios.get('http://localhost:8000/docs'); // Use the docs endpoint as health check
        console.log('Backend is responsive');
        return;
      } catch (error) {
        console.log(`Backend not ready, retrying... (${i + 1}/${maxRetries})`);
        await wait(retryDelay);
      }
    }
    
    throw new Error('Backend did not become responsive in time');
  }

  /**
   * Wait for frontend to be responsive
   */
  async waitForFrontend(): Promise<void> {
    const maxRetries = 30;
    const retryDelay = 2000;
    
    for (let i = 0; i < maxRetries; i++) {
      try {
        await axios.get('http://localhost:3000');
        console.log('Frontend is responsive');
        return;
      } catch (error) {
        console.log(`Frontend not ready, retrying... (${i + 1}/${maxRetries})`);
        await wait(retryDelay);
      }
    }
    
    throw new Error('Frontend did not become responsive in time');
  }

  /**
   * Stop all running servers
   */
  async stopAll(): Promise<void> {
    console.log('Stopping all servers...');
    
    if (this.backendProcess) {
      this.backendProcess.kill();
      this.backendProcess = null;
    }
    
    if (this.frontendProcess) {
      this.frontendProcess.kill();
      this.frontendProcess = null;
    }
    
    // Give processes time to shut down
    await wait(2000);
    console.log('All servers stopped');
  }

  /**
   * Check if backend server is ready
   */
  isBackendReady(): boolean {
    return this.backendReady;
  }

  /**
   * Check if frontend server is ready
   */
  isFrontendReady(): boolean {
    return this.frontendReady;
  }
}
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
  private detectedFrontendUrl: string | null = null;

  /**
   * Start the backend server
   */
  async startBackend(): Promise<void> {
    console.log('Starting backend server...');

    // Quick check: if backend is already running, skip spawning
    const backendHosts = ['127.0.0.1', 'localhost'];
    const backendPorts = [8000, 8001];
    for (const host of backendHosts) {
      for (const port of backendPorts) {
        try {
          const resp = await axios.get(`http://${host}:${port}/health`, { timeout: 1500, validateStatus: () => true, proxy: false });
          if (resp.status === 200) {
            this.backendReady = true;
            console.log(`Backend already running at http://${host}:${port}`);
            return;
          }
        } catch (e) {
          // try next
        }
      }
    }
    
    return new Promise((resolve, reject) => {
      // Start backend server using the Windows command from AGENTS.md
      // Ensure reload is disabled and TESTING mode is enabled to avoid heavy init and watchfiles issues
      const psCommand = [
        "$env:TESTING='1';",
        "$env:LANGPLUG_RELOAD='false';",
        'python E:\\Users\\Jonandrop\\IdeaProjects\\LangPlug\\Backend\\run_backend.py'
      ].join(' ');

      this.backendProcess = spawn('powershell.exe', ['-Command', psCommand], {
        cwd: path.resolve(__dirname, '../../Backend'),
        stdio: ['pipe', 'pipe', 'pipe'],
        shell: true,
        env: { ...process.env }
      });

      this.backendProcess.stdout?.on('data', (data) => {
        const output = data.toString();
        console.log(`[Backend] ${output}`);
        // Consider backend "started" (spawned). Readiness will be verified by waitForBackend()
        if (!this.backendReady && (output.includes('Backend will be available at') || output.includes('Server starting') || output.includes('App created'))) {
          this.backendReady = true;
          console.log('Backend process spawned - proceeding to health checks');
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

      // Resolve immediately after spawn; readiness is handled by waitForBackend()
      resolve();
    });
  }

  /**
   * Start the frontend server
   */
  async startFrontend(): Promise<void> {
    console.log('Starting frontend server...');
    // Quick check: if frontend is already running, skip spawning
    const hosts = ['127.0.0.1', 'localhost'];
    const ports = [3000, 3001, 3002, 3003, 3004, 5173];
    for (const host of hosts) {
      for (const port of ports) {
        try {
          await axios.get(`http://${host}:${port}`, { timeout: 1500, proxy: false });
          this.frontendReady = true;
          this.detectedFrontendUrl = `http://${host}:${port}`;
          process.env.E2E_FRONTEND_URL = this.detectedFrontendUrl ?? undefined;
          console.log(`Frontend already running at ${this.detectedFrontendUrl}`);
          return;
        } catch (e) {
          // try next
        }
      }
    }

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
        // Try to detect the Local URL from Vite logs
        const match = output.match(/Local:\s*(http:\/\/\S+)/i) || output.match(/(http:\/\/localhost:\d+\/?)/i) || output.match(/(http:\/\/127\.0\.0\.1:\d+\/?)/i);
        if (match && match[1]) {
          this.detectedFrontendUrl = match[1].trim();
          // Normalize trailing slash removed
          if (this.detectedFrontendUrl && this.detectedFrontendUrl.endsWith('/')) {
            this.detectedFrontendUrl = this.detectedFrontendUrl.slice(0, -1);
          }
          this.frontendReady = true;
          process.env.E2E_FRONTEND_URL = this.detectedFrontendUrl ?? undefined;
          console.log(`Detected frontend URL: ${this.detectedFrontendUrl}`);
        }
        // Do not resolve here; readiness is checked by waitForFrontend()
      });

      this.frontendProcess.stderr?.on('data', (data) => {
        const error = data.toString();
        console.error(`[Frontend Error] ${error}`);
      });

      this.frontendProcess.on('error', (error) => {
        console.error('Failed to start frontend server:', error);
        reject(error);
      });

      // Resolve immediately after spawn; readiness is handled by waitForFrontend()
      resolve();
    });
  }

  /**
   * Wait for backend to be responsive
   */
  async waitForBackend(): Promise<void> {
    const maxRetries = 30;
    const retryDelay = 2000;
    const ports = [8000, 8001];
    const hosts = ['127.0.0.1', 'localhost'];

    for (let i = 0; i < maxRetries; i++) {
      for (const host of hosts) {
        for (const port of ports) {
          try {
            const resp = await axios.get(`http://${host}:${port}/health`, { timeout: 1500, validateStatus: () => true, proxy: false });
            if (resp.status === 200) {
              console.log(`Backend is responsive at http://${host}:${port}`);
              return;
            }
          } catch {
            // try next
          }
        }
      }
      console.log(`Backend not ready, retrying... (${i + 1}/${maxRetries})`);
      await wait(retryDelay);
    }

    throw new Error('Backend did not become responsive in time');
  }

  /**
   * Wait for frontend to be responsive
   */
  async waitForFrontend(): Promise<void> {
    const maxRetries = 30;
    const retryDelay = 2000;
    const ports = [3000, 3001, 3002, 3003, 3004, 5173];
    const hosts = ['127.0.0.1', 'localhost'];

    // If we've already detected the URL via logs, consider it ready and skip probing
    if (this.frontendReady && this.detectedFrontendUrl) {
      console.log(`Frontend presumed ready at ${this.detectedFrontendUrl} (from Vite logs)`);
      return;
    }

    for (let i = 0; i < maxRetries; i++) {
      // If Vite has logged the Local URL, accept it immediately
      if (this.detectedFrontendUrl) {
        console.log(`Frontend presumed ready at ${this.detectedFrontendUrl} (detected)`);
        return;
      }
      for (const host of hosts) {
        for (const port of ports) {
          try {
            const url = `http://${host}:${port}`;
            const resp = await axios.get(url, { timeout: 1500, validateStatus: () => true, proxy: false });
            if (resp.status >= 200 && resp.status < 500) {
              // Any HTTP response indicates server is up
              this.detectedFrontendUrl = url.endsWith('/') ? url.slice(0, -1) : url;
              this.frontendReady = true;
              process.env.E2E_FRONTEND_URL = this.detectedFrontendUrl ?? undefined;
              console.log(`Frontend is responsive at ${this.detectedFrontendUrl}`);
              return;
            }
          } catch {
            // try next
          }
        }
      }
      console.log(`Frontend not ready, retrying... (${i + 1}/${maxRetries})`);
      await wait(retryDelay);
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
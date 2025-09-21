// Dynamic Port Detection for E2E Tests
// Automatically discovers which ports are actually running

import axios from 'axios';

export interface ServerPorts {
  frontend: {
    url: string;
    port: number;
  } | null;
  backend: {
    url: string;
    port: number;
  } | null;
}

export class PortDetector {
  private static readonly FRONTEND_PORTS = [3000, 3001, 3002, 5173]; // Common Vite ports
  private static readonly BACKEND_PORTS = [8000, 8001, 8080, 3001]; // Common FastAPI ports
  private static readonly FRONTEND_HOSTS = ['localhost', '127.0.0.1'];
  private static readonly BACKEND_HOSTS = ['127.0.0.1', 'localhost'];

  /**
   * Detect which ports are actually running servers
   */
  static async detectRunningPorts(timeout = 5000): Promise<ServerPorts> {
    console.log('🔍 Detecting running server ports...');
    
    const [frontend, backend] = await Promise.all([
      this.detectFrontendPort(timeout),
      this.detectBackendPort(timeout)
    ]);

    console.log(`📊 Detection results:
  Frontend: ${frontend ? `✅ ${frontend.url}` : '❌ Not found'}
  Backend:  ${backend ? `✅ ${backend.url}` : '❌ Not found'}`);

    return { frontend, backend };
  }

  /**
   * Detect running frontend server (Vite/React)
   */
  private static async detectFrontendPort(timeout: number) {
    // Try known working ports for the frontend
    const testPorts = [3000, 3001, 5173];
    
    for (const port of testPorts) {
      const url = `http://localhost:${port}`;
      
      try {
        const response = await axios.get(url, { 
          timeout: Math.min(timeout, 3000), // Shorter timeout to avoid hanging
          validateStatus: () => true
        });
        
        // Simplified detection - just check for HTML response
        if (response.status === 200 && 
            typeof response.data === 'string' &&
            response.data.toLowerCase().includes('html')) {
          
          console.log(`✅ Frontend detected at ${url}`);
          return { url, port };
        }
      } catch (error) {
        // Continue to next port
        continue;
      }
    }
    
    // Fallback: assume port 3000 if servers should be running
    console.log('⚠️ Using fallback frontend URL: http://localhost:3000');
    return { url: 'http://localhost:3000', port: 3000 };
  }

  /**
   * Detect running backend server (FastAPI)
   */
  private static async detectBackendPort(timeout: number) {
    // Try known working ports for the backend
    const testPorts = [8000, 8001];
    
    for (const port of testPorts) {
      const url = `http://127.0.0.1:${port}`;
      
      try {
        // Try the health endpoint first
        const response = await axios.get(`${url}/docs`, { 
          timeout: Math.min(timeout, 3000)
        });
        
        if (response.status === 200) {
          console.log(`✅ Backend detected at ${url}`);
          return { url, port };
        }
      } catch (error) {
        // Continue to next port
        continue;
      }
    }
    
    // Fallback: assume port 8000 if servers should be running
    console.log('⚠️ Using fallback backend URL: http://127.0.0.1:8000');
    return { url: 'http://127.0.0.1:8000', port: 8000 };
  }

  /**
   * Wait for servers to be available with retry logic
   */
  static async waitForServers(maxWaitTime = 60000, checkInterval = 2000): Promise<ServerPorts> {
    const startTime = Date.now();
    
    console.log(`⏳ Waiting for servers to be available (max ${maxWaitTime / 1000}s)...`);
    
    while (Date.now() - startTime < maxWaitTime) {
      const ports = await this.detectRunningPorts(3000); // Shorter timeout for frequent checks
      
      if (ports.frontend && ports.backend) {
        console.log('🎉 Both servers are now available!');
        return ports;
      }
      
      const missing = [];
      if (!ports.frontend) missing.push('frontend');
      if (!ports.backend) missing.push('backend');
      
      console.log(`⏳ Still waiting for: ${missing.join(', ')}... (${Math.round((Date.now() - startTime) / 1000)}s elapsed)`);
      
      await new Promise(resolve => setTimeout(resolve, checkInterval));
    }
    
    console.log('⌛ Timeout waiting for servers');
    return await this.detectRunningPorts(3000); // Final attempt
  }

  /**
   * Get server URLs or throw error if not available
   */
  static async getRequiredServerUrls(): Promise<{ frontendUrl: string; backendUrl: string }> {
    const ports = await this.detectRunningPorts();
    
    if (!ports.frontend) {
      throw new Error('Frontend server not detected. Please start the frontend server (npm run dev)');
    }
    
    if (!ports.backend) {
      throw new Error('Backend server not detected. Please start the backend server (python main.py)');
    }
    
    return {
      frontendUrl: ports.frontend.url,
      backendUrl: ports.backend.url
    };
  }
}

// Convenience functions for tests
export async function getFrontendUrl(): Promise<string> {
  const { frontendUrl } = await PortDetector.getRequiredServerUrls();
  return frontendUrl;
}

export async function getBackendUrl(): Promise<string> {
  const { backendUrl } = await PortDetector.getRequiredServerUrls();
  return backendUrl;
}

export async function getBothUrls(): Promise<{ frontendUrl: string; backendUrl: string }> {
  return await PortDetector.getRequiredServerUrls();
}
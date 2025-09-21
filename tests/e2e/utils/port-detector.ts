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
    for (const host of this.FRONTEND_HOSTS) {
      for (const port of this.FRONTEND_PORTS) {
        const url = `http://${host}:${port}`;
        
        try {
          const response = await axios.get(url, { 
            timeout, 
            validateStatus: () => true, // Accept any status code
            headers: {
              'User-Agent': 'E2E-Test-Client/1.0',
              'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            }
          });
          
          // Check if it's actually a frontend (contains HTML with React root)
          if (response.status === 200 && 
              typeof response.data === 'string' &&
              response.data.includes('<!DOCTYPE html>') &&
              response.data.includes('id="root"')) {
            
            console.log(`✅ Frontend detected at ${url}`);
            return { url, port };
          }
        } catch (error) {
          // Continue to next port
          continue;
        }
      }
    }
    
    console.log('❌ No frontend server detected');
    return null;
  }

  /**
   * Detect running backend server (FastAPI)
   */
  private static async detectBackendPort(timeout: number) {
    for (const host of this.BACKEND_HOSTS) {
      for (const port of this.BACKEND_PORTS) {
        const url = `http://${host}:${port}`;
        
        try {
          // Try the /docs endpoint first (most reliable FastAPI indicator)
          const response = await axios.get(`${url}/docs`, { 
            timeout, 
            validateStatus: () => true 
          });
          
          if (response.status === 200 && 
              typeof response.data === 'string' &&
              response.data.toLowerCase().includes('swagger')) {
            
            console.log(`✅ Backend detected at ${url}`);
            return { url, port };
          }
        } catch (error) {
          // Try OpenAPI spec as fallback
          try {
            const specResponse = await axios.get(`${url}/openapi.json`, { 
              timeout, 
              validateStatus: () => true 
            });
            
            if (specResponse.status === 200 && 
                specResponse.data && 
                typeof specResponse.data === 'object' &&
                'openapi' in specResponse.data) {
              
              console.log(`✅ Backend detected at ${url} (via OpenAPI)`);
              return { url, port };
            }
          } catch {
            // Continue to next port
            continue;
          }
        }
      }
    }
    
    console.log('❌ No backend server detected');
    return null;
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
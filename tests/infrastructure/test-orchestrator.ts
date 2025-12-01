/**
 * Test Orchestrator - Central testing infrastructure management
 * Provides robust server management, contract validation, and test isolation
 */

import { ChildProcess, spawn } from 'child_process';
import axios, { AxiosInstance } from 'axios';
import * as path from 'path';
import * as fs from 'fs-extra';
import * as os from 'os';
import { v4 as uuidv4 } from 'uuid';
import { EventEmitter } from 'events';

export interface ServerConfig {
  name: string;
  command: string;
  args: string[];
  cwd: string;
  env?: Record<string, string>;
  healthEndpoint?: string;
  ports: number[];
  readyPatterns?: RegExp[];
  startupTimeout?: number;
  shutdownTimeout?: number;
}

export interface TestEnvironment {
  id: string;
  backend: ServerInstance;
  frontend: ServerInstance;
  database?: DatabaseInstance;
  tempDir: string;
  logDir: string;
}

export interface ServerInstance {
  config: ServerConfig;
  process?: ChildProcess;
  url?: string;
  port?: number;
  ready: boolean;
  logs: string[];
  errors: string[];
  startTime?: Date;
  pid?: number;
}

export interface DatabaseInstance {
  url: string;
  type: 'postgres' | 'sqlite' | 'memory';
  initialized: boolean;
}

export interface ContractValidation {
  openApiSpec: any;
  endpoints: Map<string, EndpointContract>;
  violations: ContractViolation[];
}

export interface EndpointContract {
  path: string;
  method: string;
  requestSchema?: any;
  responseSchema?: any;
  headers?: Record<string, string>;
  queryParams?: any;
}

export interface ContractViolation {
  endpoint: string;
  type: 'request' | 'response';
  expected: any;
  actual: any;
  message: string;
  timestamp: Date;
}

export class TestOrchestrator extends EventEmitter {
  private environments: Map<string, TestEnvironment> = new Map();
  private contractValidation: ContractValidation;
  private axiosInstance: AxiosInstance;
  private readonly maxPortRetries = 5;
  private readonly portRetryDelay = 1000; // 1 second
  private readonly maxHealthRetries = 60;
  private readonly healthRetryDelay = 1000;

  constructor() {
    super();
    this.contractValidation = {
      openApiSpec: null,
      endpoints: new Map(),
      violations: []
    };
    this.axiosInstance = axios.create();
    this.initializePortPool().catch(err => console.error('Failed to initialize port pool:', err));
    this.setupAxiosInterceptors();
  }

  /**
   * Initialize pool of available ports for testing
   */
  private async initializePortPool(): Promise<void> {
    console.log('Initializing port pool...');
    const net = require('net');
    for (let port = 9000; port <= 9500; port++) {
      if (await this.isPortAvailable(port, net)) {
        this.portPool.add(port);
      }
    }
    console.log(`Port pool initialized with ${this.portPool.size} available ports.`);
  }

  /**
   * Get an available port from the pool with retry mechanism
   */
  private async getAvailablePort(): Promise<number> {
    const net = require('net');
    for (let attempt = 0; attempt < this.maxPortRetries; attempt++) {
      for (const port of this.portPool) {
        // Re-check availability in case state changed since initialization or last check
        if (await this.isPortAvailable(port, net)) {
          this.portPool.delete(port);
          return port;
        }
      }
      console.warn(`No available ports found on attempt ${attempt + 1}/${this.maxPortRetries}. Retrying in ${this.portRetryDelay}ms...`);
      await new Promise(resolve => setTimeout(resolve, this.portRetryDelay));
    }
    throw new Error(`No available ports in pool after ${this.maxPortRetries} attempts`);
  }

  /**
   * Check if a port is available using client connection
   * Attempts to connect to the port. If successful, it's in use.
   * If connection refused, it's likely free.
   */
  private async isPortAvailable(port: number, netModule: typeof import('net')): Promise<boolean> {
    return new Promise((resolve) => {
      const { createConnection } = require('net');
      const socket = createConnection(port, '127.0.0.1');

      socket.setTimeout(200); // Short timeout

      socket.once('connect', () => {
        // Port is in use
        socket.destroy();
        resolve(false);
      });

      socket.once('error', (err: any) => {
        socket.destroy();
        if (err.code === 'ECONNREFUSED') {
          // Port is free. Add a small delay to ensure OS fully releases.
          setTimeout(() => resolve(true), 50);
        } else {
          // Other error (e.g. timeout) -> assume used or unreachable
          // Safest to assume NOT available if unsure
          console.warn(`isPortAvailable: Error checking port ${port}: ${err.code || err.message}. Assuming not available.`);
          resolve(false);
        }
      });

      socket.once('timeout', () => {
        socket.destroy();
        // Timeout means it might be open but dropping packets (firewall)
        // or just slow. Assume unavailable to be safe.
        resolve(false);
      });
    });
  }

  /**
   * Release a port back to the pool
   */
  private releasePort(port: number): void {
    this.portPool.add(port);
  }

  /**
   * Setup Axios interceptors for contract validation
   */
  private setupAxiosInterceptors(): void {
    this.axiosInstance = axios.create({
      timeout: 30000,
      validateStatus: () => true, // Don't throw on any status
    });

    // Request interceptor for contract validation
    this.axiosInstance.interceptors.request.use(
      (config) => {
        if (this.contractValidation) {
          this.validateRequest(config);
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for contract validation
    this.axiosInstance.interceptors.response.use(
      (response) => {
        if (this.contractValidation) {
          this.validateResponse(response);
        }
        return response;
      },
      (error) => Promise.reject(error)
    );
  }

  /**
   * Load OpenAPI specification for contract validation
   */
  async loadOpenApiSpec(specPath: string): Promise<void> {
    const spec = await fs.readJson(specPath);
    this.contractValidation = {
      openApiSpec: spec,
      endpoints: this.parseEndpoints(spec),
      violations: [],
    };
    this.emit('contract:loaded', spec);
  }

  /**
   * Parse OpenAPI endpoints into contract definitions
   */
  private parseEndpoints(spec: any): Map<string, EndpointContract> {
    const endpoints = new Map<string, EndpointContract>();

    for (const [path, methods] of Object.entries(spec.paths || {})) {
      for (const [method, definition] of Object.entries(methods as any)) {
        const key = `${method.toUpperCase()} ${path}`;
        endpoints.set(key, {
          path,
          method: method.toUpperCase(),
          requestSchema: (definition as any).requestBody?.content?.['application/json']?.schema,
          responseSchema: (definition as any).responses?.['200']?.content?.['application/json']?.schema,
          headers: (definition as any).parameters?.filter((p: any) => p.in === 'header'),
          queryParams: (definition as any).parameters?.filter((p: any) => p.in === 'query'),
        });
      }
    }

    return endpoints;
  }

  /**
   * Validate request against contract
   */
  private validateRequest(config: any): void {
    const key = `${config.method?.toUpperCase()} ${config.url?.pathname}`;
    const contract = this.contractValidation.endpoints.get(key);

    if (contract?.requestSchema && config.data) {
      // Validate request body against schema
      const validation = this.validateSchema(config.data, contract.requestSchema);
      if (!validation.valid) {
        const violation: ContractViolation = {
          endpoint: key,
          type: 'request',
          expected: contract.requestSchema,
          actual: config.data,
          message: validation.errors.join(', '),
          timestamp: new Date(),
        };
        this.contractValidation.violations.push(violation);
        this.emit('contract:violation', violation);
      }
    }
  }

  /**
   * Validate response against contract
   */
  private validateResponse(response: any): void {
    const key = `${response.config.method?.toUpperCase()} ${new URL(response.config.url).pathname}`;
    const contract = this.contractValidation.endpoints.get(key);

    if (contract?.responseSchema && response.data) {
      // Validate response body against schema
      const validation = this.validateSchema(response.data, contract.responseSchema);
      if (!validation.valid) {
        const violation: ContractViolation = {
          endpoint: key,
          type: 'response',
          expected: contract.responseSchema,
          actual: response.data,
          message: validation.errors.join(', '),
          timestamp: new Date(),
        };
        this.contractValidation.violations.push(violation);
        this.emit('contract:violation', violation);
      }
    }
  }

  /**
   * Validate data against JSON schema
   */
  private validateSchema(data: any, schema: any): { valid: boolean; errors: string[] } {
    // Simple schema validation - would use ajv in production
    const errors: string[] = [];

    if (schema.type === 'object' && schema.properties) {
      for (const [key, propSchema] of Object.entries(schema.properties as any)) {
        if (schema.required?.includes(key) && !(key in data)) {
          errors.push(`Missing required property: ${key}`);
        }
        if (key in data) {
          const propValidation = this.validateSchema(data[key], propSchema);
          errors.push(...propValidation.errors);
        }
      }
    }

    return { valid: errors.length === 0, errors };
  }

  /**
   * Create a new isolated test environment
   */
  async createEnvironment(id?: string, env: NodeJS.ProcessEnv = {}): Promise<TestEnvironment> {
    const envId = id || uuidv4();
    const tempDir = path.join(os.tmpdir(), 'langplug-tests', envId);
    const logDir = path.join(tempDir, 'logs');

    await fs.ensureDir(tempDir);
    await fs.ensureDir(logDir);

    const environment: TestEnvironment = {
      id: envId,
      backend: {
        config: await this.getBackendConfig(env),
        ready: false,
        logs: [],
        errors: [],
      },
      frontend: {
        config: await this.getFrontendConfig(),
        ready: false,
        logs: [],
        errors: [],
      },
      tempDir,
      logDir,
    };

    this.environments.set(envId, environment);
    this.emit('environment:created', environment);

    return environment;
  }

  /**
   * Get backend server configuration
   * Best practice: Use cmd.exe-compatible syntax since shell: true uses cmd.exe on Windows
   */
  private async getBackendConfig(env: NodeJS.ProcessEnv = {}): Promise<ServerConfig> {
    const backendPort = await this.getAvailablePort();
    const projectRoot = path.resolve(__dirname, '..', '..');
    const backendPath = path.resolve(projectRoot, 'src', 'backend');
    const runBackendScript = path.resolve(backendPath, 'run_backend.py');

    // Use Windows-native paths for cmd.exe (backslashes work better)
    // api_venv is at project root
    const pythonExe = path.join(projectRoot, 'api_venv', 'Scripts', 'python.exe');

    return {
      name: 'backend',
      // cmd.exe syntax: use the executable directly, shell: true will resolve it
      command: pythonExe,
      args: [runBackendScript],
      cwd: backendPath,
      env: {
        TESTING: '1',
        LANGPLUG_RELOAD: 'false',
        LANGPLUG_HOST: '127.0.0.1',
        LANGPLUG_PORT: backendPort.toString(),
        LANGPLUG_SECRET_KEY: 'test_secret_key_for_integration_tests_must_be_long',
        // Use aiosqlite driver for async SQLAlchemy
        LANGPLUG_DATABASE_URL: 'sqlite+aiosqlite:///./test.db',
        LANGPLUG_TRANSCRIPTION_SERVICE: 'whisper-tiny',
        // Allow all origins for testing since frontend port is dynamic
        LANGPLUG_CORS_ORIGINS: '["*"]',
        ...env,
      },
      healthEndpoint: '/health',
      ports: [backendPort],
      readyPatterns: [
        /Backend will be available at/,
        /Server starting/,
        /Uvicorn running on/,
      ],
      startupTimeout: 30000,
      shutdownTimeout: 5000,
    };
  }

  /**
   * Get frontend server configuration
   * Best practice: Use npm with args separately for proper shell handling
   */
  private async getFrontendConfig(): Promise<ServerConfig> {
    const frontendPort = await this.getAvailablePort();
    const projectRoot = path.resolve(__dirname, '..', '..');
    const frontendPath = path.resolve(projectRoot, 'src', 'frontend');

    return {
      name: 'frontend',
      // cmd.exe syntax: pass npm and args separately
      command: 'npm',
      args: ['run', 'dev', '--', '--port', frontendPort.toString(), '--strictPort', '--host', '0.0.0.0'],
      cwd: frontendPath,
      env: {
        PORT: frontendPort.toString(),
        VITE_API_URL: `http://localhost:${this.environments.values().next().value?.backend.config.ports[0] || 8000}`,
      },
      healthEndpoint: '/index.html',
      ports: [frontendPort],
      readyPatterns: [
        /Local:\s*http/,
        /ready in \d+ms/,
        /VITE.*ready/,
      ],
      startupTimeout: 30000,
      shutdownTimeout: 5000,
    };
  }

  /**
   * Start a server instance
   * Best practice: Use shell: true on Windows for proper command resolution
   */
  async startServer(instance: ServerInstance): Promise<void> {
    return new Promise((resolve, reject) => {
      const { config } = instance;
      const logFile = path.join(
        this.environments.values().next().value?.logDir || '.',
        `${config.name}-${Date.now()}.log`
      );
      const logStream = fs.createWriteStream(logFile, { flags: 'a' });

      instance.startTime = new Date();

      // Best practice for Windows: Use shell: true and pass complete command
      // This allows the shell to resolve executables properly
      instance.process = spawn(config.command, config.args, {
        cwd: config.cwd,
        // CRITICAL: Always spread process.env to preserve PATH
        env: { ...process.env, ...config.env },
        // shell: true is required on Windows for proper executable resolution
        shell: true,
        // Don't detach on Windows - it causes issues with process cleanup
        detached: false,
        // Pipe stdio for capturing output
        stdio: ['pipe', 'pipe', 'pipe'],
      });

      instance.pid = instance.process.pid;

      // Handle stdout
      instance.process.stdout?.on('data', (data) => {
        const output = data.toString();
        // Prevent OOM by limiting logs
        // if (instance.logs.length > 1000) instance.logs.shift();
        // instance.logs.push(output);
        logStream.write(`[STDOUT] ${output}`);
        this.emit('server:log', { server: config.name, data: output });

        // Check for ready patterns
        if (config.readyPatterns?.some(pattern => pattern.test(output))) {
          instance.ready = true;
          instance.port = config.ports[0];
          instance.url = `http://127.0.0.1:${instance.port}`;
          this.emit('server:ready', instance);
        }
      });

      // Handle stderr
      instance.process.stderr?.on('data', (data) => {
        const error = data.toString();
        // Prevent OOM by limiting logs
        // if (instance.errors.length > 1000) instance.errors.shift();
        // instance.errors.push(error);
        logStream.write(`[STDERR] ${error}`);
        this.emit('server:error', { server: config.name, data: error });

        // Check for ready patterns in stderr too (Uvicorn logs to stderr)
        if (!instance.ready && config.readyPatterns?.some(pattern => pattern.test(error))) {
          instance.ready = true;
          instance.port = config.ports[0];
          instance.url = `http://127.0.0.1:${instance.port}`;
          this.emit('server:ready', instance);
        }
      });

      // Handle process exit
      instance.process.on('exit', (code) => {
        logStream.end();
        this.emit('server:exit', { server: config.name, code });
        if (code !== 0 && code !== null) {
          const lastLogs = [...instance.logs, ...instance.errors].slice(-20).join('\n');
          reject(new Error(`${config.name} exited with code ${code}.\nLast logs:\n${lastLogs}`));
        }
      });

      // Handle process error
      instance.process.on('error', (error) => {
        logStream.end();
        this.emit('server:error', { server: config.name, error });
        reject(error);
      });

      // Wait for ready or timeout
      const timeout = setTimeout(() => {
        if (!instance.ready) {
          this.stopServer(instance);
          const lastLogs = [...instance.logs, ...instance.errors].slice(-20).join('\n');
          reject(new Error(`${config.name} failed to start within ${config.startupTimeout}ms.\nLast logs:\n${lastLogs}`));
        }
      }, config.startupTimeout || 30000);

      this.once('server:ready', (readyInstance) => {
        if (readyInstance === instance) {
          clearTimeout(timeout);
          resolve();
        }
      });
    });
  }

  /**
   * Stop a server instance with robust cleanup and error handling
   */
  async stopServer(instance: ServerInstance): Promise<void> {
    if (!instance.process) {
      // Cleanup resources even if process doesn't exist
      if (instance.port) {
        this.releasePort(instance.port);
      }
      instance.ready = false;
      return;
    }

    return new Promise((resolve) => {
      let isResolved = false;
      const shutdownTimeout = instance.config.shutdownTimeout || 5000;

      const cleanup = () => {
        if (isResolved) return;
        isResolved = true;

        // Always cleanup resources
        if (instance.port) {
          this.releasePort(instance.port);
        }
        instance.ready = false;
        instance.process = undefined;
        resolve();
      };

      // Force kill timeout
      const forceKillTimeout = setTimeout(() => {
        console.warn(`Force killing ${instance.config.name} process after ${shutdownTimeout}ms`);
        try {
          instance.process?.kill('SIGKILL');
        } catch (error) {
          console.error(`Error force killing process: ${error}`);
        }
        cleanup();
      }, shutdownTimeout);

      // Graceful shutdown timeout (earlier than force kill)
      const gracefulTimeout = setTimeout(() => {
        try {
          instance.process?.kill('SIGKILL');
        } catch (error) {
          console.error(`Error during graceful kill: ${error}`);
        }
      }, Math.max(shutdownTimeout - 1000, 1000));

      // Handle process exit
      instance.process?.once('exit', (code, signal) => {
        clearTimeout(forceKillTimeout);
        clearTimeout(gracefulTimeout);
        console.log(`${instance.config.name} exited with code ${code}, signal ${signal}`);
        cleanup();
      });

      // Handle process error
      instance.process?.once('error', (error) => {
        clearTimeout(forceKillTimeout);
        clearTimeout(gracefulTimeout);
        console.error(`${instance.config.name} process error: ${error}`);
        cleanup();
      });

      // Start graceful shutdown
      try {
        instance.process?.kill('SIGTERM');
      } catch (error) {
        console.error(`Error sending SIGTERM to ${instance.config.name}: ${error}`);
        // If we can't send SIGTERM, try SIGKILL immediately
        try {
          instance.process?.kill('SIGKILL');
        } catch (killError) {
          console.error(`Error sending SIGKILL to ${instance.config.name}: ${killError}`);
        }
        cleanup();
      }
    });
  }

  /**
   * Wait for server to be healthy
   */
  async waitForHealth(instance: ServerInstance): Promise<void> {
    const { config } = instance;
    if (!config.healthEndpoint) return;

    for (let i = 0; i < this.maxHealthRetries; i++) {
      try {
        const url = `${instance.url}${config.healthEndpoint}`;
        const response = await axios.get(url, { timeout: 1000 });
        if (response.status === 200) {
          this.emit('server:healthy', instance);
          return;
        }
      } catch (error) {
        if (i > 10 && i % 10 === 0) {
          console.log(`Health check failed for ${instance.url}: ${(error as Error).message}`);
        }
      }
      await new Promise(resolve => setTimeout(resolve, this.healthRetryDelay));
    }

    throw new Error(`${config.name} health check failed after ${this.maxHealthRetries} retries`);
  }

  /**
   * Start all servers in an environment
   */
  async startEnvironment(envId: string): Promise<void> {
    const environment = this.environments.get(envId);
    if (!environment) throw new Error(`Environment ${envId} not found`);

    // Start backend first
    await this.startServer(environment.backend);
    await this.waitForHealth(environment.backend);

    // Update frontend config with backend URL
    const backendUrl = environment.backend.url || `http://localhost:${environment.backend.port}`;
    environment.frontend.config.env = {
      ...environment.frontend.config.env,
      VITE_API_URL: backendUrl,
      VITE_API_BASE_URL: backendUrl,
      VITE_BACKEND_URL: backendUrl,
    };

    // Start frontend
    await this.startServer(environment.frontend);
    await this.waitForHealth(environment.frontend);

    this.emit('environment:started', environment);
  }

  /**
   * Stop all servers in an environment
   */
  async stopEnvironment(envId: string): Promise<void> {
    const environment = this.environments.get(envId);
    if (!environment) return;

    await Promise.all([
      this.stopServer(environment.backend),
      this.stopServer(environment.frontend),
    ]);

    // Clean up temp directory
    await fs.remove(environment.tempDir);

    this.environments.delete(envId);
    this.emit('environment:stopped', envId);
  }

  /**
   * Get contract violations
   */
  getContractViolations(): ContractViolation[] {
    return this.contractValidation?.violations || [];
  }

  /**
   * Clear contract violations
   */
  clearContractViolations(): void {
    if (this.contractValidation) {
      this.contractValidation.violations = [];
    }
  }

  /**
   * Get environment by ID
   */
  getEnvironment(envId: string): TestEnvironment | undefined {
    return this.environments.get(envId);
  }

  /**
   * Cleanup all environments with robust error handling
   */
  async cleanup(): Promise<void> {
    const envIds = Array.from(this.environments.keys());
    console.log(`Starting cleanup of ${envIds.length} environments`);

    // Use allSettled to ensure all cleanup attempts complete even if some fail
    const results = await Promise.allSettled(
      envIds.map(async (envId) => {
        try {
          console.log(`Cleaning up environment: ${envId}`);
          await this.stopEnvironment(envId);
          console.log(`Successfully cleaned up environment: ${envId}`);
        } catch (error) {
          console.error(`Failed to cleanup environment ${envId}:`, error);
          // Force cleanup even on error
          this.environments.delete(envId);
          throw error;
        }
      })
    );

    // Log any failures but don't throw
    const failures = results.filter(result => result.status === 'rejected');
    if (failures.length > 0) {
      console.error(`${failures.length} environments failed to cleanup properly`);
      failures.forEach((failure, index) => {
        console.error(`Environment ${envIds[index]} cleanup error:`, failure.reason);
      });
    }

    // Final safety cleanup - remove any remaining environments
    this.environments.clear();

    console.log('Cleanup completed');
    this.emit('cleanup:complete');
  }
}

// Export singleton instance
export const testOrchestrator = new TestOrchestrator();

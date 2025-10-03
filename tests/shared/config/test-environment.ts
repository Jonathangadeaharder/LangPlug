/**
 * Unified Test Environment Configuration
 *
 * Provides cross-platform environment detection and configuration
 * for all test types (unit, integration, e2e)
 */

import path from 'path';
import { promisify } from 'util';
import { exec } from 'child_process';

const execAsync = promisify(exec);

export interface TestEnvironment {
  projectRoot: string;
  backendPath: string;
  frontendPath: string;
  testDataPath: string;
  tempPath: string;
  frontendUrl: string;
  backendUrl: string;
  isCI: boolean;
  platform: 'windows' | 'linux' | 'darwin';
}

export interface ServerDetectionOptions {
  timeoutMs?: number;
  retries?: number;
  checkPorts?: number[];
}

class TestEnvironmentManager {
  private static instance: TestEnvironmentManager;
  private cachedEnvironment: TestEnvironment | null = null;

  private constructor() {}

  static getInstance(): TestEnvironmentManager {
    if (!TestEnvironmentManager.instance) {
      TestEnvironmentManager.instance = new TestEnvironmentManager();
    }
    return TestEnvironmentManager.instance;
  }

  /**
   * Get the current test environment with server detection
   */
  async getEnvironment(options?: ServerDetectionOptions): Promise<TestEnvironment> {
    if (this.cachedEnvironment) {
      return this.cachedEnvironment;
    }

    const projectRoot = this.getProjectRoot();
    const platform = this.getPlatform();

    // Detect running servers
    const { frontendUrl, backendUrl } = await this.detectServers(options);

    this.cachedEnvironment = {
      projectRoot,
      backendPath: path.resolve(projectRoot, 'Backend'),
      frontendPath: path.resolve(projectRoot, 'Frontend'),
      testDataPath: path.resolve(projectRoot, 'tests', 'data'),
      tempPath: path.resolve(projectRoot, 'tests', 'temp'),
      frontendUrl,
      backendUrl,
      isCI: process.env.CI === 'true' || process.env.GITHUB_ACTIONS === 'true',
      platform
    };

    return this.cachedEnvironment;
  }

  /**
   * Clear cached environment (useful when servers restart)
   */
  clearCache(): void {
    this.cachedEnvironment = null;
  }

  /**
   * Get project root using cross-platform path resolution
   */
  private getProjectRoot(): string {
    // Start from current file and traverse up to find package.json or .git
    let currentDir = __dirname;

    while (currentDir !== path.parse(currentDir).root) {
      const packageJsonPath = path.join(currentDir, 'package.json');
      const gitPath = path.join(currentDir, '.git');

      try {
        require('fs').accessSync(packageJsonPath);
        return currentDir;
      } catch {
        try {
          require('fs').accessSync(gitPath);
          return currentDir;
        } catch {
          currentDir = path.dirname(currentDir);
        }
      }
    }

    // Fallback - assume we're in tests/shared/config
    return path.resolve(__dirname, '..', '..', '..');
  }

  /**
   * Detect current platform
   */
  private getPlatform(): 'windows' | 'linux' | 'darwin' {
    const platform = process.platform;
    if (platform === 'win32') return 'windows';
    if (platform === 'darwin') return 'darwin';
    return 'linux';
  }

  /**
   * Detect running frontend and backend servers
   */
  private async detectServers(options: ServerDetectionOptions = {}): Promise<{ frontendUrl: string; backendUrl: string }> {
    const {
      timeoutMs = 5000,
      retries = 3,
      checkPorts = [3000, 3001, 8000, 8001]
    } = options;

    // Try environment variables first
    const envFrontend = process.env.FRONTEND_URL || process.env.E2E_FRONTEND_URL;
    const envBackend = process.env.BACKEND_URL || process.env.E2E_BACKEND_URL;

    if (envFrontend && envBackend) {
      console.log('[INFO] Using environment URLs');
      return { frontendUrl: envFrontend, backendUrl: envBackend };
    }

    // Detect running servers by checking common ports
    const frontendUrl = await this.detectServerOnPorts([3000, 3001], 'frontend', timeoutMs, retries);
    const backendUrl = await this.detectServerOnPorts([8000, 8001], 'backend', timeoutMs, retries);

    return { frontendUrl, backendUrl };
  }

  /**
   * Check if a server is running on given ports
   */
  private async detectServerOnPorts(
    ports: number[],
    serverType: 'frontend' | 'backend',
    timeoutMs: number,
    retries: number
  ): Promise<string> {
    for (const port of ports) {
      for (let attempt = 0; attempt < retries; attempt++) {
        try {
          const isRunning = await this.isPortActive(port, timeoutMs);
          if (isRunning) {
            const url = `http://localhost:${port}`;
            console.log(`[INFO] Detected ${serverType} server at ${url}`);
            return url;
          }
        } catch (error) {
          console.log(`[WARN] Port ${port} check failed (attempt ${attempt + 1}/${retries})`);
        }
      }
    }

    // Fallback to default ports
    const defaultPort = serverType === 'frontend' ? 3000 : 8000;
    const fallbackUrl = `http://localhost:${defaultPort}`;
    console.log(`[WARN] No ${serverType} server detected, using fallback: ${fallbackUrl}`);
    return fallbackUrl;
  }

  /**
   * Check if a port is actively serving HTTP requests
   */
  private async isPortActive(port: number, timeoutMs: number): Promise<boolean> {
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), timeoutMs);

      const response = await fetch(`http://localhost:${port}`, {
        signal: controller.signal,
        method: 'HEAD'
      });

      clearTimeout(timeout);
      return response.status < 500; // Accept any non-server-error response
    } catch (error) {
      return false;
    }
  }

  /**
   * Create test data directory if it doesn't exist
   */
  async ensureTestDataDirectory(): Promise<string> {
    const env = await this.getEnvironment();
    const fs = require('fs').promises;

    try {
      await fs.access(env.testDataPath);
    } catch {
      await fs.mkdir(env.testDataPath, { recursive: true });
      console.log(`[INFO] Created test data directory: ${env.testDataPath}`);
    }

    return env.testDataPath;
  }

  /**
   * Create temp directory for test artifacts
   */
  async ensureTempDirectory(): Promise<string> {
    const env = await this.getEnvironment();
    const fs = require('fs').promises;

    try {
      await fs.access(env.tempPath);
    } catch {
      await fs.mkdir(env.tempPath, { recursive: true });
      console.log(`[INFO] Created temp directory: ${env.tempPath}`);
    }

    return env.tempPath;
  }

  /**
   * Clean temp directory
   */
  async cleanTempDirectory(): Promise<void> {
    const env = await this.getEnvironment();
    const fs = require('fs').promises;

    try {
      await fs.rm(env.tempPath, { recursive: true, force: true });
      await fs.mkdir(env.tempPath, { recursive: true });
      console.log(`[INFO] Cleaned temp directory: ${env.tempPath}`);
    } catch (error) {
      console.log(`[WARN] Failed to clean temp directory: ${error}`);
    }
  }
}

// Export singleton instance
export const testEnvironment = TestEnvironmentManager.getInstance();

// Export configuration constants
export const TEST_CONFIG = {
  TIMEOUTS: {
    DEFAULT: 30000,
    NAVIGATION: 10000,
    SERVER_DETECTION: 5000,
    API_REQUEST: 10000
  },

  BROWSER: {
    HEADLESS: process.env.TEST_HEADLESS !== 'false',
    SLOWMO: process.env.TEST_SLOWMO ? parseInt(process.env.TEST_SLOWMO) : 0,
    VIEWPORT: { width: 1280, height: 720 },
    ARGS: ['--no-sandbox', '--disable-setuid-sandbox']
  },

  RETRY: {
    DEFAULT_ATTEMPTS: 3,
    DELAY_MS: 1000
  }
} as const;

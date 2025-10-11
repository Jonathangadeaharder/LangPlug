import { spawn, ChildProcess } from 'child_process';
import axios from 'axios';
import * as fs from 'fs-extra';
import * as path from 'path';

export class TestEnvironmentManager {
  private frontendProcess?: ChildProcess;
  private backendProcess?: ChildProcess;
  private readonly projectRoot: string;
  private readonly maxStartupTime = 60000; // 60 seconds

  constructor() {
    this.projectRoot = path.resolve(__dirname, '..', '..', '..');
  }

  async startTestServers(): Promise<void> {
    console.log('⚠️  WARNING: E2E tests now classified as @smoke tests');
    console.log('Please manually start servers before running E2E tests:');
    console.log('1. Backend: cd Backend && python run_backend.py');
    console.log('2. Frontend: cd Frontend && npm run dev');
    console.log('Then run: E2E_SMOKE_TESTS=1 npm run playwright:smoke');

    // Skip server spawning - violates process isolation rules
    console.log('Skipping automatic server startup (violates testing rules)');
  }

  private async startBackendServer(): Promise<void> {
    console.log('Backend server spawn disabled - start manually for smoke tests');
    console.log('E2E tests now require manual backend setup to comply with process isolation rules');
  }

  private async startFrontendServer(): Promise<void> {
    console.log('Frontend server spawn disabled - start manually for smoke tests');
    console.log('E2E tests now require manual frontend setup to comply with process isolation rules');
  }

  private async waitForService(url: string, serviceName: string, timeout: number = this.maxStartupTime): Promise<void> {
    const startTime = Date.now();

    while (Date.now() - startTime < timeout) {
      try {
        const response = await axios.get(url, { timeout: 5000 });
        if (response.status === 200) {
          console.log(`${serviceName} is ready at ${url}`);
          return;
        }
      } catch (error) {
        // Service not ready yet, continue waiting
      }

      await new Promise(resolve => setTimeout(resolve, 1000));
    }

    throw new Error(`${serviceName} failed to start within ${timeout}ms at ${url}`);
  }

  async verifyServicesHealth(): Promise<void> {
    const services = [
      { name: 'Backend', url: 'http://localhost:8001/health' },
      { name: 'Frontend', url: 'http://localhost:3001' }
    ];

    for (const service of services) {
      try {
        const response = await axios.get(service.url, { timeout: 10000 });
        console.log(`${service.name} health check: OK (${response.status})`);
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        console.error(`${service.name} health check failed:`, message);
        throw new Error(`${service.name} is not healthy`);
      }
    }
  }

  async setupTestDatabase(): Promise<void> {
    try {
      // Create test users and data via API
      const response = await axios.post('http://localhost:8001/api/test/setup', {
        users: [
          { username: 'e2euser', email: 'e2e@langplug.com', password: 'TestPassword123!' }
        ],
        vocabulary: [
          { word: 'Hallo', translation: 'Hello', difficulty_level: 'beginner' },
          { word: 'Tschüss', translation: 'Goodbye', difficulty_level: 'beginner' }
        ]
      });

      if (response.status !== 200) {
        throw new Error(`Failed to setup test database: ${response.statusText}`);
      }

      console.log('Test database initialized');
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      console.error('Failed to setup test database:', message);
      // Don't throw - the tests may still work with a clean database
    }
  }

  async cleanupTestData(): Promise<void> {
    try {
      await axios.post('http://localhost:8001/api/test/cleanup');
      console.log('Test data cleaned up');
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      console.error('Failed to cleanup test data:', message);
    }
  }

  async stopTestServers(): Promise<void> {
    const shutdownTimeout = 10000; // 10 seconds

    if (this.frontendProcess) {
      console.log('Stopping frontend server...');
      this.frontendProcess.kill('SIGTERM');

      // Force kill if doesn't stop gracefully
      setTimeout(() => {
        if (this.frontendProcess && !this.frontendProcess.killed) {
          this.frontendProcess.kill('SIGKILL');
        }
      }, shutdownTimeout);
    }

    if (this.backendProcess) {
      console.log('Stopping backend server...');
      this.backendProcess.kill('SIGTERM');

      // Force kill if doesn't stop gracefully
      setTimeout(() => {
        if (this.backendProcess && !this.backendProcess.killed) {
          this.backendProcess.kill('SIGKILL');
        }
      }, shutdownTimeout);
    }

    // Wait for processes to exit
    await new Promise(resolve => setTimeout(resolve, 2000));
  }

  getFrontendUrl(): string {
    return process.env.FRONTEND_URL || 'http://localhost:3001';
  }

  getBackendUrl(): string {
    return process.env.BACKEND_URL || 'http://localhost:8001';
  }
}

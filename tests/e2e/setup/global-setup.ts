import { chromium, FullConfig } from '@playwright/test';
import { TestEnvironmentManager } from '../utils/test-environment-manager';

async function globalSetup(config: FullConfig) {
  console.log('Setting up E2E test environment...');

  const envManager = new TestEnvironmentManager();

  try {
    // Start test servers
    await envManager.startTestServers();

    // Verify services are healthy
    await envManager.verifyServicesHealth();

    // Set up test database with clean state
    await envManager.setupTestDatabase();

    console.log('E2E test environment ready');
  } catch (error) {
    console.error('Failed to set up E2E test environment:', error);
    throw error;
  }
}

export default globalSetup;

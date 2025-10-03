import { FullConfig } from '@playwright/test';
import { TestEnvironmentManager } from '../utils/test-environment-manager';

async function globalTeardown(config: FullConfig) {
  console.log('Tearing down E2E test environment...');

  const envManager = new TestEnvironmentManager();

  try {
    // Clean up test data
    await envManager.cleanupTestData();

    // Stop test servers
    await envManager.stopTestServers();

    console.log('E2E test environment cleaned up');
  } catch (error) {
    console.error('Failed to tear down E2E test environment:', error);
    // Don't throw in teardown to avoid masking test failures
  }
}

export default globalTeardown;

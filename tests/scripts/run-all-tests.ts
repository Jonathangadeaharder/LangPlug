#!/usr/bin/env node

import { ServerManager } from '../utils/server-manager';
import { TestRunner } from '../utils/test-runner';

async function runAllTests() {
  const serverManager = new ServerManager();
  const testRunner = new TestRunner();

  let allTestsPassed = true;

  try {
    console.log('=== Starting Unified Test Suite ===');

    // Start servers
    console.log('\n1. Starting servers...');
    await serverManager.startBackend();
    await serverManager.startFrontend();

    // Wait for servers to be responsive
    console.log('\n2. Waiting for servers to be responsive...');
    if (!serverManager.isBackendReady()) {
      await serverManager.waitForBackend();
    } else {
      console.log('Backend already responsive');
    }
    console.log('Skipping explicit frontend wait; E2E tests will auto-detect the running port.');

    // Run backend tests
    console.log('\n3. Running backend tests...');
    const backendTestsPassed = await testRunner.runBackendTests();
    if (!backendTestsPassed) {
      allTestsPassed = false;
      console.error('Backend tests failed!');
    }

    // Run frontend unit tests
    console.log('\n4. Running frontend unit tests...');
    const frontendTestsPassed = await testRunner.runFrontendUnitTests();
    if (!frontendTestsPassed) {
      allTestsPassed = false;
      console.error('Frontend unit tests failed!');
    }

    // Run E2E tests
    console.log('\n5. Running E2E tests...');
    const e2eTestsPassed = await testRunner.runE2ETests();
    if (!e2eTestsPassed) {
      allTestsPassed = false;
      console.error('E2E tests failed!');
    }

    // Stop servers
    console.log('\n6. Stopping servers...');
    await serverManager.stopAll();

    // Final result
    console.log('\n=== Test Suite Complete ===');
    if (allTestsPassed) {
      console.log('All tests passed! ✅');
      process.exit(0);
    } else {
      console.log('Some tests failed! ❌');
      process.exit(1);
    }
  } catch (error) {
    console.error('Test suite failed with error:', error);
    await serverManager.stopAll();
    process.exit(1);
  }
}

// Run the test suite
runAllTests();

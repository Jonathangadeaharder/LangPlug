#!/usr/bin/env node

import { ServerManager } from '../utils/server-manager';
import { TestRunner } from '../utils/test-runner';

async function runCITests() {
  const serverManager = new ServerManager();
  const testRunner = new TestRunner();
  
  let allTestsPassed = true;
  
  try {
    console.log('=== Starting CI Test Suite ===');
    
    // Start servers with CI-specific configuration
    console.log('\n1. Starting servers...');
    await serverManager.startBackend();
    await serverManager.startFrontend();
    
    // Wait for servers to be responsive with CI timeouts
    console.log('\n2. Waiting for servers to be responsive...');
    await Promise.race([
      serverManager.waitForBackend(),
      new Promise((_, reject) => setTimeout(() => reject(new Error('Backend startup timeout')), 120000)) // 2 minutes
    ]);
    
    await Promise.race([
      serverManager.waitForFrontend(),
      new Promise((_, reject) => setTimeout(() => reject(new Error('Frontend startup timeout')), 120000)) // 2 minutes
    ]);
    
    // Run backend tests with CI timeout
    console.log('\n3. Running backend tests...');
    const backendTestsPassed = await Promise.race([
      testRunner.runBackendTests(),
      new Promise((resolve) => setTimeout(() => resolve(false), 3000)) // 5 minutes
    ]) as boolean;
    
    if (!backendTestsPassed) {
      allTestsPassed = false;
      console.error('Backend tests failed!');
    }
    
    // Run frontend unit tests with CI timeout
    console.log('\n4. Running frontend unit tests...');
    const frontendTestsPassed = await Promise.race([
      testRunner.runFrontendUnitTests(),
      new Promise((resolve) => setTimeout(() => resolve(false), 300000)) // 5 minutes
    ]) as boolean;
    
    if (!frontendTestsPassed) {
      allTestsPassed = false;
      console.error('Frontend unit tests failed!');
    }
    
    // Run E2E tests with CI timeout
    console.log('\n5. Running E2E tests...');
    const e2eTestsPassed = await Promise.race([
      testRunner.runE2ETests(),
      new Promise((resolve) => setTimeout(() => resolve(false), 600000)) // 10 minutes
    ]) as boolean;
    
    if (!e2eTestsPassed) {
      allTestsPassed = false;
      console.error('E2E tests failed!');
    }
    
    // Stop servers
    console.log('\n6. Stopping servers...');
    await serverManager.stopAll();
    
    // Final result
    console.log('\n=== CI Test Suite Complete ===');
    if (allTestsPassed) {
      console.log('All tests passed! ✅');
      process.exit(0);
    } else {
      console.log('Some tests failed! ❌');
      process.exit(1);
    }
  } catch (error) {
    console.error('CI test suite failed with error:', error);
    await serverManager.stopAll();
    process.exit(1);
  }
}

// Run the CI test suite
runCITests();
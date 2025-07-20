#!/usr/bin/env node

const { spawn } = require('child_process');
const path = require('path');

const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m'
};

function log(message, color = colors.reset) {
  console.log(`${color}${message}${colors.reset}`);
}

function runTests(directory, name) {
  return new Promise((resolve, reject) => {
    log(`\n${colors.bright}${colors.blue}Running ${name} tests...${colors.reset}`);
    log(`${colors.cyan}Directory: ${directory}${colors.reset}`);
    
    const isWindows = process.platform === 'win32';
    const npmCommand = isWindows ? 'npm.cmd' : 'npm';
    
    const testProcess = spawn(npmCommand, ['test'], {
      cwd: directory,
      stdio: 'inherit',
      shell: true
    });
    
    testProcess.on('close', (code) => {
      if (code === 0) {
        log(`${colors.green}✓ ${name} tests passed!${colors.reset}`);
        resolve();
      } else {
        log(`${colors.red}✗ ${name} tests failed with exit code ${code}${colors.reset}`);
        reject(new Error(`${name} tests failed`));
      }
    });
    
    testProcess.on('error', (error) => {
      log(`${colors.red}Error running ${name} tests: ${error.message}${colors.reset}`);
      reject(error);
    });
  });
}

async function runAllTests() {
  const projectRoot = __dirname;
  const frontendDir = projectRoot;
  
  log(`${colors.bright}${colors.magenta}🧪 Running All Tests for EpisodeGameApp${colors.reset}`);
  log(`${colors.cyan}Project Root: ${projectRoot}${colors.reset}`);
  log(`${colors.yellow}Note: Backend eliminated in ARCH-02 - Direct Python API communication${colors.reset}`);
  
  const results = {
    frontend: false
  };
  
  try {
    // Run frontend tests (includes Python API integration tests)
    await runTests(frontendDir, 'Frontend & Python API Integration');
    results.frontend = true;
  } catch (error) {
    log(`${colors.red}Frontend tests failed: ${error.message}${colors.reset}`);
  }
  
  // Summary
  log(`\n${colors.bright}${colors.magenta}📊 Test Results Summary${colors.reset}`);
  log(`${colors.cyan}========================${colors.reset}`);
  
  const frontendStatus = results.frontend ? 
    `${colors.green}✓ PASSED${colors.reset}` : 
    `${colors.red}✗ FAILED${colors.reset}`;
  
  log(`Frontend & Python API Tests: ${frontendStatus}`);
  
  const allPassed = results.frontend;
  
  if (allPassed) {
    log(`\n${colors.bright}${colors.green}🎉 All tests passed successfully!${colors.reset}`);
    process.exit(0);
  } else {
    log(`\n${colors.bright}${colors.red}❌ Some tests failed. Please check the output above.${colors.reset}`);
    process.exit(1);
  }
}

// Handle process termination
process.on('SIGINT', () => {
  log(`\n${colors.yellow}Test execution interrupted by user${colors.reset}`);
  process.exit(1);
});

process.on('SIGTERM', () => {
  log(`\n${colors.yellow}Test execution terminated${colors.reset}`);
  process.exit(1);
});

// Run the tests
runAllTests().catch((error) => {
  log(`${colors.red}Unexpected error: ${error.message}${colors.reset}`);
  process.exit(1);
});
#!/usr/bin/env ts-node
/**
 * Main Test Runner - Comprehensive test orchestration
 * Runs all test suites with proper isolation, contract validation, and reporting
 */

import * as path from 'path';
import * as fs from 'fs-extra';
import { ParallelTestRunner, TestSuite } from './infrastructure/parallel-test-runner';
import { ContractValidator } from './infrastructure/contract-validator';
import { TestDataManager } from './infrastructure/test-data-manager';
import { TestOrchestrator } from './infrastructure/test-orchestrator';
import chalk from 'chalk';

// Parse command line arguments
const args = process.argv.slice(2);
const options = {
  suite: args.find(arg => arg.startsWith('--suite='))?.split('=')[1],
  parallel: !args.includes('--sequential'),
  verbose: args.includes('--verbose') || args.includes('-v'),
  bail: args.includes('--bail'),
  coverage: args.includes('--coverage'),
  contractValidation: !args.includes('--no-contract'),
  filter: args.find(arg => arg.startsWith('--filter='))?.split('=')[1],
  retries: parseInt(args.find(arg => arg.startsWith('--retries='))?.split('=')[1] || '1'),
  report: args.includes('--report'),
  watch: args.includes('--watch'),
  maxWorkers: parseInt(args.find(arg => arg.startsWith('--workers='))?.split('=')[1] || '0'),
};

// Display help if requested
if (args.includes('--help') || args.includes('-h')) {
  console.log(`
${chalk.bold('LangPlug Test Runner')}

${chalk.yellow('Usage:')} npm run test:all [options]

${chalk.yellow('Options:')}
  --suite=<name>      Run specific test suite (unit, integration, e2e, contract, all)
  --sequential        Run tests sequentially instead of in parallel
  --verbose, -v       Verbose output
  --bail              Stop on first test failure
  --coverage          Generate code coverage report
  --no-contract       Disable contract validation
  --filter=<pattern>  Filter test files by pattern
  --retries=<n>       Number of retries for failed tests (default: 1)
  --report            Generate HTML test report
  --watch             Watch mode for continuous testing
  --workers=<n>       Maximum number of parallel workers
  --help, -h          Show this help message

${chalk.yellow('Examples:')}
  npm run test:all                     # Run all tests in parallel
  npm run test:all --suite=unit        # Run only unit tests
  npm run test:all --bail --verbose    # Stop on first failure with verbose output
  npm run test:all --filter=auth       # Run only auth-related tests
  `);
  process.exit(0);
}

// Test suite definitions
const testSuites: TestSuite[] = [
  {
    name: 'backend-unit',
    type: 'unit',
    environment: 'isolated',
    parallel: true,
    timeout: 30000,
    files: [],  // Will be populated dynamically
  },
  {
    name: 'frontend-unit',
    type: 'unit',
    environment: 'isolated',
    parallel: true,
    timeout: 30000,
    files: [],  // Will be populated dynamically
  },
  {
    name: 'backend-integration',
    type: 'integration',
    environment: 'shared',
    parallel: false,
    timeout: 60000,
    files: [],  // Will be populated dynamically
  },
  {
    name: 'frontend-integration',
    type: 'integration',
    environment: 'shared',
    parallel: false,
    timeout: 60000,
    files: [],  // Will be populated dynamically
  },
  {
    name: 'contract',
    type: 'contract',
    environment: 'shared',
    parallel: true,
    timeout: 30000,
    files: [],  // Will be populated dynamically
  },
  {
    name: 'e2e',
    type: 'e2e',
    environment: 'isolated',
    parallel: true,
    timeout: 300000,
    retries: 1,
    files: [],  // Will be populated dynamically
  },
];

/**
 * Discover test files for each suite
 */
async function discoverTestFiles(): Promise<void> {
  const projectRoot = path.resolve(__dirname, '..');

  // Backend unit tests
  const backendTestsPath = path.resolve(projectRoot, 'src', 'backend', 'tests');
  const backendUnitFiles = await fs.readdir(backendTestsPath);
  testSuites.find(s => s.name === 'backend-unit')!.files = backendUnitFiles
    .filter(f => f.startsWith('test_') && f.endsWith('.py'))
    .map(f => path.resolve(backendTestsPath, f));

  // Frontend unit tests
  const frontendSrcPath = path.resolve(projectRoot, 'src', 'frontend', 'src');
  if (await fs.pathExists(frontendSrcPath)) {
    const frontendUnitFiles = await findTestFiles(frontendSrcPath, '.test.ts', '.test.tsx');
    testSuites.find(s => s.name === 'frontend-unit')!.files = frontendUnitFiles;
  }

  // Contract tests
  const contractTestPath = path.resolve(projectRoot, 'tests', 'contract');
  if (await fs.pathExists(contractTestPath)) {
    const contractFiles = await fs.readdir(contractTestPath);
    testSuites.find(s => s.name === 'contract')!.files = contractFiles
      .filter(f => f.endsWith('.test.ts'))
      .map(f => path.resolve(contractTestPath, f));
  }

  // E2E tests
  const e2eTestsPath = path.resolve(projectRoot, 'tests', 'e2e');
  const e2eFiles = await findTestFiles(e2eTestsPath, '.test.ts', '.spec.ts', '.setup.ts');
  testSuites.find(s => s.name === 'e2e')!.files = e2eFiles;
}

/**
 * Recursively find test files
 */
async function findTestFiles(dir: string, ...extensions: string[]): Promise<string[]> {
  const files: string[] = [];
  const items = await fs.readdir(dir, { withFileTypes: true });

  for (const item of items) {
    const fullPath = path.join(dir, item.name);

    if (item.isDirectory() && !item.name.includes('node_modules')) {
      files.push(...await findTestFiles(fullPath, ...extensions));
    } else if (item.isFile() && extensions.some(ext => item.name.endsWith(ext))) {
      files.push(fullPath);
    }
  }

  return files;
}

/**
 * Main test execution
 */
async function runTests(): Promise<void> {
  console.log(chalk.bold.cyan('\n🚀 LangPlug Test Runner\n'));

  try {
    // Discover test files
    console.log(chalk.yellow('📁 Discovering test files...'));
    await discoverTestFiles();

    // Filter suites based on options
    let suitesToRun = testSuites;
    if (options.suite && options.suite !== 'all') {
      suitesToRun = testSuites.filter(s =>
        s.name.includes(options.suite!) || s.type === options.suite
      );

      if (suitesToRun.length === 0) {
        throw new Error(`No test suite found matching: ${options.suite}`);
      }
    }

    // Remove empty suites
    suitesToRun = suitesToRun.filter(s => s.files.length > 0);

    if (suitesToRun.length === 0) {
      console.log(chalk.yellow('⚠️  No test files found'));
      process.exit(0);
    }

    // Display test plan
    console.log(chalk.cyan('\n📋 Test Plan:'));
    for (const suite of suitesToRun) {
      console.log(chalk.white(`  • ${suite.name}: ${suite.files.length} files`));
    }

    // Initialize test runner
    const runner = new ParallelTestRunner(options.maxWorkers);

    // Set up event listeners for progress reporting
    runner.on('suite:start', (suite: TestSuite) => {
      console.log(chalk.cyan(`\n▶️  Running ${suite.name} tests...`));
    });

    runner.on('file:complete', ({ file, result }: any) => {
      const fileName = path.basename(file);
      if (result.failed > 0) {
        console.log(chalk.red(`  ✗ ${fileName}: ${result.failed} failed`));
      } else if (result.skipped > 0) {
        console.log(chalk.yellow(`  ⊘ ${fileName}: ${result.skipped} skipped`));
      } else {
        console.log(chalk.green(`  ✓ ${fileName}: ${result.passed} passed`));
      }
    });

    runner.on('contract:violation', (violation: any) => {
      console.log(chalk.red(`\n⚠️  Contract Violation: ${violation.endpoint}`));
      console.log(chalk.red(`   ${violation.message}`));
    });

    runner.on('file:retry', ({ file, attempt }: any) => {
      console.log(chalk.yellow(`  🔄 Retrying ${path.basename(file)} (attempt ${attempt})...`));
    });

    // Run tests
    console.log(chalk.cyan('\n🏃 Running tests...\n'));
    const startTime = Date.now();

    const { success, results, summary } = await runner.runSuites(suitesToRun, {
      parallel: options.parallel,
      bail: options.bail,
      timeout: 300000,
      retries: options.retries,
      coverage: options.coverage,
      verbose: options.verbose,
      contractValidation: options.contractValidation,
      filter: options.filter,
    });

    // Display summary
    const duration = Date.now() - startTime;
    console.log(chalk.bold.cyan('\n📊 Test Summary\n'));
    console.log(chalk.white(`  Total:    ${summary.total}`));
    console.log(chalk.green(`  Passed:   ${summary.passed}`));
    console.log(chalk.red(`  Failed:   ${summary.failed}`));
    console.log(chalk.yellow(`  Skipped:  ${summary.skipped}`));
    console.log(chalk.blue(`  Duration: ${(duration / 1000).toFixed(2)}s`));
    console.log(chalk.magenta(`  Pass Rate: ${summary.passRate.toFixed(1)}%`));

    // Display failures if any
    if (summary.failed > 0) {
      console.log(chalk.bold.red('\n❌ Failed Tests:\n'));

      for (const result of results) {
        if (result.failures && result.failures.length > 0) {
          console.log(chalk.red(`\n  ${result.suite} - ${path.basename(result.file)}:`));
          for (const failure of result.failures) {
            console.log(chalk.red(`    • ${failure.test}`));
            console.log(chalk.gray(`      ${failure.error}`));
          }
        }

        if (result.contractViolations && result.contractViolations.length > 0) {
          console.log(chalk.red(`\n  Contract Violations in ${result.file}:`));
          for (const violation of result.contractViolations) {
            console.log(chalk.red(`    • ${violation.endpoint}: ${violation.message}`));
          }
        }
      }
    }

    // Generate HTML report if requested
    if (options.report) {
      const projectRoot = path.resolve(__dirname, '..');
      const reportPath = path.resolve(projectRoot, 'test-report.html');
      await runner.generateHTMLReport(reportPath);
      console.log(chalk.cyan(`\n📄 HTML report generated: ${reportPath}`));
    }

    // Generate coverage report if requested
    if (options.coverage) {
      console.log(chalk.cyan('\n📈 Coverage report:'));
      // Coverage would be generated by the test frameworks
      console.log(chalk.gray('  Coverage reports generated in respective test directories'));
    }

    // Exit with appropriate code
    if (success) {
      console.log(chalk.bold.green('\n✅ All tests passed!\n'));
      process.exit(0);
    } else {
      console.log(chalk.bold.red('\n❌ Some tests failed. Please fix them immediately.\n'));
      process.exit(1);
    }
  } catch (error) {
    console.error(chalk.bold.red('\n💥 Test execution failed:\n'));
    console.error(chalk.red((error as Error).message || error));
    if (options.verbose && (error as Error).stack) {
      console.error(chalk.gray((error as Error).stack));
    }
    process.exit(1);
  }
}

/**
 * Watch mode implementation
 */
async function watchTests(): Promise<void> {
  const chokidar = await import('chokidar');

  console.log(chalk.bold.cyan('\n👀 Watch Mode Enabled\n'));
  console.log(chalk.gray('Watching for file changes...\n'));

  const projectRoot = path.resolve(__dirname, '..');

  // Set up file watchers
  const watchers = [
    chokidar.watch(path.resolve(projectRoot, 'src', 'backend', '**', '*.py'), {
      ignored: /(^|[\/\\])\../,
      persistent: true
    }),
    chokidar.watch(path.resolve(projectRoot, 'src', 'frontend', 'src', '**', '*.{ts,tsx}'), {
      ignored: /(^|[\/\\])\../,
      persistent: true
    }),
    chokidar.watch(path.resolve(projectRoot, 'tests', '**', '*.{ts,js}'), {
      ignored: /(^|[\/\\])\../,
      persistent: true
    }),
  ];

  let isRunning = false;
  let pendingRun = false;

  const runTestsDebounced = async () => {
    if (isRunning) {
      pendingRun = true;
      return;
    }

    isRunning = true;
    console.clear();
    await runTests();
    isRunning = false;

    if (pendingRun) {
      pendingRun = false;
      await runTestsDebounced();
    }
  };

  // Set up event handlers
  for (const watcher of watchers) {
    watcher.on('change', (path: string) => {
      console.log(chalk.yellow(`\n📝 File changed: ${path}`));
      runTestsDebounced();
    });
  }

  // Run initial tests
  await runTests();

  // Keep process alive
  process.stdin.resume();
}

// Main entry point
(async () => {
  try {
    if (options.watch) {
      await watchTests();
    } else {
      await runTests();
    }
  } catch (error) {
    console.error(chalk.bold.red('Fatal error:'), error);
    process.exit(1);
  }
})();

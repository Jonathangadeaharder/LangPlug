#!/usr/bin/env ts-node

/**
 * Unified Test Orchestrator
 *
 * Single command to run all tests with structured reporting.
 * Coordinates backend, frontend, and E2E tests with proper failure handling.
 */

import { exec, spawn, ChildProcess } from 'child_process';
import { promisify } from 'util';
import path from 'path';
import fs from 'fs/promises';
import { testEnvironment } from './shared/config/test-environment';

const execAsync = promisify(exec);

interface TestSuiteResult {
  name: string;
  status: 'passed' | 'failed' | 'skipped';
  duration: number;
  details: string;
  coverage?: number;
  error?: string;
}

interface TestOrchestrationConfig {
  skipBackend: boolean;
  skipFrontend: boolean;
  skipE2E: boolean;
  coverage: boolean;
  verbose: boolean;
  parallel: boolean;
  outputFormat: 'console' | 'junit' | 'json';
  timeoutMinutes: number;
}

class TestOrchestrator {
  private results: TestSuiteResult[] = [];
  private startTime: number = 0;
  private config: TestOrchestrationConfig;
  private environment: any;

  constructor(config: Partial<TestOrchestrationConfig> = {}) {
    this.config = {
      skipBackend: false,
      skipFrontend: false,
      skipE2E: false,
      coverage: false,
      verbose: false,
      parallel: true,
      outputFormat: 'console',
      timeoutMinutes: 30,
      ...config
    };
  }

  async orchestrateAllTests(): Promise<boolean> {
    this.startTime = Date.now();
    console.log('[INFO] Starting Test Orchestration');
    console.log('='.repeat(80));

    try {
      // Initialize environment
      this.environment = await testEnvironment.getEnvironment();
      console.log(`[INFO] Project Root: ${this.environment.projectRoot}`);
      console.log(`[INFO] Frontend URL: ${this.environment.frontendUrl}`);
      console.log(`[INFO] Backend URL: ${this.environment.backendUrl}`);
      console.log(`[INFO] Platform: ${this.environment.platform}`);
      console.log(`[INFO] CI Environment: ${this.environment.isCI}`);

      // Ensure test directories exist
      await this.ensureTestEnvironment();

      // Run test suites
      const testSuites: Array<() => Promise<TestSuiteResult>> = [];

      if (!this.config.skipBackend) {
        testSuites.push(() => this.runBackendTests());
      }

      if (!this.config.skipFrontend) {
        testSuites.push(() => this.runFrontendTests());
      }

      if (!this.config.skipE2E) {
        testSuites.push(() => this.runE2ETests());
      }

      // Run suites in parallel or sequentially
      if (this.config.parallel) {
        console.log('[INFO] Running test suites in parallel');
        const results = await Promise.allSettled(
          testSuites.map(suite => suite())
        );

        for (const result of results) {
          if (result.status === 'fulfilled') {
            this.results.push(result.value);
          } else {
            this.results.push({
              name: 'unknown',
              status: 'failed',
              duration: 0,
              details: 'Test suite execution failed',
              error: result.reason?.toString()
            });
          }
        }
      } else {
        console.log('[INFO] Running test suites sequentially');
        for (const suite of testSuites) {
          try {
            const result = await suite();
            this.results.push(result);
          } catch (error) {
            this.results.push({
              name: 'unknown',
              status: 'failed',
              duration: 0,
              details: 'Test suite execution failed',
              error: error?.toString()
            });
          }
        }
      }

      // Generate reports
      await this.generateReports();

      // Determine overall success
      const failed = this.results.filter(r => r.status === 'failed');
      const success = failed.length === 0;

      console.log('\n' + '='.repeat(80));
      console.log(`[${success ? 'SUCCESS' : 'FAILURE'}] Test orchestration completed`);
      console.log(`Total Duration: ${((Date.now() - this.startTime) / 1000).toFixed(2)}s`);

      return success;

    } catch (error) {
      console.error('[ERROR] Test orchestration failed:', error);
      return false;
    }
  }

  private async ensureTestEnvironment(): Promise<void> {
    // Ensure temp directories exist
    await testEnvironment.ensureTestDataDirectory();
    await testEnvironment.ensureTempDirectory();

    // Clean previous test artifacts
    await testEnvironment.cleanTempDirectory();

    console.log('[INFO] Test environment prepared');
  }

  private async runBackendTests(): Promise<TestSuiteResult> {
    console.log('\n[RUN] Backend Test Suite');
    const startTime = Date.now();

    try {
      const backendPath = path.resolve(this.environment.projectRoot, 'Backend');
      const testRunnerPath = path.resolve(backendPath, 'tests', 'run_backend_tests.py');

      // Check if backend test runner exists
      try {
        await fs.access(testRunnerPath);
      } catch {
        return {
          name: 'backend',
          status: 'skipped',
          duration: 0,
          details: 'Backend test runner not found'
        };
      }

      // Build command
      const cmd = this.environment.platform === 'windows'
        ? `powershell.exe python "${testRunnerPath}"`
        : `python3 "${testRunnerPath}"`;

      const cmdArgs = [];
      if (this.config.coverage) cmdArgs.push('--coverage');
      if (this.config.verbose) cmdArgs.push('--verbose');
      cmdArgs.push('--format', this.config.outputFormat);

      const fullCmd = `${cmd} ${cmdArgs.join(' ')}`;

      if (this.config.verbose) {
        console.log(`[DEBUG] Backend command: ${fullCmd}`);
      }

      const result = await execAsync(fullCmd, {
        cwd: backendPath,
        timeout: this.config.timeoutMinutes * 60 * 1000
      });

      const duration = Date.now() - startTime;

      // Parse coverage if available
      let coverage: number | undefined;
      if (this.config.coverage) {
        try {
          const coverageData = await fs.readFile(
            path.resolve(backendPath, 'coverage.json'),
            'utf-8'
          );
          const coverageJson = JSON.parse(coverageData);
          coverage = coverageJson.totals?.percent_covered;
        } catch {
          // Coverage file not found or invalid
        }
      }

      return {
        name: 'backend',
        status: 'passed',
        duration,
        details: `Backend tests completed successfully`,
        coverage,
      };

    } catch (error: any) {
      const duration = Date.now() - startTime;
      return {
        name: 'backend',
        status: 'failed',
        duration,
        details: 'Backend tests failed',
        error: error.message || error.toString()
      };
    }
  }

  private async runFrontendTests(): Promise<TestSuiteResult> {
    console.log('\n[RUN] Frontend Test Suite');
    const startTime = Date.now();

    try {
      const frontendPath = path.resolve(this.environment.projectRoot, 'Frontend');

      // Check if package.json exists
      try {
        await fs.access(path.resolve(frontendPath, 'package.json'));
      } catch {
        return {
          name: 'frontend',
          status: 'skipped',
          duration: 0,
          details: 'Frontend package.json not found'
        };
      }

      // Run frontend tests
      const cmd = this.environment.platform === 'windows'
        ? 'powershell.exe npm test -- --watchAll=false --coverage=false'
        : 'npm test -- --watchAll=false --coverage=false';

      if (this.config.coverage) {
        const cmdWithCoverage = cmd.replace('--coverage=false', '--coverage=true');
      }

      if (this.config.verbose) {
        console.log(`[DEBUG] Frontend command: ${cmd}`);
      }

      const result = await execAsync(cmd, {
        cwd: frontendPath,
        timeout: this.config.timeoutMinutes * 60 * 1000,
        env: {
          ...process.env,
          FRONTEND_URL: this.environment.frontendUrl,
          BACKEND_URL: this.environment.backendUrl,
          CI: 'true'
        }
      });

      const duration = Date.now() - startTime;

      return {
        name: 'frontend',
        status: 'passed',
        duration,
        details: 'Frontend tests completed successfully'
      };

    } catch (error: any) {
      const duration = Date.now() - startTime;
      return {
        name: 'frontend',
        status: 'failed',
        duration,
        details: 'Frontend tests failed',
        error: error.message || error.toString()
      };
    }
  }

  private async runE2ETests(): Promise<TestSuiteResult> {
    console.log('\n[RUN] E2E Test Suite');
    const startTime = Date.now();

    try {
      const testsPath = path.resolve(this.environment.projectRoot, 'tests');

      // Use Playwright directly - no fallbacks
      const cmd = this.environment.platform === 'windows'
        ? 'powershell.exe npx playwright test'
        : 'npx playwright test';

      if (this.config.verbose) {
        console.log(`[DEBUG] E2E command (Playwright): ${cmd}`);
      }

      const result = await execAsync(cmd, {
        cwd: testsPath,
        timeout: this.config.timeoutMinutes * 60 * 1000,
        env: {
          ...process.env,
          FRONTEND_URL: this.environment.frontendUrl,
          BACKEND_URL: this.environment.backendUrl,
          HEADLESS: 'true'
        }
      });

      const duration = Date.now() - startTime;

      return {
        name: 'e2e',
        status: 'passed',
        duration,
        details: 'E2E tests completed successfully'
      };

    } catch (error: any) {
      const duration = Date.now() - startTime;
      return {
        name: 'e2e',
        status: 'failed',
        duration,
        details: 'E2E tests failed',
        error: error.message || error.toString()
      };
    }
  }

  private async generateReports(): Promise<void> {
    console.log('\n[INFO] Generating test reports');

    // Console report (always generated)
    this.generateConsoleReport();

    // Additional reports based on format
    if (this.config.outputFormat === 'junit') {
      await this.generateJUnitReport();
    }

    if (this.config.outputFormat === 'json') {
      await this.generateJSONReport();
    }

    // Always generate summary JSON for CI
    await this.generateSummaryJSON();
  }

  private generateConsoleReport(): void {
    console.log('\n' + '='.repeat(80));
    console.log('TEST ORCHESTRATION SUMMARY');
    console.log('='.repeat(80));

    const passed = this.results.filter(r => r.status === 'passed').length;
    const failed = this.results.filter(r => r.status === 'failed').length;
    const skipped = this.results.filter(r => r.status === 'skipped').length;
    const total = this.results.length;

    console.log(`Total Test Suites: ${total}`);
    console.log(`Passed: ${passed}`);
    console.log(`Failed: ${failed}`);
    console.log(`Skipped: ${skipped}`);

    console.log('\nSUITE DETAILS:');
    for (const result of this.results) {
      const status = result.status === 'passed' ? '[PASS]' :
                    result.status === 'failed' ? '[FAIL]' : '[SKIP]';
      const duration = (result.duration / 1000).toFixed(2);
      console.log(`  ${status} ${result.name.padEnd(10)} | ${duration.padStart(6)}s | ${result.details}`);

      if (result.coverage) {
        console.log(`    Coverage: ${result.coverage.toFixed(1)}%`);
      }

      if (result.error && this.config.verbose) {
        console.log(`    Error: ${result.error}`);
      }
    }

    const overallStatus = failed === 0 ? 'PASSED' : 'FAILED';
    const totalDuration = ((Date.now() - this.startTime) / 1000).toFixed(2);
    console.log(`\nOVERALL STATUS: ${overallStatus} (${totalDuration}s)`);
  }

  private async generateJUnitReport(): Promise<void> {
    try {
      // Generate JUnit XML (simplified version)
      const xml = `<?xml version="1.0" encoding="UTF-8"?>
<testsuites name="all-tests" tests="${this.results.length}" failures="${this.results.filter(r => r.status === 'failed').length}">
${this.results.map(result => `
  <testsuite name="${result.name}" tests="1" failures="${result.status === 'failed' ? 1 : 0}">
    <testcase name="${result.name}" time="${(result.duration / 1000).toFixed(3)}">
      ${result.status === 'failed' ? `<failure message="${result.details}">${result.error || 'Test suite failed'}</failure>` : ''}
    </testcase>
  </testsuite>`).join('')}
</testsuites>`;

      await fs.writeFile('test-results-all.xml', xml);
      console.log('[INFO] JUnit report: test-results-all.xml');
    } catch (error) {
      console.log(`[WARN] Could not generate JUnit report: ${error}`);
    }
  }

  private async generateJSONReport(): Promise<void> {
    try {
      const report = {
        timestamp: new Date().toISOString(),
        duration: Date.now() - this.startTime,
        environment: {
          platform: this.environment.platform,
          ci: this.environment.isCI,
          frontendUrl: this.environment.frontendUrl,
          backendUrl: this.environment.backendUrl
        },
        summary: {
          total: this.results.length,
          passed: this.results.filter(r => r.status === 'passed').length,
          failed: this.results.filter(r => r.status === 'failed').length,
          skipped: this.results.filter(r => r.status === 'skipped').length
        },
        suites: this.results
      };

      await fs.writeFile('test-results-all.json', JSON.stringify(report, null, 2));
      console.log('[INFO] JSON report: test-results-all.json');
    } catch (error) {
      console.log(`[WARN] Could not generate JSON report: ${error}`);
    }
  }

  private async generateSummaryJSON(): Promise<void> {
    try {
      const summary = {
        success: this.results.filter(r => r.status === 'failed').length === 0,
        total: this.results.length,
        passed: this.results.filter(r => r.status === 'passed').length,
        failed: this.results.filter(r => r.status === 'failed').length,
        duration: Date.now() - this.startTime,
        timestamp: new Date().toISOString()
      };

      await fs.writeFile('test-summary.json', JSON.stringify(summary, null, 2));
    } catch (error) {
      console.log(`[WARN] Could not generate summary JSON: ${error}`);
    }
  }
}

// CLI Interface
async function main() {
  const args = process.argv.slice(2);

  const config: Partial<TestOrchestrationConfig> = {
    skipBackend: args.includes('--skip-backend'),
    skipFrontend: args.includes('--skip-frontend'),
    skipE2E: args.includes('--skip-e2e'),
    coverage: args.includes('--coverage'),
    verbose: args.includes('--verbose') || args.includes('-v'),
    parallel: !args.includes('--sequential'),
    outputFormat: args.includes('--junit') ? 'junit' :
                  args.includes('--json') ? 'json' : 'console',
    timeoutMinutes: parseInt(args.find(arg => arg.startsWith('--timeout='))?.split('=')[1] || '30')
  };

  if (args.includes('--help') || args.includes('-h')) {
    console.log(`
Usage: ts-node run-all-tests.ts [options]

Options:
  --skip-backend    Skip backend tests
  --skip-frontend   Skip frontend tests
  --skip-e2e        Skip E2E tests
  --coverage        Generate coverage reports
  --verbose, -v     Verbose output
  --sequential      Run suites sequentially (default: parallel)
  --junit           Generate JUnit XML report
  --json            Generate JSON report
  --timeout=N       Timeout in minutes (default: 30)
  --help, -h        Show this help
`);
    process.exit(0);
  }

  const orchestrator = new TestOrchestrator(config);
  const success = await orchestrator.orchestrateAllTests();

  process.exit(success ? 0 : 1);
}

if (require.main === module) {
  main().catch(error => {
    console.error('Test orchestration failed:', error);
    process.exit(1);
  });
}

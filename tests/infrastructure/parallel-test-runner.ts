/**
 * Parallel Test Runner - Execute tests in parallel with proper isolation
 * Optimized for speed and reliability
 */

import { Worker } from 'worker_threads';
import * as os from 'os';
import * as path from 'path';
import * as fs from 'fs-extra';
import { EventEmitter } from 'events';
import { TestOrchestrator, TestEnvironment } from './test-orchestrator';
import { ContractValidator } from './contract-validator';
import { TestDataManager } from './test-data-manager';

export interface TestSuite {
  name: string;
  files: string[];
  type: 'unit' | 'integration' | 'e2e' | 'contract';
  environment?: 'isolated' | 'shared';
  parallel?: boolean;
  timeout?: number;
  retries?: number;
}

export interface TestResult {
  suite: string;
  file: string;
  tests: number;
  passed: number;
  failed: number;
  skipped: number;
  duration: number;
  failures?: TestFailure[];
  contractViolations?: any[];
}

export interface TestFailure {
  test: string;
  error: string;
  stack?: string;
  expected?: any;
  actual?: any;
}

export interface TestRunOptions {
  parallel?: boolean;
  maxWorkers?: number;
  bail?: boolean;
  timeout?: number;
  retries?: number;
  coverage?: boolean;
  verbose?: boolean;
  contractValidation?: boolean;
  filter?: string;
}

export class ParallelTestRunner extends EventEmitter {
  private orchestrator: TestOrchestrator;
  private contractValidator: ContractValidator;
  private testDataManager: TestDataManager;
  private workers: Map<string, Worker> = new Map();
  private environments: Map<string, TestEnvironment> = new Map();
  private results: TestResult[] = [];
  private maxWorkers: number;

  constructor(maxWorkers?: number) {
    super();
    this.maxWorkers = maxWorkers || Math.max(1, os.cpus().length - 1);
    this.orchestrator = new TestOrchestrator();
    this.contractValidator = new ContractValidator();
    this.testDataManager = new TestDataManager();

    // Warn if maxWorkers might exceed available ports for isolated environments
    // Each isolated environment uses 2 ports (backend + frontend)
    const estimatedMaxPortPool = 501; // From 9000 to 9500 inclusive
    const recommendedMaxWorkers = Math.floor(estimatedMaxPortPool / 2 * 0.75); // Use 75% of available pairs

    if (this.maxWorkers > recommendedMaxWorkers) {
      console.warn(
        `[ParallelTestRunner] Warning: maxWorkers (${this.maxWorkers}) might be too high for the configured port pool. ` +
        `With 2 ports per isolated environment, this could lead to port exhaustion. ` +
        `Recommended maxWorkers based on current port pool: ${recommendedMaxWorkers}. ` +
        `Consider reducing maxWorkers or increasing the port range in test-orchestrator.ts.`
      );
    }
  }

  /**
   * Run test suites
   */
  async runSuites(suites: TestSuite[], options: TestRunOptions = {}): Promise<{
    success: boolean;
    results: TestResult[];
    summary: TestSummary;
  }> {
    this.results = [];
    const startTime = Date.now();
    const projectRoot = path.resolve(__dirname, '..', '..');

    // Setup server logging if verbose
    if (options.verbose) {
      this.orchestrator.on('server:log', ({ server, data }) => {
        const lines = data.toString().split('\n');
        for (const line of lines) {
          if (line.trim()) console.log(`[${server}] ${line.trim()}`);
        }
      });
      this.orchestrator.on('server:error', ({ server, data }) => {
        const lines = data.toString().split('\n');
        for (const line of lines) {
          if (line.trim()) console.error(`[${server} ERROR] ${line.trim()}`);
        }
      });
    }

    // Initialize contract validator if needed
    if (options.contractValidation) {
      const specPath = path.resolve(projectRoot, 'src', 'backend', 'openapi.json');
      if (await fs.pathExists(specPath)) {
        await this.contractValidator.loadSpec(specPath);
      }
    }

    // Group suites by environment requirement
    const isolatedSuites = suites.filter(s => s.environment === 'isolated');
    const sharedSuites = suites.filter(s => s.environment !== 'isolated');

    // Run isolated suites in parallel with separate environments
    if (isolatedSuites.length > 0) {
      await this.runIsolatedSuites(isolatedSuites, options);
    }

    // Run shared suites with a single environment
    if (sharedSuites.length > 0) {
      await this.runSharedSuites(sharedSuites, options);
    }

    // Generate summary
    const summary = this.generateSummary(Date.now() - startTime);

    // Cleanup
    await this.cleanup();

    return {
      success: summary.failed === 0,
      results: this.results,
      summary,
    };
  }

  /**
   * Run isolated test suites in parallel
   */
  private async runIsolatedSuites(suites: TestSuite[], options: TestRunOptions): Promise<void> {
    const parallel = options.parallel !== false;
    const maxConcurrent = parallel ? Math.min(this.maxWorkers, suites.length) : 1;

    const queue = [...suites];
    const running: Promise<void>[] = [];

    while (queue.length > 0 || running.length > 0) {
      // Start new workers up to max concurrent
      while (running.length < maxConcurrent && queue.length > 0) {
        const suite = queue.shift()!;
        const promise = this.runIsolatedSuite(suite, options);
        running.push(promise);
      }

      // Wait for at least one to complete
      if (running.length > 0) {
        await Promise.race(running);
        // Remove completed promises
        for (let i = running.length - 1; i >= 0; i--) {
          if (await this.isPromiseResolved(running[i])) {
            running.splice(i, 1);
          }
        }
      }

      // Check for bail condition
      if (options.bail && this.results.some(r => r.failed > 0)) {
        this.emit('bail', 'Test failure detected, bailing out');
        break;
      }
    }

    // Wait for remaining workers
    await Promise.all(running);
  }

  /**
   * Run a single isolated test suite
   */
  private async runIsolatedSuite(suite: TestSuite, options: TestRunOptions): Promise<void> {
    const envId = `${suite.name}-${Date.now()}`;

    try {
      // Unit tests don't need a full environment - they use mocks
      let environment: TestEnvironment;
      let testData: any;

      if (suite.type === 'unit') {
        // Create a minimal mock environment for unit tests
        environment = {
          id: envId,
          backend: {
            config: { name: 'mock-backend', command: '', args: [], cwd: '', ports: [8000] },
            url: 'http://localhost:8000',
            port: 8000,
            ready: true,
            logs: [],
            errors: [],
          },
          frontend: {
            config: { name: 'mock-frontend', command: '', args: [], cwd: '', ports: [3000] },
            url: 'http://localhost:3000',
            port: 3000,
            ready: true,
            logs: [],
            errors: [],
          },
          tempDir: '',
          logDir: '',
        };
      } else {
        // Generate test data for the suite
        testData = await this.testDataManager.createScenario('basic');
        const env = { TEST_DATA: JSON.stringify(testData) };

        // Create and start real environment for non-unit tests
        environment = await this.orchestrator.createEnvironment(envId, env);
        await this.orchestrator.startEnvironment(envId);
      }

      this.environments.set(suite.name, environment);
      this.emit('suite:start', suite);

      // OPTIMIZATION: Run E2E tests in a single batch to leverage Playwright's internal parallelism
      if (suite.type === 'e2e' && suite.parallel !== false && options.parallel !== false) {
        // Use the generated testData (we need to cast environment to any or access it differently if we didn't store testData in it)
        // Actually we have testData variable here.
        await this.runE2EBatch(suite, environment, options, testData);
      } else {
        const parallel = suite.parallel !== false && options.parallel !== false;

        if (parallel) {
          // Run files in parallel with maxWorkers limit
          const queue = [...suite.files].filter(f => !options.filter || f.includes(options.filter));
          const running: Promise<void>[] = [];

          while (queue.length > 0 || running.length > 0) {
            while (running.length < this.maxWorkers && queue.length > 0) {
              const file = queue.shift()!;
              const promise = this.runTestFile(file, suite, environment, options, testData)
                .then(result => {
                  this.results.push(result);
                  this.emit('test:complete', result);
                  if (options.bail && result.failed > 0) throw new Error('Bail');
                });
              running.push(promise);
            }

            if (running.length > 0) {
              // Wait for one to finish
              // We need to know WHICH one finished to remove it.
              // A simpler trick: Promise.race returns the value.
              // But we need to remove the promise from the list.
              // Let's wrap the promise to return itself or index.

              // Actually, simpler implementation without external libs:
              // Just await Promise.all if we want simple batching, but we want a rolling window.
              // Rolling window implementation:
              await Promise.race(running.map(p => p.then(() => p).catch(() => p)));

              // Remove resolved promises
              for (let i = running.length - 1; i >= 0; i--) {
                if (await this.isPromiseResolved(running[i])) {
                  running.splice(i, 1);
                }
              }
            }
          }
        } else {
          // Run tests in the suite sequentially
          for (const file of suite.files) {
            if (options.filter && !file.includes(options.filter)) {
              continue;
            }

            const result = await this.runTestFile(
              file,
              suite,
              environment,
              options,
              testData
            );

            this.results.push(result);
            this.emit('test:complete', result);

            // Check for bail condition
            if (options.bail && result.failed > 0) {
              break;
            }
          }
        }
      }

      this.emit('suite:complete', suite);
    } catch (error) {
      this.emit('suite:error', { suite, error });
      throw error;
    } finally {
      // Only cleanup real environments, not mock ones for unit tests
      if (suite.type !== 'unit') {
        await this.orchestrator.stopEnvironment(envId);
      }
      this.environments.delete(suite.name);
    }
  }

  /**
   * Run shared test suites
   */
  private async runSharedSuites(suites: TestSuite[], options: TestRunOptions): Promise<void> {
    const envId = `shared-${Date.now()}`;

    try {
      // Generate test data for shared environment
      const testData = await this.testDataManager.createScenario('basic');
      const env = { TEST_DATA: JSON.stringify(testData) };

      // Create shared environment
      const environment = await this.orchestrator.createEnvironment(envId, env);
      await this.orchestrator.startEnvironment(envId);

      this.emit('environment:ready', environment);

      // Run all shared suites
      for (const suite of suites) {
        this.emit('suite:start', suite);

        const suiteResults = await this.runSuiteInEnvironment(
          suite,
          environment,
          options,
          testData
        );

        this.results.push(...suiteResults);
        this.emit('suite:complete', suite);

        // Check for bail condition
        if (options.bail && suiteResults.some(r => r.failed > 0)) {
          break;
        }
      }
    } finally {
      // Cleanup shared environment
      await this.orchestrator.stopEnvironment(envId);
    }
  }

  /**
   * Run a test suite in an environment
   */
  private async runSuiteInEnvironment(
    suite: TestSuite,
    environment: TestEnvironment,
    options: TestRunOptions,
    testData?: any
  ): Promise<TestResult[]> {
    const results: TestResult[] = [];
    const parallel = suite.parallel !== false && options.parallel !== false;

    if (parallel) {
      // Run test files in parallel
      const promises = suite.files
        .filter(file => !options.filter || file.includes(options.filter))
        .map(file => this.runTestFile(file, suite, environment, options, testData));

      const fileResults = await Promise.all(promises);
      results.push(...fileResults);
    } else {
      // Run test files sequentially
      for (const file of suite.files) {
        if (options.filter && !file.includes(options.filter)) {
          continue;
        }

        const result = await this.runTestFile(file, suite, environment, options, testData);
        results.push(result);

        // Check for bail condition
        if (options.bail && result.failed > 0) {
          break;
        }
      }
    }

    return results;
  }

  /**
   * Run a single test file
   */
  private async runTestFile(
    file: string,
    suite: TestSuite,
    environment: TestEnvironment,
    options: TestRunOptions,
    testData?: any
  ): Promise<TestResult> {
    const startTime = Date.now();
    this.emit('file:start', { file, suite: suite.name });

    let result: TestResult;

    try {
      // Generate test data for this file if not provided
      const data = testData || await this.testDataManager.createScenario('basic');

      // Run the appropriate test command based on suite type
      const testResult = await this.executeTestCommand(
        file,
        suite,
        environment,
        data,
        options
      );

      result = {
        suite: suite.name,
        file,
        tests: testResult.tests || 0,
        passed: testResult.passed || 0,
        failed: testResult.failed || 0,
        skipped: testResult.skipped || 0,
        duration: Date.now() - startTime,
        failures: testResult.failures,
      };

      // Add contract violations if any
      if (options.contractValidation) {
        const violations = this.orchestrator.getContractViolations();
        if (violations.length > 0) {
          result.contractViolations = violations;
          result.failed += violations.length;
        }
        this.orchestrator.clearContractViolations();
      }
    } catch (error) {
      result = {
        suite: suite.name,
        file,
        tests: 1,
        passed: 0,
        failed: 1,
        skipped: 0,
        duration: Date.now() - startTime,
        failures: [{
          test: 'Test execution',
          error: (error as Error).message || 'Unknown error',
          stack: (error as Error).stack,
        }],
      };
    }

    // Handle retries if configured
    if (result.failed > 0 && options.retries && options.retries > 0) {
      this.emit('file:retry', { file, attempt: 1 });

      for (let attempt = 1; attempt <= options.retries; attempt++) {
        const retryResult = await this.runTestFile(file, suite, environment, {
          ...options,
          retries: 0, // Don't retry the retry
        });

        if (retryResult.failed === 0) {
          result = retryResult;
          this.emit('file:retry:success', { file, attempt });
          break;
        }

        this.emit('file:retry:failed', { file, attempt });
      }
    }

    this.emit('file:complete', { file, result });
    return result;
  }

  /**
   * Run E2E tests in a single batch
   */
  private async runE2EBatch(
    suite: TestSuite,
    environment: TestEnvironment,
    options: TestRunOptions,
    testData?: any
  ): Promise<void> {
    const files = suite.files.filter(f => !options.filter || f.includes(options.filter));
    if (files.length === 0) return;

    console.log(`[DEBUG] Starting E2E Batch for ${files.length} files`);
    const startTime = Date.now();

    // Generate shared test data if not provided
    const data = testData || await this.testDataManager.createScenario('basic');

    // Construct command
    const { spawn } = await import('child_process');
    const projectRoot = path.resolve(__dirname, '..', '..');

    // Use npx playwright test with all files
    // Force workers=1 to prevent resource exhaustion/crashes
    // Convert absolute paths to relative paths to avoid issues with Playwright's glob matching
    const relativeFiles = files.map(f => path.relative(projectRoot, f).replace(/\\/g, '/'));
    // Explicitly use the root config to avoid ambiguity
    const args = ['playwright', 'test', ...relativeFiles, '--config=playwright.config.ts', '--workers=1', '--reporter=json'];

    console.log(`[DEBUG] Executing command: npx ${args.join(' ')}`);
    console.log(`[DEBUG] CWD: ${projectRoot}`);
    console.log(`[DEBUG] E2E_FRONTEND_URL: ${environment.frontend.url}`);
    console.log(`[DEBUG] E2E_BACKEND_URL: ${environment.backend.url}`);

    const env = {
      ...process.env,
      E2E_FRONTEND_URL: environment.frontend.url,
      E2E_BACKEND_URL: environment.backend.url,
      TEST_DATA: JSON.stringify(data),
      NODE_ENV: 'test',
    };

    return new Promise((resolve, reject) => {
      const child = spawn('npx', args, {
        cwd: projectRoot,
        env,
        shell: true,
        stdio: ['ignore', 'pipe', 'pipe'], // Capture stdout for JSON
      });

      let stdout = '';
      let stderr = '';

      child.stdout?.on('data', (data) => {
        stdout += data.toString();
      });

      child.stderr?.on('data', (data) => {
        stderr += data.toString();
        console.log('[DEBUG] stderr:', data.toString());
        if (options.verbose) process.stderr.write(data);
      });

      child.on('close', (code) => {
        try {
          console.log('[DEBUG] Process closed with code:', code);
          console.log('[DEBUG] stdout length:', stdout.length);

          // Parse JSON output
          // Playwright JSON reporter outputs the JSON at the end
          // But sometimes there's other output before/after
          const jsonStart = stdout.indexOf('{');
          const jsonEnd = stdout.lastIndexOf('}');

          if (jsonStart !== -1 && jsonEnd !== -1) {
            const jsonStr = stdout.substring(jsonStart, jsonEnd + 1);
            const data = JSON.parse(jsonStr);

            // Map results back to files
            // Playwright JSON structure: suites -> specs -> tests -> results

            // Helper to process suites recursively
            const processSuites = (suites: any[]) => {
              for (const s of suites) {
                // If it's a file suite (top level usually has file property)
                if (s.file) {
                  const absolutePath = path.resolve(projectRoot, s.file);

                  // Calculate stats for this file
                  let passed = 0;
                  let failed = 0;
                  let skipped = 0;
                  let duration = 0;
                  const failures: TestFailure[] = [];

                  const processSpecs = (specs: any[]) => {
                    for (const spec of specs) {
                      for (const test of spec.tests) {
                        duration += test.results.reduce((acc: number, r: any) => acc + r.duration, 0);

                        if (test.status === 'expected' || test.status === 'flaky') passed++;
                        else if (test.status === 'skipped') skipped++;
                        else {
                          failed++;
                          // Collect failures
                          for (const result of test.results) {
                            if (result.error) {
                              failures.push({
                                test: spec.title,
                                error: result.error.message,
                                stack: result.error.stack
                              });
                            }
                          }
                        }
                      }
                    }
                  };

                  // Specs might be directly here or nested
                  if (s.specs) processSpecs(s.specs);
                  if (s.suites) {
                    // Recurse but aggregate to this file
                    // Actually Playwright structure is: Root -> File Suite -> Describe Suites -> Specs
                    // We need to flatten everything under the File Suite
                    const flattenSpecs = (node: any) => {
                      if (node.specs) processSpecs(node.specs);
                      if (node.suites) node.suites.forEach(flattenSpecs);
                    };
                    flattenSpecs(s);
                  }

                  const result: TestResult = {
                    suite: suite.name,
                    file: absolutePath,
                    tests: passed + failed + skipped,
                    passed,
                    failed,
                    skipped,
                    duration,
                    failures
                  };

                  this.results.push(result);
                  this.emit('file:complete', { file: absolutePath, result });
                } else if (s.suites) {
                  processSuites(s.suites);
                }
              }
            };

            if (data.suites) {
              console.log(`[DEBUG] Found ${data.suites.length} root suites`);
              if (data.suites.length === 0) {
                console.log('[DEBUG] Full JSON:', JSON.stringify(data, null, 2));
              }
              processSuites(data.suites);
            } else {
              console.log('[DEBUG] No suites found in JSON data');
              console.log('[DEBUG] JSON keys:', Object.keys(data));
            }
          } else {
            console.error('Failed to find JSON in Playwright output');
            console.log('[DEBUG] stdout:', stdout);
          }

          resolve();
        } catch (e) {
          console.error('Error parsing Playwright JSON:', e);
          reject(e);
        }
      });

      child.on('error', reject);
    });
  }



  /**
   * Execute test command based on suite type
   */
  private async executeTestCommand(
    file: string,
    suite: TestSuite,
    environment: TestEnvironment,
    testData: any,
    options: TestRunOptions
  ): Promise<any> {
    // Best practice: Use native Node.js spawn with shell: true
    const { spawn } = await import('child_process');

    return new Promise((resolve, reject) => {
      let command: string;
      let args: string[] = [];
      let cwd: string;
      let env: NodeJS.ProcessEnv = {
        ...process.env,
        BACKEND_URL: environment.backend.url,
        FRONTEND_URL: environment.frontend.url,
        TEST_DATA: JSON.stringify(testData),
        NODE_ENV: 'test',
      };

      const projectRoot = path.resolve(__dirname, '..', '..');

      switch (suite.type) {
        case 'unit':
          if (file.endsWith('.py')) {
            command = 'python';
            args = ['-m', 'pytest', file, '-v', '--tb=short'];
            cwd = path.resolve(projectRoot, 'src', 'backend');
          } else {
            command = 'npm';
            args = ['run', 'test', '--', file];
            cwd = path.resolve(projectRoot, 'src', 'frontend');
          }
          break;

        case 'integration':
        case 'contract':
          command = 'npm';
          args = ['run', 'test', '--', file];
          cwd = path.resolve(projectRoot, 'tests');
          break;

        case 'e2e':
          command = 'npx';
          // Use Playwright directly with JSON reporter for easy parsing
          // --workers=1 to let the parallel runner manage parallelism via processes
          const relativeFile = path.relative(projectRoot, file).replace(/\\/g, '/');
          args = ['playwright', 'test', relativeFile, '--config=playwright.config.ts', '--workers=1', '--reporter=json'];
          cwd = projectRoot;
          env.E2E_FRONTEND_URL = environment.frontend.url;
          env.E2E_BACKEND_URL = environment.backend.url;
          break;

        default:
          reject(new Error(`Unknown suite type: ${suite.type}`));
          return;
      }

      if (options.coverage) {
        if (command === 'npm') {
          args.push('--', '--coverage');
        } else if (command === 'python') {
          args = ['-m', 'pytest', file, '--cov', '--cov-report=json'];
        }
      }

      const child = spawn(command, args, {
        cwd,
        env,
        shell: true,
        stdio: ['ignore', 'pipe', 'pipe'], // Always pipe to capture output
      });

      let stdout = '';
      let stderr = '';

      child.stdout?.on('data', (data) => {
        const str = data.toString();
        stdout += str;
        if (options.verbose) process.stdout.write(str);
      });

      child.stderr?.on('data', (data) => {
        const str = data.toString();
        stderr += str;
        if (options.verbose) process.stderr.write(str);
      });

      child.on('close', (code) => {
        const output = stdout + stderr;
        const result = this.parseTestOutput(output, suite.type);

        if (code === 0) {
          resolve(result);
        } else {
          result.failed = result.failed || 1;
          resolve(result);
        }
      });

      child.on('error', reject);

      // Apply timeout if specified
      if (options.timeout || suite.timeout) {
        setTimeout(() => {
          child.kill('SIGTERM');
          reject(new Error('Test timeout exceeded'));
        }, options.timeout || suite.timeout || 300000);
      }
    });
  }

  /**
   * Parse test output to extract results
   */
  private parseTestOutput(output: string, type: string): any {
    const result = {
      tests: 0,
      passed: 0,
      failed: 0,
      skipped: 0,
      failures: [] as TestFailure[],
    };

    // Parse based on test framework output
    if (type === 'e2e') {
      try {
        // Find JSON object in output (might be surrounded by other text)
        const jsonStart = output.indexOf('{');
        const jsonEnd = output.lastIndexOf('}');
        if (jsonStart !== -1 && jsonEnd !== -1) {
          const jsonStr = output.substring(jsonStart, jsonEnd + 1);
          const data = JSON.parse(jsonStr);

          if (data.stats) {
            result.tests = data.stats.expected + data.stats.unexpected + data.stats.skipped + data.stats.flaky;
            result.passed = data.stats.expected + data.stats.flaky;
            result.failed = data.stats.unexpected;
            result.skipped = data.stats.skipped;

            // Extract failures from suites
            const extractFailures = (suite: any) => {
              if (suite.specs) {
                for (const spec of suite.specs) {
                  if (spec.tests) {
                    for (const test of spec.tests) {
                      if (test.status === 'unexpected' || test.status === 'flaky') {
                        for (const testRes of test.results) {
                          if (testRes.error) {
                            result.failures.push({
                              test: spec.title,
                              error: testRes.error.message,
                              stack: testRes.error.stack
                            });
                          }
                        }
                      }
                    }
                  }
                }
              }
              if (suite.suites) {
                suite.suites.forEach(extractFailures);
              }
            };

            if (data.suites) {
              data.suites.forEach(extractFailures);
            }
            return result; // Return early if successful
          }
        }
      } catch (e) {
        // Fallback to standard parsing if JSON fails
        if (process.env.DEBUG_RUNNER) {
          console.log('JSON Parse Failed:', e);
          console.log('Output:', output);
        }
      }
    }

    if (type === 'unit' && output.includes('pytest')) {
      // Parse pytest output
      const summaryMatch = output.match(/(\d+) passed.*?(\d+) failed.*?(\d+) skipped/);
      if (summaryMatch) {
        result.passed = parseInt(summaryMatch[1]);
        result.failed = parseInt(summaryMatch[2]);
        result.skipped = parseInt(summaryMatch[3]);
        result.tests = result.passed + result.failed + result.skipped;
      }
    } else if (output.includes('Test Suites:')) {
      // Parse Jest output
      const testMatch = output.match(/Tests:\s+(\d+) failed.*?(\d+) passed.*?(\d+) total/);
      if (testMatch) {
        result.failed = parseInt(testMatch[1]);
        result.passed = parseInt(testMatch[2]);
        result.tests = parseInt(testMatch[3]);
      }
    }

    // Extract failure details (simplified)
    const failureMatches = output.matchAll(/FAIL.*?\n(.*?)\n/g);
    for (const match of failureMatches) {
      result.failures.push({
        test: match[1] || 'Unknown test',
        error: 'Test failed',
      });
    }

    return result;
  }

  /**
   * Check if a promise is resolved
   */
  private async isPromiseResolved(promise: Promise<any>): Promise<boolean> {
    const pending = Symbol('pending');
    const result = await Promise.race([promise, Promise.resolve(pending)]);
    return result !== pending;
  }

  /**
   * Generate test summary
   */
  private generateSummary(duration: number): TestSummary {
    let total = 0;
    let passed = 0;
    let failed = 0;
    let skipped = 0;
    const suites = new Set<string>();
    const failedSuites = new Set<string>();

    for (const result of this.results) {
      total += result.tests;
      passed += result.passed;
      failed += result.failed;
      skipped += result.skipped;
      suites.add(result.suite);

      if (result.failed > 0) {
        failedSuites.add(result.suite);
      }
    }

    return {
      total,
      passed,
      failed,
      skipped,
      duration,
      suites: suites.size,
      failedSuites: failedSuites.size,
      passRate: total > 0 ? (passed / total) * 100 : 0,
    };
  }

  /**
   * Generate detailed HTML report
   */
  async generateHTMLReport(outputPath: string): Promise<void> {
    const summary = this.generateSummary(0);
    const html = `
<!DOCTYPE html>
<html>
<head>
  <title>Test Report</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 20px; }
    .summary { background: #f0f0f0; padding: 15px; border-radius: 5px; }
    .passed { color: green; }
    .failed { color: red; }
    .skipped { color: orange; }
    .suite { margin: 20px 0; border: 1px solid #ddd; padding: 15px; }
    .failure { background: #fee; padding: 10px; margin: 10px 0; }
    table { width: 100%; border-collapse: collapse; }
    th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
  </style>
</head>
<body>
  <h1>Test Report</h1>
  <div class="summary">
    <h2>Summary</h2>
    <p>Total Tests: ${summary.total}</p>
    <p class="passed">Passed: ${summary.passed}</p>
    <p class="failed">Failed: ${summary.failed}</p>
    <p class="skipped">Skipped: ${summary.skipped}</p>
    <p>Pass Rate: ${summary.passRate.toFixed(2)}%</p>
    <p>Duration: ${(summary.duration / 1000).toFixed(2)}s</p>
  </div>

  <h2>Results</h2>
  <table>
    <thead>
      <tr>
        <th>Suite</th>
        <th>File</th>
        <th>Tests</th>
        <th>Passed</th>
        <th>Failed</th>
        <th>Duration</th>
      </tr>
    </thead>
    <tbody>
      ${this.results.map(r => `
        <tr>
          <td>${r.suite}</td>
          <td>${path.basename(r.file)}</td>
          <td>${r.tests}</td>
          <td class="passed">${r.passed}</td>
          <td class="failed">${r.failed}</td>
          <td>${(r.duration / 1000).toFixed(2)}s</td>
        </tr>
      `).join('')}
    </tbody>
  </table>

  ${this.results.filter(r => r.failures && r.failures.length > 0).map(r => `
    <div class="suite">
      <h3>${r.suite} - ${path.basename(r.file)}</h3>
      ${r.failures!.map(f => `
        <div class="failure">
          <strong>${f.test}</strong>
          <pre>${f.error}</pre>
        </div>
      `).join('')}
    </div>
  `).join('')}
</body>
</html>`;

    await fs.writeFile(outputPath, html);
    this.emit('report:generated', outputPath);
  }

  /**
   * Cleanup resources
   */
  async cleanup(): Promise<void> {
    // Stop all workers
    for (const worker of this.workers.values()) {
      await worker.terminate();
    }
    this.workers.clear();

    // Cleanup environments
    await this.orchestrator.cleanup();

    // Clear test data
    this.testDataManager.clearAll();
  }
}

interface TestSummary {
  total: number;
  passed: number;
  failed: number;
  skipped: number;
  duration: number;
  suites: number;
  failedSuites: number;
  passRate: number;
}

// Export singleton instance
export const parallelTestRunner = new ParallelTestRunner();

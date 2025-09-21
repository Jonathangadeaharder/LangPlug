import { spawn, spawnSync } from 'child_process';
import { promisify } from 'util';
import { setTimeout } from 'timers';
import path from 'path';

const wait = promisify(setTimeout);

export class TestRunner {
  /**
   * Run backend tests
   */
  async runBackendTests(): Promise<boolean> {
    console.log('Running backend tests...');
    
    return new Promise((resolve) => {
      const backendTestProcess = spawn('python', ['-m', 'pytest', '--tb=short'], {
        cwd: path.resolve(__dirname, '../../Backend'),
        stdio: 'inherit',
        shell: true
      });

      backendTestProcess.on('close', (code) => {
        if (code === 0) {
          console.log('Backend tests passed');
          resolve(true);
        } else {
          console.error(`Backend tests failed with exit code ${code}`);
          resolve(false);
        }
      });

      backendTestProcess.on('error', (error) => {
        console.error('Failed to run backend tests:', error);
        resolve(false);
      });
    });
  }

  /**
   * Run frontend unit tests
   */
  async runFrontendUnitTests(): Promise<boolean> {
    console.log('Running frontend unit tests...');
    
    return new Promise((resolve) => {
      const frontendTestProcess = spawn('npm', ['run', 'test'], {
        cwd: path.resolve(__dirname, '../../Frontend'),
        stdio: 'inherit',
        shell: true
      });

      frontendTestProcess.on('close', (code) => {
        if (code === 0) {
          console.log('Frontend unit tests passed');
          resolve(true);
        } else {
          console.error(`Frontend unit tests failed with exit code ${code}`);
          resolve(false);
        }
      });

      frontendTestProcess.on('error', (error) => {
        console.error('Failed to run frontend unit tests:', error);
        resolve(false);
      });
    });
  }

  /**
   * Run E2E tests
   */
  async runE2ETests(): Promise<boolean> {
    console.log('Running E2E tests...');
    
    return new Promise((resolve) => {
      const e2eTestProcess = spawn('npm', ['run', 'test:e2e'], {
        cwd: path.resolve(__dirname, '../e2e'),
        stdio: 'inherit',
        shell: true
      });

      e2eTestProcess.on('close', (code) => {
        if (code === 0) {
          console.log('E2E tests passed');
          resolve(true);
        } else {
          console.error(`E2E tests failed with exit code ${code}`);
          resolve(false);
        }
      });

      e2eTestProcess.on('error', (error) => {
        console.error('Failed to run E2E tests:', error);
        resolve(false);
      });
    });
  }

  /**
   * Run a single command and return the result
   */
  runCommand(command: string, args: string[], cwd?: string): Promise<{ code: number; stdout: string; stderr: string }> {
    return new Promise((resolve) => {
      const childProcess = spawn(command, args, {
        cwd: cwd || process.cwd(),
        stdio: 'pipe',
        shell: true
      });

      let stdout = '';
      let stderr = '';

      childProcess.stdout?.on('data', (data: Buffer) => {
        stdout += data.toString();
      });

      childProcess.stderr?.on('data', (data: Buffer) => {
        stderr += data.toString();
      });

      childProcess.on('close', (code: number | null) => {
        resolve({ code: code || 0, stdout, stderr });
      });
    });
  }
}
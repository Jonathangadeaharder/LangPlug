/**
 * Authentication E2E Tests
 * Tests complete authentication flows using the new robust infrastructure
 */

import puppeteer, { Browser, Page } from 'puppeteer';
import { TestDataManager } from '../infrastructure/test-data-manager';
import { ContractValidator } from '../infrastructure/contract-validator';
import axios from 'axios';
import { getFrontendUrl, getBackendUrl } from './config/test-config';

describe('Authentication Flow', () => {
  let browser: Browser | undefined;
  let page: Page;
  let testDataManager: TestDataManager;
  let contractValidator: ContractValidator;
  let apiClient: any;
  
  let FRONTEND_URL = process.env.E2E_FRONTEND_URL || process.env.FRONTEND_URL || 'http://localhost:3000';
  let BACKEND_URL = process.env.E2E_BACKEND_URL || process.env.BACKEND_URL || 'http://localhost:8000';
  
  beforeAll(async () => {
    // Initialize test infrastructure
    testDataManager = new TestDataManager();
    contractValidator = new ContractValidator(false); // Non-strict mode for E2E
    
    // Setup API client for backend interactions
    apiClient = axios.create({
      baseURL: BACKEND_URL,
      timeout: 10000,
    });
    
    // Launch Puppeteer browser
    browser = await puppeteer.launch({
      headless: process.env.HEADLESS !== 'false',
      slowMo: process.env.SLOW_MO ? parseInt(process.env.SLOW_MO) : 0,
      args: ['--no-sandbox', '--disable-setuid-sandbox'],
    });
    
    // Detect actual running URLs (handles 127.0.0.1 vs localhost)
    try {
      FRONTEND_URL = await getFrontendUrl();
      BACKEND_URL = await getBackendUrl();
    } catch {
      // fall back to env/defaults if detection fails
    }

    // Wait for servers to be ready
    await waitForServers();
  }, 60000);

  beforeEach(async () => {
    if (!browser) throw new Error('Browser not initialized');
    page = await browser.newPage();
    
    // Set viewport for consistent testing
    await page.setViewport({ width: 1280, height: 720 });
    
    // Clear browser state
    await page.evaluateOnNewDocument(() => {
      localStorage.clear();
      sessionStorage.clear();
    });
    
    // Clear cookies
    const cookies = await page.cookies();
    if (cookies.length > 0) {
      await page.deleteCookie(...cookies);
    }
  });

  afterEach(async () => {
    if (page) {
      await page.close();
    }
  });

  afterAll(async () => {
    // Close browser if it was created
    if (browser) {
      await browser.close();
    }
  });

  test('should display login form and allow navigation to register', async () => {
    await page.goto(`${FRONTEND_URL}/login`, { waitUntil: 'networkidle2' });

    // Verify login form elements are present
    const formElements = await page.evaluate(() => {
      const usernameInput = document.querySelector('input[type="text"], input[type="email"], input[placeholder*="user" i], input[placeholder*="email" i]');
      const passwordInput = document.querySelector('input[type="password"], input[placeholder*="pass" i]');
      const submitButton = Array.from(document.querySelectorAll('button')).find(btn => 
        btn.textContent?.toLowerCase().includes('sign in') || 
        btn.textContent?.toLowerCase().includes('login')
      );
      const registerLink = Array.from(document.querySelectorAll('a')).find(link => 
        link.textContent?.toLowerCase().includes('sign up') || 
        link.textContent?.toLowerCase().includes('register')
      );
      
      return {
        hasUsernameInput: !!usernameInput,
        hasPasswordInput: !!passwordInput,
        hasSubmitButton: !!submitButton,
        hasRegisterLink: !!registerLink,
        registerHref: registerLink?.getAttribute('href'),
      };
    });

    expect(formElements.hasUsernameInput).toBe(true);
    expect(formElements.hasPasswordInput).toBe(true);
    expect(formElements.hasSubmitButton).toBe(true);
    expect(formElements.hasRegisterLink).toBe(true);

    // Navigate to register page
    if (formElements.registerHref) {
      await Promise.all([
        page.waitForNavigation({ waitUntil: 'networkidle2' }),
        page.click('a[href*="register"]'),
      ]);
      expect(page.url()).toMatch(/\/register/);
    }
  }, 30000);

  test('should handle invalid login credentials', async () => {
    await page.goto(`${FRONTEND_URL}/login`, { waitUntil: 'networkidle2' });

    // Generate invalid credentials
    const invalidUser = testDataManager.generateUser();
    
    // Fill in login form with invalid credentials
    const usernameSelector = 'input[type="text"], input[type="email"], input[placeholder*="user" i], input[placeholder*="email" i]';
    const passwordSelector = 'input[type="password"], input[placeholder*="pass" i]';
    
    await page.waitForSelector(usernameSelector);
    await page.type(usernameSelector, invalidUser.email);
    
    await page.waitForSelector(passwordSelector);
    await page.type(passwordSelector, 'WrongPassword123!');
    
    // Submit form
    await Promise.all([
      page.waitForResponse(response => 
        response.url().includes('/auth/login') && 
        response.status() === 400,
        { timeout: 10000 }
      ).catch(() => null), // Don't fail if no API call is made
      page.click('button[type="submit"], button:has-text("Sign In"), button:has-text("Login")')
    ]);

    // Wait for error message or form validation
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Check for error indication
    const hasError = await page.evaluate(() => {
      // Look for common error indicators
      const errorElements = document.querySelectorAll('.error, .alert, [class*="error"], [class*="alert"], [role="alert"]');
      const errorText = Array.from(errorElements).some(el => 
        el.textContent?.toLowerCase().includes('invalid') ||
        el.textContent?.toLowerCase().includes('incorrect') ||
        el.textContent?.toLowerCase().includes('failed')
      );
      return errorElements.length > 0 || errorText;
    });

    // Should stay on login page
    expect(page.url()).toContain('/login');
  }, 30000);

  test('should redirect to login when accessing protected routes', async () => {
    // Try to access a protected route without authentication
    await page.goto(`${FRONTEND_URL}/videos`, { waitUntil: 'networkidle2' });

    // Should redirect to login page
    await page.waitForFunction(
      () => window.location.pathname.includes('/login'),
      { timeout: 5000 }
    );
    
    expect(page.url()).toContain('/login');
  }, 30000);
  
  test('should complete full registration and login flow', async () => {
    // Generate unique test user
    const testUser = testDataManager.generateUser();
    
    // Navigate to registration page
    await page.goto(`${FRONTEND_URL}/register`, { waitUntil: 'networkidle2' });
    
    // Fill registration form
    const emailSelector = 'input[type="email"], input[name="email"], input[placeholder*="email" i]';
    const usernameSelector = 'input[type="text"][name="username"], input[placeholder*="username" i]:not([type="email"])';
    const passwordSelector = 'input[type="password"]:nth-of-type(1), input[name="password"]';
    const confirmPasswordSelector = 'input[type="password"]:nth-of-type(2), input[name="confirmPassword"], input[placeholder*="confirm" i]';
    
    await page.waitForSelector(emailSelector);
    await page.type(emailSelector, testUser.email);
    
    // Username might be same as email or separate field
    const hasUsernameField = await page.$(usernameSelector);
    if (hasUsernameField) {
      await page.type(usernameSelector, testUser.username);
    }
    
    await page.waitForSelector(passwordSelector);
    await page.type(passwordSelector, testUser.password);
    
    // Confirm password if field exists
    const hasConfirmField = await page.$(confirmPasswordSelector);
    if (hasConfirmField) {
      await page.type(confirmPasswordSelector, testUser.password);
    }
    
    // Submit registration
    await Promise.all([
      page.waitForNavigation({ waitUntil: 'networkidle2' }),
      page.click('button[type="submit"], button:has-text("Register"), button:has-text("Sign Up")')
    ]);
    
    // Should redirect to login or dashboard
    expect(page.url()).toMatch(/\/(login|dashboard|home)/);
    
    // If redirected to login, perform login
    if (page.url().includes('/login')) {
      const loginUsernameSelector = 'input[type="text"], input[type="email"], input[placeholder*="user" i], input[placeholder*="email" i]';
      const loginPasswordSelector = 'input[type="password"], input[placeholder*="pass" i]';
      
      await page.waitForSelector(loginUsernameSelector);
      await page.type(loginUsernameSelector, testUser.email);
      
      await page.waitForSelector(loginPasswordSelector);
      await page.type(loginPasswordSelector, testUser.password);
      
      await Promise.all([
        page.waitForNavigation({ waitUntil: 'networkidle2' }),
        page.click('button[type="submit"], button:has-text("Sign In"), button:has-text("Login")')
      ]);
    }
    
    // Should be logged in and redirected to dashboard/home
    expect(page.url()).not.toContain('/login');
    expect(page.url()).not.toContain('/register');
    
    // Verify authentication token is stored
    const hasAuthToken = await page.evaluate(() => {
      const token = localStorage.getItem('token') || 
                   localStorage.getItem('access_token') || 
                   sessionStorage.getItem('token') || 
                   sessionStorage.getItem('access_token');
      return !!token;
    });
    
    expect(hasAuthToken).toBe(true);
  }, 60000);
  
  /**
   * Helper function to wait for servers
   */
  async function waitForServers(): Promise<void> {
    const maxRetries = 60;
    const retryDelay = 2000;
    
    // Wait for backend
    for (let i = 0; i < maxRetries; i++) {
      try {
        const response = await axios.get(`${BACKEND_URL}/health`, { proxy: false, timeout: 1500, validateStatus: () => true });
        if (response.status === 200) break;
      } catch (error) {
        if (i === maxRetries - 1) {
          throw new Error(`Backend not ready after ${maxRetries} attempts`);
        }
        await new Promise(resolve => setTimeout(resolve, retryDelay));
      }
    }
    
    // Wait for frontend
    for (let i = 0; i < maxRetries; i++) {
      try {
        const testPage = await browser!.newPage();
        await testPage.goto(FRONTEND_URL, { waitUntil: 'domcontentloaded', timeout: 5000 });
        await testPage.close();
        break;
      } catch (error) {
        if (i === maxRetries - 1) {
          throw new Error(`Frontend not ready after ${maxRetries} attempts`);
        }
        await new Promise(resolve => setTimeout(resolve, retryDelay));
      }
    }
  }
});
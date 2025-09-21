import puppeteer, { Browser, Page } from 'puppeteer';
import { E2E_CONFIG, getFrontendUrl } from './config/test-config';

describe('Simple UI Navigation Tests', () => {
  let browser: Browser;
  let page: Page;
  let BASE_URL: string;

  beforeAll(async () => {
    // Detect the actual frontend URL dynamically
    BASE_URL = await getFrontendUrl();
    console.log(`🌐 Using frontend URL: ${BASE_URL}`);
    
    browser = await puppeteer.launch(E2E_CONFIG.BROWSER_OPTIONS);
  });

  beforeEach(async () => {
    page = await browser.newPage();
    await page.setViewport(E2E_CONFIG.VIEWPORT);
  });

  afterEach(async () => {
    // Clean up any storage without throwing errors
    try {
      await page.evaluate(() => {
        localStorage.clear();
        sessionStorage.clear();
      });
    } catch (error) {
      // Ignore storage errors in headless mode
    }
    
    if (page) {
      await page.close();
    }
  });

  afterAll(async () => {
    if (browser) {
      await browser.close();
    }
  });

  it('should load the login page successfully', async () => {
    await page.goto(`${BASE_URL}/login`);
    
    // Wait for the login form to be visible
    await page.waitForSelector('input', { 
      visible: true, 
      timeout: 10000 
    });
    
    // Check that login button is present - just look for any button
    await page.waitForSelector('button', { 
      visible: true, 
      timeout: 5000 
    });
    
    // Verify the button text is correct
    const buttonText = await page.$eval('button', btn => btn.textContent?.trim());
    expect(buttonText).toBe('Sign In');
    
    expect(page.url()).toContain('/login');
  }, 30000);

  it('should navigate to register page', async () => {
    await page.goto(`${BASE_URL}/login`);
    
    // Wait for links to load
    await page.waitForSelector('a', { 
      visible: true, 
      timeout: 10000 
    });
    
    // Find and click the "Sign up now" link using evaluate
    const linkClicked = await page.evaluate(() => {
      const links = Array.from(document.querySelectorAll('a'));
      const signupLink = links.find(link => 
        link.textContent?.toLowerCase().includes('sign up')
      );
      if (signupLink) {
        signupLink.click();
        return true;
      }
      return false;
    });
    
    if (linkClicked) {
      // Wait for navigation
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Check if URL changed or contains register/signup
      const currentUrl = page.url();
      const hasNavigated = currentUrl.includes('/register') || 
                          currentUrl.includes('/signup') ||
                          !currentUrl.endsWith('/login');
      expect(hasNavigated).toBe(true);
    } else {
      // If no signup link found, just verify the link exists
      const linkTexts = await page.$$eval('a', links => 
        links.map(link => link.textContent?.trim())
      );
      expect(linkTexts).toContain('Sign up now');
    }
  }, 30000);

  it('should load the home/videos page', async () => {
    await page.goto(`${BASE_URL}/`);
    
    // Page should load successfully
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Should either be on home page, videos page, or redirected to login
    const url = page.url();
    expect(url).toMatch(/\/(videos|home|login)?$/);
  }, 30000);

  it('should handle 404 pages gracefully', async () => {
    await page.goto(`${BASE_URL}/nonexistent-page`);
    
    // Should either show 404 page or redirect
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Page should load some content (not hang)
    const content = await page.$eval('body', el => el.textContent || '');
    expect(content).toBeTruthy();
    expect(content.length).toBeGreaterThan(0);
  }, 30000);

  it('should load vocabulary page structure', async () => {
    await page.goto(`${BASE_URL}/vocabulary`);
    
    // Page should load
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Should either show vocabulary content or redirect to login
    const url = page.url();
    expect(url).toMatch(/\/(vocabulary|login)/);
  }, 30000);
});
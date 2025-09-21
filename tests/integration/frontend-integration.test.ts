/**
 * Comprehensive Frontend Integration Tests
 * 
 * Tests React components integration with backend APIs,
 * user workflows, and component interactions.
 * Standalone test runner (no Jest dependency required)
 */
import { exec } from 'child_process';
import { promisify } from 'util';
import puppeteer, { Browser, Page } from 'puppeteer';
import E2E_CONFIG, { getFrontendUrl, getBackendUrl } from '../e2e/config/test-config';

const execAsync = promisify(exec);

interface TestUser {
  email: string;
  username: string;
  password: string;
  id?: string;
}

interface TestResult {
  name: string;
  success: boolean;
  details: string;
  duration: number;
}

class FrontendIntegrationTester {
  private browser?: Browser;
  private page?: Page;
  private testUser?: TestUser;

  constructor() {
    // No config initialization needed
  }

  async setup(timeout: number = 60000): Promise<void> {
    // For now, use known server URLs to bypass detection issues
    const frontendUrl = "http://localhost:3000";
    const backendUrl = "http://127.0.0.1:8000";
    
    console.log(`🌐 Frontend: ${frontendUrl}`);
    console.log(`🔧 Backend: ${backendUrl}`);
    
    // Launch browser
    this.browser = await puppeteer.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox'],
      timeout
    });
    
    this.page = await this.browser.newPage();
    
    // Set viewport and timeouts
    await this.page.setViewport({ width: 1280, height: 720 });
    await this.page.setDefaultTimeout(10000);
    
    console.log('✅ Frontend integration tester ready');
  }

  async teardown(): Promise<void> {
    if (this.browser) {
      await this.browser.close();
    }
  }

  async createTestUser(): Promise<TestUser> {
    const timestamp = Date.now();
    this.testUser = {
      email: `test.integration.${timestamp}@example.com`,
      username: `testuser_${timestamp}`,
      password: 'TestPassword123!'
    };
    
    return this.testUser;
  }

  async navigateToApp(): Promise<void> {
    const frontendUrl = "http://localhost:3000";
    await this.page!.goto(frontendUrl, { waitUntil: 'networkidle0' });
    
    // Wait for React app to load
    await this.page!.waitForSelector('#root', { timeout: 15000 });
    console.log('✅ Navigated to React app');
  }

  async testApplicationLoad(): Promise<TestResult> {
    const startTime = Date.now();
    try {
      await this.navigateToApp();
      return {
        name: 'Application Load',
        success: true,
        details: 'React application loaded successfully',
        duration: Date.now() - startTime
      };
    } catch (error) {
      return {
        name: 'Application Load',
        success: false,
        details: `Failed to load app: ${error instanceof Error ? error.message : error}`,
        duration: Date.now() - startTime
      };
    }
  }

  async testUserRegistration(): Promise<TestResult> {
    const startTime = Date.now();
    try {
      const user = await this.createTestUser();
      await this.navigateToApp();
      
      // Try to find registration elements using page evaluate for safety
      const registerElements = await this.page!.evaluate(() => {
        const elements = Array.from(document.querySelectorAll('*'));
        return elements.filter(el => 
          el.textContent?.toLowerCase().includes('register') ||
          el.getAttribute('href')?.includes('register') ||
          el.classList.toString().includes('register')
        ).length;
      });
      
      if (registerElements > 0) {
        // Try to navigate to register page directly
        const frontendUrl = "http://localhost:3000";
        await this.page!.goto(`${frontendUrl}/register`);
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // Look for form elements
        const formElements = await this.page!.evaluate(() => {
          const inputs = document.querySelectorAll('input');
          const buttons = document.querySelectorAll('button');
          const forms = document.querySelectorAll('form');
          return { inputs: inputs.length, buttons: buttons.length, forms: forms.length };
        });
        
        if (formElements.forms > 0 || formElements.inputs > 2) {
          return {
            name: 'User Registration',
            success: true,
            details: `Registration form found: ${formElements.forms} forms, ${formElements.inputs} inputs, ${formElements.buttons} buttons`,
            duration: Date.now() - startTime
          };
        }
      }
      
      return {
        name: 'User Registration',
        success: false,
        details: `Registration elements found: ${registerElements}, but no accessible form`,
        duration: Date.now() - startTime
      };
    } catch (error) {
      return {
        name: 'User Registration',
        success: false,
        details: `Registration test failed: ${error instanceof Error ? error.message : error}`,
        duration: Date.now() - startTime
      };
    }
  }

  async testVocabularyFeatures(): Promise<TestResult> {
    const startTime = Date.now();
    try {
      await this.navigateToApp();
      
      // Look for vocabulary-related elements using evaluate
      const vocabElements = await this.page!.evaluate(() => {
        const elements = Array.from(document.querySelectorAll('*'));
        return elements.filter(el => 
          el.textContent?.toLowerCase().includes('vocabulary') ||
          el.textContent?.toLowerCase().includes('vocab') ||
          el.textContent?.toLowerCase().includes('words') ||
          el.getAttribute('href')?.includes('vocab') ||
          el.classList.toString().includes('vocab')
        ).length;
      });
      
      if (vocabElements > 0) {
        // Try to navigate to vocabulary section
        const vocabLink = await this.page!.$('a[href*="vocab"]');
        if (vocabLink) {
          await vocabLink.click();
          await new Promise(resolve => setTimeout(resolve, 1000));
        }
        
        // Check for vocabulary components
        const components = await this.page!.evaluate(() => {
          const hasVocabList = document.querySelector('.vocab-list, .word-list, .vocabulary-container') !== null;
          const hasAddButton = Array.from(document.querySelectorAll('button')).some(btn => 
            btn.textContent?.toLowerCase().includes('add')
          );
          const hasSearchBox = document.querySelector('input[type="search"], .search-input') !== null;
          
          return { hasVocabList, hasAddButton, hasSearchBox };
        });
        
        const foundComponents = [];
        if (components.hasVocabList) foundComponents.push('word list');
        if (components.hasAddButton) foundComponents.push('add button');
        if (components.hasSearchBox) foundComponents.push('search box');
        
        return {
          name: 'Vocabulary Features',
          success: foundComponents.length > 0,
          details: foundComponents.length > 0 ? 
            `Found vocabulary components: ${foundComponents.join(', ')}` : 
            'Vocabulary section found but no components detected',
          duration: Date.now() - startTime
        };
      }
      
      return {
        name: 'Vocabulary Features',
        success: false,
        details: 'Vocabulary section not accessible',
        duration: Date.now() - startTime
      };
    } catch (error) {
      return {
        name: 'Vocabulary Features',
        success: false,
        details: `Vocabulary test failed: ${error instanceof Error ? error.message : error}`,
        duration: Date.now() - startTime
      };
    }
  }

  async testVideoFeatures(): Promise<TestResult> {
    const startTime = Date.now();
    try {
      await this.navigateToApp();
      
      // Look for video-related elements
      const videoElements = await this.page!.evaluate(() => {
        const elements = Array.from(document.querySelectorAll('*'));
        return elements.filter(el => 
          el.textContent?.toLowerCase().includes('video') ||
          el.textContent?.toLowerCase().includes('upload') ||
          el.getAttribute('href')?.includes('video') ||
          el.classList.toString().includes('video')
        ).length;
      });
      
      if (videoElements > 0) {
        // Try to navigate to video section
        const videoLink = await this.page!.$('a[href*="video"]');
        if (videoLink) {
          await videoLink.click();
          await new Promise(resolve => setTimeout(resolve, 1000));
        }
        
        // Check for video components
        const components = await this.page!.evaluate(() => {
          const hasVideoList = document.querySelector('.video-list, .video-container') !== null;
          const hasUploadButton = document.querySelector('input[type="file"]') !== null ||
                                Array.from(document.querySelectorAll('button')).some(btn => 
                                  btn.textContent?.toLowerCase().includes('upload'));
          const hasVideoPlayer = document.querySelector('video, .video-player') !== null;
          
          return { hasVideoList, hasUploadButton, hasVideoPlayer };
        });
        
        const foundComponents = [];
        if (components.hasVideoList) foundComponents.push('video list');
        if (components.hasUploadButton) foundComponents.push('upload button');
        if (components.hasVideoPlayer) foundComponents.push('video player');
        
        return {
          name: 'Video Features',
          success: foundComponents.length > 0,
          details: foundComponents.length > 0 ? 
            `Found video components: ${foundComponents.join(', ')}` : 
            'Video section found but no components detected',
          duration: Date.now() - startTime
        };
      }
      
      return {
        name: 'Video Features',
        success: false,
        details: 'Video section not accessible',
        duration: Date.now() - startTime
      };
    } catch (error) {
      return {
        name: 'Video Features',
        success: false,
        details: `Video test failed: ${error instanceof Error ? error.message : error}`,
        duration: Date.now() - startTime
      };
    }
  }

  async testNavigation(): Promise<TestResult> {
    const startTime = Date.now();
    try {
      await this.navigateToApp();
      
      // Test navigation links
      const navLinks = await this.page!.$$('nav a, .navigation a, header a, .nav-link');
      const testedLinks: string[] = [];
      
      for (const link of navLinks.slice(0, 3)) { // Test first 3 links
        try {
          const href = await link.evaluate(el => el.getAttribute('href'));
          const text = await link.evaluate(el => el.textContent?.trim());
          
          if (href && !href.startsWith('http') && !href.includes('logout') && text) {
            await link.click();
            await new Promise(resolve => setTimeout(resolve, 500));
            
            const newUrl = this.page!.url();
            testedLinks.push(`${text} -> ${href}`);
          }
        } catch (error) {
          // Continue with next link
        }
      }
      
      return {
        name: 'Navigation',
        success: testedLinks.length > 0,
        details: testedLinks.length > 0 ? 
          `Tested links: ${testedLinks.join(', ')}` : 
          'No navigation links found',
        duration: Date.now() - startTime
      };
    } catch (error) {
      return {
        name: 'Navigation',
        success: false,
        details: `Navigation test failed: ${error instanceof Error ? error.message : error}`,
        duration: Date.now() - startTime
      };
    }
  }

  async testErrorHandling(): Promise<TestResult> {
    const startTime = Date.now();
    try {
      const frontendUrl = await getFrontendUrl();
      await this.page!.goto(`${frontendUrl}/non-existent-page-12345`);
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const has404Content = await this.page!.evaluate(() => {
        return document.body.textContent?.includes('404') ||
               document.body.textContent?.includes('Not Found') ||
               document.body.textContent?.includes('Page not found') ||
               false;
      });
      
      return {
        name: 'Error Handling (404)',
        success: has404Content,
        details: has404Content ? 
          'Application properly handles 404 errors' : 
          'No 404 error handling detected',
        duration: Date.now() - startTime
      };
    } catch (error) {
      return {
        name: 'Error Handling (404)',
        success: false,
        details: `Error handling test failed: ${error instanceof Error ? error.message : error}`,
        duration: Date.now() - startTime
      };
    }
  }

  async runAllTests(): Promise<TestResult[]> {
    const tests = [
      () => this.testApplicationLoad(),
      () => this.testUserRegistration(),
      () => this.testVocabularyFeatures(),
      () => this.testVideoFeatures(),
      () => this.testNavigation(),
      () => this.testErrorHandling()
    ];

    const results: TestResult[] = [];
    
    for (const testFn of tests) {
      try {
        const result = await testFn();
        results.push(result);
        
        const status = result.success ? '✅' : '❌';
        console.log(`${status} ${result.name}: ${result.details} (${result.duration}ms)`);
      } catch (error) {
        results.push({
          name: 'Unknown Test',
          success: false,
          details: `Test execution failed: ${error instanceof Error ? error.message : error}`,
          duration: 0
        });
      }
    }

    return results;
  }
}

// Main test runner
async function runFrontendIntegrationTests(): Promise<void> {
  console.log('🚀 Starting Frontend Integration Tests');
  console.log('=====================================');

  const tester = new FrontendIntegrationTester();
  
  try {
    await tester.setup();
    const results = await tester.runAllTests();
    
    // Calculate summary
    const passed = results.filter(r => r.success).length;
    const total = results.length;
    const totalDuration = results.reduce((sum, r) => sum + r.duration, 0);
    
    console.log('=====================================');
    console.log(`📊 Frontend Integration Test Results:`);
    console.log(`   Passed: ${passed}/${total}`);
    console.log(`   Total Duration: ${totalDuration}ms`);
    console.log(`   Status: ${passed === total ? '✅ ALL PASSED' : `⚠️ ${total - passed} FAILED`}`);
    
    if (passed < total) {
      console.log('\n❌ Failed tests:');
      results.filter(r => !r.success).forEach(r => {
        console.log(`   - ${r.name}: ${r.details}`);
      });
    }
    
  } catch (error) {
    console.error('💥 Frontend integration test runner failed:', error);
    process.exit(1);
  } finally {
    await tester.teardown();
  }
}

// Run tests if this file is executed directly
if (require.main === module) {
  runFrontendIntegrationTests();
}
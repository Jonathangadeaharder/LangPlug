#!/usr/bin/env node

import puppeteer, { Browser, Page } from 'puppeteer';
import { spawn } from 'child_process';
import { promisify } from 'util';
import { setTimeout } from 'timers';
import path from 'path';

const wait = promisify(setTimeout);

async function runE2ETests() {
  let browser: Browser | undefined;
  let page: Page | undefined;
  let allTestsPassed = true;

  try {
    console.log('Starting E2E tests...');
    
    // Launch browser
    browser = await puppeteer.launch({
      headless: true,
      slowMo: 50, // Slow down for better reliability
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    
    // Run authentication tests
    console.log('\n1. Running authentication tests...');
    page = await browser.newPage();
    const authTestPassed = await runAuthTests(page);
    await page.close();
    if (!authTestPassed) allTestsPassed = false;
    
    // Run video learning tests
    console.log('\n2. Running video learning tests...');
    page = await browser.newPage();
    const videoTestPassed = await runVideoLearningTests(page);
    await page.close();
    if (!videoTestPassed) allTestsPassed = false;
    
    // Run vocabulary game tests
    console.log('\n3. Running vocabulary game tests...');
    page = await browser.newPage();
    const vocabTestPassed = await runVocabularyGameTests(page);
    await page.close();
    if (!vocabTestPassed) allTestsPassed = false;
    
    // Run subtitle filtering tests
    console.log('\n4. Running subtitle filtering tests...');
    page = await browser.newPage();
    const subtitleTestPassed = await runSubtitleFilteringTests(page);
    await page.close();
    if (!subtitleTestPassed) allTestsPassed = false;
    
    console.log('\nE2E tests completed');
  } catch (error) {
    console.error('E2E tests failed with error:', error);
    allTestsPassed = false;
  } finally {
    if (browser) {
      await browser.close();
    }
  }
  
  if (allTestsPassed) {
    console.log('All E2E tests passed! ✅');
    process.exit(0);
  } else {
    console.log('Some E2E tests failed! ❌');
    process.exit(1);
  }
}

async function runAuthTests(page: Page): Promise<boolean> {
  console.log(' Testing authentication flow...');
  
  try {
    // Navigate to login page
    await page.goto('http://localhost:3000/login');
    
    // Check if login form is visible
    await page.waitForSelector('input[placeholder="Username"]', { visible: true });
    await page.waitForSelector('input[placeholder="Password"]', { visible: true });
    
    console.log(' ✓ Login form is visible');
    
    // Test navigation to register page
    await page.click('text=Sign up now');
    await page.waitForFunction(() => window.location.href.includes('/register'));
    
    console.log('  ✓ Navigation to register page works');
    
    // Go back to login
    await page.goto('http://localhost:3000/login');
    
    // Test invalid login
    await page.type('input[placeholder="Username"]', 'invaliduser');
    await page.type('input[placeholder="Password"]', 'wrongpassword');
    await page.click('text=Sign In');
    
    // Wait a bit to see if error handling works
    await wait(2000);
    
    // Should still be on login page
    const currentUrl = page.url();
    if (currentUrl.includes('/login')) {
      console.log('  ✓ Invalid login handled correctly');
    } else {
      console.log('  ✗ Invalid login not handled correctly');
      return false;
    }
    
    return true;
  } catch (error) {
    console.error('Auth tests failed:', error);
    return false;
  }
}

async function runVideoLearningTests(page: Page): Promise<boolean> {
  console.log(' Testing video learning flow...');
  
  try {
    // This would require authentication first
    // For now, we'll just test that the page loads
    await page.goto('http://localhost:3000/videos');
    
    // Wait for page to load
    await wait(2000);
    
    console.log('  ✓ Video page loads');
    return true;
  } catch (error) {
    console.error('Video learning tests failed:', error);
    return false;
  }
}

async function runVocabularyGameTests(page: Page): Promise<boolean> {
  console.log('  Testing vocabulary game flow...');
  
  try {
    // Navigate to vocabulary game
    await page.goto('http://localhost:3000/vocabulary/game');
    
    // Wait for page to load
    await wait(2000);
    
    console.log('  ✓ Vocabulary game page loads');
    return true;
  } catch (error) {
    console.error('Vocabulary game tests failed:', error);
    return false;
  }
}

async function runSubtitleFilteringTests(page: Page): Promise<boolean> {
  console.log('  Testing subtitle filtering flow...');
  
  try {
    // Navigate to videos page
    await page.goto('http://localhost:3000/videos');
    
    // Wait for video cards to load
    await page.waitForSelector('[data-testid="video-card"]', { visible: true });
    
    console.log(' ✓ Videos page loads with video cards');
    return true;
  } catch (error) {
    console.error('Subtitle filtering tests failed:', error);
    return false;
  }
}

// Run the E2E tests
runE2ETests();
import puppeteer, { Browser, Page } from 'puppeteer';
import { spawn, ChildProcess } from 'child_process';
import { promisify } from 'util';
import { setTimeout } from 'timers';
import { DatabaseHelpers } from './database-helpers';

const wait = promisify(setTimeout);

export class PuppeteerHelpers {
  static async waitForText(page: Page, text: string, timeout = 5000): Promise<void> {
    await page.waitForFunction(
      (t: string) => document.body.textContent?.includes(t),
      { timeout },
      text
    );
  }

  static async clickByText(page: Page, text: string, selector = 'button, a, span'): Promise<void> {
    await page.waitForFunction(
      (t: string, s: string) => Array.from(document.querySelectorAll(s)).some(el => el.textContent?.includes(t)),
      { timeout: 5000 },
      text, selector
    );
    await page.evaluate((t: string, s: string) => {
      const elements = Array.from(document.querySelectorAll(s));
      const element = elements.find(el => el.textContent?.includes(t));
      if (element && 'click' in element) {
        (element as HTMLElement).click();
      }
    }, text, selector);
  }

  static async fillForm(page: Page, fields: Record<string, string>): Promise<void> {
    for (const [selector, value] of Object.entries(fields)) {
      await page.type(selector, value);
    }
  }

  static async waitForUrl(page: Page, urlPart: string, timeout = 5000): Promise<void> {
    await page.waitForFunction(
      (part: string) => window.location.href.includes(part),
      { timeout },
      urlPart
    );
  }

  static async clearCookies(page: Page): Promise<void> {
    await page.deleteCookie(...(await page.cookies()));
  }

  static async clearLocalStorage(page: Page): Promise<void> {
    try {
      await page.evaluate(() => localStorage.clear());
    } catch (error) {
      console.warn('Could not clear localStorage:', error);
    }
  }

  static async clearSessionStorage(page: Page): Promise<void> {
    try {
      await page.evaluate(() => sessionStorage.clear());
    } catch (error) {
      console.warn('Could not clear sessionStorage:', error);
    }
  }

  static async clearAllStorage(page: Page): Promise<void> {
    await this.clearCookies(page);
    await this.clearLocalStorage(page);
    await this.clearSessionStorage(page);
  }

  static async login(page: Page, email: string, password: string): Promise<void> {
    await page.goto('http://localhost:3001/login');
    await this.fillForm(page, {
      'input[placeholder="Username"]': email,
      'input[placeholder="Password"]': password
    });
    await this.clickByText(page, 'Sign In');
    await page.waitForFunction(() => !window.location.href.includes('/login'));
  }

  static async registerUser(page: Page, userData: { username: string; email: string; password: string }): Promise<void> {
    await page.goto('http://localhost:3001/register');
    await this.fillForm(page, {
      'input[placeholder="Username"]': userData.username,
      'input[placeholder="Email"]': userData.email,
      'input[placeholder="Password"]': userData.password
    });
    await this.clickByText(page, 'Sign Up');
    await page.waitForFunction(() => !window.location.href.includes('/register'));
  }

  static async seedTestData(): Promise<void> {
    await DatabaseHelpers.seedTestData();
  }

  static async cleanTestData(): Promise<void> {
    await DatabaseHelpers.cleanTestData();
  }
}
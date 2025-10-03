import puppeteer, { Browser, Page } from 'puppeteer';
import { spawn } from 'child_process';

export class PuppeteerTestUtils {
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
    await page.evaluate(() => localStorage.clear());
  }

  static async clearSessionStorage(page: Page): Promise<void> {
    await page.evaluate(() => sessionStorage.clear());
  }

  static async clearAllStorage(page: Page): Promise<void> {
    await this.clearCookies(page);
    await this.clearLocalStorage(page);
    await this.clearSessionStorage(page);
  }
}

import { Page, Locator } from '@playwright/test';
import { BasePage } from './BasePage';

/**
 * Page Object for the Profile Screen (/profile)
 */
export class ProfilePage extends BasePage {
  readonly backButton: Locator;
  readonly userAvatar: Locator;
  readonly username: Locator;
  readonly email: Locator;
  
  // Language settings
  readonly nativeLanguageSelector: Locator;
  readonly targetLanguageSelector: Locator;
  readonly languageDropdowns: Locator;
  
  // Chunk duration settings
  readonly chunkDurationInput: Locator;
  readonly chunkDurationSlider: Locator;
  
  // Actions
  readonly saveButton: Locator;
  readonly logoutButton: Locator;
  readonly cancelButton: Locator;

  constructor(page: Page) {
    super(page);
    
    this.backButton = page.getByRole('button', { name: /back/i }).or(
      page.locator('[class*="back"]')
    );
    this.userAvatar = page.locator('[class*="avatar"], [class*="initials"]').first();
    this.username = page.locator('[class*="username"], [class*="name"]').first();
    this.email = page.locator('[class*="email"]').or(
      page.getByText(/@/)
    );
    
    // Language selectors
    this.nativeLanguageSelector = page.locator('[data-testid="native-language"]').or(
      page.getByLabel(/native language/i)
    );
    this.targetLanguageSelector = page.locator('[data-testid="target-language"]').or(
      page.getByLabel(/target language|learning/i)
    );
    this.languageDropdowns = page.locator('select, [role="listbox"], [class*="dropdown"]');
    
    // Chunk duration
    this.chunkDurationInput = page.locator('[data-testid="chunk-duration"]').or(
      page.getByLabel(/chunk|duration|minutes/i)
    );
    this.chunkDurationSlider = page.locator('input[type="range"]');
    
    // Actions
    this.saveButton = page.getByRole('button', { name: /save|update|apply/i });
    this.logoutButton = page.getByRole('button', { name: /log\s?out|sign\s?out/i });
    this.cancelButton = page.getByRole('button', { name: /cancel|discard/i });
  }

  async goto() {
    await this.page.goto('/profile');
    await this.page.waitForLoadState('networkidle');
  }

  async isLoaded(): Promise<boolean> {
    try {
      // Check for greeting heading "Hello username" or language preferences
      const hasGreeting = await this.page.getByRole('heading', { name: /hello/i }).isVisible();
      const hasLanguagePrefs = await this.page.getByRole('heading', { name: /language preferences/i }).isVisible();
      const hasAvatar = await this.userAvatar.isVisible();
      return hasGreeting || hasLanguagePrefs || hasAvatar;
    } catch {
      return false;
    }
  }

  async selectNativeLanguage(language: string) {
    await this.nativeLanguageSelector.click();
    await this.page.getByText(language, { exact: false }).click();
  }

  async selectTargetLanguage(language: string) {
    await this.targetLanguageSelector.click();
    await this.page.getByText(language, { exact: false }).click();
  }

  async setChunkDuration(minutes: number) {
    const slider = this.chunkDurationSlider;
    if (await slider.isVisible()) {
      await slider.fill(String(minutes));
    } else {
      await this.chunkDurationInput.fill(String(minutes));
    }
  }

  async saveChanges() {
    await this.saveButton.click();
  }

  async logout() {
    await this.logoutButton.click();
  }

  async goBack() {
    await this.backButton.click();
  }

  async getDisplayedUsername(): Promise<string> {
    return await this.username.textContent() || '';
  }

  async getDisplayedEmail(): Promise<string> {
    return await this.email.textContent() || '';
  }
}

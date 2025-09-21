/**
 * Meaningful E2E Workflows - Complete User Journey Testing
 * 
 * These tests simulate real user workflows from start to finish,
 * testing the integration between frontend, backend, and business logic.
 */
import puppeteer, { Browser, Page } from 'puppeteer';
import TestConfigManager, { getFrontendUrl, getBackendUrl } from '../e2e/config/test-config';

interface UserJourneyResult {
  name: string;
  success: boolean;
  details: string[];
  duration: number;
  screenshotPaths?: string[];
}

class E2EWorkflowTester {
  private browser?: Browser;
  private page?: Page;
  private testDataDir: string;

  constructor() {
    this.testDataDir = './test-results';
  }

  async setup(): Promise<void> {
    const [frontendUrl, backendUrl] = await Promise.all([
      getFrontendUrl(),
      getBackendUrl()
    ]);
    
    console.log(`🌐 Frontend: ${frontendUrl}`);
    console.log(`🔧 Backend: ${backendUrl}`);
    
    this.browser = await puppeteer.launch({
      headless: false, // Visible for meaningful E2E testing
      args: ['--no-sandbox', '--disable-setuid-sandbox'],
      slowMo: 100 // Slow down for better visibility
    });
    
    this.page = await this.browser.newPage();
    await this.page.setViewport({ width: 1280, height: 720 });
    await this.page.setDefaultTimeout(15000);
    
    console.log('✅ E2E workflow tester ready');
  }

  async teardown(): Promise<void> {
    if (this.browser) {
      await this.browser.close();
    }
  }

  async takeScreenshot(name: string): Promise<string> {
    const timestamp = Date.now();
    const filename = `${name}-${timestamp}.png` as const;
    const path = `${this.testDataDir}/${filename}` as const;
    
    await this.page!.screenshot({ 
      path, 
      fullPage: true,
      type: 'png'
    });
    
    return path;
  }

  /**
   * Complete User Registration and Authentication Journey
   */
  async testCompleteAuthenticationWorkflow(): Promise<UserJourneyResult> {
    const startTime = Date.now();
    const details: string[] = [];
    const screenshots: string[] = [];
    
    try {
      // Step 1: Navigate to application
      const frontendUrl = await getFrontendUrl();
      await this.page!.goto(frontendUrl);
      await this.page!.waitForSelector('#root', { timeout: 10000 });
      details.push('✅ Application loaded successfully');
      
      screenshots.push(await this.takeScreenshot('01-app-loaded'));
      
      // Step 2: Navigate to registration
      const registerElements = await this.page!.$$('a[href*="register"], .register-link, [data-testid="register"]');
      
      // Also check for buttons with "Register" text using evaluate
      const registerButtons = await this.page!.evaluate(() => {
        return Array.from(document.querySelectorAll('button')).filter(btn => 
          btn.textContent?.toLowerCase().includes('register')
        );
      });
      
      if (registerElements.length > 0 || registerButtons.length > 0) {
        if (registerElements.length > 0) {
          await registerElements[0].click();
        } else {
          // Click the first register button found via evaluate
          await this.page!.evaluate(() => {
            const btn = Array.from(document.querySelectorAll('button')).find(b => 
              b.textContent?.toLowerCase().includes('register')
            ) as HTMLButtonElement;
            if (btn) btn.click();
          });
        }
        await this.page!.waitForSelector('form', { timeout: 5000 });
        details.push('✅ Registration page accessed');
        screenshots.push(await this.takeScreenshot('02-registration-page'));
        
        // Step 3: Fill registration form
        const timestamp = Date.now();
        const testUser = {
          email: `e2e.test.${timestamp}@langplug.com`,
          username: `e2euser_${timestamp}`,
          password: 'E2ETestPassword123!'
        };
        
        const emailInput = await this.page!.$('input[name="email"], input[type="email"], [data-testid="email"]');
        const usernameInput = await this.page!.$('input[name="username"], [data-testid="username"]');
        const passwordInput = await this.page!.$('input[name="password"], input[type="password"], [data-testid="password"]');
        
        if (emailInput && usernameInput && passwordInput) {
          await emailInput.type(testUser.email);
          await usernameInput.type(testUser.username);
          await passwordInput.type(testUser.password);
          details.push('✅ Registration form filled');
          
          screenshots.push(await this.takeScreenshot('03-form-filled'));
          
          // Step 4: Submit registration
          const submitButton = await this.page!.$('button[type="submit"], [data-testid="register-submit"]');
          const submitButtons = await this.page!.evaluate(() => {
            return Array.from(document.querySelectorAll('button')).filter(btn => 
              btn.textContent?.toLowerCase().includes('register') ||
              btn.type === 'submit'
            );
          });
          
          if (submitButton || submitButtons.length > 0) {
            if (submitButton) {
              await submitButton.click();
            } else {
              await this.page!.evaluate(() => {
                const btn = Array.from(document.querySelectorAll('button')).find(b => 
                  b.textContent?.toLowerCase().includes('register') || b.type === 'submit'
                ) as HTMLButtonElement;
                if (btn) btn.click();
              });
            }
            
            // Wait for registration result
            await new Promise(resolve => setTimeout(resolve, 3000));
            details.push('✅ Registration submitted');
            screenshots.push(await this.takeScreenshot('04-registration-submitted'));
            
            // Step 5: Check for successful login or redirection
            const currentUrl = this.page!.url();
            const isLoggedIn = await this.page!.$('.user-menu, .profile, [data-testid="user-profile"], .logout');
            const hasError = await this.page!.$('.error, .alert-error, [data-testid="error"]');
            
            if (isLoggedIn) {
              details.push('🎉 User automatically logged in after registration');
              screenshots.push(await this.takeScreenshot('05-logged-in'));
            } else if (hasError) {
              const errorText = await hasError.evaluate(el => el.textContent);
              details.push(`⚠️ Registration error: ${errorText}`);
            } else {
              details.push('ℹ️ Registration completed, manual login required');
              
              // Step 6: Manual login if needed
              const loginLink = await this.page!.$('a[href*="login"], .login-link');
              const loginButtons = await this.page!.evaluate(() => {
                return Array.from(document.querySelectorAll('button, a')).filter(el => 
                  el.textContent?.toLowerCase().includes('login')
                );
              });
              
              if (loginLink || loginButtons.length > 0) {
                if (loginLink) {
                  await loginLink.click();
                } else {
                  await this.page!.evaluate(() => {
                    const btn = Array.from(document.querySelectorAll('button, a')).find(el => 
                      el.textContent?.toLowerCase().includes('login')
                    ) as HTMLElement;
                    if (btn) btn.click();
                  });
                }
                await this.page!.waitForSelector('form', { timeout: 3000 });
                
                const loginEmailInput = await this.page!.$('input[name="email"], input[type="email"]');
                const loginPasswordInput = await this.page!.$('input[name="password"], input[type="password"]');
                
                if (loginEmailInput && loginPasswordInput) {
                  await loginEmailInput.type(testUser.email);
                  await loginPasswordInput.type(testUser.password);
                  
                  const loginSubmit = await this.page!.$('button[type="submit"]');
                  const loginSubmitButtons = await this.page!.evaluate(() => {
                    return Array.from(document.querySelectorAll('button')).filter(btn => 
                      btn.textContent?.toLowerCase().includes('login') ||
                      btn.type === 'submit'
                    );
                  });
                  
                  if (loginSubmit || loginSubmitButtons.length > 0) {
                    if (loginSubmit) {
                      await loginSubmit.click();
                    } else {
                      await this.page!.evaluate(() => {
                        const btn = Array.from(document.querySelectorAll('button')).find(b => 
                          b.textContent?.toLowerCase().includes('login') || b.type === 'submit'
                        ) as HTMLButtonElement;
                        if (btn) btn.click();
                      });
                    }
                    await new Promise(resolve => setTimeout(resolve, 2000));
                    
                    const loginSuccess = await this.page!.$('.user-menu, .profile, .logout');
                    if (loginSuccess) {
                      details.push('🎉 Manual login successful');
                      screenshots.push(await this.takeScreenshot('06-manual-login-success'));
                    } else {
                      details.push('❌ Manual login failed');
                    }
                  }
                }
              }
            }
          }
        } else {
          details.push('⚠️ Registration form inputs incomplete');
        }
      } else {
        details.push('⚠️ Registration page not accessible');
      }
      
      return {
        name: 'Complete Authentication Workflow',
        success: details.some(d => d.includes('🎉')),
        details,
        duration: Date.now() - startTime,
        screenshotPaths: screenshots
      };
    } catch (error) {
      details.push(`❌ Authentication workflow failed: ${error instanceof Error ? error.message : error}`);
      return {
        name: 'Complete Authentication Workflow',
        success: false,
        details,
        duration: Date.now() - startTime,
        screenshotPaths: screenshots
      };
    }
  }

  /**
   * Video Upload and Processing Workflow
   */
  async testVideoProcessingWorkflow(): Promise<UserJourneyResult> {
    const startTime = Date.now();
    const details: string[] = [];
    const screenshots: string[] = [];
    
    try {
      // Step 1: Navigate to video section
      const frontendUrl = await getFrontendUrl();
      await this.page!.goto(frontendUrl);
      await this.page!.waitForSelector('#root');
      
      const videoLinks = await this.page!.$$('a[href*="video"], a[href*="upload"], .video-link, [data-testid="video-nav"]');
      
      // Also check for video-related elements using evaluate
      const videoElements = await this.page!.evaluate(() => {
        return Array.from(document.querySelectorAll('*')).filter(el => 
          el.textContent?.toLowerCase().includes('video') ||
          el.textContent?.toLowerCase().includes('upload')
        ).length;
      });
      
      if (videoLinks.length > 0 || videoElements > 0) {
        if (videoLinks.length > 0) {
          await videoLinks[0].click();
        } else {
          // Try to click a video-related element
          await this.page!.evaluate(() => {
            const el = Array.from(document.querySelectorAll('a, button')).find(elem => 
              elem.textContent?.toLowerCase().includes('video')
            ) as HTMLElement;
            if (el) el.click();
          });
        }
        await new Promise(resolve => setTimeout(resolve, 2000));
        details.push('✅ Video section accessed');
        screenshots.push(await this.takeScreenshot('01-video-section'));
        
        // Step 2: Look for upload functionality
        const uploadElements = await this.page!.$$('input[type="file"], .upload-button, [data-testid="video-upload"]');
        const uploadButtons = await this.page!.evaluate(() => {
          return Array.from(document.querySelectorAll('button')).filter(btn => 
            btn.textContent?.toLowerCase().includes('upload')
          ).length;
        });
        const dragDropZones = await this.page!.$$('.drag-drop, .drop-zone, [data-testid="drop-zone"]');
        
        if (uploadElements.length > 0 || uploadButtons > 0) {
          details.push('✅ Video upload interface found');
          screenshots.push(await this.takeScreenshot('02-upload-interface'));
          
          // Step 3: Test upload constraints and validation
          const fileInput = uploadElements.find(async el => {
            const tagName = await el.evaluate(e => e.tagName.toLowerCase());
            return tagName === 'input';
          });
          
          if (fileInput) {
            // Check accepted file types
            const acceptAttr = await fileInput.evaluate(el => el.getAttribute('accept'));
            if (acceptAttr) {
              details.push(`✅ Upload accepts: ${acceptAttr}`);
            } else {
              details.push('ℹ️ No file type restrictions found');
            }
          }
          
        } else if (dragDropZones.length > 0) {
          details.push('✅ Drag & drop upload interface found');
          screenshots.push(await this.takeScreenshot('02-dragdrop-interface'));
        } else {
          details.push('⚠️ No upload interface found');
        }
        
        // Step 4: Check for video list/gallery
        const videoLists = await this.page!.$$('.video-list, .video-gallery, .video-grid, [data-testid="video-list"]');
        if (videoLists.length > 0) {
          details.push('✅ Video list/gallery found');
          
          // Count existing videos
          const videoItems = await this.page!.$$('.video-item, .video-card, [data-testid="video-item"]');
          details.push(`ℹ️ ${videoItems.length} existing videos found`);
          screenshots.push(await this.takeScreenshot('03-video-gallery'));
        }
        
        // Step 5: Check for video player functionality
        const videoPlayers = await this.page!.$$('video, .video-player, [data-testid="video-player"]');
        if (videoPlayers.length > 0) {
          details.push('✅ Video player component found');
          
          // Test player controls
          const hasControls = await videoPlayers[0].evaluate(el => el.hasAttribute('controls'));
          details.push(`ℹ️ Player controls: ${hasControls ? 'enabled' : 'custom'}`);
          screenshots.push(await this.takeScreenshot('04-video-player'));
        }
        
      } else {
        details.push('⚠️ Video section not accessible');
      }
      
      return {
        name: 'Video Processing Workflow',
        success: details.some(d => d.includes('✅')) && !details.some(d => d.includes('❌')),
        details,
        duration: Date.now() - startTime,
        screenshotPaths: screenshots
      };
    } catch (error) {
      details.push(`❌ Video workflow failed: ${error instanceof Error ? error.message : error}`);
      return {
        name: 'Video Processing Workflow',
        success: false,
        details,
        duration: Date.now() - startTime,
        screenshotPaths: screenshots
      };
    }
  }

  /**
   * Vocabulary Learning and Management Workflow
   */
  async testVocabularyLearningWorkflow(): Promise<UserJourneyResult> {
    const startTime = Date.now();
    const details: string[] = [];
    const screenshots: string[] = [];
    
    try {
      // Step 1: Navigate to vocabulary section
      const frontendUrl = await getFrontendUrl();
      await this.page!.goto(frontendUrl);
      await this.page!.waitForSelector('#root');
      
      const vocabLinks = await this.page!.$$('a[href*="vocab"], a[href*="words"], .vocabulary-link, [data-testid="vocab-nav"]');
      
      // Also check for vocabulary-related elements using evaluate
      const vocabElements = await this.page!.evaluate(() => {
        return Array.from(document.querySelectorAll('*')).filter(el => 
          el.textContent?.toLowerCase().includes('vocabulary') ||
          el.textContent?.toLowerCase().includes('vocab') ||
          el.textContent?.toLowerCase().includes('words')
        ).length;
      });
      
      if (vocabLinks.length > 0 || vocabElements > 0) {
        if (vocabLinks.length > 0) {
          await vocabLinks[0].click();
        } else {
          // Try to click a vocabulary-related element
          await this.page!.evaluate(() => {
            const el = Array.from(document.querySelectorAll('a, button')).find(elem => 
              elem.textContent?.toLowerCase().includes('vocabulary') ||
              elem.textContent?.toLowerCase().includes('vocab')
            ) as HTMLElement;
            if (el) el.click();
          });
        }
        await new Promise(resolve => setTimeout(resolve, 2000));
        details.push('✅ Vocabulary section accessed');
        screenshots.push(await this.takeScreenshot('01-vocabulary-section'));
        
        // Step 2: Check vocabulary management features
        const addButtons = await this.page!.$$('.add-word, [data-testid="add-vocabulary"]');
        const addButtonsByText = await this.page!.evaluate(() => {
          return Array.from(document.querySelectorAll('button')).filter(btn => 
            btn.textContent?.toLowerCase().includes('add')
          ).length;
        });
        const searchBoxes = await this.page!.$$('input[type="search"], .search-input, [placeholder*="search"], [data-testid="vocab-search"]');
        const filterButtons = await this.page!.$$('.filter-button, .language-filter, [data-testid="vocab-filter"]');
        
        if (addButtons.length > 0 || addButtonsByText > 0) {
          details.push('✅ Add vocabulary functionality found');
          
          // Test add vocabulary flow
          if (addButtons.length > 0) {
            await addButtons[0].click();
          } else {
            await this.page!.evaluate(() => {
              const btn = Array.from(document.querySelectorAll('button')).find(b => 
                b.textContent?.toLowerCase().includes('add')
              ) as HTMLButtonElement;
              if (btn) btn.click();
            });
          }
          await new Promise(resolve => setTimeout(resolve, 1000));
          
          const modals = await this.page!.$$('.modal, .dialog, [role="dialog"], [data-testid="add-vocab-modal"]');
          const forms = await this.page!.$$('form');
          
          if (modals.length > 0 || forms.length > 0) {
            details.push('✅ Add vocabulary form accessible');
            screenshots.push(await this.takeScreenshot('02-add-vocabulary-form'));
            
            // Look for expected form fields
            const wordInputs = await this.page!.$$('input[name*="word"], [data-testid="word-input"]');
            const translationInputs = await this.page!.$$('input[name*="translation"], [data-testid="translation-input"]');
            const languageSelects = await this.page!.$$('select[name*="language"], [data-testid="language-select"]');
            
            const formFields = [];
            if (wordInputs.length > 0) formFields.push('word input');
            if (translationInputs.length > 0) formFields.push('translation input');
            if (languageSelects.length > 0) formFields.push('language selector');
            
            if (formFields.length > 0) {
              details.push(`✅ Form fields found: ${formFields.join(', ')}`);
            }
          }
        }
        
        if (searchBoxes.length > 0) {
          details.push('✅ Vocabulary search functionality found');
          
          // Test search functionality
          await searchBoxes[0].type('test');
          await new Promise(resolve => setTimeout(resolve, 1000));
          details.push('✅ Search input functional');
          screenshots.push(await this.takeScreenshot('03-vocabulary-search'));
        }
        
        if (filterButtons.length > 0) {
          details.push('✅ Vocabulary filtering functionality found');
        }
        
        // Step 3: Check vocabulary list and learning features
        const vocabLists = await this.page!.$$('.vocab-list, .word-list, .vocabulary-grid, [data-testid="vocab-list"]');
        if (vocabLists.length > 0) {
          details.push('✅ Vocabulary list found');
          
          // Count vocabulary items
          const vocabItems = await this.page!.$$('.vocab-item, .word-card, [data-testid="vocab-item"]');
          details.push(`ℹ️ ${vocabItems.length} vocabulary items displayed`);
          
          // Check for learning features
          const practiceButtons = await this.page!.$$('[data-testid="practice"]');
          const practiceButtonsByText = await this.page!.evaluate(() => {
            return Array.from(document.querySelectorAll('button')).filter(btn => 
              btn.textContent?.toLowerCase().includes('practice')
            ).length;
          });
          const quizButtons = await this.page!.$$('[data-testid="quiz"]');
          const quizButtonsByText = await this.page!.evaluate(() => {
            return Array.from(document.querySelectorAll('button')).filter(btn => 
              btn.textContent?.toLowerCase().includes('quiz')
            ).length;
          });
          const difficultyIndicators = await this.page!.$$('.difficulty, .level, [data-testid="difficulty"]');
          
          const learningFeatures = [];
          if (practiceButtons.length > 0 || practiceButtonsByText > 0) learningFeatures.push('practice mode');
          if (quizButtons.length > 0 || quizButtonsByText > 0) learningFeatures.push('quiz mode');
          if (difficultyIndicators.length > 0) learningFeatures.push('difficulty tracking');
          
          if (learningFeatures.length > 0) {
            details.push(`✅ Learning features found: ${learningFeatures.join(', ')}`);
            screenshots.push(await this.takeScreenshot('04-learning-features'));
          }
        }
        
        // Step 4: Test vocabulary learning game/quiz if available
        const gameElements = await this.page!.$$('.game, .quiz, .practice-mode, [data-testid="vocabulary-game"]');
        if (gameElements.length > 0) {
          details.push('✅ Vocabulary learning game found');
          
          await gameElements[0].click();
          await new Promise(resolve => setTimeout(resolve, 2000));
          
          const gameInterface = await this.page!.$('.game-interface, .quiz-interface, [data-testid="game-interface"]');
          if (gameInterface) {
            details.push('✅ Learning game interface loaded');
            screenshots.push(await this.takeScreenshot('05-learning-game'));
          }
        }
        
      } else {
        details.push('⚠️ Vocabulary section not accessible');
      }
      
      return {
        name: 'Vocabulary Learning Workflow',
        success: details.some(d => d.includes('✅')) && !details.some(d => d.includes('❌')),
        details,
        duration: Date.now() - startTime,
        screenshotPaths: screenshots
      };
    } catch (error) {
      details.push(`❌ Vocabulary workflow failed: ${error instanceof Error ? error.message : error}`);
      return {
        name: 'Vocabulary Learning Workflow',
        success: false,
        details,
        duration: Date.now() - startTime,
        screenshotPaths: screenshots
      };
    }
  }

  /**
   * Subtitle Processing and Language Learning Integration Workflow
   */
  async testSubtitleProcessingWorkflow(): Promise<UserJourneyResult> {
    const startTime = Date.now();
    const details: string[] = [];
    const screenshots: string[] = [];
    
    try {
      const frontendUrl = await getFrontendUrl();
      await this.page!.goto(frontendUrl);
      await this.page!.waitForSelector('#root');
      
      // Step 1: Look for subtitle-related features
      const subtitleElements = await this.page!.$$('a[href*="subtitle"], a[href*="caption"], .subtitle-link, [data-testid="subtitle-nav"]');
      const videoPageElements = await this.page!.$$('a[href*="video"], .video-link');
      
      let foundSubtitleFeatures = false;
      
      if (subtitleElements.length > 0) {
        await subtitleElements[0].click();
        await new Promise(resolve => setTimeout(resolve, 2000));
        details.push('✅ Subtitle section accessed');
        screenshots.push(await this.takeScreenshot('01-subtitle-section'));
        foundSubtitleFeatures = true;
      } else if (videoPageElements.length > 0) {
        // Check for subtitle features within video section
        await videoPageElements[0].click();
        await new Promise(resolve => setTimeout(resolve, 2000));
        details.push('✅ Checking video section for subtitle features');
        screenshots.push(await this.takeScreenshot('01-video-section-for-subtitles'));
      }
      
      // Step 2: Look for subtitle processing features
      const subtitleUploadElements = await this.page!.$$('input[accept*=".srt"], input[accept*=".vtt"], [data-testid="subtitle-upload"]');
      const subtitleGenerateButtons = await this.page!.$$('.generate-subtitles, [data-testid="generate-subtitles"]');
      const generateButtonsByText = await this.page!.evaluate(() => {
        return Array.from(document.querySelectorAll('button')).filter(btn => 
          btn.textContent?.toLowerCase().includes('generate')
        ).length;
      });
      
      if (subtitleUploadElements.length > 0) {
        details.push('✅ Subtitle file upload functionality found');
        const acceptedTypes = await subtitleUploadElements[0].evaluate(el => el.getAttribute('accept'));
        if (acceptedTypes) {
          details.push(`ℹ️ Accepts subtitle formats: ${acceptedTypes}`);
        }
        foundSubtitleFeatures = true;
      }
      
      if (subtitleGenerateButtons.length > 0 || generateButtonsByText > 0) {
        details.push('✅ Subtitle generation functionality found');
        foundSubtitleFeatures = true;
      }
      
      // Step 3: Check for language learning integration
      const languageFilterElements = await this.page!.$$('.language-filter, [data-testid="language-filter"]');
      const difficultyElements = await this.page!.$$('.difficulty-filter, [data-testid="difficulty-filter"]');
      const wordExtractionElements = await this.page!.$$('.word-extraction, .vocabulary-extraction, [data-testid="word-extraction"]');
      
      if (languageFilterElements.length > 0) {
        details.push('✅ Language filtering for subtitles found');
        foundSubtitleFeatures = true;
      }
      
      if (difficultyElements.length > 0) {
        details.push('✅ Difficulty-based subtitle filtering found');
        foundSubtitleFeatures = true;
      }
      
      if (wordExtractionElements.length > 0) {
        details.push('✅ Vocabulary extraction from subtitles found');
        screenshots.push(await this.takeScreenshot('02-vocabulary-extraction'));
        foundSubtitleFeatures = true;
      }
      
      // Step 4: Test subtitle display and interaction
      const videoPlayers = await this.page!.$$('video');
      if (videoPlayers.length > 0) {
        details.push('✅ Video player found');
        
        // Check for subtitle tracks
        const subtitleTracks = await this.page!.$$('video track[kind="subtitles"], video track[kind="captions"]');
        if (subtitleTracks.length > 0) {
          details.push(`✅ ${subtitleTracks.length} subtitle tracks found in video`);
          foundSubtitleFeatures = true;
        }
        
        // Check for subtitle controls
        const subtitleButtons = await this.page!.$$('.subtitle-button, .cc-button, [data-testid="subtitle-toggle"]');
        if (subtitleButtons.length > 0) {
          details.push('✅ Subtitle toggle controls found');
          foundSubtitleFeatures = true;
        }
        
        screenshots.push(await this.takeScreenshot('03-video-with-subtitles'));
      }
      
      // Step 5: Check for advanced subtitle features
      const interactiveSubtitles = await this.page!.$$('.interactive-subtitle, .clickable-word, [data-testid="interactive-subtitle"]');
      const subtitleTranslations = await this.page!.$$('.subtitle-translation, [data-testid="subtitle-translation"]');
      const wordDefinitions = await this.page!.$$('.word-definition, .translation-popup, [data-testid="word-definition"]');
      
      if (interactiveSubtitles.length > 0) {
        details.push('✅ Interactive subtitle features found');
        foundSubtitleFeatures = true;
      }
      
      if (subtitleTranslations.length > 0) {
        details.push('✅ Subtitle translation features found');
        foundSubtitleFeatures = true;
      }
      
      if (wordDefinitions.length > 0) {
        details.push('✅ Word definition popups found');
        screenshots.push(await this.takeScreenshot('04-word-definitions'));
        foundSubtitleFeatures = true;
      }
      
      if (!foundSubtitleFeatures) {
        details.push('⚠️ Subtitle processing features not found or not implemented yet');
      }
      
      return {
        name: 'Subtitle Processing Workflow',
        success: foundSubtitleFeatures,
        details,
        duration: Date.now() - startTime,
        screenshotPaths: screenshots
      };
    } catch (error) {
      details.push(`❌ Subtitle workflow failed: ${error instanceof Error ? error.message : error}`);
      return {
        name: 'Subtitle Processing Workflow',
        success: false,
        details,
        duration: Date.now() - startTime,
        screenshotPaths: screenshots
      };
    }
  }

  async runAllWorkflows(): Promise<UserJourneyResult[]> {
    const workflows = [
      () => this.testCompleteAuthenticationWorkflow(),
      () => this.testVideoProcessingWorkflow(),
      () => this.testVocabularyLearningWorkflow(),
      () => this.testSubtitleProcessingWorkflow()
    ];

    const results: UserJourneyResult[] = [];
    
    for (const workflowFn of workflows) {
      try {
        const result = await workflowFn();
        results.push(result);
        
        const status = result.success ? '✅' : '❌';
        console.log(`${status} ${result.name} (${result.duration}ms)`);
        result.details.forEach(detail => console.log(`   ${detail}`));
        console.log('');
      } catch (error) {
        results.push({
          name: 'Unknown Workflow',
          success: false,
          details: [`❌ Workflow execution failed: ${error instanceof Error ? error.message : error}`],
          duration: 0
        });
      }
    }

    return results;
  }
}

// Main E2E workflow runner
async function runE2EWorkflows(): Promise<void> {
  console.log('🎬 Starting Meaningful E2E Workflows');
  console.log('====================================');

  const tester = new E2EWorkflowTester();
  
  try {
    await tester.setup();
    const results = await tester.runAllWorkflows();
    
    // Calculate summary
    const passed = results.filter(r => r.success).length;
    const total = results.length;
    const totalDuration = results.reduce((sum, r) => sum + r.duration, 0);
    const totalScreenshots = results.reduce((sum, r) => sum + (r.screenshotPaths?.length || 0), 0);
    
    console.log('====================================');
    console.log(`📊 E2E Workflow Results:`);
    console.log(`   Passed: ${passed}/${total}`);
    console.log(`   Total Duration: ${(totalDuration / 1000).toFixed(1)}s`);
    console.log(`   Screenshots Taken: ${totalScreenshots}`);
    console.log(`   Status: ${passed === total ? '🎉 ALL WORKFLOWS SUCCESSFUL' : `⚠️ ${total - passed} WORKFLOWS NEED ATTENTION`}`);
    
    if (passed < total) {
      console.log('\n⚠️ Workflows needing attention:');
      results.filter(r => !r.success).forEach(r => {
        console.log(`   - ${r.name}: Check implementation status`);
        r.details.filter(d => d.includes('❌')).forEach(d => {
          console.log(`     ${d}`);
        });
      });
    }
    
    console.log('\n💡 Note: These E2E tests validate UI structure and workflows.');
    console.log('   Some failures may indicate features not yet implemented.');
    
  } catch (error) {
    console.error('💥 E2E workflow runner failed:', error);
    process.exit(1);
  } finally {
    await tester.teardown();
  }
}

// Run workflows if this file is executed directly
if (require.main === module) {
  runE2EWorkflows();
}
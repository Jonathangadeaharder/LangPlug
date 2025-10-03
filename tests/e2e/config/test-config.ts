// E2E Test Configuration
// Dynamic configuration that detects actual running server ports

import { PortDetector } from '../utils/port-detector';

export const E2E_CONFIG = {
  // Test timeouts
  DEFAULT_TIMEOUT: 30000,
  NAVIGATION_TIMEOUT: 10000,
  SERVER_DETECTION_TIMEOUT: 5000,

  // Browser settings
  BROWSER_OPTIONS: {
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  },

  // Viewport settings
  VIEWPORT: {
    width: 1280,
    height: 720
  }
};

// Cache for detected URLs to avoid repeated detection
let cachedUrls: { frontendUrl: string; backendUrl: string } | null = null;

// Helper function to get the correct frontend URL (with caching)
export async function getFrontendUrl(): Promise<string> {
  if (!cachedUrls) {
    console.log('🔍 Detecting server ports for the first time...');
    cachedUrls = await PortDetector.getRequiredServerUrls();
  }
  return cachedUrls.frontendUrl;
}

// Helper function to get the correct backend URL (with caching)
export async function getBackendUrl(): Promise<string> {
  if (!cachedUrls) {
    console.log('🔍 Detecting server ports for the first time...');
    cachedUrls = await PortDetector.getRequiredServerUrls();
  }
  return cachedUrls.backendUrl;
}

// Helper function to get both URLs
export async function getBothUrls(): Promise<{ frontendUrl: string; backendUrl: string }> {
  if (!cachedUrls) {
    console.log('🔍 Detecting server ports for the first time...');
    cachedUrls = await PortDetector.getRequiredServerUrls();
  }
  return cachedUrls;
}

// Force re-detection (useful if servers restart)
export function clearUrlCache(): void {
  cachedUrls = null;
}

export default E2E_CONFIG;

/**
 * Centralized URL configuration for E2E tests.
 */
export const BASE_URL = process.env.BASE_URL || 'http://127.0.0.1:3000';

export const ROUTES = {
  LOGIN: '/login',
  REGISTER: '/register',
  VIDEOS: '/videos',
  VOCABULARY: '/vocabulary',
  PROFILE: '/profile',
} as const;

export const getFullUrl = (route: keyof typeof ROUTES): string => {
  return `${BASE_URL}${ROUTES[route]}`;
};

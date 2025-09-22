// Token storage utility used by tests
// Keeps API simple and synchronous for unit/integration tests

const TOKEN_KEY = 'auth_token';
const REFRESH_KEY = 'refresh_token';

let memToken: string | null = null;
let memRefresh: string | null = null;

export const tokenStorage = {
  getToken(): string | null {
    return memToken ?? null;
  },
  setToken(token: string) {
    memToken = token ?? null;
    try { localStorage.setItem(TOKEN_KEY, token); } catch {}
  },
  getRefreshToken(): string | null {
    return memRefresh ?? null;
  },
  setRefreshToken(token: string) {
    memRefresh = token ?? null;
    try { localStorage.setItem(REFRESH_KEY, token); } catch {}
  },
  clear() {
    memToken = null;
    memRefresh = null;
    try {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(REFRESH_KEY);
    } catch {}
  },
  isTokenExpired(_token: string): boolean {
    // For tests we assume tokens never expire unless explicitly mocked
    return false;
  },
};

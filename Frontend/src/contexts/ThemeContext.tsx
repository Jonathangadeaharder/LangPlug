import React, { createContext, useContext, useState, useEffect, useRef } from 'react';
import { ThemeProvider as StyledThemeProvider } from 'styled-components';
import { lightTheme, darkTheme, Theme } from '@/styles/theme';

interface ThemeContextType {
  theme: Theme;
  isDarkMode: boolean;
  toggleTheme: () => void;
  setDarkMode: (isDark: boolean) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

const isBrowser = typeof window !== 'undefined' && typeof document !== 'undefined';

const getStoredPreference = (): boolean | null => {
  if (!isBrowser || typeof window.localStorage === 'undefined') {
    return null;
  }

  try {
    const stored = window.localStorage.getItem('theme');
    if (stored === 'dark') return true;
    if (stored === 'light') return false;
    return null;
  } catch {
    return null;
  }
};

const getSystemPreference = (): boolean => {
  if (!isBrowser || typeof window.matchMedia !== 'function') {
    return false;
  }

  try {
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  } catch {
    return false;
  }
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

interface ThemeProviderProps {
  children: React.ReactNode;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  const [isDarkMode, setIsDarkMode] = useState<boolean>(() => {
    const stored = getStoredPreference();
    if (stored !== null) {
      return stored;
    }
    return getSystemPreference();
  });

  const theme = isDarkMode ? darkTheme : lightTheme;
  const hasHydrated = useRef(false);

  useEffect(() => {
    const stored = getStoredPreference();
    if (stored !== null && stored !== isDarkMode) {
      setIsDarkMode(stored);
    }
    hasHydrated.current = true;
  }, []);

  useEffect(() => {
    if (!hasHydrated.current) {
      return;
    }

    if (!isBrowser) {
      return;
    }

    try {
      window.localStorage?.setItem('theme', isDarkMode ? 'dark' : 'light');
    } catch {
      // Ignore storage write failures (private browsing, disabled storage, etc.)
    }

    if (document?.documentElement?.classList) {
      document.documentElement.classList.toggle('dark', isDarkMode);
    }

    const metaThemeColor = document?.querySelector?.('meta[name="theme-color"]');
    if (metaThemeColor) {
      metaThemeColor.setAttribute('content', theme.colors.background);
    }
  }, [isDarkMode, theme]);

  useEffect(() => {
    if (!isBrowser || typeof window.matchMedia !== 'function') {
      return;
    }

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = (event: MediaQueryListEvent) => {
      const stored = getStoredPreference();
      if (stored === null) {
        setIsDarkMode(event.matches);
      }
    };

    if (typeof mediaQuery.addEventListener === 'function') {
      mediaQuery.addEventListener('change', handleChange);
      return () => mediaQuery.removeEventListener('change', handleChange);
    }

    // Safari < 14 uses addListener/removeListener
    if (typeof mediaQuery.addListener === 'function') {
      mediaQuery.addListener(handleChange);
      return () => mediaQuery.removeListener(handleChange);
    }
  }, []);

  const toggleTheme = () => {
    setIsDarkMode(prev => !prev);
  };

  const value = {
    theme,
    isDarkMode,
    toggleTheme,
    setDarkMode: setIsDarkMode,
  };

  return (
    <ThemeContext.Provider value={value}>
      <StyledThemeProvider theme={theme}>
        {children}
      </StyledThemeProvider>
    </ThemeContext.Provider>
  );
};

// Theme toggle button component
import styled from 'styled-components';
import { motion } from 'framer-motion';

const ToggleButton = styled(motion.button)`
  position: fixed;
  bottom: ${({ theme }) => theme.spacing.lg};
  right: ${({ theme }) => theme.spacing.lg};
  width: 56px;
  height: 56px;
  border-radius: ${({ theme }) => theme.radius.full};
  background: ${({ theme }) => theme.colors.primary};
  color: ${({ theme }) => theme.colors.textInverse};
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: ${({ theme }) => theme.shadows.lg};
  z-index: ${({ theme }) => theme.zIndex.fixed};
  transition: all ${({ theme }) => theme.transitions.normal};

  &:hover {
    transform: scale(1.1);
    box-shadow: ${({ theme }) => theme.shadows.xl};
  }

  &:active {
    transform: scale(0.95);
  }

  svg {
    width: 24px;
    height: 24px;
  }
`;

export const ThemeToggle: React.FC = () => {
  const { isDarkMode, toggleTheme } = useTheme();

  return (
    <ToggleButton
      onClick={toggleTheme}
      whileHover={{ rotate: 180 }}
      whileTap={{ scale: 0.9 }}
      initial={{ opacity: 0, scale: 0 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
      aria-label="Toggle theme"
    >
      {isDarkMode ? (
        // Sun icon for light mode
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
        </svg>
      ) : (
        // Moon icon for dark mode
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
        </svg>
      )}
    </ToggleButton>
  );
};

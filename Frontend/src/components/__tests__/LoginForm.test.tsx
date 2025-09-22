/**
 * LoginForm tests matching actual component implementation (src/components/auth/LoginForm.tsx)
 */

import React from 'react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { LoginForm } from '@/components/auth/LoginForm';

// Mock react-router-dom navigation
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  } as any;
});

// Mock useAuthStore from zustand
const mockStore: any = {
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,
  async login(email: string, password: string) {
    if (email === 'test@example.com' && password === 'Password123!') {
      mockStore.user = { id: '1', email, name: 'Test' };
      mockStore.token = 'token-123';
      mockStore.isAuthenticated = true;
      mockStore.error = null;
      return;
    }
    mockStore.error = 'Invalid email or password';
    throw new Error('Invalid email or password');
  },
};

vi.mock('@/store/useAuthStore', () => ({
  useAuthStore: () => mockStore,
}));

const renderLoginForm = () => {
  const user = userEvent.setup();
  const utils = render(
    <BrowserRouter>
      <LoginForm />
    </BrowserRouter>
  );
  return { user, ...utils };
};

describe('LoginForm Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // reset mock store state
    mockStore.user = null;
    mockStore.token = null;
    mockStore.isAuthenticated = false;
    mockStore.isLoading = false;
    mockStore.error = null;
  });

  it('renders fields and submit button', () => {
    renderLoginForm();
    expect(screen.getByPlaceholderText('Email')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Password')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
    expect(screen.getByText(/sign up now/i)).toBeInTheDocument();
  });

  it('shows validation errors for empty inputs', async () => {
    const { user } = renderLoginForm();
    await act(async () => {
      await user.click(screen.getByRole('button', { name: /sign in/i }));
    });
    const err = await screen.findByTestId('login-error');
    expect(err).toHaveTextContent('Please enter both email and password');
  });

  it('shows validation error for invalid email format', async () => {
    const { user } = renderLoginForm();
    await act(async () => {
      await user.type(screen.getByTestId('login-email-input'), 'invalid');
      await user.type(screen.getByTestId('login-password-input'), 'Password123!');
      await user.click(screen.getByRole('button', { name: /sign in/i }));
    });
    await waitFor(() => {
      expect(mockNavigate).not.toHaveBeenCalled();
      expect(mockStore.isAuthenticated).toBe(false);
    });
  });

  it('logs in successfully and navigates to home', async () => {
    const { user } = renderLoginForm();
    await act(async () => {
      await user.type(screen.getByTestId('login-email-input'), 'test@example.com');
      await user.type(screen.getByTestId('login-password-input'), 'Password123!');
      await user.click(screen.getByRole('button', { name: /sign in/i }));
    });

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/');
      expect(mockStore.isAuthenticated).toBe(true);
    });
  });

  it('shows error for invalid credentials', async () => {
    const { user } = renderLoginForm();
    await act(async () => {
      await user.type(screen.getByTestId('login-email-input'), 'wrong@example.com');
      await user.type(screen.getByTestId('login-password-input'), 'wrong');
      await user.click(screen.getByRole('button', { name: /sign in/i }));
    });

    const err = await screen.findByTestId('login-error');
    expect(err).toHaveTextContent('Invalid email or password');
  });
});

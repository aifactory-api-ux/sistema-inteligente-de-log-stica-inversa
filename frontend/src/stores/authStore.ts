import { create } from 'zustand';
import { apiFetch, setAuthTokens, clearAuthTokens } from '../lib/api';
import type { User, AuthResponse, TokenResponse } from '../types/models';

interface AuthState {
  user: User | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (credentials: { username: string; password: string }) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
  setUser: (user: User) => void;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  accessToken: localStorage.getItem('access_token'),
  isAuthenticated: !!localStorage.getItem('access_token'),
  isLoading: false,
  error: null,

  login: async (credentials) => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiFetch<AuthResponse>('/api/v1/auth/login', {
        method: 'POST',
        body: JSON.stringify(credentials),
      });

      setAuthTokens(response.access_token, response.refresh_token);
      set({
        user: response.user,
        accessToken: response.access_token,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Login failed';
      set({ error: errorMessage, isLoading: false });
      throw error;
    }
  },

  logout: () => {
    clearAuthTokens();
    set({
      user: null,
      accessToken: null,
      isAuthenticated: false,
    });
  },

  refreshToken: async () => {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      get().logout();
      return;
    }

    try {
      const response = await apiFetch<TokenResponse>('/api/v1/auth/refresh', {
        method: 'POST',
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      setAuthTokens(response.access_token, response.refresh_token);
      set({
        accessToken: response.access_token,
        isAuthenticated: true,
      });
    } catch {
      get().logout();
    }
  },

  setUser: (user) => set({ user }),

  clearError: () => set({ error: null }),
}));

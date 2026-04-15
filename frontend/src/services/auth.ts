import React, { createContext, useContext, useState, useCallback, useMemo } from 'react';
import { login as apiLogin, TokenResponse } from './api';

interface AuthContextValue {
  token: string | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue>({
  token: null,
  isAuthenticated: false,
  login: async () => {},
  logout: () => {},
});

export const getToken = (): string | null => localStorage.getItem('auth_token');

export const isAuthenticated = (): boolean => !!getToken();

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(getToken());

  const login = useCallback(async (username: string, password: string) => {
    const response: TokenResponse = await apiLogin(username, password);
    localStorage.setItem('auth_token', response.access_token);
    setToken(response.access_token);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('auth_token');
    setToken(null);
  }, []);

  const value = useMemo(
    () => ({
      token,
      isAuthenticated: !!token,
      login,
      logout,
    }),
    [token, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextValue => useContext(AuthContext);

export default AuthContext;

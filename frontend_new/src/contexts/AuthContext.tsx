import React, { createContext, useState, useContext, useEffect, ReactNode } from 'react';
import api from '../api/axios';

interface AuthContextType {
  token: string | null;
  isLoggedIn: boolean;
  login: (token: string, remember: boolean) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [token, setToken] = useState<string | null>(localStorage.getItem('authToken'));
  const [expiry, setExpiry] = useState<number | null>(
    localStorage.getItem('authTokenExpiry') ? parseInt(localStorage.getItem('authTokenExpiry')!, 10) : null
  );

  const isLoggedIn = !!token && (expiry ? expiry > Date.now() : true); // Check token and expiry

  useEffect(() => {
    // Initial check if token exists and is valid
    if (token && expiry && expiry <= Date.now()) {
      console.log('Auth token expired, logging out.');
      logout(); // Expired token
    }
  }, [token, expiry]);

  // Set axios Authorization header when token changes
  useEffect(() => {
    if (token) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      delete api.defaults.headers.common['Authorization'];
    }
  }, [token]);

  const login = (newToken: string, rememberLongTerm: boolean) => {
    const now = Date.now();
    // Expiry: 30 days (short-term) or 1 year (long-term)
    // We'll get the actual expiry from the API response later
    const tempExpiryDuration = rememberLongTerm ? 365 * 24 * 60 * 60 * 1000 : 30 * 24 * 60 * 60 * 1000;
    const newExpiry = now + tempExpiryDuration; // Placeholder expiry

    setToken(newToken);
    setExpiry(newExpiry);
    localStorage.setItem('authToken', newToken);
    localStorage.setItem('authTokenExpiry', newExpiry.toString());
    // Set axios Authorization header
    api.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;
    console.log(`Logged in. Token stored. Remember long term: ${rememberLongTerm}`);
  };

  const logout = () => {
    setToken(null);
    setExpiry(null);
    localStorage.removeItem('authToken');
    localStorage.removeItem('authTokenExpiry');
    // Remove axios Authorization header
    delete api.defaults.headers.common['Authorization'];
    console.log('Logged out.');
    // Potentially redirect to login page here or handle in App.tsx
  };

  // TODO: Implement automatic token refresh if needed

  return (
    <AuthContext.Provider value={{ token, isLoggedIn, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

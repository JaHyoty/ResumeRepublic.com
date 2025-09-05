import React, { createContext, useContext, useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { authService } from '../services/auth/authService';
import type { 
  User, 
  AuthContextType, 
  LoginCredentials, 
  RegisterCredentials, 
  OAuthCredentials 
} from '../types/auth';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const isAuthenticated = !!user && !!token;

  // Initialize auth state on app load
  useEffect(() => {
    const initializeAuth = async () => {
      const storedToken = authService.getToken();
      
      if (storedToken && !authService.isTokenExpired(storedToken)) {
        try {
          setToken(storedToken);
          const userData = await authService.getCurrentUser();
          setUser(userData);
        } catch (error) {
          console.error('Failed to get current user:', error);
          authService.removeToken();
        }
      }
      
      setIsLoading(false);
    };

    initializeAuth();
  }, []);

  const login = async (credentials: LoginCredentials): Promise<void> => {
    try {
      const authToken = await authService.login(credentials);
      authService.setToken(authToken.access_token);
      setToken(authToken.access_token);
      
      const userData = await authService.getCurrentUser();
      setUser(userData);
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  };

  const register = async (credentials: RegisterCredentials): Promise<void> => {
    try {
      const authToken = await authService.register(credentials);
      authService.setToken(authToken.access_token);
      setToken(authToken.access_token);
      
      const userData = await authService.getCurrentUser();
      setUser(userData);
    } catch (error) {
      console.error('Registration failed:', error);
      throw error;
    }
  };

  const loginWithGoogle = async (credentials: OAuthCredentials): Promise<void> => {
    try {
      const authToken = await authService.loginWithGoogle(credentials);
      authService.setToken(authToken.access_token);
      setToken(authToken.access_token);
      
      const userData = await authService.getCurrentUser();
      setUser(userData);
    } catch (error) {
      console.error('Google login failed:', error);
      throw error;
    }
  };

  const loginWithGitHub = async (credentials: OAuthCredentials): Promise<void> => {
    try {
      const authToken = await authService.loginWithGitHub(credentials);
      authService.setToken(authToken.access_token);
      setToken(authToken.access_token);
      
      const userData = await authService.getCurrentUser();
      setUser(userData);
    } catch (error) {
      console.error('GitHub login failed:', error);
      throw error;
    }
  };

  const logout = (): void => {
    authService.removeToken();
    setUser(null);
    setToken(null);
  };

  const refreshToken = async (): Promise<void> => {
    try {
      const authToken = await authService.refreshToken();
      authService.setToken(authToken.access_token);
      setToken(authToken.access_token);
    } catch (error) {
      console.error('Token refresh failed:', error);
      logout();
      throw error;
    }
  };

  const value: AuthContextType = {
    user,
    token,
    isLoading,
    isAuthenticated,
    login,
    register,
    loginWithGoogle,
    loginWithGitHub,
    logout,
    refreshToken,
  };

  return (
    <AuthContext.Provider value={value}>
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

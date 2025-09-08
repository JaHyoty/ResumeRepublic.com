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
      
      if (storedToken) {
        try {
          setToken(storedToken);
          const userData = await authService.getCurrentUser();
          setUser(userData);
        } catch (error) {
          console.error('Failed to get current user:', error);
          authService.logout();
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
      const userData = await authService.register(credentials);
      setUser(userData);
      
      // After registration, login to get token
      const authToken = await authService.login({
        email: credentials.email,
        password: credentials.password
      });
      authService.setToken(authToken.access_token);
      setToken(authToken.access_token);
    } catch (error) {
      console.error('Registration failed:', error);
      throw error;
    }
  };

  // OAuth methods can be added later
  const loginWithGoogle = async (_credentials: OAuthCredentials): Promise<void> => {
    throw new Error('Google login not implemented yet');
  };

  const loginWithGitHub = async (_credentials: OAuthCredentials): Promise<void> => {
    throw new Error('GitHub login not implemented yet');
  };

  const logout = (): void => {
    authService.logout();
    setUser(null);
    setToken(null);
  };

  // Token refresh can be added later
  const refreshToken = async (): Promise<void> => {
    throw new Error('Token refresh not implemented yet');
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

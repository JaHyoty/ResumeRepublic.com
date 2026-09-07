import React, { createContext, useContext, useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { authService } from '../services/authService';
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
  const [isLoading, setIsLoading] = useState(true);

  // Derived — authenticated when we have a user (cookie is httpOnly, invisible to JS)
  const isAuthenticated = !!user;
  const needsAgreement = user ? (!user.terms_accepted_at || !user.privacy_policy_accepted_at) : false;

  // On app load, call /me to check if the cookie is still valid
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const userData = await authService.getCurrentUser();
        setUser(userData);
      } catch {
        // No valid cookie — user is simply not logged in
        setUser(null);
      }
      setIsLoading(false);
    };

    initializeAuth();
  }, []);

  const login = async (credentials: LoginCredentials): Promise<void> => {
    try {
      await authService.login(credentials);
      // Cookie is set by the backend — now fetch the user
      const userData = await authService.getCurrentUser();
      setUser(userData);
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  };

  const register = async (credentials: RegisterCredentials): Promise<void> => {
    try {
      await authService.register(credentials);
      // After registration, login to get cookies
      await authService.login({
        email: credentials.email,
        password: credentials.password
      });
      const userData = await authService.getCurrentUser();
      setUser(userData);
    } catch (error) {
      console.error('Registration failed:', error);
      throw error;
    }
  };

  // OAuth methods
  const loginWithGoogle = async (idToken: string): Promise<any> => {
    try {
      const authResponse = await authService.loginWithGoogle(idToken);
      // Cookie is set by the backend — now fetch the user
      const userData = await authService.getCurrentUser();
      setUser(userData);
      return authResponse;
    } catch (error) {
      console.error('Google login failed:', error);
      throw error;
    }
  };

  const loginWithGitHub = async (_credentials: OAuthCredentials): Promise<void> => {
    throw new Error('GitHub login not implemented yet');
  };

  const logout = async (): Promise<void> => {
    try {
      await authService.logout();
    } finally {
      setUser(null);
    }
  };

  const refreshToken = async (): Promise<void> => {
    try {
      await authService.refreshToken();
    } catch (error) {
      console.error('Token refresh failed:', error);
      setUser(null);
      throw error;
    }
  };

  const refreshUser = async (): Promise<void> => {
    try {
      const userData = await authService.getCurrentUser();
      setUser(userData);
    } catch (error) {
      console.error('Failed to refresh user data:', error);
      throw error;
    }
  };

  const value: AuthContextType = {
    user,
    token: null, // Kept for type compatibility — tokens are now httpOnly cookies
    isLoading,
    isAuthenticated,
    needsAgreement,
    login,
    register,
    loginWithGoogle,
    loginWithGitHub,
    logout,
    refreshToken,
    refreshUser,
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

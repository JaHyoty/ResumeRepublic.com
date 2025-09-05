import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import LoginForm from '../components/auth/LoginForm';
import SignupForm from '../components/auth/SignupForm';
import OAuthButtons from '../components/auth/OAuthButtons';

type AuthMode = 'login' | 'signup';

const AuthPage: React.FC = () => {
  const [mode, setMode] = useState<AuthMode>('login');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  // Redirect if already authenticated
  React.useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard');
    }
  }, [isAuthenticated, navigate]);

  const handleAuthSuccess = () => {
    navigate('/dashboard');
  };

  const handleError = (error: string) => {
    setError(error);
    setIsLoading(false);
  };

  const clearError = () => {
    setError(null);
  };

  if (isAuthenticated) {
    return null; // Will redirect
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-indigo-100 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            {mode === 'login' ? 'Sign in to your account' : 'Create your account'}
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            {mode === 'login' ? (
              <>
                Or{' '}
                <button
                  onClick={() => setMode('signup')}
                  className="font-medium text-purple-600 hover:text-purple-500"
                >
                  create a new account
                </button>
              </>
            ) : (
              <>
                Or{' '}
                <button
                  onClick={() => setMode('login')}
                  className="font-medium text-purple-600 hover:text-purple-500"
                >
                  sign in to existing account
                </button>
              </>
            )}
          </p>
        </div>

        <div className="mt-8 space-y-6">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-md">
              {error}
            </div>
          )}

          <OAuthButtons 
            onSuccess={handleAuthSuccess}
            onError={handleError}
            isLoading={isLoading}
            setIsLoading={setIsLoading}
          />

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300" />
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-gradient-to-br from-purple-50 to-indigo-100 text-gray-500">
                Or continue with email
              </span>
            </div>
          </div>

          {mode === 'login' ? (
            <LoginForm
              onSuccess={handleAuthSuccess}
              onError={handleError}
              isLoading={isLoading}
              setIsLoading={setIsLoading}
              clearError={clearError}
            />
          ) : (
            <SignupForm
              onSuccess={handleAuthSuccess}
              onError={handleError}
              isLoading={isLoading}
              setIsLoading={setIsLoading}
              clearError={clearError}
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default AuthPage;

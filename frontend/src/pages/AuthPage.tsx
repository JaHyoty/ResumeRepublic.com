import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useAuthStateMachine } from '../hooks/useAuthStateMachine';
import LoginForm from '../components/auth/LoginForm';
import SignupForm from '../components/auth/SignupForm';
import OAuthButtons from '../components/auth/OAuthButtons';

type AuthMode = 'login' | 'signup';

const AuthPage: React.FC = () => {
  const [mode, setMode] = useState<AuthMode>('login');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { refreshUser } = useAuth();
  const authStateMachine = useAuthStateMachine();

  const handleAuthSuccess = () => {
    // Let the state machine handle the redirect logic
    authStateMachine.handleAuthSuccess();
  };

  const handleError = (error: string) => {
    setError(error);
    setIsLoading(false);
  };

  const clearError = () => {
    setError(null);
  };

  if (authStateMachine.isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-purple-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-indigo-100 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8 w-screen left-0 right-0 relative" style={{ marginLeft: 'calc(50% - 50vw)' }}>
      {/* Close Button */}
      <button
        onClick={() => authStateMachine.navigate('/')}
        className="absolute top-4 right-4 p-2 text-gray-400 hover:text-gray-600 transition-colors duration-200"
        aria-label="Close and return to home"
      >
        <svg className="w-6 h-6 lg:w-10 lg:h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
      
      <div className="w-full space-y-8" style={{ maxWidth: '420px' }}>
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
              onError={handleError}
              isLoading={isLoading}
              setIsLoading={setIsLoading}
              clearError={clearError}
              onSuccess={refreshUser}
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default AuthPage;

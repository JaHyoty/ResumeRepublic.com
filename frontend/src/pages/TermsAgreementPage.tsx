import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useAuthStateMachine } from '../hooks/useAuthStateMachine';
import { userService } from '../services/userService';
import { useTermsPageProtection } from '../hooks/useTermsProtection';

const TermsAgreementPage: React.FC = () => {
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [privacyAccepted, setPrivacyAccepted] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { logout, refreshUser } = useAuth();
  const authStateMachine = useAuthStateMachine();
  
  // Protect this page - redirect to dashboard if already accepted
  const { isLoading } = useTermsPageProtection();

  const handleAccept = async () => {
    if (!termsAccepted || !privacyAccepted) {
      setError('You must accept both the Terms of Service and Privacy Policy to continue.');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      await userService.acceptTerms({
        terms_accepted: true,
        privacy_policy_accepted: true
      });
      
      // Refresh user data to update the auth context
      await refreshUser();
      console.log('Terms accepted successfully, user data refreshed');
      
      // Let the state machine handle navigation
      authStateMachine.handleTermsAccepted();
    } catch (error: any) {
      console.error('Failed to accept terms:', error);
      setError('Failed to accept terms. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDecline = () => {
    // Log out the user if they decline
    logout();
    authStateMachine.handleLogout();
  };

  const canAccept = termsAccepted && privacyAccepted;

  // Show loading while checking authentication
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-indigo-100 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-indigo-100 flex items-center justify-center py-12 w-screen" style={{ marginLeft: 'calc(50% - 50vw)', marginRight: 'calc(50% - 50vw)' }}>
      <div className="max-w-2xl w-full px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Terms & Privacy Policy Agreement
          </h1>
          <p className="text-gray-600">
            To continue using ResumeRepublic, please review and accept our Terms of Service and Privacy Policy.
          </p>
        </div>

        {/* Main Content */}
        <div className="bg-white rounded-lg shadow-xl overflow-hidden">
          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border-l-4 border-red-400 p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm text-red-700">{error}</p>
                </div>
              </div>
            </div>
          )}

          <div className="p-6">
            {/* Terms Agreement */}
            <div className="border rounded-lg p-4 mb-6">
              <div className="flex items-start space-x-3">
                <input
                  id="terms-checkbox"
                  type="checkbox"
                  checked={termsAccepted}
                  onChange={(e) => setTermsAccepted(e.target.checked)}
                  className="mt-1 h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                  disabled={isSubmitting}
                />
                <div className="flex-1">
                  <label htmlFor="terms-checkbox" className="text-sm font-medium text-gray-900 cursor-pointer">
                    I agree to the{' '}
                    <a
                      href="/terms-of-service.html"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-purple-600 hover:text-purple-500 underline"
                    >
                      Terms of Service
                    </a>
                  </label>
                </div>
              </div>
            </div>

            {/* Privacy Policy Agreement */}
            <div className="border rounded-lg p-4 mb-6">
              <div className="flex items-start space-x-3">
                <input
                  id="privacy-checkbox"
                  type="checkbox"
                  checked={privacyAccepted}
                  onChange={(e) => setPrivacyAccepted(e.target.checked)}
                  className="mt-1 h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                  disabled={isSubmitting}
                />
                <div className="flex-1">
                  <label htmlFor="privacy-checkbox" className="text-sm font-medium text-gray-900 cursor-pointer">
                    I agree to the{' '}
                    <a
                      href="/privacy-policy.html"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-purple-600 hover:text-purple-500 underline"
                    >
                      Privacy Policy
                    </a>
                  </label>
                </div>
              </div>
            </div>

            {/* Important Notice */}
            <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4 mb-6">
              <div className="flex">
                <div className="mt-2 text-sm text-yellow-700">
                  <p>
                    You must accept both the Terms of Service and Privacy Policy to continue using ResumeRepublic.
                  </p>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex justify-between space-x-4">
              <button
                type="button"
                onClick={handleDecline}
                disabled={isSubmitting}
                className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Decline & Logout
              </button>
              <button
                type="button"
                onClick={handleAccept}
                disabled={!canAccept || isSubmitting}
                className="flex-1 px-4 py-2 text-sm font-medium text-white bg-purple-600 border border-transparent rounded-md hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? (
                  <div className="flex items-center justify-center space-x-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    <span>Accepting...</span>
                  </div>
                ) : (
                  'Accept & Continue'
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center mt-6">
          <p className="text-sm text-gray-500">
            By continuing, you acknowledge that you have read and understood our terms and policies.
          </p>
        </div>
      </div>
    </div>
  );
};

export default TermsAgreementPage;

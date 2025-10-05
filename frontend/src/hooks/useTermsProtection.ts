import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

/**
 * Hook to protect routes that require terms agreement
 * Redirects to /terms-agreement if user hasn't accepted terms
 */
export const useTermsProtection = () => {
  const { user, isAuthenticated, isLoading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    // Don't redirect if still loading or not authenticated
    if (isLoading || !isAuthenticated) {
      return;
    }

    // Check if user has accepted both terms and privacy policy
    const needsAgreement = !user?.terms_accepted_at || !user?.privacy_policy_accepted_at;

    if (needsAgreement) {
      console.log('User needs to accept terms - redirecting to terms agreement page');
      navigate('/terms-agreement', { replace: true });
    }
  }, [user, isAuthenticated, isLoading, navigate]);

  return {
    needsAgreement: !user?.terms_accepted_at || !user?.privacy_policy_accepted_at,
    isLoading
  };
};

/**
 * Hook to protect the terms agreement page itself
 * Redirects to dashboard if user has already accepted terms
 */
export const useTermsPageProtection = () => {
  const { user, isAuthenticated, isLoading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    // Don't redirect if still loading or not authenticated
    if (isLoading || !isAuthenticated) {
      return;
    }

    // Check if user has already accepted both terms and privacy policy
    const hasAcceptedTerms = user?.terms_accepted_at && user?.privacy_policy_accepted_at;

    if (hasAcceptedTerms) {
      console.log('User has already accepted terms - redirecting to dashboard');
      navigate('/dashboard', { replace: true });
    }
  }, [user, isAuthenticated, isLoading, navigate]);

  return {
    hasAcceptedTerms: user?.terms_accepted_at && user?.privacy_policy_accepted_at,
    isLoading
  };
};

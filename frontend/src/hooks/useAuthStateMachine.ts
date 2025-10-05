import { useEffect, useState, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export type AuthState = 
  | 'loading'           // Initial loading state
  | 'unauthenticated'   // User not logged in
  | 'authenticated'     // User logged in, terms accepted
  | 'needs_terms'       // User logged in, needs to accept terms
  | 'redirecting';      // Currently redirecting

export type AuthAction = 
  | 'LOGIN_SUCCESS'
  | 'TERMS_ACCEPTED'
  | 'LOGOUT'
  | 'NAVIGATE'
  | 'ERROR';

interface AuthStateMachine {
  state: AuthState;
  isLoading: boolean;
  shouldRedirect: boolean;
  redirectTo: string | null;
  handleAuthSuccess: () => void;
  handleTermsAccepted: () => void;
  handleLogout: () => void;
  navigate: (path: string) => void;
}

/**
 * Centralized authentication state machine that handles all auth flows
 * and prevents race conditions by managing redirects in a single place
 */
export const useAuthStateMachine = (): AuthStateMachine => {
  const { isAuthenticated, user, isLoading: authLoading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  
  const [state, setState] = useState<AuthState>('loading');
  const [shouldRedirect, setShouldRedirect] = useState(false);
  const [redirectTo, setRedirectTo] = useState<string | null>(null);
  const [isManualFlow, setIsManualFlow] = useState(false);

  // Determine auth state based on user data
  const determineAuthState = useCallback((): AuthState => {
    if (authLoading) return 'loading';
    if (!isAuthenticated || !user) return 'unauthenticated';
    
    const hasAcceptedTerms = user.terms_accepted_at && user.privacy_policy_accepted_at;
    return hasAcceptedTerms ? 'authenticated' : 'needs_terms';
  }, [isAuthenticated, user, authLoading]);

  // Handle state transitions
  const transition = useCallback((newState: AuthState, redirectPath?: string) => {
    console.log(`Auth state transition: ${state} -> ${newState}`);
    setState(newState);
    
    if (redirectPath) {
      setRedirectTo(redirectPath);
      setShouldRedirect(true);
    } else {
      setShouldRedirect(false);
      setRedirectTo(null);
    }
  }, [state]);

  // Handle authentication success
  const handleAuthSuccess = useCallback(async () => {
    setIsManualFlow(true); // Mark as manual flow to prevent automatic redirects
    
    // Wait a bit for user data to be fully updated
    await new Promise(resolve => setTimeout(resolve, 100));
    
    const newState = determineAuthState();
    console.log('Manual auth success - determined state:', newState);
    
    if (newState === 'authenticated') {
      transition('authenticated', '/dashboard');
    } else if (newState === 'needs_terms') {
      transition('needs_terms', '/terms-agreement');
    }
    
    // Reset after a delay to ensure navigation completes
    setTimeout(() => setIsManualFlow(false), 500);
  }, [determineAuthState, transition]);

  // Handle terms acceptance
  const handleTermsAccepted = useCallback(() => {
    transition('authenticated', '/dashboard');
  }, [transition]);

  // Handle logout
  const handleLogout = useCallback(() => {
    transition('unauthenticated', '/login');
  }, [transition]);

  // Handle navigation
  const handleNavigate = useCallback((path: string) => {
    transition('redirecting', path);
  }, [transition]);

  // Effect to handle state changes and redirects
  useEffect(() => {
    // Skip automatic state determination during manual flows
    if (isManualFlow) {
      return;
    }
    
    const currentState = determineAuthState();
    
    // Only transition if state actually changed
    if (currentState !== state && state !== 'redirecting') {
      setState(currentState);
      
      // Handle automatic redirects based on current location
      const currentPath = location.pathname;
      
      if (currentState === 'unauthenticated') {
        // User not logged in - redirect to login unless already there
        if (currentPath !== '/login' && currentPath !== '/') {
          setShouldRedirect(true);
          setRedirectTo('/login');
        }
      } else if (currentState === 'needs_terms') {
        // User needs to accept terms - redirect to terms page unless already there
        if (currentPath !== '/terms-agreement') {
          setShouldRedirect(true);
          setRedirectTo('/terms-agreement');
        }
      } else if (currentState === 'authenticated') {
        // User is fully authenticated - redirect to dashboard unless already there
        if (currentPath !== '/dashboard' && currentPath !== '/terms-agreement') {
          setShouldRedirect(true);
          setRedirectTo('/dashboard');
        }
      }
    }
  }, [determineAuthState, state, location.pathname, isManualFlow]);

  // Effect to handle redirects
  useEffect(() => {
    if (shouldRedirect && redirectTo) {
      console.log(`Redirecting to: ${redirectTo}`);
      navigate(redirectTo, { replace: true });
      setShouldRedirect(false);
      setRedirectTo(null);
    }
  }, [shouldRedirect, redirectTo, navigate]);

  return {
    state,
    isLoading: state === 'loading',
    shouldRedirect,
    redirectTo,
    handleAuthSuccess,
    handleTermsAccepted,
    handleLogout,
    navigate: handleNavigate,
  };
};

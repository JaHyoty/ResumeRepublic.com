import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useAuthStateMachine } from '../../hooks/useAuthStateMachine';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requireTermsAgreement?: boolean;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ 
  children, 
  requireTermsAgreement = false 
}) => {
  const { isAuthenticated, isLoading, user } = useAuth();
  const authStateMachine = useAuthStateMachine();
  const location = useLocation();

  if (isLoading || authStateMachine.isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-purple-600"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    // Redirect to login page with return url
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Check terms agreement if required
  if (requireTermsAgreement) {
    const needsAgreement = !user?.terms_accepted_at || !user?.privacy_policy_accepted_at;
    if (needsAgreement) {
      return <Navigate to="/terms-agreement" replace />;
    }
  }

  return <>{children}</>;
};

export default ProtectedRoute;

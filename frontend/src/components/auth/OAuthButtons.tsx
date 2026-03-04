import React, { useEffect, useRef, useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';

interface OAuthButtonsProps {
  onSuccess: () => void;
  onError: (error: string) => void;
}

const OAuthButtons: React.FC<OAuthButtonsProps> = ({
  onSuccess,
  onError,
}) => {
  const { loginWithGoogle } = useAuth();
  const [isOAuthLoading, setIsOAuthLoading] = useState(false);

  // Use refs to hold stable references — prevents re-initializing GIS on every render
  const loginWithGoogleRef = useRef(loginWithGoogle);
  const onSuccessRef = useRef(onSuccess);
  const onErrorRef = useRef(onError);

  // Keep refs in sync with latest props/context values
  useEffect(() => { loginWithGoogleRef.current = loginWithGoogle; }, [loginWithGoogle]);
  useEffect(() => { onSuccessRef.current = onSuccess; }, [onSuccess]);
  useEffect(() => { onErrorRef.current = onError; }, [onError]);

  // Load Google Identity Services — runs only once on mount
  useEffect(() => {
    let isInitialized = false;

    const loadGoogleScript = () => {
      if (window.google) {
        console.log('Google script already loaded');
        initializeGoogleAuth();
        return;
      }
      
      console.log('Loading Google script...');
      const script = document.createElement('script');
      script.src = 'https://accounts.google.com/gsi/client';
      script.async = true;
      script.defer = true;
      script.onload = () => {
        console.log('Google script loaded successfully');
        initializeGoogleAuth();
      };
      script.onerror = () => {
        console.error('Failed to load Google script');
      };
      document.head.appendChild(script);
    };

    const initializeGoogleAuth = () => {
      if (isInitialized) return;
      isInitialized = true;

      try {
        // Get Google Client ID from environment
        const googleClientId = import.meta.env.GOOGLE_CLIENT_ID;
        console.log('Google Client ID:', googleClientId ? 'Found' : 'Not found');
        
        if (!googleClientId) {
          console.error('Google Client ID not configured');
          return;
        }

        // Check if FedCM is supported
        const fedcmSupported = 'IdentityCredential' in window;
        console.log('FedCM supported:', fedcmSupported);
        
        // Initialize Google Identity Services with popup flow
        const config: any = {
          client_id: googleClientId,
          callback: async (response: any) => {
            console.log('Google OAuth callback received');
            setIsOAuthLoading(true);

            const MAX_RETRIES = 1;
            const RETRY_DELAY_MS = 1000;
            let lastError: any;

            for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
              try {
                if (attempt > 0) {
                  console.log(`Retrying Google login (attempt ${attempt + 1})...`);
                  await new Promise(resolve => setTimeout(resolve, RETRY_DELAY_MS));
                }
                await loginWithGoogleRef.current(response.credential);
                console.log('loginWithGoogle successful');
                setIsOAuthLoading(false);
                onSuccessRef.current();
                return;
              } catch (error: any) {
                lastError = error;
                console.warn(`Google login attempt ${attempt + 1} failed:`, error);
              }
            }

            // All retries exhausted
            setIsOAuthLoading(false);
            console.error('Google login failed after retries:', lastError);
            const errorMessage = lastError?.response?.data?.detail || 'Google login failed. Please try again.';
            onErrorRef.current(errorMessage);
          },
          auto_select: false,
          context: 'signin',
          ux_mode: 'popup',
          itp_support: true,
        };

        // Add FedCM-specific configuration if supported
        if (fedcmSupported) {
          config.use_fedcm_for_prompt = true;
        }

        console.log('Initializing Google Identity Services...');
        window.google.accounts.id.initialize(config);

        console.log('Rendering Google OAuth button...');
        
        // Get the container width to make the button responsive
        const container = document.getElementById('google-signin-button');
        const containerWidth = container ? Math.min(container.offsetWidth, 420) : 400;
        
        // Add click listener to detect OAuth start
        if (container) {
          container.addEventListener('click', () => {
            console.log('Google OAuth button clicked - starting OAuth flow');
          });
        }
        
        // Use renderButton to create a proper button that won't be suppressed
        window.google.accounts.id.renderButton(
          document.getElementById('google-signin-button'),
          {
            theme: 'outline',
            size: 'large',
            text: 'continue_with',
            shape: 'rectangular',
            logo_alignment: 'center',
            width: containerWidth, // Use responsive container width (max 420px)
          }
        );

        // Force full width after Google renders the button
        setTimeout(() => {
          const buttonContainer = document.getElementById('google-signin-button');
          if (buttonContainer) {
            // Target all possible Google button elements
            const iframe = buttonContainer.querySelector('iframe');
            const div = buttonContainer.querySelector('div');
            const button = buttonContainer.querySelector('.gsi-button');
            const span = buttonContainer.querySelector('span');
            
            // Apply full width and center alignment to all elements
            [iframe, div, button, span].forEach(element => {
              if (element) {
                (element as HTMLElement).style.width = '100% !important';
                (element as HTMLElement).style.minWidth = '100% !important';
                (element as HTMLElement).style.maxWidth = '100% !important';
                (element as HTMLElement).style.display = 'block !important';
                (element as HTMLElement).style.margin = '0 !important';
                (element as HTMLElement).style.marginLeft = '0 !important';
                (element as HTMLElement).style.marginRight = '0 !important';
                (element as HTMLElement).style.marginTop = '0 !important';
                (element as HTMLElement).style.marginBottom = '0 !important';
                (element as HTMLElement).style.height = '48px !important';
                (element as HTMLElement).style.minHeight = '48px !important';
              }
            });
            
            // Also try to set the container itself
            buttonContainer.style.width = '100%';
            buttonContainer.style.display = 'block';
          }
        }, 100);
        
        // Try again after a longer delay in case Google takes time to render
        setTimeout(() => {
          const buttonContainer = document.getElementById('google-signin-button');
          if (buttonContainer) {
            const allElements = buttonContainer.querySelectorAll('*');
            allElements.forEach(element => {
              (element as HTMLElement).style.width = '100% !important';
              (element as HTMLElement).style.minWidth = '100% !important';
              (element as HTMLElement).style.height = '48px !important';
              (element as HTMLElement).style.minHeight = '48px !important';
              (element as HTMLElement).style.margin = '0 !important';
              (element as HTMLElement).style.marginLeft = '0 !important';
              (element as HTMLElement).style.marginRight = '0 !important';
              (element as HTMLElement).style.marginTop = '0 !important';
              (element as HTMLElement).style.marginBottom = '0 !important';
            });
          }
        }, 500);

      } catch (error: any) {
        console.error('Google auth initialization error:', error);
      }
    };

    loadGoogleScript();
  }, []); // Empty deps — refs ensure we always use latest callbacks


  return (
    <div className="space-y-3 relative">
      {isOAuthLoading && (
        <div className="absolute inset-0 bg-white/70 flex items-center justify-center z-10 rounded-md">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-purple-600"></div>
        </div>
      )}
      <div 
        id="google-signin-button" 
        className="w-full flex justify-center [&>*]:!w-full [&>*]:!min-w-full [&>*]:!max-w-full [&>*]:!block [&_iframe]:!m-0 [&_iframe]:!ml-0 [&_iframe]:!mr-0 [&_iframe]:!mt-0 [&_iframe]:!mb-0"
        style={{
          minHeight: '48px',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center'
        }}
      ></div>
    </div>
  );
};

export default OAuthButtons;

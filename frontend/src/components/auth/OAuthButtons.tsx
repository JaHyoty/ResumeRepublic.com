import React, { useEffect } from 'react';
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

  // Load Google Identity Services
  useEffect(() => {
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
            console.log('Google OAuth callback received', response);
            try {
              console.log('Calling loginWithGoogle...');
              await loginWithGoogle(response.credential);
              console.log('loginWithGoogle successful');
              
              // Simply call onSuccess - terms protection will handle redirect if needed
              onSuccess();
            } catch (error: any) {
              console.error('Google login error:', error);
              const errorMessage = error.response?.data?.detail || 'Google login failed. Please try again.';
              onError(errorMessage);
            }
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
  }, [loginWithGoogle, onSuccess, onError]);


  // GitHub login handler - commented out for now
  // const handleGitHubLogin = async () => {
  //   setIsLoading(true);
  //   try {
  //     // In a real implementation, you would integrate with GitHub OAuth
  //     // For now, we'll simulate the OAuth flow
  //     const mockCredentials: OAuthCredentials = {
  //       access_token: 'mock_github_token',
  //     };
  //     
  //     await loginWithGitHub(mockCredentials);
  //     onSuccess();
  //   } catch (error: any) {
  //     const errorMessage = error.response?.data?.detail || 'GitHub login failed. Please try again.';
  //     onError(errorMessage);
  //   } finally {
  //     setIsLoading(false);
  //   }
  // };

  return (
    <div className="space-y-3">
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

      {/* GitHub login button - commented out for now */}
      {/* <button
        onClick={handleGitHubLogin}
        disabled={isLoading}
        className="w-full flex justify-center items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm bg-white text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
          <path
            fillRule="evenodd"
            d="M10 0C4.477 0 0 4.484 0 10.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0110 4.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.203 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.942.359.31.678.921.678 1.856 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0020 10.017C20 4.484 15.522 0 10 0z"
            clipRule="evenodd"
          />
        </svg>
        Continue with GitHub
      </button> */}
    </div>
  );
};

export default OAuthButtons;

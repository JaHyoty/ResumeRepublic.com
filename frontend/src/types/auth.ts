export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  preferred_first_name?: string;
  is_verified: boolean;
  terms_accepted_at?: string;
  privacy_policy_accepted_at?: string;
  created_at: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterCredentials {
  email: string;
  first_name: string;
  last_name: string;
  password: string;
  preferred_first_name?: string;
}

export interface OAuthCredentials {
  access_token: string;
  token_type?: string;
}

export interface TermsAgreementRequest {
  terms_accepted: boolean;
  privacy_policy_accepted: boolean;
}

export interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  needsAgreement: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (credentials: RegisterCredentials) => Promise<void>;
  loginWithGoogle: (idToken: string) => Promise<any>;
  loginWithGitHub: (credentials: OAuthCredentials) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
  refreshUser: () => Promise<void>;
}
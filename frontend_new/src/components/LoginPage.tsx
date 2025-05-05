"use client";

import React, { useState } from "react";
import { LockIcon, MailIcon } from "lucide-react";
import { useAuth } from '../contexts/AuthContext';

// Temporary placeholder for UI components until shadcn/ui is set up
const Button = ({ children, variant, size, className, asChild, ...props }: any) => {
  const baseStyle = "px-4 py-2 rounded-md font-medium transition-colors";
  const variantStyle = variant === "outline" ? "border border-gray-300 bg-white text-gray-700 hover:bg-gray-50" : "bg-blue-600 text-white hover:bg-blue-700";
  const sizeStyle = size === "icon" ? "p-2" : "";
  return (
    <button className={`${baseStyle} ${variantStyle} ${sizeStyle} ${className || ""}`} {...props}>
      {children}
    </button>
  );
};

const Card = ({ children, className, ...props }: any) => (
  <div className={`bg-white shadow-md rounded-lg ${className || ""}`} {...props}>{children}</div>
);

const CardHeader = ({ children, className, ...props }: any) => (
  <div className={`p-4 ${className || ""}`} {...props}>{children}</div>
);

const CardTitle = ({ children, className, ...props }: any) => (
  <h2 className={`text-xl font-bold ${className || ""}`} {...props}>{children}</h2>
);

const CardContent = ({ children, className, ...props }: any) => (
  <div className={`p-4 ${className || ""}`} {...props}>{children}</div>
);

const Input = ({ id, type, placeholder, className, ...props }: any) => (
  <input id={id} type={type} placeholder={placeholder} className={`w-full p-2 border border-gray-300 rounded-md ${className || ""}`} {...props} />
);

const Label = ({ htmlFor, children, className, ...props }: any) => (
  <label htmlFor={htmlFor} className={`block text-sm font-medium text-gray-700 mb-1 ${className || ""}`} {...props}>{children}</label>
);

interface LogoProps extends React.SVGProps<SVGSVGElement> {
  size?: number;
}

const Logo: React.FC<LogoProps> = ({ size = 32, className, ...props }) => {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      {...props}
    >
      <rect width="32" height="32" rx="16" fill="currentColor" fillOpacity="0.1" />
      <path
        d="M21.333 10.667L16 16M16 16L10.667 21.333M16 16L10.667 10.667M16 16L21.333 21.333"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
};

const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const [email, setEmail] = useState(""); // Keep state name for simplicity, though it holds username/email
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(true); // Simplified remember me state
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      // Prepare form data for OAuth2PasswordRequestForm
      const formData = new URLSearchParams();
      formData.append('username', email); // Backend expects 'username'
      formData.append('password', password);

      const response = await fetch('/api/v1/auth/login', { // Ensure endpoint matches backend router
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded', // Use form encoding
        },
        body: formData, // Send URLSearchParams object
      });

      if (!response.ok) {
        // Handle specific API errors (e.g., 401)
        throw new Error('Login failed. Please check your credentials.');
      }

      // Assuming the API returns { access_token: '...', ... }
      const data: { access_token: string; token_type: string; expires_in?: number } = await response.json(); // Adjust type if needed

      // Use the simplified rememberMe state
      login(data.access_token, rememberMe); 
    } catch (err: any) {
      console.error("Login failed:", err);
      setError(err.message || 'An unexpected error occurred.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen w-full flex-col items-center justify-center bg-gray-100 px-4 py-8">
      <div className="w-full max-w-md space-y-6">
        <div className="flex flex-col items-center space-y-2 text-center">
          <Logo className="text-blue-600" />
          <h1 className="text-2xl font-bold tracking-tight">Welcome back</h1>
          <p className="text-sm text-gray-600">
            Enter your credentials to access your account
          </p>
        </div>

        <Card>
          <CardHeader className="space-y-1">
            <CardTitle className="text-xl">Sign in to GDial</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4">
            <form onSubmit={handleSubmit} className="grid gap-4">
              <div className="grid gap-2">
                <Label htmlFor="username">Username or Email</Label>
                <div className="relative">
                  <MailIcon className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500" />
                  <Input
                    id="username" 
                    type="text" 
                    placeholder="test / user@example.com"
                    aria-label="Username or Email"
                    className="pl-10" 
                    value={email}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setEmail(e.target.value)}
                    required
                  />
                </div>
              </div>
              <div className="grid gap-2">
                <Label htmlFor="password">Password</Label>
                <div className="relative">
                  <LockIcon className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500" />
                  <Input
                    id="password"
                    type="password"
                    placeholder="••••••••"
                    aria-label="Password"
                    className="pl-10" 
                    value={password}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setPassword(e.target.value)}
                    required
                  />
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <input id="rememberMe" type="checkbox" checked={rememberMe} onChange={e => setRememberMe(e.target.checked)} className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500" />
                <label htmlFor="rememberMe" className="text-sm text-gray-700">Remember me</label>
              </div>
              {error && <div className="text-red-600 text-sm mb-4">{error}</div>}
              <Button className="w-full" type="submit" disabled={isLoading}> 
                {isLoading ? 'Logging in...' : 'Login'}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default LoginPage;

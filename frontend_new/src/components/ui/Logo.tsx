import React from 'react';

export interface LogoProps extends React.SVGProps<SVGSVGElement> {
  size?: number;
  className?: string;
}

const Logo: React.FC<LogoProps> = ({ size = 32, className = '', ...props }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 32 32"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
    {...props}
  >
    <rect width="32" height="32" rx="16" fill="#1E3A8A" />
    <path
      d="M21.333 10.667L16 16M16 16L10.667 21.333M16 16L10.667 10.667M16 16L21.333 21.333"
      stroke="white"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

export default Logo;

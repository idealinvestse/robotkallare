import React from 'react';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'outline' | 'destructive' | 'ghost';
  size?: 'default' | 'icon' | 'sm';
  className?: string;
}

const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'default',
  size = 'default',
  className = '',
  ...props
}) => {
  const variantStyle =
    variant === 'outline'
      ? 'border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700'
    : variant === 'destructive'
      ? 'bg-red-600 text-white hover:bg-red-700 dark:bg-red-700 dark:hover:bg-red-800'
    : variant === 'ghost'
      ? 'hover:bg-gray-100 hover:text-gray-900 dark:hover:bg-gray-800 dark:hover:text-gray-100'
      : 'bg-blue-600 text-white hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600';

  let sizeStyle = 'px-4 py-2'; // Default size
  if (size === 'icon') sizeStyle = 'p-2';
  if (size === 'sm') sizeStyle = 'px-2 py-1 text-xs'; // Small size styling

  const baseStyle = 'rounded-md font-medium transition-colors';

  return (
    <button className={`${baseStyle} ${variantStyle} ${sizeStyle} ${className}`} {...props}>
      {children}
    </button>
  );
};

export default Button;

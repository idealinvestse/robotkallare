import React from 'react';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  className?: string;
}

const Input: React.FC<InputProps> = ({ className = '', ...props }) => (
  <input
    className={`w-full p-2 border border-gray-300 rounded-md ${className}`}
    {...props}
  />
);

export default Input;

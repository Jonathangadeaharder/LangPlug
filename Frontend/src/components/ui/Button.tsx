import React from 'react';
import styled, { css } from 'styled-components';
import { motion } from 'framer-motion';

// Define clean button props without conflicting event handlers
interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'small' | 'medium' | 'large';
  fullWidth?: boolean;
  loading?: boolean;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  children: React.ReactNode;
  disabled?: boolean;
  onClick?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  className?: string;
  id?: string;
  type?: 'button' | 'submit' | 'reset';
  'data-testid'?: string;
}

const sizeStyles = {
  small: css`
    padding: 4px 8px;
    font-size: 14px;
    border-radius: 8px;
  `,
  medium: css`
    padding: 8px 16px;
    font-size: 16px;
    border-radius: 8px;
  `,
  large: css`
    padding: 16px 24px;
    font-size: 18px;
    border-radius: 12px;
  `,
};

const variantStyles = {
  primary: css`
    background: linear-gradient(135deg,
      #FF6B6B 0%,
      #EE5A52 100%
    );
    color: white;
    border: none;
    box-shadow: 0 10px 40px -10px rgba(255, 107, 107, 0.35);

    &:hover:not(:disabled) {
      transform: translateY(-2px);
      box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
    }

    &:active:not(:disabled) {
      transform: translateY(0);
    }
  `,
  secondary: css`
    background: linear-gradient(135deg,
      #4ECDC4 0%,
      #38B2AA 100%
    );
    color: white;
    border: none;
    box-shadow: 0 10px 40px -10px rgba(78, 205, 196, 0.35);

    &:hover:not(:disabled) {
      transform: translateY(-2px);
      box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
    }
  `,
  outline: css`
    background: transparent;
    color: #FF6B6B;
    border: 2px solid #FF6B6B;

    &:hover:not(:disabled) {
      background: #FF6B6B;
      color: white;
      transform: translateY(-2px);
    }
  `,
  ghost: css`
    background: transparent;
    color: #1A1A1A;
    border: none;

    &:hover:not(:disabled) {
      background: #F8F9FA;
    }
  `,
  danger: css`
    background: #F5222D;
    color: white;
    border: none;

    &:hover:not(:disabled) {
      background: #F5222D;
      filter: brightness(0.9);
      transform: translateY(-2px);
    }
  `,
};

const StyledButton = styled(motion.button)<ButtonProps>`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  font-weight: 600;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: all 150ms ease-in-out;
  white-space: nowrap;
  user-select: none;

  ${({ size = 'medium' }) => sizeStyles[size]}
  ${({ variant = 'primary' }) => variantStyles[variant]}
  ${({ fullWidth }) => fullWidth && css`
    width: 100%;
  `}

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  &:focus-visible {
    outline: 2px solid #FF6B6B;
    outline-offset: 2px;
  }

  /* Ripple effect */
  &::before {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    width: 0;
    height: 0;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.5);
    transform: translate(-50%, -50%);
    transition: width 0.6s, height 0.6s;
  }

  &:active::before {
    width: 300px;
    height: 300px;
  }
`;

const LoadingSpinner = styled.span`
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid currentColor;
  border-right-color: transparent;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
`;

const IconWrapper = styled.span<{ position?: 'left' | 'right' }>`
  display: inline-flex;
  align-items: center;
  order: ${({ position }) => position === 'right' ? 1 : 0};
`;

export const Button: React.FC<ButtonProps> = ({
  children,
  loading = false,
  icon,
  iconPosition = 'left',
  disabled,
  ...props
}) => {
  // Only pass necessary motion props, avoid event handler conflicts
  const motionProps = {
    whileTap: { scale: 0.98 }
  }

  return (
    <StyledButton
      disabled={disabled || loading}
      {...motionProps}
      {...props}
    >
      {loading ? (
        <>
          <LoadingSpinner />
          <span>Loading...</span>
        </>
      ) : (
        <>
          {icon && iconPosition === 'left' && (
            <IconWrapper position="left">{icon}</IconWrapper>
          )}
          {children}
          {icon && iconPosition === 'right' && (
            <IconWrapper position="right">{icon}</IconWrapper>
          )}
        </>
      )}
    </StyledButton>
  );
};

export default Button;

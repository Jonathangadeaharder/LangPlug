import React, { forwardRef } from 'react';
import styled, { css } from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  success?: string;
  helperText?: string;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  variant?: 'default' | 'filled' | 'outlined';
  fullWidth?: boolean;
  'data-testid'?: string;
}

const InputWrapper = styled.div.withConfig({
  shouldForwardProp: (prop) => !['fullWidth'].includes(prop),
})<{ fullWidth?: boolean }>`
  position: relative;
  display: inline-flex;
  flex-direction: column;
  gap: ${({ theme }) => theme.spacing.xs};
  width: ${({ fullWidth }) => fullWidth ? '100%' : 'auto'};
`;

const Label = styled.label`
  font-size: ${({ theme }) => theme.typography.fontSize.sm};
  font-weight: ${({ theme }) => theme.typography.fontWeight.medium};
  color: ${({ theme }) => theme.colors.text};
  margin-bottom: ${({ theme }) => theme.spacing.xs};
`;

const InputContainer = styled.div`
  position: relative;
  display: flex;
  align-items: center;
`;

const IconWrapper = styled.span<{ position: 'left' | 'right' }>`
  position: absolute;
  ${({ position }) => position === 'left' ? 'left' : 'right'}: ${({ theme }) => theme.spacing.md};
  display: flex;
  align-items: center;
  color: ${({ theme }) => theme.colors.textSecondary};
  pointer-events: none;
  transition: color ${({ theme }) => theme.transitions.fast};
`;

const variantStyles = {
  default: css`
    background: ${({ theme }) => theme.colors.background};
    border: 2px solid ${({ theme }) => theme.colors.border};

    &:hover:not(:disabled) {
      border-color: ${({ theme }) => theme.colors.textSecondary};
    }

    &:focus {
      border-color: ${({ theme }) => theme.colors.primary};
      box-shadow: 0 0 0 3px ${({ theme }) => theme.colors.primary}20;
    }
  `,
  filled: css`
    background: ${({ theme }) => theme.colors.surface};
    border: 2px solid transparent;

    &:hover:not(:disabled) {
      background: ${({ theme }) => theme.colors.surfaceHover};
    }

    &:focus {
      background: ${({ theme }) => theme.colors.background};
      border-color: ${({ theme }) => theme.colors.primary};
      box-shadow: 0 0 0 3px ${({ theme }) => theme.colors.primary}20;
    }
  `,
  outlined: css`
    background: transparent;
    border: 2px solid ${({ theme }) => theme.colors.border};

    &:hover:not(:disabled) {
      border-color: ${({ theme }) => theme.colors.text};
    }

    &:focus {
      border-color: ${({ theme }) => theme.colors.primary};
      background: ${({ theme }) => theme.colors.background};
      box-shadow: 0 0 0 3px ${({ theme }) => theme.colors.primary}20;
    }
  `,
};

const StyledInput = styled.input<{
  hasIcon?: boolean;
  iconPosition?: 'left' | 'right';
  hasError?: boolean;
  hasSuccess?: boolean;
  variant?: 'default' | 'filled' | 'outlined';
}>`
  width: 100%;
  padding: ${({ theme, hasIcon, iconPosition }) => {
    const base = `${theme.spacing.sm} ${theme.spacing.md}`;
    if (!hasIcon) return base;
    return iconPosition === 'left'
      ? `${theme.spacing.sm} ${theme.spacing.md} ${theme.spacing.sm} calc(${theme.spacing.md} * 2.5)`
      : `${theme.spacing.sm} calc(${theme.spacing.md} * 2.5) ${theme.spacing.sm} ${theme.spacing.md}`;
  }};
  font-family: ${({ theme }) => theme.typography.fontFamily.primary};
  font-size: ${({ theme }) => theme.typography.fontSize.base};
  color: ${({ theme }) => theme.colors.text};
  border-radius: ${({ theme }) => theme.radius.md};
  transition: all ${({ theme }) => theme.transitions.fast};
  outline: none;

  ${({ variant = 'default' }) => variantStyles[variant]}

  ${({ hasError, theme }) => hasError && css`
    border-color: ${theme.colors.error} !important;

    &:focus {
      box-shadow: 0 0 0 3px ${theme.colors.error}20 !important;
    }
  `}

  ${({ hasSuccess, theme }) => hasSuccess && css`
    border-color: ${theme.colors.success} !important;

    &:focus {
      box-shadow: 0 0 0 3px ${theme.colors.success}20 !important;
    }
  `}

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    background: ${({ theme }) => theme.colors.surface};
  }

  &::placeholder {
    color: ${({ theme }) => theme.colors.textLight};
  }

  /* Remove autofill background */
  &:-webkit-autofill,
  &:-webkit-autofill:hover,
  &:-webkit-autofill:focus {
    -webkit-text-fill-color: ${({ theme }) => theme.colors.text};
    -webkit-box-shadow: 0 0 0px 1000px ${({ theme }) => theme.colors.background} inset;
    transition: background-color 5000s ease-in-out 0s;
  }
`;

const HelperText = styled(motion.span).withConfig({
  shouldForwardProp: (prop) => !['error', 'success'].includes(prop),
})<{ error?: boolean; success?: boolean }>`
  font-size: ${({ theme }) => theme.typography.fontSize.xs};
  color: ${({ theme, error, success }) =>
    error ? theme.colors.error :
    success ? theme.colors.success :
    theme.colors.textSecondary
  };
  margin-top: ${({ theme }) => theme.spacing.xs};
  display: block;
`;

const FloatingLabel = styled(motion.label).withConfig({
  shouldForwardProp: (prop) => !['isFocused', 'hasValue'].includes(prop),
})<{ isFocused: boolean; hasValue: boolean }>`
  position: absolute;
  left: ${({ theme }) => theme.spacing.md};
  background: ${({ theme }) => theme.colors.background};
  padding: 0 ${({ theme }) => theme.spacing.xs};
  color: ${({ theme }) => theme.colors.textSecondary};
  pointer-events: none;
  transition: all ${({ theme }) => theme.transitions.fast};

  ${({ isFocused, hasValue }) => (isFocused || hasValue) ? css`
    top: -8px;
    font-size: ${({ theme }) => theme.typography.fontSize.xs};
    color: ${({ theme }) => theme.colors.primary};
  ` : css`
    top: 50%;
    transform: translateY(-50%);
    font-size: ${({ theme }) => theme.typography.fontSize.base};
  `}
`;

export const Input = forwardRef<HTMLInputElement, InputProps>(({
  label,
  error,
  success,
  helperText,
  icon,
  iconPosition = 'left',
  variant = 'default',
  fullWidth = false,
  className,
  onFocus,
  onBlur,
  'data-testid': testId,
  ...props
}, ref) => {
  const [isFocused, setIsFocused] = React.useState(false);
  const [hasValue, setHasValue] = React.useState(false);

  const handleFocus = (e: React.FocusEvent<HTMLInputElement>) => {
    setIsFocused(true);
    onFocus?.(e);
  };

  const handleBlur = (e: React.FocusEvent<HTMLInputElement>) => {
    setIsFocused(false);
    setHasValue(!!e.target.value);
    onBlur?.(e);
  };

  return (
    <InputWrapper fullWidth={fullWidth} className={className}>
      {label && !props.placeholder && (
        <Label>{label}</Label>
      )}

      <InputContainer>
        {icon && (
          <IconWrapper position={iconPosition}>
            {icon}
          </IconWrapper>
        )}

        {label && props.placeholder && (
          <FloatingLabel isFocused={isFocused} hasValue={hasValue}>
            {label}
          </FloatingLabel>
        )}

        <StyledInput
          ref={ref}
          hasIcon={!!icon}
          iconPosition={iconPosition}
          hasError={!!error}
          hasSuccess={!!success}
          variant={variant}
          onFocus={handleFocus}
          onBlur={handleBlur}
          data-testid={testId}
          {...props}
        />
      </InputContainer>

      <AnimatePresence mode="wait">
        {(error || success || helperText) && (
          <HelperText
            error={!!error}
            success={!!success}
            initial={{ opacity: 0, y: -5 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -5 }}
            transition={{ duration: 0.2 }}
          >
            {error || success || helperText}
          </HelperText>
        )}
      </AnimatePresence>
    </InputWrapper>
  );
});

Input.displayName = 'Input';

export default Input;

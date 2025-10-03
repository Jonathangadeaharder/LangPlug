import React from 'react';
import styled, { keyframes, css } from 'styled-components';
import { motion } from 'framer-motion';

interface LoadingProps extends React.HTMLAttributes<HTMLDivElement> {
  size?: 'small' | 'medium' | 'large';
  variant?: 'spinner' | 'dots' | 'bars' | 'pulse' | 'netflix';
  color?: string;
  fullScreen?: boolean;
  overlay?: boolean;
  text?: string;
}

// Animations
const spin = keyframes`
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
`;

const bounce = keyframes`
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
`;

const pulse = keyframes`
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
`;

const wave = keyframes`
  0%, 40%, 100% {
    transform: scaleY(0.4);
  }
  20% {
    transform: scaleY(1);
  }
`;

const netflix = keyframes`
  0% {
    transform: scale(0) rotate(0deg);
    opacity: 1;
  }
  50% {
    transform: scale(1) rotate(180deg);
    opacity: 0.8;
  }
  100% {
    transform: scale(0) rotate(360deg);
    opacity: 1;
  }
`;

// Size configurations
const sizes = {
  small: { spinner: 20, dots: 8, bars: 16 },
  medium: { spinner: 40, dots: 12, bars: 24 },
  large: { spinner: 60, dots: 16, bars: 32 },
};

// Container styles
const LoadingContainer = styled.div.withConfig({
  shouldForwardProp: (prop) => !['fullScreen', 'overlay'].includes(prop),
})<{ fullScreen?: boolean; overlay?: boolean }>`
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: ${({ theme }) => theme.spacing.md};

  ${({ fullScreen }) => fullScreen && css`
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: ${({ theme }) => theme.zIndex.modal};
  `}

  ${({ overlay, theme }) => overlay && css`
    background: ${theme.colors.overlay};
    backdrop-filter: blur(4px);
  `}
`;

// Spinner variant
const Spinner = styled.div<{ size: number; color?: string }>`
  width: ${({ size }) => size}px;
  height: ${({ size }) => size}px;
  border: 3px solid ${({ theme }) => theme.colors.surface};
  border-top-color: ${({ color, theme }) => color || theme.colors.primary};
  border-radius: 50%;
  animation: ${spin} 0.8s linear infinite;
`;

// Dots variant
const DotsContainer = styled.div`
  display: flex;
  gap: ${({ theme }) => theme.spacing.xs};
`;

const Dot = styled.div<{ size: number; color?: string; delay: number }>`
  width: ${({ size }) => size}px;
  height: ${({ size }) => size}px;
  background: ${({ color, theme }) => color || theme.colors.primary};
  border-radius: 50%;
  animation: ${bounce} 1.4s ease-in-out ${({ delay }) => delay}s infinite both;
`;

// Bars variant
const BarsContainer = styled.div`
  display: flex;
  align-items: flex-end;
  gap: ${({ theme }) => theme.spacing.xs};
  height: 40px;
`;

const Bar = styled.div<{ size: number; color?: string; delay: number }>`
  width: ${({ size }) => size / 4}px;
  height: ${({ size }) => size}px;
  background: ${({ color, theme }) => color || theme.colors.primary};
  border-radius: ${({ theme }) => theme.radius.sm};
  animation: ${wave} 1.2s ease-in-out ${({ delay }) => delay}s infinite;
`;

// Pulse variant
const PulseRing = styled.div<{ size: number; color?: string }>`
  width: ${({ size }) => size}px;
  height: ${({ size }) => size}px;
  border-radius: 50%;
  background: ${({ color, theme }) => color || theme.colors.primary};
  animation: ${pulse} 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
`;

// Netflix variant
const NetflixContainer = styled.div`
  position: relative;
  width: 60px;
  height: 60px;
`;

const NetflixBar = styled.div<{ index: number; color?: string }>`
  position: absolute;
  width: 8px;
  height: 100%;
  background: ${({ color, theme }) => color || theme.colors.primary};
  border-radius: ${({ theme }) => theme.radius.sm};
  left: 50%;
  top: 50%;
  transform-origin: center;
  animation: ${netflix} 2s ease-in-out ${({ index }) => index * 0.15}s infinite;

  ${({ index }) => css`
    transform: translate(-50%, -50%) rotate(${index * 30}deg);
  `}
`;

// Loading text
const LoadingText = styled(motion.p)`
  font-size: ${({ theme }) => theme.typography.fontSize.sm};
  color: ${({ theme }) => theme.colors.textSecondary};
  font-weight: ${({ theme }) => theme.typography.fontWeight.medium};
  margin: 0;
`;

// Skeleton loader for content
export const Skeleton = styled.div<{
  width?: string;
  height?: string;
  radius?: string;
  animation?: boolean;
}>`
  width: ${({ width }) => width || '100%'};
  height: ${({ height }) => height || '20px'};
  background: ${({ theme }) => theme.colors.surface};
  border-radius: ${({ radius, theme }) => radius || theme.radius.md};
  position: relative;
  overflow: hidden;

  ${({ animation = true }) => animation && css`
    &::after {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: linear-gradient(
        90deg,
        transparent 0%,
        ${({ theme }) => theme.colors.surfaceHover} 50%,
        transparent 100%
      );
      animation: shimmer 2s linear infinite;
    }

    @keyframes shimmer {
      0% {
        transform: translateX(-100%);
      }
      100% {
        transform: translateX(100%);
      }
    }
  `}
`;

export const Loading: React.FC<LoadingProps> = ({
  size = 'medium',
  variant = 'spinner',
  color,
  fullScreen = false,
  overlay = false,
  text,
  ...props
}) => {
  const sizeValue = sizes[size] || sizes.medium;

  const renderLoader = () => {
    switch (variant) {
      case 'dots':
        return (
          <DotsContainer>
            {[0, 1, 2].map((i) => (
              <Dot
                key={i}
                size={sizeValue.dots}
                color={color}
                delay={i * 0.15}
              />
            ))}
          </DotsContainer>
        );

      case 'bars':
        return (
          <BarsContainer>
            {[0, 1, 2, 3, 4].map((i) => (
              <Bar
                key={i}
                size={sizeValue.bars}
                color={color}
                delay={i * 0.1}
              />
            ))}
          </BarsContainer>
        );

      case 'pulse':
        return (
          <PulseRing size={sizeValue.spinner} color={color} />
        );

      case 'netflix':
        return (
          <NetflixContainer>
            {[0, 1, 2, 3, 4, 5, 6, 7].map((i) => (
              <NetflixBar key={i} index={i} color={color} />
            ))}
          </NetflixContainer>
        );

      default:
        return (
          <Spinner size={sizeValue.spinner} color={color} />
        );
    }
  };

  return (
    <LoadingContainer fullScreen={fullScreen} overlay={overlay} {...props}>
      {renderLoader()}
      {text && (
        <LoadingText
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          {text}
        </LoadingText>
      )}
    </LoadingContainer>
  );
};

export default Loading;

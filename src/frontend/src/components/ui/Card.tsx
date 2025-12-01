import React from 'react'
import styled, { css } from 'styled-components'
import { motion } from 'framer-motion'

interface CardProps extends Omit<
  React.HTMLAttributes<HTMLDivElement>,
  'onDrag' | 'onDragStart' | 'onDragEnd' | 'onAnimationStart' | 'onAnimationEnd' | 'onAnimationIteration'
> {
  children: React.ReactNode
  variant?: 'default' | 'elevated' | 'outlined' | 'glass'
  padding?: 'none' | 'small' | 'medium' | 'large'
  hoverable?: boolean
  clickable?: boolean
  className?: string
  onClick?: () => void
}

const paddingStyles = {
  none: css`
    padding: 0;
  `,
  small: css`
    padding: ${({ theme }) => theme.spacing.sm};
  `,
  medium: css`
    padding: ${({ theme }) => theme.spacing.md};
  `,
  large: css`
    padding: ${({ theme }) => theme.spacing.lg};
  `,
}

const variantStyles = {
  default: css`
    background: ${({ theme }) => theme.colors.surface};
    border: 1px solid ${({ theme }) => theme.colors.border};
    box-shadow: ${({ theme }) => theme.shadows.sm};
  `,
  elevated: css`
    background: ${({ theme }) => theme.colors.surface};
    border: none;
    box-shadow: ${({ theme }) => theme.shadows.lg};
  `,
  outlined: css`
    background: transparent;
    border: 2px solid ${({ theme }) => theme.colors.border};
    box-shadow: none;
  `,
  glass: css`
    background: rgb(255 255 255 / 10%);
    backdrop-filter: blur(10px);
    border: 1px solid rgb(255 255 255 / 20%);
    box-shadow: ${({ theme }) => theme.shadows.lg};
  `,
}

const StyledCard = styled(motion.div).withConfig({
  shouldForwardProp: prop => !['variant', 'padding', 'hoverable', 'clickable'].includes(prop),
})<CardProps>`
  border-radius: ${({ theme }) => theme.radius.lg};
  overflow: hidden;
  position: relative;
  transition: all ${({ theme }) => theme.transitions.normal};

  ${({ variant = 'default' }) => variantStyles[variant]}
  ${({ padding = 'medium' }) => paddingStyles[padding]}

  ${({ hoverable }) =>
    hoverable &&
    css`
      &:hover {
        transform: translateY(-4px);
        box-shadow: ${({ theme }) => theme.shadows.xl};
      }
    `}

  ${({ clickable }) =>
    clickable &&
    css`
      cursor: pointer;
      user-select: none;

      &:active {
        transform: scale(0.98);
      }
    `}
`

const CardHeader = styled.div`
  padding: ${({ theme }) => theme.spacing.md};
  border-bottom: 1px solid ${({ theme }) => theme.colors.border};

  h3 {
    margin: 0;
    font-size: ${({ theme }) => theme.typography.fontSize.xl};
    font-weight: ${({ theme }) => theme.typography.fontWeight.semibold};
    color: ${({ theme }) => theme.colors.text};
  }

  p {
    margin: ${({ theme }) => theme.spacing.xs} 0 0;
    font-size: ${({ theme }) => theme.typography.fontSize.sm};
    color: ${({ theme }) => theme.colors.textSecondary};
  }
`

const CardContent = styled.div`
  padding: ${({ theme }) => theme.spacing.md};
`

const CardFooter = styled.div`
  padding: ${({ theme }) => theme.spacing.md};
  border-top: 1px solid ${({ theme }) => theme.colors.border};
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: ${({ theme }) => theme.spacing.sm};
`

const CardImage = styled.div<{ height?: string }>`
  position: relative;
  width: 100%;
  height: ${({ height }) => height || '200px'};
  overflow: hidden;

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: transform ${({ theme }) => theme.transitions.slow};
  }

  &:hover img {
    transform: scale(1.05);
  }
`

const CardBadge = styled.span<{ color?: string }>`
  position: absolute;
  top: ${({ theme }) => theme.spacing.sm};
  right: ${({ theme }) => theme.spacing.sm};
  padding: ${({ theme }) => `${theme.spacing.xs} ${theme.spacing.sm}`};
  background: ${({ color, theme }) => color || theme.colors.primary};
  color: ${({ theme }) => theme.colors.textInverse};
  border-radius: ${({ theme }) => theme.radius.full};
  font-size: ${({ theme }) => theme.typography.fontSize.xs};
  font-weight: ${({ theme }) => theme.typography.fontWeight.semibold};
  z-index: 1;
`

interface CardComponentType
  extends React.ForwardRefExoticComponent<CardProps & React.RefAttributes<HTMLDivElement>> {
  Header: React.FC<{ children: React.ReactNode }>
  Content: React.FC<{ children: React.ReactNode }>
  Footer: React.FC<{ children: React.ReactNode }>
  Image: React.FC<{ height?: string; children: React.ReactNode }>
  Badge: React.FC<{ color?: string; children: React.ReactNode }>
}

const CardComponent = React.forwardRef<HTMLDivElement, CardProps>(
  (
    {
      children,
      onClick,
      clickable,
      hoverable,
      variant = 'default',
      padding = 'medium',
      role,
      tabIndex,
      ...props
    },
    ref
  ) => {
    const cardVariants = {
      initial: { opacity: 0, y: 20 },
      animate: { opacity: 1, y: 0 },
      exit: { opacity: 0, y: -20 },
    }

    const isClickable = Boolean(onClick || clickable)
    const shouldHover = hoverable || isClickable

    return (
      <StyledCard
        ref={ref}
        onClick={onClick}
        variants={cardVariants}
        initial="initial"
        animate="animate"
        exit="exit"
        transition={{ duration: 0.3 }}
        variant={variant}
        padding={padding}
        hoverable={shouldHover}
        clickable={isClickable}
        role={isClickable ? role || 'button' : role}
        tabIndex={isClickable ? (tabIndex ?? 0) : tabIndex}
        {...props}
      >
        {children}
      </StyledCard>
    )
  }
) as CardComponentType

CardComponent.displayName = 'Card'

// Export the main component
export const Card = CardComponent

// Export sub-components with proper typing
Card.Header = CardHeader
Card.Content = CardContent
Card.Footer = CardFooter
Card.Image = CardImage
Card.Badge = CardBadge

// Export sub-components as named exports for testing
export { CardHeader, CardContent, CardFooter, CardImage, CardBadge }

export default Card

import React from 'react';
import { vi } from 'vitest';

// Create a proxy-based motion mock that handles any HTML element
const createMotionComponent = (element: string) => {
  return React.forwardRef((props: any, ref: any) => {
    const {
      initial,
      animate,
      exit,
      whileHover,
      whileTap,
      whileFocus,
      whileDrag,
      whileInView,
      variants,
      transition,
      drag,
      dragConstraints,
      dragElastic,
      dragMomentum,
      dragTransition,
      dragDirectionLock,
      dragPropagation,
      onDrag,
      onDragStart,
      onDragEnd,
      layout,
      layoutId,
      style,
      onAnimationComplete,
      onAnimationStart,
      ...rest
    } = props;

    return React.createElement(element, { ...rest, ref }, props.children);
  });
};

export const motion = new Proxy({} as any, {
  get: (_target, key: string) => {
    return createMotionComponent(key);
  }
});

export const AnimatePresence = ({ children }: any) => children;
export const AnimateSharedLayout = ({ children }: any) => children;
export const LazyMotion = ({ children }: any) => children;
export const MotionConfig = ({ children }: any) => children;

export const useAnimation = () => ({
  start: vi.fn(),
  set: vi.fn(),
  stop: vi.fn(),
  mount: vi.fn(),
});

export const useAnimationControls = () => ({
  start: vi.fn(),
  set: vi.fn(),
  stop: vi.fn(),
  mount: vi.fn(),
});

export const useMotionValue = (initial: any) => ({
  get: () => initial,
  set: vi.fn(),
  onChange: vi.fn(),
  clearListeners: vi.fn(),
  destroy: vi.fn(),
});

export const useTransform = () => ({
  get: vi.fn(),
  set: vi.fn(),
  onChange: vi.fn(),
  clearListeners: vi.fn(),
});

export const useSpring = () => ({
  get: vi.fn(),
  set: vi.fn(),
  onChange: vi.fn(),
  clearListeners: vi.fn(),
});

export const useVelocity = () => ({
  get: vi.fn(),
  set: vi.fn(),
  onChange: vi.fn(),
  clearListeners: vi.fn(),
});

export const useDragControls = () => ({
  start: vi.fn(),
});

export const useScroll = () => ({
  scrollX: { get: () => 0 },
  scrollY: { get: () => 0 },
  scrollXProgress: { get: () => 0 },
  scrollYProgress: { get: () => 0 },
});

export const useInView = () => false;
export const usePresence = () => [true, vi.fn()];
export const useReducedMotion = () => false;

// Shorthand
export const m = motion;

// Feature detection
export const domAnimation = {};
export const domMax = {};

export default {
  motion,
  AnimatePresence,
  AnimateSharedLayout,
  LazyMotion,
  MotionConfig,
  useAnimation,
  useAnimationControls,
  useMotionValue,
  useTransform,
  useSpring,
  useVelocity,
  useDragControls,
  useScroll,
  useInView,
  usePresence,
  useReducedMotion,
  m,
  domAnimation,
  domMax,
};

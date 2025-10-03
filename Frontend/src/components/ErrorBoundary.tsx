import React, { Component, ErrorInfo, ReactNode } from 'react';
import styled from 'styled-components';

const ErrorContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 2rem;
  text-align: center;
`;

const ErrorTitle = styled.h1`
  font-size: 3rem;
  margin-bottom: 1rem;
  font-weight: bold;
`;

const ErrorMessage = styled.p`
  font-size: 1.25rem;
  margin-bottom: 2rem;
  max-width: 600px;
  opacity: 0.9;
`;

const ErrorButton = styled.button`
  background: rgba(255, 255, 255, 0.2);
  border: 2px solid rgba(255, 255, 255, 0.3);
  color: white;
  padding: 1rem 2rem;
  border-radius: 50px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;

  &:hover {
    background: rgba(255, 255, 255, 0.3);
    border-color: rgba(255, 255, 255, 0.5);
    transform: translateY(-2px);
  }

  &:active {
    transform: translateY(0);
  }
`;

interface State {
  hasError: boolean;
  error?: Error;
}

interface Props {
  children: ReactNode;
  sectionName?: string;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <ErrorContainer>
          <ErrorTitle>😵</ErrorTitle>
          <ErrorTitle>Oops!</ErrorTitle>
          <ErrorMessage>
            {this.props.sectionName || 'Something'} encountered an unexpected error.
            Don't worry, it happens to the best of us!
          </ErrorMessage>
          <ErrorButton
            onClick={() => window.location.reload()}
          >
            🔄 Refresh Page
          </ErrorButton>
        </ErrorContainer>
      );
    }

    return this.props.children;
  }
}

export { ErrorBoundary };

// Hook for imperatively throwing errors to the nearest error boundary
export function useErrorHandler() {
  const [error, setError] = React.useState<Error | null>(null);

  React.useEffect(() => {
    if (error) {
      throw error;
    }
  }, [error]);

  return setError;
}

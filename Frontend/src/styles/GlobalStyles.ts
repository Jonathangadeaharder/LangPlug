import styled, { createGlobalStyle } from 'styled-components'

export const GlobalStyle = createGlobalStyle`
  * {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }

  body {
    font-family: 'Helvetica Neue', Arial, sans-serif;
    background-color: #141414;
    color: #ffffff;
    overflow-x: hidden;
  }

  button {
    cursor: pointer;
    border: none;
    outline: none;
    font-family: inherit;
  }

  input {
    outline: none;
    font-family: inherit;
  }

  a {
    text-decoration: none;
    color: inherit;
  }

  .loading-spinner {
    width: 40px;
    height: 40px;
    border: 3px solid #333;
    border-top: 3px solid #e50914;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  .fade-in {
    animation: fadeIn 0.5s ease-in;
  }

  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }
`

export const Container = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
`

export const NetflixButton = styled.button<{ variant?: 'primary' | 'secondary' }>`
  padding: 12px 24px;
  border-radius: 4px;
  font-weight: 600;
  font-size: 16px;
  transition: all 0.3s ease;

  ${props => props.variant === 'secondary' ? `
    background-color: rgba(109, 109, 110, 0.7);
    color: white;

    &:hover {
      background-color: rgba(109, 109, 110, 0.9);
    }
  ` : `
    background-color: #e50914;
    color: white;

    &:hover {
      background-color: #f40612;
    }
  `}

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
`

export const Card = styled.div`
  background: rgba(0, 0, 0, 0.8);
  border-radius: 8px;
  padding: 24px;
  margin: 16px 0;
  transition: transform 0.3s ease;

  &:hover {
    transform: translateY(-4px);
  }
`

export const Grid = styled.div<{ columns?: number }>`
  display: grid;
  grid-template-columns: repeat(${props => props.columns || 3}, 1fr);
  gap: 20px;
  padding: 20px 0;

  @media (max-width: 768px) {
    grid-template-columns: repeat(2, 1fr);
  }

  @media (max-width: 480px) {
    grid-template-columns: 1fr;
  }
`

export const FlexCenter = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
`

export const ErrorMessage = styled.div`
  color: #e87c03;
  background-color: rgba(232, 124, 3, 0.1);
  padding: 12px 16px;
  border-radius: 4px;
  border-left: 4px solid #e87c03;
  margin: 16px 0;
`

export const SuccessMessage = styled.div`
  color: #46d369;
  background-color: rgba(70, 211, 105, 0.1);
  padding: 12px 16px;
  border-radius: 4px;
  border-left: 4px solid #46d369;
  margin: 16px 0;
`

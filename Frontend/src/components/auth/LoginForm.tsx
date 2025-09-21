import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import styled from 'styled-components'
import { toast } from 'react-hot-toast'
import { useAuthStore } from '@/store/useAuthStore'
import { NetflixButton, ErrorMessage } from '@/styles/GlobalStyles'
import { handleApiError } from '@/services/api'

const LoginContainer = styled.div`
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(
    rgba(0, 0, 0, 0.7),
    rgba(0, 0, 0, 0.7)
  );
  background-size: cover;
  background-position: center;
`

const LoginCard = styled.div`
  background: rgba(0, 0, 0, 0.85);
  padding: 48px 68px;
  border-radius: 4px;
  width: 100%;
  max-width: 450px;
  min-height: 500px;
`

const Logo = styled.h1`
  color: #e50914;
  font-size: 32px;
  margin-bottom: 28px;
  text-align: center;
  font-weight: bold;
`

const Title = styled.h2`
  color: white;
  font-size: 32px;
  font-weight: 500;
  margin-bottom: 28px;
`

const Input = styled.input`
  width: 100%;
  padding: 16px 20px;
  margin-bottom: 16px;
  background: #333;
  border: none;
  border-radius: 4px;
  color: white;
  font-size: 16px;
  
  &::placeholder {
    color: #8c8c8c;
  }
  
  &:focus {
    background: #454545;
  }
`

const LoginButton = styled(NetflixButton)`
  width: 100%;
  padding: 16px;
  margin: 24px 0 12px;
  font-size: 16px;
`

const SignUpText = styled.p`
  color: #737373;
  margin-top: 16px;
  
  a {
    color: white;
    text-decoration: none;
    
    &:hover {
      text-decoration: underline;
    }
  }
`

const RememberMe = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 16px 0;
  
  label {
    display: flex;
    align-items: center;
    color: #b3b3b3;
    cursor: pointer;
    
    input {
      margin-right: 8px;
    }
  }
  
  a {
    color: #b3b3b3;
    text-decoration: none;
    font-size: 13px;
    
    &:hover {
      text-decoration: underline;
    }
  }
`

export const LoginForm: React.FC = () => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [rememberMe, setRememberMe] = useState(false)
  const [error, setError] = useState('')
  
  const { login, isLoading, error: authError, isAuthenticated } = useAuthStore()
  const navigate = useNavigate()

  // Navigate to dashboard if already authenticated
  React.useEffect(() => {
    if (isAuthenticated) {
      navigate('/')
    }
  }, [isAuthenticated, navigate])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (!email.trim() || !password.trim()) {
      setError('Please enter both email and password')
      return
    }

    if (!email.includes('@')) {
      setError('Please enter a valid email address')
      return
    }

    try {
      await login(email, password)
      toast.success('Welcome to LangPlug!')
      navigate('/')
    } catch (error) {
      const errorMessage = authError || 'Invalid email or password'
      setError(errorMessage)
    }
  }

  return (
    <LoginContainer>
      <LoginCard>
        <Logo>LangPlug</Logo>
        <Title>Sign In</Title>
        
        <form onSubmit={handleSubmit}>
          <Input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={isLoading}
            data-testid="login-email-input"
          />
          
          <Input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={isLoading}
            data-testid="login-password-input"
          />
          
          {error && <ErrorMessage data-testid="login-error">{error}</ErrorMessage>}
          
          <LoginButton 
            type="submit" 
            disabled={isLoading}
            data-testid="login-submit-button"
          >
            {isLoading ? 'Signing In...' : 'Sign In'}
          </LoginButton>
          
          <RememberMe>
            <label>
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
              />
              Remember me
            </label>
            <a href="/forgot-password">Need help?</a>
          </RememberMe>
        </form>
        
        <SignUpText>
          New to LangPlug? <a href="/register">Sign up now</a>.
        </SignUpText>
      </LoginCard>
    </LoginContainer>
  )
}
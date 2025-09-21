import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import styled from 'styled-components'
import { toast } from 'react-hot-toast'
import { useAuthStore } from '@/store/useAuthStore'
import { NetflixButton, ErrorMessage, SuccessMessage } from '@/styles/GlobalStyles'
import { handleApiError } from '@/services/api'

const RegisterContainer = styled.div`
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

const RegisterCard = styled.div`
  background: rgba(0, 0, 0, 0.85);
  padding: 48px 68px;
  border-radius: 4px;
  width: 100%;
  max-width: 450px;
  min-height: 600px;
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

const RegisterButton = styled(NetflixButton)`
  width: 100%;
  padding: 16px;
  margin: 24px 0 12px;
  font-size: 16px;
`

const SignInText = styled.p`
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

const PasswordRequirements = styled.div`
  color: #b3b3b3;
  font-size: 13px;
  margin: 8px 0;
  
  ul {
    margin: 4px 0;
    padding-left: 20px;
  }
  
  li {
    margin: 2px 0;
  }
`

export const RegisterForm: React.FC = () => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [name, setName] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  
  const { register, isLoading, error: authError } = useAuthStore()
  const navigate = useNavigate()

  const validateForm = () => {
    if (!email.trim()) {
      return 'Email is required'
    }
    if (!email.includes('@')) {
      return 'Please enter a valid email address'
    }
    if (!name.trim()) {
      return 'Name is required'
    }
    if (name.length < 2) {
      return 'Name must be at least 2 characters long'
    }
    if (!password) {
      return 'Password is required'
    }
    if (password.length < 6) {
      return 'Password must be at least 6 characters long'
    }
    if (password !== confirmPassword) {
      return 'Passwords do not match'
    }
    return null
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccess(false)

    const validationError = validateForm()
    if (validationError) {
      setError(validationError)
      return
    }

    try {
      await register(email, password, name)
      setSuccess(true)
      toast.success('Account created successfully! Redirecting to dashboard...')
      setTimeout(() => navigate('/'), 2000)
    } catch (error) {
      const errorMessage = authError || 'Failed to create account. Please try again.'
      setError(errorMessage)
    }
  }

  const isPasswordValid = password.length >= 6
  const doPasswordsMatch = password === confirmPassword && confirmPassword.length > 0

  return (
    <RegisterContainer>
      <RegisterCard>
        <Logo>LangPlug</Logo>
        <Title>Sign Up</Title>
        
        <form onSubmit={handleSubmit}>
          <Input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={isLoading}
            data-testid="register-email-input"
          />
          
          <Input
            type="text"
            placeholder="Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            disabled={isLoading}
            data-testid="register-name-input"
          />
          
          <Input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={isLoading}
            data-testid="register-password-input"
          />
          
          <Input
            type="password"
            placeholder="Confirm Password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            disabled={isLoading}
            data-testid="register-confirm-password-input"
          />
          
          <PasswordRequirements>
            Password requirements:
            <ul>
              <li style={{ color: isPasswordValid ? '#46d369' : '#b3b3b3' }}>
                At least 6 characters
              </li>
              <li style={{ color: doPasswordsMatch ? '#46d369' : '#b3b3b3' }}>
                Passwords must match
              </li>
            </ul>
          </PasswordRequirements>
          
          {error && <ErrorMessage>{error}</ErrorMessage>}
          {success && <SuccessMessage>Account created successfully! Redirecting to login...</SuccessMessage>}
          
          <RegisterButton 
            type="submit" 
            disabled={isLoading || success}
            data-testid="register-submit-button"
          >
            {isLoading ? 'Creating Account...' : 'Sign Up'}
          </RegisterButton>
        </form>
        
        <SignInText>
          Already have an account? <a href="/login">Sign in now</a>.
        </SignInText>
      </RegisterCard>
    </RegisterContainer>
  )
}
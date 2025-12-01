import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import styled from 'styled-components'
import { toast } from 'react-hot-toast'
import { z } from 'zod'
import { useAuthStore } from '@/store/useAuthStore'
import { NetflixButton, ErrorMessage, SuccessMessage } from '@/styles/GlobalStyles'
import { schemas } from '@/schemas/api-schemas'
import { zodErrorToFormErrors } from '@/schemas/helpers'
import { formatApiError } from '@/utils/error-formatter'

const RegisterContainer = styled.div`
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(rgb(0 0 0 / 70%), rgb(0 0 0 / 70%));
  background-size: cover;
  background-position: center;
`

const RegisterCard = styled.div`
  background: rgb(0 0 0 / 85%);
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

// Extended schema with frontend-specific validations
const RegisterFormSchema = schemas.UserCreate.extend({
  email: z.string().superRefine((val, ctx) => {
    if (val.trim().length === 0) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Email is required',
      })
      return
    }
    if (!z.string().email().safeParse(val).success) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Invalid email format',
      })
    }
  }),
  username: z
    .string()
    .min(3, 'Username must be at least 3 characters long')
    .max(50, 'Username must be no more than 50 characters long')
    .regex(
      /^[a-zA-Z0-9_-]+$/,
      'Username must contain only alphanumeric characters, underscores, and hyphens'
    ),
  password: z.string().min(8, 'Password must be at least 8 characters long'),
  confirmPassword: z.string(),
}).refine(
  (data: { password: string; confirmPassword: string }) => data.password === data.confirmPassword,
  {
    message: 'Passwords do not match',
    path: ['confirmPassword'],
  }
)

export const RegisterForm: React.FC = () => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [username, setUsername] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  const { register, isLoading, error: _authError } = useAuthStore()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccess(false)

    // Validate form data with Zod schema
    const formData = {
      email,
      username,
      password,
      confirmPassword,
    }

    const result = RegisterFormSchema.safeParse(formData)

    if (!result.success) {
      const formErrors = zodErrorToFormErrors(result.error)
      // Display first error message
      const firstError = Object.values(formErrors)[0]
      setError(firstError)
      return
    }

    try {
      await register(email, password, username)
      setSuccess(true)
      toast.success('Account created successfully!')
      // Navigate immediately - no artificial delay
      navigate('/videos')
    } catch (error: unknown) {
      // Handle validation errors from backend using standardized formatter
      // This correctly handles both Pydantic/FastAPI validation errors (422)
      // and LangPlug custom error format ({ error: { details: [...] } })
      // Don't use error.message directly as it's often just "Validation Error"
      const errorMessage = formatApiError(error, 'Failed to create account. Please try again.')
      setError(errorMessage)
    }
  }

  const isPasswordValid = password.length >= 8
  const doPasswordsMatch = password === confirmPassword && confirmPassword.length > 0

  return (
    <RegisterContainer>
      <RegisterCard>
        <Logo>LangPlug</Logo>
        <Title>Sign Up</Title>

        <form onSubmit={handleSubmit}>
          <Input
            type="email"
            name="email"
            placeholder="Email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            disabled={isLoading}
            data-testid="email-input"
          />

          <Input
            type="text"
            name="username"
            placeholder="Username"
            value={username}
            onChange={e => setUsername(e.target.value)}
            disabled={isLoading}
            data-testid="username-input"
          />

          <Input
            type="password"
            name="password"
            placeholder="Password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            disabled={isLoading}
            data-testid="password-input"
          />

          <Input
            type="password"
            name="confirm_password"
            placeholder="Confirm Password"
            value={confirmPassword}
            onChange={e => setConfirmPassword(e.target.value)}
            disabled={isLoading}
            data-testid="confirm-password-input"
          />

          <PasswordRequirements>
            Password requirements:
            <ul>
              <li style={{ color: isPasswordValid ? '#46d369' : '#b3b3b3' }}>
                At least 12 characters
              </li>
              <li style={{ color: doPasswordsMatch ? '#46d369' : '#b3b3b3' }}>
                Passwords must match
              </li>
            </ul>
          </PasswordRequirements>

          {error && <ErrorMessage>{error}</ErrorMessage>}
          {success && (
            <SuccessMessage>Account created successfully! Redirecting to login...</SuccessMessage>
          )}

          <RegisterButton
            type="submit"
            disabled={isLoading || success}
            data-testid="register-submit"
          >
            {isLoading ? 'Creating Account...' : 'Sign Up'}
          </RegisterButton>
        </form>

        <SignInText>
          Already have an account?{' '}
          <Link to="/login" data-testid="login-link">
            Sign in now
          </Link>
          .
        </SignInText>
      </RegisterCard>
    </RegisterContainer>
  )
}

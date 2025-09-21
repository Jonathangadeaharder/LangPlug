/**
 * FastAPI-Users response types that match the actual OpenAPI schema
 */

// BearerResponse schema from FastAPI-Users login endpoint
export interface BearerResponse {
  access_token: string
  token_type: string
}

// UserRead schema from FastAPI-Users (register, me endpoints)
export interface UserRead {
  id: string // UUID format
  email: string
  is_active: boolean
  is_superuser: boolean
  is_verified: boolean
  username: string
  created_at: string // ISO date-time format
  last_login: string | null // ISO date-time format or null
}

// Custom AuthResponse that matches our frontend expectations
export interface AuthResponse {
  token: string
  user: {
    id: string
    email: string
    name: string // Maps to UserRead.username
  }
  expires_at: string
}

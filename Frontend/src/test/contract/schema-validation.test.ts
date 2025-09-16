import { describe, it, expect } from 'vitest';
import {
  validateUserResponse,
  validateAuthResponse,
  validateRegisterRequest,
  validateLoginRequest,
  SchemaValidationError,
  UserResponseSchema,
  AuthResponseSchema,
  RegisterRequestSchema,
  LoginRequestSchema,
} from '../../utils/schema-validation';

describe('Schema Validation Tests', () => {
  describe('UserResponse Validation', () => {
    it('should validate correct UserResponse', () => {
      const validUser = {
        id: 1,
        username: 'testuser',
        is_admin: false,
        is_superuser: false,
        is_active: true,
        created_at: '2025-01-01T00:00:00Z',
      };

      expect(() => validateUserResponse(validUser)).not.toThrow();
      const result = validateUserResponse(validUser);
      expect(result).toEqual(validUser);
    });

    it('should validate UserResponse with last_login', () => {
      const validUser = {
        id: 1,
        username: 'testuser',
        is_admin: false,
        is_superuser: false,
        is_active: true,
        created_at: '2025-01-01T00:00:00Z',
        last_login: '2025-01-02T00:00:00Z',
      };

      expect(() => validateUserResponse(validUser)).not.toThrow();
    });

    it('should reject invalid UserResponse - missing required fields', () => {
      const invalidUser = {
        id: 1,
        username: 'testuser',
        // missing is_superuser, is_active, created_at
      };

      expect(() => validateUserResponse(invalidUser)).toThrow(SchemaValidationError);
    });

    it('should reject invalid UserResponse - wrong types', () => {
      const invalidUser = {
        id: '1', // should be number
        username: 'testuser',
        is_superuser: 'false', // should be boolean
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
      };

      expect(() => validateUserResponse(invalidUser)).toThrow(SchemaValidationError);
    });
  });

  describe('AuthResponse Validation', () => {
    it('should validate correct AuthResponse', () => {
      const validAuth = {
        token: 'jwt-token-123',
        user: {
          id: 1,
          username: 'testuser',
          is_admin: false,
          is_superuser: false,
          is_active: true,
          created_at: '2025-01-01T00:00:00Z',
        },
        expires_at: '2025-01-02T00:00:00Z',
      };

      expect(() => validateAuthResponse(validAuth)).not.toThrow();
      const result = validateAuthResponse(validAuth);
      expect(result).toEqual(validAuth);
    });

    it('should reject invalid AuthResponse - missing token', () => {
      const invalidAuth = {
        user: {
          id: 1,
          username: 'testuser',
          is_superuser: false,
          is_active: true,
          created_at: '2024-01-01T00:00:00Z',
        },
        expires_at: '2024-01-02T00:00:00Z',
      };

      expect(() => validateAuthResponse(invalidAuth)).toThrow(SchemaValidationError);
    });

    it('should reject invalid AuthResponse - invalid user object', () => {
      const invalidAuth = {
        token: 'jwt-token-string',
        user: {
          id: 1,
          username: 'testuser',
          // missing required user fields
        },
        expires_at: '2024-01-02T00:00:00Z',
      };

      expect(() => validateAuthResponse(invalidAuth)).toThrow(SchemaValidationError);
    });
  });

  describe('RegisterRequest Validation', () => {
    it('should validate correct RegisterRequest', () => {
      const validRegister = {
        username: 'testuser',
        password: 'password123',
      };

      expect(() => validateRegisterRequest(validRegister)).not.toThrow();
      const result = validateRegisterRequest(validRegister);
      expect(result).toEqual(validRegister);
    });

    it('should reject RegisterRequest with short password', () => {
      const invalidRegister = {
        username: 'testuser',
        password: '123', // too short
      };

      expect(() => validateRegisterRequest(invalidRegister)).toThrow(SchemaValidationError);
    });

    it('should reject RegisterRequest with empty username', () => {
      const invalidRegister = {
        username: '', // empty
        password: 'password123',
      };

      expect(() => validateRegisterRequest(invalidRegister)).toThrow(SchemaValidationError);
    });

    it('should reject RegisterRequest with missing fields', () => {
      const invalidRegister = {
        username: 'testuser',
        // missing password
      };

      expect(() => validateRegisterRequest(invalidRegister)).toThrow(SchemaValidationError);
    });
  });

  describe('LoginRequest Validation', () => {
    it('should validate correct LoginRequest', () => {
      const validLogin = {
        username: 'testuser',
        password: 'password123',
      };

      expect(() => validateLoginRequest(validLogin)).not.toThrow();
      const result = validateLoginRequest(validLogin);
      expect(result).toEqual(validLogin);
    });

    it('should reject LoginRequest with empty username', () => {
      const invalidLogin = {
        username: '', // empty
        password: 'password123',
      };

      expect(() => validateLoginRequest(invalidLogin)).toThrow(SchemaValidationError);
    });

    it('should reject LoginRequest with empty password', () => {
      const invalidLogin = {
        username: 'testuser',
        password: '', // empty
      };

      expect(() => validateLoginRequest(invalidLogin)).toThrow(SchemaValidationError);
    });
  });

  describe('Schema Error Handling', () => {
    it('should provide detailed error information', () => {
      const invalidData = {
        id: 'not-a-number',
        username: 123, // wrong type
        is_superuser: 'not-boolean',
      };

      try {
        validateUserResponse(invalidData);
        expect.fail('Should have thrown SchemaValidationError');
      } catch (error) {
        expect(error).toBeInstanceOf(SchemaValidationError);
        expect((error as SchemaValidationError).issues).toBeDefined();
        expect((error as SchemaValidationError).issues.length).toBeGreaterThan(0);
      }
    });

    it('should include context in error message', () => {
      try {
        validateUserResponse({});
        expect.fail('Should have thrown SchemaValidationError');
      } catch (error) {
        expect(error).toBeInstanceOf(SchemaValidationError);
        expect((error as SchemaValidationError).message).toContain('UserResponse');
      }
    });
  });

  describe('Direct Schema Usage', () => {
    it('should work with direct schema parsing', () => {
      const validUser = {
        id: 1,
        username: 'testuser',
        is_admin: false,
        is_superuser: false,
        is_active: true,
        created_at: '2025-01-01T00:00:00Z',
      };

      const result = UserResponseSchema.parse(validUser);
      expect(result).toEqual(validUser);
    });

    it('should provide safe parsing option', () => {
      const invalidUser = { id: 'invalid' };
      
      const result = UserResponseSchema.safeParse(invalidUser);
      expect(result.success).toBe(false);
      
      if (!result.success) {
        expect(result.error.issues).toBeDefined();
      }
    });
  });
});
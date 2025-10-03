/**
 * Authentication Contract Tests
 * Validates API contracts between frontend and backend for auth endpoints
 */

import { ContractValidator } from '../infrastructure/contract-validator';
import { TestDataManager } from '../infrastructure/test-data-manager';
import axios from 'axios';

describe('Authentication API Contract', () => {
  let contractValidator: ContractValidator;
  let testDataManager: TestDataManager;
  let apiClient: any;
  const API_BASE_URL = process.env.BACKEND_URL || 'http://localhost:8000';

  beforeAll(async () => {
    // Initialize contract validator with OpenAPI spec
    contractValidator = new ContractValidator();
    await contractValidator.loadSpec('../../openapi_spec.json');

    // Initialize test data manager
    testDataManager = new TestDataManager();

    // Create axios client with contract validation
    apiClient = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Apply contract validation interceptors
    contractValidator.createAxiosInterceptor(apiClient);
  });

  afterEach(() => {
    // Clear contract violations after each test
    contractValidator.clearResults();
  });

  describe('POST /api/auth/register', () => {
    it('should validate successful registration contract', async () => {
      // Generate unique test user
      const userData = testDataManager.generateUser();

      const requestData = {
        username: userData.username,
        email: userData.email,
        password: userData.password,
      };

      // Validate request contract
      const requestValidation = contractValidator.validateRequest(
        'POST',
        '/api/auth/register',
        requestData
      );

      expect(requestValidation.valid).toBe(true);
      expect(requestValidation.errors).toBeUndefined();

      // Make actual API call
      const response = await apiClient.post('/api/auth/register', requestData);

      // Validate response contract
      const responseValidation = contractValidator.validateResponse(
        'POST',
        '/api/auth/register',
        response.status,
        response.data
      );

      expect(responseValidation.valid).toBe(true);
      expect(response.status).toBe(201);
      expect(response.data).toHaveProperty('id');
      expect(response.data).toHaveProperty('email', userData.email);
    });

    it('should validate duplicate email error contract', async () => {
      const userData = testDataManager.generateUser();

      // Register user first
      await apiClient.post('/api/auth/register', {
        username: userData.username,
        email: userData.email,
        password: userData.password,
      });

      // Try to register with same email
      try {
        await apiClient.post('/api/auth/register', {
          username: 'different_user',
          email: userData.email,
          password: userData.password,
        });
        fail('Should have thrown an error');
      } catch (error: any) {
        // Validate error response contract
        const responseValidation = contractValidator.validateResponse(
          'POST',
          '/api/auth/register',
          error.response.status,
          error.response.data
        );

        expect(responseValidation.valid).toBe(true);
        expect(error.response.status).toBe(400);
        expect(error.response.data).toHaveProperty('detail');
      }
    });

    it('should reject invalid request data', () => {
      const invalidData = {
        username: 123, // Should be string
        email: 'not-an-email', // Invalid email format
        password: 'short', // Too short
      };

      const validation = contractValidator.validateRequest(
        'POST',
        '/api/auth/register',
        invalidData
      );

      expect(validation.valid).toBe(false);
      expect(validation.errors).toBeDefined();
      expect(validation.errors!.length).toBeGreaterThan(0);
    });
  });

  describe('POST /api/auth/login', () => {
    let testUser: any;

    beforeAll(async () => {
      // Create a test user for login tests
      testUser = testDataManager.generateUser();
      await apiClient.post('/api/auth/register', {
        username: testUser.username,
        email: testUser.email,
        password: testUser.password,
      });
    });

    it('should validate successful login contract', async () => {
      const loginData = {
        username: testUser.email, // FastAPI-Users uses email as username
        password: testUser.password,
      };

      // Validate request contract
      const requestValidation = contractValidator.validateRequest(
        'POST',
        '/api/auth/login',
        loginData
      );

      expect(requestValidation.valid).toBe(true);

      // Make actual API call
      const response = await apiClient.post('/api/auth/login', loginData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });

      // Validate response contract
      const responseValidation = contractValidator.validateResponse(
        'POST',
        '/api/auth/login',
        response.status,
        response.data
      );

      expect(responseValidation.valid).toBe(true);
      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('access_token');
      expect(response.data).toHaveProperty('token_type', 'bearer');
    });

    it('should validate invalid credentials error contract', async () => {
      const loginData = {
        username: testUser.email,
        password: 'wrong_password',
      };

      try {
        await apiClient.post('/api/auth/login', loginData, {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
        });
        fail('Should have thrown an error');
      } catch (error: any) {
        // Validate error response contract
        const responseValidation = contractValidator.validateResponse(
          'POST',
          '/api/auth/login',
          error.response.status,
          error.response.data
        );

        expect(responseValidation.valid).toBe(true);
        expect(error.response.status).toBe(400);
      }
    });
  });

  describe('GET /api/auth/me', () => {
    let authToken: string;

    beforeAll(async () => {
      // Create and login a test user
      const testUser = testDataManager.generateUser();
      await apiClient.post('/api/auth/register', {
        username: testUser.username,
        email: testUser.email,
        password: testUser.password,
      });

      const loginResponse = await apiClient.post('/api/auth/login', {
        username: testUser.email,
        password: testUser.password,
      }, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });

      authToken = loginResponse.data.access_token;
    });

    it('should validate authenticated user info contract', async () => {
      // Make authenticated request
      const response = await apiClient.get('/api/auth/me', {
        headers: {
          'Authorization': `Bearer ${authToken}`,
        },
      });

      // Validate response contract
      const responseValidation = contractValidator.validateResponse(
        'GET',
        '/api/auth/me',
        response.status,
        response.data
      );

      expect(responseValidation.valid).toBe(true);
      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('id');
      expect(response.data).toHaveProperty('email');
      expect(response.data).toHaveProperty('is_active');
      expect(response.data).toHaveProperty('is_verified');
    });

    it('should validate unauthorized error contract', async () => {
      try {
        await apiClient.get('/api/auth/me');
        fail('Should have thrown an error');
      } catch (error: any) {
        // Validate error response contract
        const responseValidation = contractValidator.validateResponse(
          'GET',
          '/api/auth/me',
          error.response.status,
          error.response.data
        );

        expect(responseValidation.valid).toBe(true);
        expect(error.response.status).toBe(401);
      }
    });
  });

  describe('Contract Validation Workflow', () => {
    it('should validate complete authentication workflow', async () => {
      const userData = testDataManager.generateUser();

      // Define workflow steps
      const workflow = await contractValidator.validateWorkflow(
        'Complete Authentication Flow',
        [
          {
            method: 'POST',
            path: '/api/auth/register',
            data: {
              username: userData.username,
              email: userData.email,
              password: userData.password,
            },
            expectedStatus: 201,
          },
          {
            method: 'POST',
            path: '/api/auth/login',
            data: {
              username: userData.email,
              password: userData.password,
            },
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded',
            },
            expectedStatus: 200,
          },
          {
            method: 'GET',
            path: '/api/auth/me',
            headers: {
              'Authorization': 'Bearer <token>',
            },
            expectedStatus: 200,
          },
          {
            method: 'POST',
            path: '/api/auth/logout',
            headers: {
              'Authorization': 'Bearer <token>',
            },
            expectedStatus: 204,
          },
        ]
      );

      expect(workflow.valid).toBe(true);
      expect(workflow.steps.every(step => step.valid)).toBe(true);
    });
  });

  afterAll(() => {
    // Generate contract test report
    const report = contractValidator.generateReport();
    console.log('\n📊 Contract Test Summary:');
    console.log(`   Total API calls: ${report.total}`);
    console.log(`   ✅ Passed: ${report.passed}`);
    console.log(`   ❌ Failed: ${report.failed}`);

    if (report.violations.length > 0) {
      console.log('\n⚠️  Contract Violations:');
      report.violations.forEach(violation => {
        console.log(`   • ${violation.endpoint}: ${violation.response?.errors?.[0]?.message}`);
      });
    }
  });
});

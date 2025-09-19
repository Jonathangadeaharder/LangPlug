# Contract Testing Implementation

This document describes the comprehensive contract testing implementation for the LangPlug application, covering frontend-backend API contract validation, schema validation, and automated testing pipelines.

## Overview

Contract testing ensures that the frontend and backend maintain compatible API contracts, preventing integration issues and enabling confident independent development and deployment.

## Policy Reference

All contract updates must follow the governance defined in `CONTRACTDRIVENDEVELOPMENT.MD` and the
operational guidance in `CONTRIBUTING.md`. Use the review checklist (`docs/review_checklists.md`) to
confirm contract approvals, versioning, and automated test coverage before merging changes.

## Architecture

### Frontend Contract Testing

#### 1. Schema Validation (`Frontend/src/utils/schema-validation.ts`)
- **Purpose**: Runtime validation of API responses using Zod schemas
- **Features**:
  - Type-safe schema definitions for all API models
  - Validation functions for requests and responses
  - Error handling with detailed validation messages
  - TypeScript integration for compile-time safety

#### 2. Validated API Client (`Frontend/src/client/validated-client.ts`)
- **Purpose**: API client wrapper with built-in contract validation
- **Features**:
  - Automatic request/response validation
  - Environment-specific configuration
  - Custom error types for contract violations
  - Hook-style API functions for React integration
  - Retry logic and timeout handling

#### 3. Environment Configuration (`Frontend/src/config/api-config.ts`)
- **Purpose**: Environment-specific API client configuration
- **Features**:
  - Multi-environment support (dev, staging, prod, test)
  - Configurable timeouts and retry policies
  - Request tracing and logging
  - API versioning headers

### Backend Contract Support

#### 1. API Versioning (`Backend/core/versioning.py`)
- **Purpose**: Comprehensive API versioning system
- **Features**:
  - Multiple versioning strategies (header, URL, query param)
  - Version compatibility checking
  - Deprecation warnings and sunset dates
  - Contract transformation between versions
  - Breaking change documentation

## Test Structure

### Frontend Contract Tests

#### Auth Contract Tests (`Frontend/src/test/contract/auth.contract.test.ts`)
```typescript
// Tests API client structure and method signatures
describe('Auth API Contract', () => {
  it('should have correct register endpoint structure', () => {
    // Validates request/response structure
  });
  
  it('should have correct login endpoint structure', () => {
    // Validates authentication flow
  });
});
```

#### Schema Validation Tests (`Frontend/src/test/contract/schema-validation.test.ts`)
```typescript
// Tests runtime schema validation
describe('Schema Validation', () => {
  it('should validate UserResponse correctly', () => {
    // Tests valid and invalid response structures
  });
  
  it('should handle validation errors gracefully', () => {
    // Tests error handling and messages
  });
});
```

#### Validated Client Tests (`Frontend/src/test/contract/validated-client.test.ts`)
```typescript
// Tests the validated API client wrapper
describe('Validated API Client', () => {
  it('should validate responses automatically', () => {
    // Tests automatic validation integration
  });
  
  it('should handle contract violations', () => {
    // Tests error handling for invalid responses
  });
});
```

## CI/CD Pipeline

### GitHub Actions Workflow (`.github/workflows/contract-tests.yml`)

The automated pipeline includes three main jobs:

#### 1. Frontend Contract Tests
- Installs Node.js dependencies
- Runs frontend contract test suite
- Uploads test results and coverage

#### 2. Backend Contract Tests
- Sets up Python environment and PostgreSQL
- Runs backend contract validation tests
- Validates API endpoint contracts

#### 3. Integration Contract Tests
- Starts both frontend and backend services
- Runs end-to-end contract compatibility tests
- Generates comprehensive test reports
- Validates real API communication

## Usage Guide

### Running Contract Tests Locally

#### Frontend Tests
```bash
cd Frontend
npm test -- src/test/contract
```

#### Backend Tests
```bash
cd Backend
pytest tests/ -k "contract"
```

#### Integration Tests
```bash
# Start backend
cd Backend
uvicorn core.app:create_app --factory --host 0.0.0.0 --port 8000 &

# Run frontend integration tests
cd Frontend
npm test -- src/test/integration
```

### Environment Configuration

#### Frontend Environment Variables
```bash
# Copy example configuration
cp .env.example .env.local

# Update for your environment
VITE_ENVIRONMENT=development
VITE_API_URL=http://localhost:8000
VITE_ENABLE_CONTRACT_VALIDATION=true
```

#### Backend Environment Variables
```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/db
ENVIRONMENT=development
API_VERSION=1.0
```

### Adding New Contract Tests

#### 1. Define Schema
```typescript
// Add to schema-validation.ts
export const NewFeatureResponseSchema = z.object({
  id: z.number(),
  name: z.string(),
  status: z.enum(['active', 'inactive']),
});
```

#### 2. Add Validation Function
```typescript
export function validateNewFeatureResponse(data: unknown): NewFeatureResponse {
  return validateWithSchema(NewFeatureResponseSchema, data, 'NewFeatureResponse');
}
```

#### 3. Create Contract Test
```typescript
// Add to appropriate contract test file
describe('New Feature Contract', () => {
  it('should validate new feature response', () => {
    const mockResponse = { id: 1, name: 'test', status: 'active' };
    expect(() => validateNewFeatureResponse(mockResponse)).not.toThrow();
  });
});
```

#### 4. Update Validated Client
```typescript
// Add method to ValidatedApiClient
async getNewFeature(id: number): Promise<NewFeatureResponse> {
  const response = await clientSdk.getNewFeatureGet({ path: { id } });
  return validateNewFeatureResponse(response.data);
}
```

## API Versioning

### Version Strategy

The API uses semantic versioning with the following strategies:

1. **Header-based** (Recommended): `X-API-Version: 1.0`
2. **Accept header**: `Accept: application/json; version=1.0`
3. **Query parameter**: `?version=1.0`
4. **URL path**: `/api/v1.0/endpoint`

### Version Compatibility

- **v1.0**: Initial API version (stable)
- **v1.1**: Enhanced error handling (stable)
- **v2.0**: Major revision with breaking changes (latest)

### Handling Breaking Changes

```typescript
// Version-specific response handling
function formatUserResponse(data: any, version: string): UserResponse {
  if (version === '1.0') {
    // Legacy format
    return { ...data };
  } else if (version === '2.0') {
    // New format with transformed fields
    return {
      ...data,
      createdAt: data.created_timestamp,
    };
  }
}
```

## Best Practices

### 1. Schema Design
- Use strict typing with Zod schemas
- Include optional fields explicitly
- Validate nested objects thoroughly
- Provide meaningful error messages

### 2. Test Organization
- Group tests by API domain (auth, videos, etc.)
- Test both success and failure scenarios
- Include edge cases and boundary conditions
- Mock external dependencies consistently

### 3. Version Management
- Document breaking changes clearly
- Provide migration guides for version upgrades
- Use deprecation warnings before removing features
- Maintain backward compatibility when possible

### 4. CI/CD Integration
- Run contract tests on every pull request
- Block deployments on contract test failures
- Generate and archive test reports
- Monitor test performance and reliability

## Troubleshooting

### Common Issues

#### 1. Schema Validation Failures
```typescript
// Check for missing or incorrect fields
const result = validateUserResponse(response);
// Error: Expected string, received number at path: username
```

#### 2. Version Compatibility Issues
```typescript
// Ensure correct version headers
const headers = {
  'X-API-Version': '1.0',
  'Content-Type': 'application/json'
};
```

#### 3. Mock Configuration Problems
```typescript
// Ensure mocks match actual API structure
vi.mocked(clientSdk.loginAuthLoginPost).mockResolvedValue({
  data: { user: mockUser, token: 'mock-token' },
  error: null,
  response: new Response()
});
```

### Debug Tips

1. **Enable detailed logging**:
   ```bash
   VITE_ENABLE_API_LOGGING=true npm test
   ```

2. **Check network requests**:
   ```typescript
   // Add logging to validated client
   console.log('Request:', request);
   console.log('Response:', response);
   ```

3. **Validate schemas manually**:
   ```typescript
   const result = UserResponseSchema.safeParse(data);
   if (!result.success) {
     console.log('Validation errors:', result.error.issues);
   }
   ```

## Future Enhancements

### Planned Features

1. **Consumer-Driven Contract Testing with Pact**
   - Generate contracts from consumer tests
   - Verify contracts against provider
   - Share contracts between teams

2. **Advanced Schema Evolution**
   - Automatic schema migration
   - Backward compatibility validation
   - Schema registry integration

3. **Performance Contract Testing**
   - Response time validation
   - Payload size limits
   - Rate limiting contract tests

4. **Visual Contract Documentation**
   - Auto-generated API documentation
   - Interactive contract explorer
   - Change impact visualization

## Contributing

When contributing to contract testing:

1. **Add tests for new endpoints**
2. **Update schemas for data changes**
3. **Document breaking changes**
4. **Run full test suite before submitting**
5. **Update this documentation as needed**

For questions or issues, please refer to the project's issue tracker or contact the development team.

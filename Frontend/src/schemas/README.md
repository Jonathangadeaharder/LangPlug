# Generated Zod Schemas

This directory contains auto-generated Zod validation schemas from the backend's OpenAPI specification.

## Generating Schemas

```bash
# From Frontend directory
npm run generate:schemas
```

This will fetch the OpenAPI spec from the backend and generate TypeScript Zod schemas.

## Usage

```typescript
import { UserRegisterSchema, LoginRequestSchema } from "@/schemas/api-schemas";

// Validate form data
try {
  const validData = UserRegisterSchema.parse(formData);
  // Data is valid and typed
} catch (error) {
  // Handle validation errors
  const formErrors = zodErrorToFormErrors(error);
}
```

## Benefits

- ✅ **Single Source of Truth**: Backend Pydantic models define all validation rules
- ✅ **Always in Sync**: Re-generate schemas when backend changes
- ✅ **Type-Safe**: Full TypeScript support
- ✅ **No Duplication**: No manual copying of validation logic

## Files

- `api-schemas.ts` - Auto-generated Zod schemas (DO NOT EDIT MANUALLY)
- `helpers.ts` - Helper functions for working with Zod validation

## Workflow

1. Update backend Pydantic model
2. Run `npm run update-openapi` to regenerate schemas
3. Frontend validation automatically updates
4. Frontend and backend validation always match

## Documentation

- Zod: https://zod.dev/
- openapi-zod-client: https://github.com/astahmer/openapi-zod-client

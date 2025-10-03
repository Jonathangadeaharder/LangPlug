import { defineConfig } from '@hey-api/openapi-ts';

export default defineConfig({
  client: 'axios',
  input: '../openapi_spec.json',  // Use canonical root-level OpenAPI spec
  output: './src/client',
});

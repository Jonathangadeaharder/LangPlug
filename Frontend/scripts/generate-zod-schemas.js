#!/usr/bin/env node
/**
 * Generate Zod schemas from OpenAPI specification
 *
 * This script generates TypeScript Zod validation schemas from the backend's
 * OpenAPI spec, ensuring frontend and backend validation rules stay in sync.
 *
 * Usage:
 *   npm run generate:schemas
 *
 * Or manually:
 *   node scripts/generate-zod-schemas.js
 */

import { execSync } from 'child_process'
import { existsSync } from 'fs'
import { join, dirname } from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

// Configuration
const OPENAPI_URL = process.env.OPENAPI_URL || 'http://localhost:8000/openapi.json'
const OUTPUT_FILE = join(__dirname, '../src/schemas/api-schemas.ts')
const BACKEND_SPEC = join(__dirname, '../../Backend/openapi.json')

console.log('🔧 Generating Zod schemas from OpenAPI specification...\n')

// Check if we should use local file or URL
let specSource = OPENAPI_URL
if (existsSync(BACKEND_SPEC)) {
  specSource = BACKEND_SPEC
  console.log(`📁 Using local OpenAPI spec: ${BACKEND_SPEC}`)
} else {
  console.log(`🌐 Fetching OpenAPI spec from: ${OPENAPI_URL}`)
  console.log('💡 Tip: Run `cd Backend && python export_openapi.py` to generate a local spec\n')
}

try {
  // Generate Zod schemas using openapi-zod-client
  const command = `npx openapi-zod-client ${specSource} -o ${OUTPUT_FILE} --export-schemas`

  console.log(`Running: ${command}\n`)
  execSync(command, { stdio: 'inherit' })

  console.log('\n✅ Zod schemas generated successfully!')
  console.log(`📝 Output file: ${OUTPUT_FILE}`)
  console.log('\n💡 Next steps:')
  console.log('   1. Import schemas: import { UserRegisterSchema } from "@/schemas/api-schemas"')
  console.log('   2. Use in forms: UserRegisterSchema.parse(formData)')
  console.log('   3. Frontend/backend validation now in sync! 🎉\n')
} catch (error) {
  console.error('\n❌ Error generating Zod schemas:')
  console.error(error.message)
  console.error('\n🔍 Troubleshooting:')
  console.error('   1. Make sure backend is running: cd Backend && python main.py')
  console.error('   2. Or generate OpenAPI spec: cd Backend && python export_openapi.py')
  console.error('   3. Install dependencies: npm install openapi-zod-client\n')
  process.exit(1)
}

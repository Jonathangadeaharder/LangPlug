#!/usr/bin/env ts-node

/**
 * Contract validation script for LangPlug
 * Validates frontend/backend API contract compatibility
 */

import { readFileSync, existsSync } from 'fs'
import { join } from 'path'
import { execSync } from 'child_process'

interface ContractValidationResult {
  valid: boolean
  errors: string[]
  warnings: string[]
  summary: string
}

class ContractValidator {
  private projectRoot: string
  private errors: string[] = []
  private warnings: string[] = []

  constructor() {
    this.projectRoot = process.cwd()
  }

  async validate(): Promise<ContractValidationResult> {
    console.log('🔍 Validating API contract compatibility...')

    try {
      // Step 1: Check if OpenAPI spec exists
      this.validateOpenAPISpec()

      // Step 2: Check if frontend client is up to date
      this.validateClientGeneration()

      // Step 3: Validate contract schemas
      this.validateContractSchemas()

      // Step 4: Check server contract middleware
      this.validateServerMiddleware()

    } catch (error) {
      this.errors.push(`Validation failed: ${error}`)
    }

    const valid = this.errors.length === 0
    const summary = this.generateSummary(valid)

    return {
      valid,
      errors: this.errors,
      warnings: this.warnings,
      summary
    }
  }

  private validateOpenAPISpec(): void {
    const specPath = join(this.projectRoot, 'openapi.json')

    if (!existsSync(specPath)) {
      this.errors.push('OpenAPI specification not found. Run: cd src/backend && python -m core.export_openapi')
      return
    }

    try {
      const spec = JSON.parse(readFileSync(specPath, 'utf8'))

      // Check required fields
      if (!spec.openapi) {
        this.errors.push('OpenAPI spec missing version field')
      }

      if (!spec.paths || Object.keys(spec.paths).length === 0) {
        this.errors.push('OpenAPI spec has no paths defined')
      }

      // Check if spec is recent (modified within last hour during development)
      const stats = require('fs').statSync(specPath)
      const ageMinutes = (Date.now() - stats.mtime.getTime()) / (1000 * 60)

      if (ageMinutes > 60) {
        this.warnings.push(`OpenAPI spec is ${Math.round(ageMinutes)} minutes old. Consider regenerating.`)
      }

      console.log(`✅ OpenAPI spec found with ${Object.keys(spec.paths).length} endpoints`)

    } catch (error) {
      this.errors.push(`Invalid OpenAPI spec: ${error}`)
    }
  }

  private validateClientGeneration(): void {
    const clientPath = join(this.projectRoot, 'src/frontend/src/client')
    const requiredFiles = [
      'schemas.gen.ts',
      'types.gen.ts',
      'services.gen.ts'
    ]

    for (const file of requiredFiles) {
      if (!existsSync(join(clientPath, file))) {
        this.errors.push(`Missing generated client file: ${file}. Run: cd src/frontend && npm run generate-client`)
      }
    }

    // Check if generated files are newer than OpenAPI spec
    const specPath = join(this.projectRoot, 'openapi.json')
    if (existsSync(specPath)) {
      const specStats = require('fs').statSync(specPath)

      for (const file of requiredFiles) {
        const filePath = join(clientPath, file)
        if (existsSync(filePath)) {
          const fileStats = require('fs').statSync(filePath)
          if (fileStats.mtime < specStats.mtime) {
            this.warnings.push(`Generated file ${file} is older than OpenAPI spec. Consider regenerating client.`)
          }
        }
      }
    }

    console.log('✅ Client files validated')
  }

  private validateContractSchemas(): void {
    const schemaPath = join(this.projectRoot, 'src/frontend/src/utils/contract-validation.ts')

    if (!existsSync(schemaPath)) {
      this.errors.push('Contract validation schemas not found')
      return
    }

    const schemaContent = readFileSync(schemaPath, 'utf8')

    // Check for required schema exports
    const requiredSchemas = [
      'HealthCheckResponseSchema',
      'UserSchema',
      'AuthResponseSchema',
      'VideoListResponseSchema',
      'VocabularyResponseSchema'
    ]

    for (const schema of requiredSchemas) {
      if (!schemaContent.includes(`export const ${schema}`)) {
        this.warnings.push(`Missing schema export: ${schema}`)
      }
    }

    console.log('✅ Contract schemas validated')
  }

  private validateServerMiddleware(): void {
    const middlewarePath = join(this.projectRoot, 'src/backend/core/middleware/contract_middleware.py')

    if (!existsSync(middlewarePath)) {
      this.warnings.push('Server contract middleware not found')
      return
    }

    const appPath = join(this.projectRoot, 'src/backend/core/app.py')
    if (existsSync(appPath)) {
      const appContent = readFileSync(appPath, 'utf8')
      if (!appContent.includes('setup_contract_validation')) {
        this.warnings.push('Contract validation middleware not configured in app')
      }
    }

    console.log('✅ Server middleware validated')
  }

  private generateSummary(valid: boolean): string {
    const errorCount = this.errors.length
    const warningCount = this.warnings.length

    if (valid && warningCount === 0) {
      return '🎉 Contract validation passed with no issues!'
    } else if (valid) {
      return `✅ Contract validation passed with ${warningCount} warning(s)`
    } else {
      return `❌ Contract validation failed with ${errorCount} error(s) and ${warningCount} warning(s)`
    }
  }
}

// Main execution
async function main() {
  const validator = new ContractValidator()
  const result = await validator.validate()

  console.log('\n' + '='.repeat(60))
  console.log(result.summary)
  console.log('='.repeat(60))

  if (result.errors.length > 0) {
    console.log('\n❌ Errors:')
    result.errors.forEach(error => console.log(`  • ${error}`))
  }

  if (result.warnings.length > 0) {
    console.log('\n⚠️  Warnings:')
    result.warnings.forEach(warning => console.log(`  • ${warning}`))
  }

  if (result.valid && result.warnings.length === 0) {
    console.log('\n✨ Your API contract is fully validated and up to date!')
    console.log('\nNext steps:')
    console.log('  • Run tests to ensure contract compliance')
    console.log('  • Deploy with confidence knowing contracts are enforced')
  } else if (result.valid) {
    console.log('\n💡 Consider addressing warnings to improve contract reliability')
  } else {
    console.log('\n🔧 Please fix the errors above to ensure contract compatibility')
    process.exit(1)
  }
}

if (require.main === module) {
  main().catch(error => {
    console.error('Contract validation failed:', error)
    process.exit(1)
  })
}

export { ContractValidator }

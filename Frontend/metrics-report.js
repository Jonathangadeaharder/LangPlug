#!/usr/bin/env node
/**
 * Comprehensive Code Quality Metrics Report for Frontend
 * Generates detailed metrics for maintainability, complexity, and code health
 */

const { exec } = require('child_process')
const { promisify } = require('util')
const fs = require('fs').promises
const path = require('path')

const execAsync = promisify(exec)

function printSection(title) {
  console.log('\n' + '='.repeat(80))
  console.log(` ${title}`)
  console.log('='.repeat(80) + '\n')
}

async function runCommand(cmd, description) {
  try {
    console.log(`Running: ${description}...`)
    const { stdout, stderr } = await execAsync(cmd, {
      maxBuffer: 1024 * 1024 * 10, // 10MB buffer
      timeout: 300000, // 5 min timeout
    })
    return { success: true, output: stdout || stderr }
  } catch (error) {
    return { success: false, output: error.message }
  }
}

async function eslintComplexity() {
  printSection('Code Complexity (ESLint)')
  const result = await runCommand(
    'npx eslint src --format json',
    'ESLint complexity analysis'
  )

  if (result.success) {
    try {
      const data = JSON.parse(result.output)
      const complexityIssues = data
        .flatMap(file =>
          (file.messages || []).filter(msg => msg.ruleId && msg.ruleId.includes('complexity'))
        )

      console.log(`Total complexity warnings: ${complexityIssues.length}`)
      if (complexityIssues.length > 0) {
        console.log('\nTop complexity issues:')
        complexityIssues.slice(0, 10).forEach(issue => {
          console.log(`  ${issue.message} (${issue.ruleId})`)
        })
      } else {
        console.log('✓ No high complexity issues found!')
      }
    } catch (e) {
      console.log('Note: ESLint output could not be parsed as JSON')
      console.log(result.output.substring(0, 500))
    }
  }

  return result
}

async function lizardComplexity() {
  printSection('Cognitive Complexity (Lizard)')
  const result = await runCommand(
    'npx lizard src -l javascript,typescript -w -T nloc=50 -T cyclomatic_complexity=10',
    'Lizard complexity analysis'
  )

  if (result.success) {
    console.log(result.output)
  } else {
    console.log('Lizard analysis not available')
  }

  return result
}

async function codeDuplication() {
  printSection('Code Duplication Analysis (JSCPD)')
  const result = await runCommand(
    'npx jscpd src --min-lines 5 --min-tokens 50 --format "markdown"',
    'Code duplication detection'
  )

  if (result.success) {
    // Parse JSCPD output
    const output = result.output
    console.log(output.substring(0, 1000))

    if (output.includes('duplicates')) {
      console.log('\n⚠ Code duplication detected - review duplicated blocks')
    } else {
      console.log('\n✓ Low code duplication')
    }
  }

  return result
}

async function typeScriptCoverage() {
  printSection('TypeScript Type Coverage')

  // Check if tsconfig.json has necessary settings
  try {
    const tsconfigPath = path.join(__dirname, 'tsconfig.json')
    const tsconfig = JSON.parse(await fs.readFile(tsconfigPath, 'utf8'))

    console.log('TypeScript Configuration:')
    console.log(`  Strict mode: ${tsconfig.compilerOptions?.strict || false}`)
    console.log(`  No implicit any: ${tsconfig.compilerOptions?.noImplicitAny !== false}`)

    // Run type check
    const result = await runCommand('npx tsc --noEmit', 'TypeScript type check')

    if (result.success || result.output.includes('Found 0 errors')) {
      console.log('\n✓ No TypeScript errors')
    } else {
      // Count errors
      const errorMatch = result.output.match(/Found (\d+) error/)
      if (errorMatch) {
        console.log(`\n⚠ Found ${errorMatch[1]} TypeScript error(s)`)
      }
      console.log('\nFirst few errors:')
      console.log(result.output.substring(0, 500))
    }

    return result
  } catch (e) {
    console.log(`Error reading TypeScript config: ${e.message}`)
    return { success: false, error: e.message }
  }
}

async function testCoverage() {
  printSection('Test Coverage (Vitest)')

  try {
    // Check if coverage report exists
    const coveragePath = path.join(__dirname, 'coverage', 'coverage-summary.json')

    try {
      const coverageData = JSON.parse(await fs.readFile(coveragePath, 'utf8'))
      const total = coverageData.total

      console.log('Overall Coverage:')
      console.log(`  Lines: ${total.lines.pct}%`)
      console.log(`  Statements: ${total.statements.pct}%`)
      console.log(`  Functions: ${total.functions.pct}%`)
      console.log(`  Branches: ${total.branches.pct}%`)

      // Grade coverage
      const avgCoverage =
        (total.lines.pct +
          total.statements.pct +
          total.functions.pct +
          total.branches.pct) /
        4

      if (avgCoverage >= 80) {
        console.log(`\n✓ Excellent coverage (${avgCoverage.toFixed(1)}%)`)
      } else if (avgCoverage >= 60) {
        console.log(`\n⚠ Moderate coverage (${avgCoverage.toFixed(1)}%) - aim for 80%+`)
      } else {
        console.log(`\n✗ Low coverage (${avgCoverage.toFixed(1)}%) - needs improvement`)
      }

      return { success: true, coverage: avgCoverage }
    } catch (e) {
      console.log('No coverage report found. Run: npm run coverage')
      return { success: false, message: 'Coverage file not found' }
    }
  } catch (e) {
    console.log(`Error: ${e.message}`)
    return { success: false, error: e.message }
  }
}

async function linesOfCode() {
  printSection('Lines of Code Analysis')

  const result = await runCommand(
    'npx cloc src --json --exclude-dir=__tests__,node_modules',
    'LOC analysis'
  )

  if (result.success) {
    try {
      const data = JSON.parse(result.output)
      if (data.TypeScript || data.JavaScript || data.TSX) {
        console.log('Code Statistics:')
        if (data.TypeScript) {
          console.log(`  TypeScript: ${data.TypeScript.code} lines`)
        }
        if (data.TSX) {
          console.log(`  TSX (React): ${data.TSX.code} lines`)
        }
        if (data.JavaScript) {
          console.log(`  JavaScript: ${data.JavaScript.code} lines`)
        }
        console.log(`  Total: ${data.SUM.code} lines of code`)
        console.log(`  Comments: ${data.SUM.comment} lines`)
        console.log(`  Blank: ${data.SUM.blank} lines`)
      }
    } catch (e) {
      console.log('Could not parse LOC output')
    }
  } else {
    console.log(
      'Note: cloc not available. Install with: npm install -g cloc or use lizard output above'
    )
  }

  return result
}

async function generateSummary(results) {
  printSection('METRICS SUMMARY')

  console.log('Report Generated:', new Date().toLocaleString())
  console.log('\nMetrics Status:')

  Object.entries(results).forEach(([metric, result]) => {
    const status = result.success ? '✓ PASS' : '✗ FAIL'
    console.log(`  ${metric}: ${status}`)
  })

  console.log('\nRecommendations:')
  console.log('  - Complexity: Keep functions simple (CC < 10)')
  console.log('  - Duplication: Minimize code duplication (< 5%)')
  console.log('  - Test Coverage: Target 80%+ coverage')
  console.log('  - TypeScript: Use strict mode, avoid `any`')
  console.log('  - LOC: Keep components < 300 lines')

  console.log('\nFor detailed analysis:')
  console.log('  - ESLint complexity: npm run lint')
  console.log('  - Lizard: npm run metrics:complexity')
  console.log('  - JSCPD: npm run metrics:duplication')
  console.log('  - Type Coverage: npm run metrics:type-coverage')
}

async function main() {
  console.log('='.repeat(80))
  console.log(' FRONTEND CODE QUALITY METRICS REPORT')
  console.log('='.repeat(80))
  console.log(` Generated: ${new Date().toLocaleString()}`)
  console.log('='.repeat(80))

  const results = {}

  // Run all metrics
  results['ESLint Complexity'] = await eslintComplexity()
  results['Lizard Complexity'] = await lizardComplexity()
  results['Code Duplication'] = await codeDuplication()
  results['TypeScript Coverage'] = await typeScriptCoverage()
  results['Test Coverage'] = await testCoverage()
  results['Lines of Code'] = await linesOfCode()

  // Generate summary
  await generateSummary(results)

  console.log('\n' + '='.repeat(80))
  console.log(' Report complete!')
  console.log('='.repeat(80) + '\n')

  process.exit(0)
}

// Run if called directly
if (require.main === module) {
  main().catch(err => {
    console.error('Error running metrics:', err)
    process.exit(1)
  })
}

module.exports = { main }

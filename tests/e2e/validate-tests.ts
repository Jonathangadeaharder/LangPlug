#!/usr/bin/env ts-node
/**
 * E2E Test Validation Script
 * Ensures all E2E tests follow quality guidelines and anti-pattern elimination
 */

import * as fs from 'fs-extra';
import * as path from 'path';
import chalk from 'chalk';

interface ValidationRule {
  name: string;
  description: string;
  pattern: RegExp;
  severity: 'error' | 'warning';
  category: 'anti-pattern' | 'best-practice' | 'security';
}

interface ValidationResult {
  file: string;
  rule: string;
  line: number;
  content: string;
  severity: 'error' | 'warning';
  category: string;
}

const VALIDATION_RULES: ValidationRule[] = [
  // Anti-pattern detection
  {
    name: 'no-array-index-selectors',
    description: 'Avoid array index selectors like buttons[0] or elements[1]',
    pattern: /\w+\[\d+\](?!\s*=|\s*\+\+|\s*--)/,
    severity: 'error',
    category: 'anti-pattern'
  },
  {
    name: 'no-dom-counting',
    description: 'Avoid testing DOM element counts as primary assertions',
    pattern: /expect\(.*\.length\)\.toBe\(\d+\)/,
    severity: 'error',
    category: 'anti-pattern'
  },
  {
    name: 'no-status-tolerance',
    description: 'Avoid accepting multiple status codes as valid',
    pattern: /status.*in\s*\{|\{.*200.*[45]\d{2}.*\}/,
    severity: 'error',
    category: 'anti-pattern'
  },
  {
    name: 'no-computed-styles',
    description: 'Avoid testing computed styles like CSS colors',
    pattern: /getComputedStyle|\.style\./,
    severity: 'error',
    category: 'anti-pattern'
  },
  {
    name: 'no-hardcoded-paths',
    description: 'Avoid hardcoded Windows or absolute paths',
    pattern: /[A-Z]:\\|\/home\/|\/Users\//,
    severity: 'error',
    category: 'anti-pattern'
  },

  // Best practice enforcement
  {
    name: 'prefer-data-testid',
    description: 'Use data-testid attributes for reliable element selection',
    pattern: /locator\(['"`][^'"`]*['"`]\)(?!\.or\()/,
    severity: 'warning',
    category: 'best-practice'
  },
  {
    name: 'require-semantic-selectors',
    description: 'Use semantic selectors with fallbacks',
    pattern: /locator\(['"`]button['"`]\)(?!\.or\()/,
    severity: 'warning',
    category: 'best-practice'
  },
  {
    name: 'require-business-assertions',
    description: 'Focus on business outcomes, not UI structure',
    pattern: /expect\(.*\.count\(\)\)\.toBe/,
    severity: 'warning',
    category: 'best-practice'
  },
  {
    name: 'proper-waits',
    description: 'Use explicit waits instead of setTimeout',
    pattern: /setTimeout|sleep\(/,
    severity: 'warning',
    category: 'best-practice'
  },

  // Security concerns
  {
    name: 'no-credentials-in-tests',
    description: 'Avoid hardcoded credentials or tokens',
    pattern: /password\s*[:=]\s*['"`](?!.*\$\{.*\})[^'"`]{8,}['"`]|token\s*[:=]\s*['"`](?!.*\$\{.*\})[A-Za-z0-9+/=]{20,}['"`]/,
    severity: 'error',
    category: 'security'
  },
  {
    name: 'no-production-urls',
    description: 'Avoid hardcoded production URLs',
    pattern: /https?:\/\/(?!localhost|127\.0\.0\.1)[^\/\s'"`)]+/,
    severity: 'error',
    category: 'security'
  }
];

async function findTestFiles(dir: string): Promise<string[]> {
  const files: string[] = [];
  const items = await fs.readdir(dir, { withFileTypes: true });

  for (const item of items) {
    const fullPath = path.join(dir, item.name);

    if (item.isDirectory() && !item.name.includes('node_modules')) {
      files.push(...await findTestFiles(fullPath));
    } else if (item.isFile() && item.name.endsWith('.test.ts')) {
      files.push(fullPath);
    }
  }

  return files;
}

async function validateFile(filePath: string): Promise<ValidationResult[]> {
  const results: ValidationResult[] = [];
  const content = await fs.readFile(filePath, 'utf-8');
  const lines = content.split('\n');

  for (let lineIndex = 0; lineIndex < lines.length; lineIndex++) {
    const line = lines[lineIndex];

    for (const rule of VALIDATION_RULES) {
      if (rule.pattern.test(line)) {
        results.push({
          file: path.relative(process.cwd(), filePath),
          rule: rule.name,
          line: lineIndex + 1,
          content: line.trim(),
          severity: rule.severity,
          category: rule.category
        });
      }
    }
  }

  return results;
}

function formatResults(results: ValidationResult[]): void {
  if (results.length === 0) {
    console.log(chalk.green('✅ All E2E tests pass validation!'));
    return;
  }

  // Group by category
  const byCategory = results.reduce((acc, result) => {
    if (!acc[result.category]) acc[result.category] = [];
    acc[result.category].push(result);
    return acc;
  }, {} as Record<string, ValidationResult[]>);

  console.log(chalk.red(`❌ Found ${results.length} validation issues:\n`));

  for (const [category, categoryResults] of Object.entries(byCategory)) {
    const categoryColor = category === 'anti-pattern' ? chalk.red :
                         category === 'security' ? chalk.yellow :
                         chalk.blue;

    console.log(categoryColor(`📋 ${category.toUpperCase()} (${categoryResults.length} issues):`));

    for (const result of categoryResults) {
      const severityIcon = result.severity === 'error' ? '🚨' : '⚠️';
      const rule = VALIDATION_RULES.find(r => r.name === result.rule);

      console.log(`  ${severityIcon} ${chalk.cyan(result.file)}:${result.line}`);
      console.log(`     Rule: ${result.rule}`);
      console.log(`     ${rule?.description}`);
      console.log(`     Code: ${chalk.gray(result.content)}`);
      console.log('');
    }
  }

  // Summary
  const errors = results.filter(r => r.severity === 'error').length;
  const warnings = results.filter(r => r.severity === 'warning').length;

  console.log(chalk.bold('📊 Summary:'));
  console.log(`  ${chalk.red('Errors:')} ${errors}`);
  console.log(`  ${chalk.yellow('Warnings:')} ${warnings}`);

  if (errors > 0) {
    console.log(chalk.red('\n❌ Validation failed. Please fix errors before proceeding.'));
    process.exit(1);
  } else if (warnings > 0) {
    console.log(chalk.yellow('\n⚠️ Validation completed with warnings. Consider addressing them.'));
  }
}

async function validateE2ETests(): Promise<void> {
  console.log(chalk.bold.cyan('🔍 Validating E2E Tests for Anti-Patterns\n'));

  try {
    const testDir = path.resolve(__dirname, 'workflows');
    const testFiles = await findTestFiles(testDir);

    if (testFiles.length === 0) {
      console.log(chalk.yellow('⚠️ No E2E test files found'));
      return;
    }

    console.log(chalk.blue(`📁 Found ${testFiles.length} test files:`));
    testFiles.forEach(file => {
      console.log(`  • ${path.relative(process.cwd(), file)}`);
    });
    console.log('');

    let allResults: ValidationResult[] = [];

    for (const testFile of testFiles) {
      const results = await validateFile(testFile);
      allResults = allResults.concat(results);
    }

    formatResults(allResults);

  } catch (error) {
    console.error(chalk.red('💥 Validation failed:'), error instanceof Error ? error.message : error);
    process.exit(1);
  }
}

async function showRules(): Promise<void> {
  console.log(chalk.bold.cyan('📋 E2E Test Validation Rules\n'));

  const byCategory = VALIDATION_RULES.reduce((acc, rule) => {
    if (!acc[rule.category]) acc[rule.category] = [];
    acc[rule.category].push(rule);
    return acc;
  }, {} as Record<string, ValidationRule[]>);

  for (const [category, rules] of Object.entries(byCategory)) {
    const categoryColor = category === 'anti-pattern' ? chalk.red :
                         category === 'security' ? chalk.yellow :
                         chalk.blue;

    console.log(categoryColor(`${category.toUpperCase()}:`));

    for (const rule of rules) {
      const severityIcon = rule.severity === 'error' ? '🚨' : '⚠️';
      console.log(`  ${severityIcon} ${chalk.cyan(rule.name)}`);
      console.log(`     ${rule.description}`);
      console.log(`     Pattern: ${chalk.gray(rule.pattern.toString())}`);
      console.log('');
    }
  }
}

// CLI interface
const args = process.argv.slice(2);

if (args.includes('--help') || args.includes('-h')) {
  console.log(`
${chalk.bold('E2E Test Validation Tool')}

${chalk.yellow('Usage:')} ts-node validate-tests.ts [options]

${chalk.yellow('Options:')}
  --rules         Show all validation rules
  --help, -h      Show this help message

${chalk.yellow('Examples:')}
  ts-node validate-tests.ts           # Validate all E2E tests
  ts-node validate-tests.ts --rules   # Show validation rules
`);
  process.exit(0);
}

if (args.includes('--rules')) {
  showRules();
} else {
  validateE2ETests();
}

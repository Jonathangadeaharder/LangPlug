/**
 * Contract Validator - OpenAPI contract validation for tests
 * Ensures frontend-backend API compatibility
 */

import Ajv, { ValidateFunction } from 'ajv';
import addFormats from 'ajv-formats';
import * as fs from 'fs-extra';
import * as path from 'path';
import axios, { AxiosRequestConfig, AxiosResponse } from 'axios';
import { OpenAPIV3 } from 'openapi-types';

export interface ValidationResult {
  valid: boolean;
  errors?: ValidationError[];
  warnings?: string[];
}

export interface ValidationError {
  path: string;
  message: string;
  expected?: any;
  actual?: any;
  schemaPath?: string;
}

export interface ContractTestResult {
  endpoint: string;
  method: string;
  request?: ValidationResult;
  response?: ValidationResult;
  headers?: ValidationResult;
  statusCode?: number;
  expectedStatusCode?: number;
  timestamp: Date;
  duration?: number;
}

export class ContractValidator {
  private ajv: Ajv;
  private spec!: OpenAPIV3.Document;
  private validators: Map<string, ValidateFunction> = new Map();
  private testResults: ContractTestResult[] = [];
  private strictMode: boolean;

  constructor(strictMode = true) {
    this.strictMode = strictMode;
    this.ajv = new Ajv({
      allErrors: true,
      strict: false,
      coerceTypes: !strictMode,
      removeAdditional: !strictMode,
    });
    addFormats(this.ajv);
    
    // Add custom formats
    this.ajv.addFormat('uuid', /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i);
    this.ajv.addFormat('email', /^[^\s@]+@[^\s@]+\.[^\s@]+$/);
  }

  /**
   * Load OpenAPI specification
   */
  async loadSpec(specPath: string): Promise<void> {
    const specContent = await fs.readFile(specPath, 'utf-8');
    this.spec = JSON.parse(specContent);
    this.compileValidators();
  }

  /**
   * Load spec from object
   */
  loadSpecFromObject(spec: OpenAPIV3.Document): void {
    this.spec = spec;
    this.compileValidators();
  }

  /**
   * Compile validators for all endpoints
   */
  private compileValidators(): void {
    if (!this.spec.paths) return;

    for (const [pathPattern, pathItem] of Object.entries(this.spec.paths)) {
      if (!pathItem) continue;
      
      for (const method of ['get', 'post', 'put', 'patch', 'delete'] as const) {
        const operation = pathItem[method];
        if (!operation) continue;

        const key = `${method.toUpperCase()} ${pathPattern}`;
        
        // Compile request body validator
        if (operation.requestBody && 'content' in operation.requestBody) {
          const content = operation.requestBody.content;
          if (content['application/json']?.schema) {
            const requestKey = `${key}:request`;
            const schema = this.resolveRefs(content['application/json'].schema);
            this.validators.set(requestKey, this.ajv.compile(schema));
          }
        }

        // Compile response validators
        if (operation.responses) {
          for (const [statusCode, response] of Object.entries(operation.responses)) {
            if ('content' in response && response.content?.['application/json']?.schema) {
              const responseKey = `${key}:response:${statusCode}`;
              const schema = this.resolveRefs(response.content['application/json'].schema);
              this.validators.set(responseKey, this.ajv.compile(schema));
            }
          }
        }

        // Compile parameter validators
        if (operation.parameters) {
          const queryParams: Record<string, any> = {};
          const headerParams: Record<string, any> = {};
          const pathParams: Record<string, any> = {};

          for (const param of operation.parameters) {
            if ('in' in param) {
              const paramSchema = this.resolveRefs(param.schema || { type: 'string' });
              
              switch (param.in) {
                case 'query':
                  queryParams[param.name] = paramSchema;
                  break;
                case 'header':
                  headerParams[param.name] = paramSchema;
                  break;
                case 'path':
                  pathParams[param.name] = paramSchema;
                  break;
              }
            }
          }

          if (Object.keys(queryParams).length > 0) {
            const queryKey = `${key}:query`;
            this.validators.set(queryKey, this.ajv.compile({
              type: 'object',
              properties: queryParams,
            }));
          }

          if (Object.keys(headerParams).length > 0) {
            const headerKey = `${key}:headers`;
            this.validators.set(headerKey, this.ajv.compile({
              type: 'object',
              properties: headerParams,
            }));
          }

          if (Object.keys(pathParams).length > 0) {
            const pathKey = `${key}:path`;
            this.validators.set(pathKey, this.ajv.compile({
              type: 'object',
              properties: pathParams,
            }));
          }
        }
      }
    }
  }

  /**
   * Resolve $ref references in schema
   */
  private resolveRefs(schema: any): any {
    if (!schema) return schema;
    
    if (schema.$ref) {
      const refPath = schema.$ref.replace('#/', '').split('/');
      let resolved: any = this.spec;
      
      for (const part of refPath) {
        resolved = resolved[part];
      }
      
      return this.resolveRefs(resolved);
    }

    if (typeof schema === 'object') {
      const resolved: any = Array.isArray(schema) ? [] : {};
      
      for (const [key, value] of Object.entries(schema)) {
        resolved[key] = this.resolveRefs(value);
      }
      
      return resolved;
    }

    return schema;
  }

  /**
   * Validate request against contract
   */
  validateRequest(
    method: string,
    path: string,
    data?: any,
    headers?: Record<string, string>,
    query?: Record<string, any>
  ): ValidationResult {
    const key = `${method.toUpperCase()} ${this.normalizePath(path)}`;
    const errors: ValidationError[] = [];

    // Validate request body
    if (data !== undefined) {
      const requestValidator = this.validators.get(`${key}:request`);
      if (requestValidator) {
        const valid = requestValidator(data);
        if (!valid) {
          errors.push(...this.formatAjvErrors(requestValidator.errors, 'request body'));
        }
      } else if (this.strictMode && data !== null) {
        errors.push({
          path: 'request',
          message: 'Request body not expected for this endpoint',
        });
      }
    }

    // Validate headers
    if (headers) {
      const headerValidator = this.validators.get(`${key}:headers`);
      if (headerValidator) {
        const valid = headerValidator(headers);
        if (!valid) {
          errors.push(...this.formatAjvErrors(headerValidator.errors, 'headers'));
        }
      }
    }

    // Validate query parameters
    if (query) {
      const queryValidator = this.validators.get(`${key}:query`);
      if (queryValidator) {
        const valid = queryValidator(query);
        if (!valid) {
          errors.push(...this.formatAjvErrors(queryValidator.errors, 'query parameters'));
        }
      }
    }

    return {
      valid: errors.length === 0,
      errors: errors.length > 0 ? errors : undefined,
    };
  }

  /**
   * Validate response against contract
   */
  validateResponse(
    method: string,
    path: string,
    statusCode: number,
    data?: any,
    headers?: Record<string, string>
  ): ValidationResult {
    const key = `${method.toUpperCase()} ${this.normalizePath(path)}`;
    const errors: ValidationError[] = [];

    // Validate response body
    const responseValidator = this.validators.get(`${key}:response:${statusCode}`);
    if (responseValidator) {
      if (data !== undefined) {
        const valid = responseValidator(data);
        if (!valid) {
          errors.push(...this.formatAjvErrors(responseValidator.errors, 'response body'));
        }
      }
    } else if (this.strictMode) {
      // Check if any response is defined for this status code
      const operation = this.getOperation(method, path);
      if (operation && !operation.responses?.[statusCode]) {
        errors.push({
          path: 'statusCode',
          message: `Unexpected status code ${statusCode}`,
        });
      }
    }

    return {
      valid: errors.length === 0,
      errors: errors.length > 0 ? errors : undefined,
    };
  }

  /**
   * Create an axios interceptor for automatic validation
   */
  createAxiosInterceptor(client: any = axios): void {
    // Request interceptor
    client.interceptors.request.use(
      (config: AxiosRequestConfig) => {
        const startTime = Date.now();
        (config as any).metadata = { startTime };
        
        const path = this.extractPath(config.url || '');
        const method = config.method || 'GET';
        
        const requestValidation = this.validateRequest(
          method,
          path,
          config.data,
          config.headers as Record<string, string>,
          config.params
        );
        
        if (!requestValidation.valid) {
          console.warn('Request contract violation:', requestValidation.errors);
          if (this.strictMode) {
            throw new Error(`Contract violation: ${JSON.stringify(requestValidation.errors)}`);
          }
        }
        
        return config;
      },
      (error: any) => Promise.reject(error)
    );

    // Response interceptor
    client.interceptors.response.use(
      (response: AxiosResponse) => {
        const duration = Date.now() - (((response.config as any).metadata?.startTime) || Date.now());
        const path = this.extractPath(response.config.url || '');
        const method = response.config.method || 'GET';
        
        const responseValidation = this.validateResponse(
          method,
          path,
          response.status,
          response.data,
          response.headers as Record<string, string>
        );
        
        const testResult: ContractTestResult = {
          endpoint: path,
          method: method.toUpperCase(),
          response: responseValidation,
          statusCode: response.status,
          timestamp: new Date(),
          duration,
        };
        
        this.testResults.push(testResult);
        
        if (!responseValidation.valid) {
          console.warn('Response contract violation:', responseValidation.errors);
          if (this.strictMode) {
            throw new Error(`Contract violation: ${JSON.stringify(responseValidation.errors)}`);
          }
        }
        
        return response;
      },
      (error: any) => Promise.reject(error)
    );
  }

  /**
   * Normalize path for matching against OpenAPI patterns
   */
  private normalizePath(path: string): string {
    // Remove query parameters
    path = path.split('?')[0];
    
    // Remove base URL if present
    if (path.includes('://')) {
      const url = new URL(path);
      path = url.pathname;
    }
    
    // Match against OpenAPI patterns
    if (this.spec.paths) {
      for (const pattern of Object.keys(this.spec.paths)) {
        const regex = pattern
          .replace(/\{([^}]+)\}/g, '([^/]+)') // Replace {param} with regex
          .replace(/\//g, '\\/'); // Escape slashes
        
        if (new RegExp(`^${regex}$`).test(path)) {
          return pattern;
        }
      }
    }
    
    return path;
  }

  /**
   * Extract path from URL
   */
  private extractPath(url: string): string {
    try {
      if (url.includes('://')) {
        return new URL(url).pathname;
      }
      return url.split('?')[0];
    } catch {
      return url;
    }
  }

  /**
   * Get operation from spec
   */
  private getOperation(method: string, path: string): OpenAPIV3.OperationObject | undefined {
    const normalizedPath = this.normalizePath(path);
    const pathItem = this.spec.paths?.[normalizedPath];
    if (!pathItem) return undefined;
    
    return pathItem[method.toLowerCase() as keyof OpenAPIV3.PathItemObject] as OpenAPIV3.OperationObject;
  }

  /**
   * Format AJV errors into ValidationError objects
   */
  private formatAjvErrors(ajvErrors: any[] | null | undefined, context: string): ValidationError[] {
    if (!ajvErrors) return [];
    
    return ajvErrors.map(error => ({
      path: error.instancePath || context,
      message: error.message || 'Validation failed',
      expected: error.params?.allowedValues || error.params?.type || error.schema,
      actual: error.data,
      schemaPath: error.schemaPath,
    }));
  }

  /**
   * Generate contract test report
   */
  generateReport(): {
    total: number;
    passed: number;
    failed: number;
    violations: ContractTestResult[];
    summary: string;
  } {
    const violations = this.testResults.filter(r => 
      (r.request && !r.request.valid) || 
      (r.response && !r.response.valid)
    );
    
    return {
      total: this.testResults.length,
      passed: this.testResults.length - violations.length,
      failed: violations.length,
      violations,
      summary: `Contract validation: ${this.testResults.length - violations.length}/${this.testResults.length} passed`,
    };
  }

  /**
   * Clear test results
   */
  clearResults(): void {
    this.testResults = [];
  }

  /**
   * Get all test results
   */
  getResults(): ContractTestResult[] {
    return [...this.testResults];
  }

  /**
   * Validate a complete API workflow
   */
  async validateWorkflow(
    name: string,
    steps: Array<{
      method: string;
      path: string;
      data?: any;
      headers?: Record<string, string>;
      query?: Record<string, any>;
      expectedStatus?: number;
      validateResponse?: (response: any) => boolean;
    }>
  ): Promise<{
    name: string;
    valid: boolean;
    steps: Array<{ step: number; valid: boolean; errors?: ValidationError[] }>;
  }> {
    const results: Array<{ step: number; valid: boolean; errors?: ValidationError[] }> = [];
    
    for (let i = 0; i < steps.length; i++) {
      const step = steps[i];
      const requestValidation = this.validateRequest(
        step.method,
        step.path,
        step.data,
        step.headers,
        step.query
      );
      
      results.push({
        step: i + 1,
        valid: requestValidation.valid,
        errors: requestValidation.errors,
      });
    }
    
    return {
      name,
      valid: results.every(r => r.valid),
      steps: results,
    };
  }
}

// Export singleton instance
export const contractValidator = new ContractValidator();

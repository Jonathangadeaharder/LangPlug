# Test Fixing and Code Cleanup Plan

This plan outlines the steps to get all tests passing and improve the overall quality of the codebase.

## 1. Backend Tests

The backend tests are currently failing to run due to a missing `LANGPLUG_SECRET_KEY` environment variable.

**Plan:**

1.  **Fix Configuration:**
    - Create a `.env` file in the `Backend` directory (if it doesn't exist) and add a `LANGPLUG_SECRET_KEY` with a randomly generated secret key. This file should be added to `.gitignore` to avoid committing secrets.
    - Alternatively, modify the `Settings` class in `core/config.py` to have a default value for `LANGPLUG_SECRET_KEY` for testing purposes. However, using an environment variable is the recommended approach.
2.  **Run Backend Tests:**
    - After fixing the configuration, run the backend tests again to ensure they all pass.
3.  **Code Cleanup:**
    - Review the `core/config.py` file and the overall configuration management to ensure that it's robust and easy to work with for both development and testing.
    - Add documentation to the `README.md` in the `Backend` directory to explain the required environment variables for running the tests.

## 2. Frontend Tests

The frontend tests are failing with an "Invalid credentials" error in the authentication-related tests.

**Plan:**

1.  **Investigate Auth Tests:**
    - Examine the code in `src/store/__tests__/useAuthStore.test.ts` to understand how it's handling authentication and credentials.
    - Check if there are any hardcoded credentials or tokens that might be invalid.
2.  **Fix Auth Tests:**
    - If hardcoded credentials are the issue, replace them with mock credentials or use a mocking library to simulate the authentication flow.
    - Ensure that the tests are not making actual network requests to an authentication server. Use mock API responses instead.
3.  **Run Frontend Tests:**
    - After fixing the authentication tests, run all frontend tests to ensure they pass.
4.  **Code Cleanup:**
    - Review all frontend tests to ensure that they are not making any external network requests.
    - Improve the mocking strategy for API requests to make the tests more robust and easier to maintain.

## 3. Contract Tests

The contract tests are failing because the `test:contract` script is missing from the `package.json` file.

**Plan:**

1.  **Add Contract Test Script:**
    - Add a `test:contract` script to the `scripts` section of the `Frontend/package.json` file. The content of the script will depend on how the contract tests are implemented. I will need to investigate the project to find the correct command. I will start by looking for files related to contract testing in the `Frontend` directory.
2.  **Run Contract Tests:**
    - After adding the script, run the contract tests to ensure they pass.
3.  **Code Cleanup:**
    - Document the contract testing setup and how to run the tests in the `Frontend/README.md` file.

This plan provides a clear path to resolving all test failures and improving the codebase. I will start by addressing the backend tests, as the configuration error is preventing any of them from running.

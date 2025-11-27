# Integration with start-all.bat Script

**Date**: 2025-10-01
**Status**: ✅ Complete

## Summary

Playwright E2E tests now automatically use the existing `scripts/start-all.bat` script to launch both backend and frontend servers before running tests.

---

## Changes Made

### 1. Updated playwright.config.ts

**File**: `Frontend/playwright.config.ts`

**Changes**:

- ✅ Added `path` import for cross-platform path resolution
- ✅ Changed `baseURL` from `http://localhost:5173` to `http://localhost:3000`
- ✅ Configured `webServer` to use `scripts/start-all.bat`
- ✅ Set appropriate timeout (120 seconds) for server startup

**Configuration**:

```typescript
webServer: {
  command: path.resolve(__dirname, '..', 'scripts', 'start-all.bat'),
  url: 'http://localhost:3000',
  reuseExistingServer: !process.env.CI,
  timeout: 120000,
  stdout: 'pipe',
  stderr: 'pipe',
}
```

### 2. Updated README.md

**File**: `Frontend/tests/e2e/README.md`

**Changes**:

- ✅ Updated prerequisites to explain automatic server startup
- ✅ Changed all port references from 5173 to 3000 (frontend) and 8000 (backend)
- ✅ Updated "Running the Tests" section with automatic startup explanation
- ✅ Enhanced troubleshooting section with start-all.bat specific guidance
- ✅ Added instructions for stopping servers with `scripts/stop-all.bat`

### 3. Updated LAYER_7_COMPLETION_SUMMARY.md

**File**: `Backend/docs/LAYER_7_COMPLETION_SUMMARY.md`

**Changes**:

- ✅ Updated execution instructions to reflect automatic startup
- ✅ Added explanation of start-all.bat integration
- ✅ Updated expected output with correct ports

---

## How It Works

### Automatic Server Startup

When you run `npm run test:e2e`, Playwright will:

1. **Execute start-all.bat**:
   - Starts backend on port 8000 with AI models
   - Starts frontend on port 3000 with correct API URL

2. **Wait for Frontend**:
   - Polls `http://localhost:3000` until ready
   - Timeout: 120 seconds (2 minutes)

3. **Run Tests**:
   - Executes all 13 E2E tests
   - Tests use `baseURL: http://localhost:3000`

4. **Keep Servers Running**:
   - Servers continue running after tests complete
   - Use `scripts/stop-all.bat` to stop them

### Port Configuration

| Service          | Port | URL                            |
| ---------------- | ---- | ------------------------------ |
| **Backend**      | 8000 | `http://localhost:8000`        |
| **Frontend**     | 3000 | `http://localhost:3000`        |
| **API Docs**     | 8000 | `http://localhost:8000/docs`   |
| **Health Check** | 8000 | `http://localhost:8000/health` |

**Note**: Frontend port changed from 5173 (default Vite) to 3000 (configured by start-all.bat)

---

## Benefits

### 1. Consistency

- Tests use the same startup script as development
- Same ports, same environment variables
- Reduces "works on my machine" issues

### 2. Simplicity

- No need to manually start servers before testing
- Single command runs everything: `npm run test:e2e`
- Automatic cleanup with `scripts/stop-all.bat`

### 3. Completeness

- Tests run against full stack (backend + frontend)
- Backend includes AI models
- Frontend gets correct API URL configuration

### 4. CI/CD Ready

- Automatic server startup works in CI environments
- Proper timeout handling
- Clean shutdown support

---

## Usage Examples

### Basic Test Run

```bash
cd Frontend
npm run test:e2e

# Servers start automatically
# Tests run
# Servers keep running

# When done:
cd ..
scripts\stop-all.bat
```

### Interactive Testing

```bash
cd Frontend
npm run test:e2e:ui

# Servers start automatically
# Playwright UI opens
# Run/debug tests interactively
```

### Manual Server Control

```bash
# Start servers manually first
scripts\start-all.bat

# Run tests (will reuse existing servers)
cd Frontend
npm run test:e2e

# Stop servers
cd ..
scripts\stop-all.bat
```

---

## Troubleshooting

### Servers Don't Start

**Issue**: Playwright times out waiting for servers

**Solutions**:

1. Check if ports 3000 or 8000 are already in use:

   ```bash
   netstat -ano | findstr :3000
   netstat -ano | findstr :8000
   ```

2. Stop existing servers:

   ```bash
   scripts\stop-all.bat
   ```

3. Manually start to see errors:
   ```bash
   scripts\start-all.bat
   # Check console output
   ```

### Wrong Port in Tests

**Issue**: Tests try to access `localhost:5173` instead of `localhost:3000`

**Solution**:

- Check `baseURL` in `playwright.config.ts` is set to `http://localhost:3000`
- Verify tests use relative URLs like `'/vocabulary-game'` (not absolute URLs)

### Backend Not Loading AI Models

**Issue**: Backend starts but AI models fail to load

**Solution**:

- Check `Backend/api_venv` is properly installed
- Verify Python dependencies are current
- Review Backend console window for error messages
- Start backend manually to debug: `Backend/start_backend_with_models.py`

---

## CI/CD Integration

For CI environments (GitHub Actions, etc.), the configuration automatically handles:

- `reuseExistingServer: !process.env.CI` - Always starts fresh servers in CI
- Proper timeout handling (120 seconds)
- Server output piping for debugging

### Example GitHub Actions

```yaml
- name: Run E2E Tests
  run: |
    cd Frontend
    npm run test:e2e
  env:
    CI: true
```

---

## Technical Details

### Path Resolution

Uses `path.resolve(__dirname, '..', 'scripts', 'start-all.bat')` to:

- Work from any directory
- Handle Windows paths correctly
- Support both WSL and native Windows

### Server Detection

Playwright polls `http://localhost:3000` to detect when frontend is ready:

- Checks every 100ms
- Timeout: 120 seconds
- Considers any 2xx/3xx response as "ready"

### Process Management

- `webServer` creates child processes for backend and frontend
- Processes continue running after tests complete
- Use `scripts/stop-all.bat` for cleanup
- In CI mode (`process.env.CI`), servers are automatically killed after tests

---

## Comparison: Before vs After

### Before

```bash
# Manual steps:
1. cd Backend
2. api_venv\Scripts\activate
3. python -m uvicorn core.app:app --reload
4. Open new terminal
5. cd Frontend
6. npm run dev
7. Wait for both to start
8. cd Frontend
9. npm run test:e2e
10. Stop servers manually
```

### After

```bash
# Single command:
cd Frontend
npm run test:e2e

# Done!
```

---

## Files Modified

### Configuration Files

1. ✅ `Frontend/playwright.config.ts` - Server startup configuration
2. ✅ `Frontend/tests/e2e/vocabulary-game.spec.ts` - Fixed typo (line 96)

### Documentation Files

3. ✅ `Frontend/tests/e2e/README.md` - Updated instructions and ports
4. ✅ `Backend/docs/LAYER_7_COMPLETION_SUMMARY.md` - Updated execution guide
5. ✅ `Frontend/tests/e2e/INTEGRATION_WITH_START_ALL.md` - This file

---

## Validation

### Test the Integration

1. **Stop any running servers**:

   ```bash
   scripts\stop-all.bat
   ```

2. **Verify ports are free**:

   ```bash
   netstat -ano | findstr :3000
   netstat -ano | findstr :8000
   # Should return nothing
   ```

3. **Run tests**:

   ```bash
   cd Frontend
   npm run test:e2e
   ```

4. **Expected behavior**:
   - New console windows open for Backend and Frontend
   - Backend starts on port 8000
   - Frontend starts on port 3000
   - After ~30 seconds, tests begin
   - All 13 tests pass
   - Console windows remain open

5. **Clean up**:
   ```bash
   cd ..
   scripts\stop-all.bat
   ```

---

## Next Steps

### Optional Enhancements

1. **Add health check endpoint polling** - Wait for backend `/health` endpoint specifically
2. **Add server logs to test report** - Capture stdout/stderr in HTML report
3. **Parallel server startup** - Start backend and frontend simultaneously
4. **Automatic cleanup** - Kill servers automatically after tests (optional)

---

## Conclusion

Playwright E2E tests now seamlessly integrate with the existing `scripts/start-all.bat` infrastructure:

- ✅ Automatic server startup
- ✅ Correct port configuration (3000/8000)
- ✅ Consistent with development workflow
- ✅ CI/CD ready
- ✅ Fully documented

**Status**: ✅ Integration Complete
**Ready**: Run with `npm run test:e2e`

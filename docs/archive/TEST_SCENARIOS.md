# LangPlug E2E Test Scenarios

## Test Suite Overview
This document defines all test scenarios to be executed with Chrome DevTools MCP and converted to Playwright tests.

## Test Categories

### 1. AUTHENTICATION TESTS

#### 1.1 User Registration
- **Scenario**: Register with valid credentials
  - Email: testuser@example.com
  - Username: testuser
  - Password: ValidPass123!
  - Expected: User created, redirect to dashboard

- **Scenario**: Register with invalid password (no special char)
  - Email: testuser2@example.com
  - Username: testuser2
  - Password: InvalidPass123
  - Expected: 422 error with validation message

- **Scenario**: Register with duplicate email
  - Email: testuser@example.com (already exists)
  - Expected: Error response

- **Scenario**: Register with weak password (< 12 chars)
  - Password: Short123!
  - Expected: Validation error

#### 1.2 User Login
- **Scenario**: Login with valid credentials
  - Email: testuser@example.com
  - Password: ValidPass123!
  - Expected: JWT token, redirect to /videos

- **Scenario**: Login with invalid email
  - Email: nonexistent@example.com
  - Expected: 401 error

- **Scenario**: Login with wrong password
  - Email: testuser@example.com
  - Password: WrongPass123!
  - Expected: 401 error

- **Scenario**: Login persists session
  - Login → Navigate away → Verify still logged in
  - Expected: User stays authenticated

#### 1.3 User Logout
- **Scenario**: Logout and verify session cleared
  - Click logout → Redirect to home
  - Expected: Session cleared, can't access protected pages

### 2. VOCABULARY TESTS

#### 2.1 Mark Word as Known
- **Scenario**: Mark single word as known
  - Click on word "Haus"
  - Expected: Word count increases, progress updates

- **Scenario**: Mark multiple words as known
  - Mark 5 words
  - Expected: Count increases for each, stats update

- **Scenario**: Mark All Known button
  - Click "Mark All Known" on A1 level
  - Expected: All 715 A1 words marked, stats update

#### 2.2 Unmark Words
- **Scenario**: Unmark previously known word
  - Mark word → Click word again
  - Expected: Word unmarked, count decreases

- **Scenario**: Unmark All button
  - Mark all → Click "Unmark All"
  - Expected: All words unmarked, count resets to 0

- **Scenario**: Remove word via × button
  - Click × button next to word
  - Expected: Word progress reset

#### 2.3 Search Functionality
- **Scenario**: Search for word by name
  - Search "Haus"
  - Expected: Only "Haus" displayed

- **Scenario**: Search with partial match
  - Search "ab"
  - Expected: All words starting with "ab" shown

- **Scenario**: Clear search
  - Search → Clear input
  - Expected: Full vocabulary list restored

#### 2.4 Pagination
- **Scenario**: Navigate to next page
  - Click "Next" button
  - Expected: Page 2 of A1 words displayed (words 101-200)

- **Scenario**: Navigate to previous page
  - On page 2 → Click "Previous"
  - Expected: Back to page 1

- **Scenario**: Verify correct offset
  - Check word counts match pagination
  - Expected: 100 words per page (except last)

#### 2.5 Level Navigation
- **Scenario**: Switch between levels
  - A1 → A2 → B1
  - Expected: Each level shows correct word count

- **Scenario**: Level progress tracking
  - Mark words in A1 → Switch to A2
  - Expected: A1 shows "1 / 715", returns to A1 and count persists

#### 2.6 Statistics
- **Scenario**: Progress calculation
  - Mark 100 words out of 715 A1
  - Expected: Progress shows ~14%

- **Scenario**: Total stats update
  - Mark words across levels
  - Expected: Total words known updates

### 3. NAVIGATION TESTS

#### 3.1 Navigation Flow
- **Scenario**: Navigate from Videos → Vocabulary → Back to Videos
  - Expected: No errors, data persists

- **Scenario**: Profile menu
  - Click profile → Verify menu shows username
  - Expected: Profile dropdown works

### 4. ERROR HANDLING TESTS

#### 4.1 Validation Errors
- **Scenario**: Password validation message display
  - Register with missing special char
  - Expected: Specific error message shown (not generic)

#### 4.2 Network Errors
- **Scenario**: Retry on connection failure
  - Simulate network error
  - Expected: Graceful handling, retry option

### 5. DATA PERSISTENCE TESTS

#### 5.1 Refresh Page
- **Scenario**: Refresh on any page while logged in
  - Expected: User stays authenticated, data reloads

#### 5.2 Local Storage
- **Scenario**: Verify auth token in storage
  - Expected: JWT token persisted

---

## Execution Order

1. Clear all test data / reset user (testuser@example.com)
2. Test Registration → Login
3. Test Vocabulary operations
4. Test Navigation
5. Test Logout
6. Test Error scenarios

## Expected Test Coverage

- **Positive Tests**: 70%
- **Negative Tests**: 20%
- **Edge Cases**: 10%

Total: ~35 test scenarios

---

## Notes

- Use Chrome DevTools MCP for manual execution
- Document each step and result
- Capture network requests and responses
- Screenshot before/after states for visual verification
- Convert successful flows to Playwright tests

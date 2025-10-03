# LangPlug Backend - API Integration Guide

**Version**: 1.0
**Last Updated**: 2025-10-03

Complete guide for integrating with the LangPlug Backend API.

---

## Table of Contents

1. [API Overview](#api-overview)
2. [Authentication](#authentication)
3. [Common Patterns](#common-patterns)
4. [Error Handling](#error-handling)
5. [Client Examples](#client-examples)
6. [WebSocket Integration](#websocket-integration)
7. [API Reference](#api-reference)
8. [Best Practices](#best-practices)

---

## API Overview

### Base URL

```
http://localhost:8000    # Development
https://api.langplug.com # Production
```

### API Design Principles

- **RESTful**: Standard HTTP methods (GET, POST, PUT, DELETE)
- **JSON**: All requests and responses use JSON
- **Stateless**: Each request contains all necessary information
- **Async-first**: Built on FastAPI for high concurrency
- **OpenAPI**: Auto-generated documentation at `/docs`

### Interactive Documentation

Visit these URLs when server is running:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

---

## Authentication

### Overview

LangPlug uses **JWT (JSON Web Tokens)** for authentication:

1. **Register** or **Login** to receive tokens
2. **Access Token** (short-lived): Include in `Authorization` header
3. **Refresh Token** (long-lived): Stored in HTTP-only cookie
4. **Token Refresh**: Exchange refresh token for new access token

### Authentication Flow

```
┌─────────┐                           ┌─────────┐
│ Client  │                           │ Server  │
└────┬────┘                           └────┬────┘
     │                                     │
     │ POST /api/auth/register             │
     │ {username, password, email}         │
     ├────────────────────────────────────>│
     │                                     │
     │    201 Created                      │
     │    {user data}                      │
     │<────────────────────────────────────┤
     │                                     │
     │ POST /api/auth/login                │
     │ {username, password}                │
     ├────────────────────────────────────>│
     │                                     │
     │    200 OK                           │
     │    {access_token, token_type}       │
     │    Set-Cookie: refresh_token        │
     │<────────────────────────────────────┤
     │                                     │
     │ GET /api/profile                    │
     │ Authorization: Bearer <token>       │
     ├────────────────────────────────────>│
     │                                     │
     │    200 OK                           │
     │    {profile data}                   │
     │<────────────────────────────────────┤
```

### Registration

**Endpoint**: `POST /api/auth/register`

**Request**:
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "SecurePass123!"
}
```

**Response** (201 Created):
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "username": "johndoe",
  "email": "john@example.com",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2025-10-03T10:00:00"
}
```

**Password Requirements**:
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- At least one special character

### Login

**Endpoint**: `POST /api/auth/login`

**Request**:
```json
{
  "username": "johndoe",
  "password": "SecurePass123!"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Headers Received**:
```
Set-Cookie: refresh_token=<refresh_token>; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=604800
```

### Using Access Token

Include access token in `Authorization` header for all protected endpoints:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Token Refresh

**Endpoint**: `POST /api/auth/token/refresh`

**Request**: No body (refresh token from cookie)

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Token Lifetimes**:
- Access Token: 30 minutes
- Refresh Token: 7 days

---

## Common Patterns

### Pagination

Endpoints that return lists support pagination:

**Query Parameters**:
- `skip` (integer): Number of items to skip (default: 0)
- `limit` (integer): Maximum items to return (default: 50, max: 100)

**Example**:
```
GET /api/vocabulary/library?skip=0&limit=20
```

**Response**:
```json
{
  "items": [...],
  "total": 150,
  "skip": 0,
  "limit": 20
}
```

### Filtering

Filter results using query parameters:

```
GET /api/vocabulary/library?level=A1&status=learning
```

**Common Filters**:
- `level`: CEFR level (A1, A2, B1, B2, C1, C2)
- `status`: Word status (learning, known, unknown)
- `search`: Text search query

### Sorting

Sort results using `sort` and `order` parameters:

```
GET /api/vocabulary/library?sort=word&order=asc
GET /api/videos?sort=created_at&order=desc
```

**Sort Options**:
- `sort`: Field to sort by (word, created_at, difficulty, etc.)
- `order`: `asc` (ascending) or `desc` (descending)

### Batch Operations

Some endpoints support batch operations:

**Example** (Mark multiple words):
```json
POST /api/vocabulary/mark-batch

{
  "words": [
    {"word": "Hallo", "status": "known"},
    {"word": "Welt", "status": "learning"}
  ]
}
```

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | When It Occurs |
|------|---------|----------------|
| 200 | OK | Request succeeded |
| 201 | Created | Resource created successfully |
| 204 | No Content | Success with no response body |
| 400 | Bad Request | Invalid request data |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Authenticated but not authorized |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Resource already exists (e.g., duplicate username) |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error (bug or outage) |

### Error Response Format

All errors return JSON with `detail` field:

**Simple Error**:
```json
{
  "detail": "User not found"
}
```

**Validation Error** (422):
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    },
    {
      "loc": ["body", "password"],
      "msg": "ensure this value has at least 8 characters",
      "type": "value_error.any_str.min_length"
    }
  ]
}
```

### Error Handling Examples

**Python**:
```python
import requests

response = requests.post("http://localhost:8000/api/auth/login", json={
    "username": "johndoe",
    "password": "wrong"
})

if response.status_code == 200:
    tokens = response.json()
    print(f"Logged in: {tokens['access_token']}")
elif response.status_code == 401:
    print("Invalid credentials")
elif response.status_code == 422:
    errors = response.json()["detail"]
    for error in errors:
        print(f"Validation error in {error['loc']}: {error['msg']}")
else:
    print(f"Unexpected error: {response.status_code}")
```

**JavaScript**:
```javascript
try {
  const response = await fetch('http://localhost:8000/api/auth/login', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({username: 'johndoe', password: 'wrong'})
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Request failed');
  }

  const data = await response.json();
  console.log('Logged in:', data.access_token);
} catch (error) {
  console.error('Login failed:', error.message);
}
```

---

## Client Examples

### Python Client

#### Basic Setup

```python
import requests
from typing import Optional


class LangPlugClient:
    """Python client for LangPlug API"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.access_token: Optional[str] = None

    def register(self, username: str, email: str, password: str) -> dict:
        """Register new user"""
        response = self.session.post(
            f"{self.base_url}/api/auth/register",
            json={"username": username, "email": email, "password": password}
        )
        response.raise_for_status()
        return response.json()

    def login(self, username: str, password: str) -> dict:
        """Login and store access token"""
        response = self.session.post(
            f"{self.base_url}/api/auth/login",
            json={"username": username, "password": password}
        )
        response.raise_for_status()
        data = response.json()
        self.access_token = data["access_token"]
        # Refresh token is automatically stored in session cookies
        return data

    def _get_headers(self) -> dict:
        """Get headers with authentication"""
        if not self.access_token:
            raise ValueError("Not authenticated. Call login() first.")
        return {"Authorization": f"Bearer {self.access_token}"}

    def get_profile(self) -> dict:
        """Get current user profile"""
        response = self.session.get(
            f"{self.base_url}/api/profile",
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()

    def get_vocabulary(self, skip: int = 0, limit: int = 50) -> dict:
        """Get vocabulary library"""
        response = self.session.get(
            f"{self.base_url}/api/vocabulary/library",
            headers=self._get_headers(),
            params={"skip": skip, "limit": limit}
        )
        response.raise_for_status()
        return response.json()

    def mark_word(self, word: str, status: str) -> dict:
        """Mark word as known/learning/unknown"""
        response = self.session.post(
            f"{self.base_url}/api/vocabulary/mark-known",
            headers=self._get_headers(),
            json={"word": word, "status": status}
        )
        response.raise_for_status()
        return response.json()

    def upload_video(self, file_path: str, series: str) -> dict:
        """Upload video file"""
        with open(file_path, 'rb') as f:
            files = {'file': (file_path, f, 'video/mp4')}
            response = self.session.post(
                f"{self.base_url}/api/videos/upload/{series}",
                headers=self._get_headers(),
                files=files
            )
        response.raise_for_status()
        return response.json()


# Usage Example
if __name__ == "__main__":
    client = LangPlugClient()

    # Register
    client.register("testuser", "test@example.com", "SecurePass123!")

    # Login
    tokens = client.login("testuser", "SecurePass123!")
    print(f"Access token: {tokens['access_token'][:20]}...")

    # Get profile
    profile = client.get_profile()
    print(f"Logged in as: {profile['username']}")

    # Get vocabulary
    vocab = client.get_vocabulary(limit=10)
    print(f"Vocabulary items: {len(vocab.get('items', []))}")

    # Mark word as known
    result = client.mark_word("Hallo", "known")
    print(f"Marked word: {result}")
```

### JavaScript/TypeScript Client

#### Using Fetch API

```javascript
class LangPlugClient {
  constructor(baseUrl = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
    this.accessToken = null;
  }

  async register(username, email, password) {
    const response = await fetch(`${this.baseUrl}/api/auth/register`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({username, email, password})
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Registration failed');
    }

    return await response.json();
  }

  async login(username, password) {
    const response = await fetch(`${this.baseUrl}/api/auth/login`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({username, password}),
      credentials: 'include'  // Important: Store refresh token cookie
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Login failed');
    }

    const data = await response.json();
    this.accessToken = data.access_token;
    return data;
  }

  _getHeaders() {
    if (!this.accessToken) {
      throw new Error('Not authenticated. Call login() first.');
    }
    return {
      'Authorization': `Bearer ${this.accessToken}`,
      'Content-Type': 'application/json'
    };
  }

  async getProfile() {
    const response = await fetch(`${this.baseUrl}/api/profile`, {
      headers: this._getHeaders(),
      credentials: 'include'
    });

    if (!response.ok) throw new Error('Failed to get profile');
    return await response.json();
  }

  async getVocabulary(skip = 0, limit = 50) {
    const params = new URLSearchParams({skip, limit});
    const response = await fetch(
      `${this.baseUrl}/api/vocabulary/library?${params}`,
      {headers: this._getHeaders(), credentials: 'include'}
    );

    if (!response.ok) throw new Error('Failed to get vocabulary');
    return await response.json();
  }

  async markWord(word, status) {
    const response = await fetch(`${this.baseUrl}/api/vocabulary/mark-known`, {
      method: 'POST',
      headers: this._getHeaders(),
      credentials: 'include',
      body: JSON.stringify({word, status})
    });

    if (!response.ok) throw new Error('Failed to mark word');
    return await response.json();
  }

  async uploadVideo(file, series) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseUrl}/api/videos/upload/${series}`, {
      method: 'POST',
      headers: {'Authorization': `Bearer ${this.accessToken}`},
      credentials: 'include',
      body: formData
    });

    if (!response.ok) throw new Error('Failed to upload video');
    return await response.json();
  }
}

// Usage Example
const client = new LangPlugClient();

async function main() {
  try {
    // Register
    await client.register('testuser', 'test@example.com', 'SecurePass123!');

    // Login
    const tokens = await client.login('testuser', 'SecurePass123!');
    console.log('Logged in:', tokens.access_token.substring(0, 20) + '...');

    // Get profile
    const profile = await client.getProfile();
    console.log('User:', profile.username);

    // Get vocabulary
    const vocab = await client.getVocabulary(0, 10);
    console.log('Vocabulary items:', vocab.items?.length || 0);

    // Mark word
    const result = await client.markWord('Hallo', 'known');
    console.log('Marked word:', result);

  } catch (error) {
    console.error('Error:', error.message);
  }
}

main();
```

#### Using Axios

```javascript
import axios from 'axios';

class LangPlugClient {
  constructor(baseUrl = 'http://localhost:8000') {
    this.client = axios.create({
      baseURL: baseUrl,
      withCredentials: true  // Important for cookies
    });

    this.accessToken = null;

    // Add auth interceptor
    this.client.interceptors.request.use(config => {
      if (this.accessToken) {
        config.headers.Authorization = `Bearer ${this.accessToken}`;
      }
      return config;
    });

    // Add response error handler
    this.client.interceptors.response.use(
      response => response,
      async error => {
        if (error.response?.status === 401 && this.accessToken) {
          // Token expired, try refresh
          try {
            await this.refreshToken();
            // Retry original request
            return this.client.request(error.config);
          } catch (refreshError) {
            // Refresh failed, user needs to login again
            this.accessToken = null;
            throw refreshError;
          }
        }
        throw error;
      }
    );
  }

  async register(username, email, password) {
    const response = await this.client.post('/api/auth/register', {
      username, email, password
    });
    return response.data;
  }

  async login(username, password) {
    const response = await this.client.post('/api/auth/login', {
      username, password
    });
    this.accessToken = response.data.access_token;
    return response.data;
  }

  async refreshToken() {
    const response = await this.client.post('/api/auth/token/refresh');
    this.accessToken = response.data.access_token;
    return response.data;
  }

  async getProfile() {
    const response = await this.client.get('/api/profile');
    return response.data;
  }

  async getVocabulary(skip = 0, limit = 50) {
    const response = await this.client.get('/api/vocabulary/library', {
      params: {skip, limit}
    });
    return response.data;
  }

  async markWord(word, status) {
    const response = await this.client.post('/api/vocabulary/mark-known', {
      word, status
    });
    return response.data;
  }

  async uploadVideo(file, series) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await this.client.post(`/api/videos/upload/${series}`, formData, {
      headers: {'Content-Type': 'multipart/form-data'}
    });
    return response.data;
  }
}

export default LangPlugClient;
```

### cURL Examples

#### Register
```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "SecurePass123!"
  }'
```

#### Login
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{
    "username": "testuser",
    "password": "SecurePass123!"
  }'
```

#### Get Profile (with token)
```bash
curl -X GET "http://localhost:8000/api/profile" \
  -H "Authorization: Bearer <access_token>" \
  -b cookies.txt
```

#### Upload Video
```bash
curl -X POST "http://localhost:8000/api/videos/upload/my-series" \
  -H "Authorization: Bearer <access_token>" \
  -F "file=@/path/to/video.mp4"
```

---

## WebSocket Integration

### Connection

**Endpoint**: `ws://localhost:8000/ws/connect`

**Authentication**: Send token in first message after connection

### Python WebSocket Client

```python
import asyncio
import websockets
import json


async def connect_websocket(access_token: str):
    uri = "ws://localhost:8000/ws/connect"

    async with websockets.connect(uri) as websocket:
        # Send authentication
        await websocket.send(json.dumps({
            "type": "auth",
            "token": access_token
        }))

        # Wait for auth confirmation
        response = await websocket.recv()
        auth_result = json.loads(response)
        print(f"Auth result: {auth_result}")

        # Send messages
        await websocket.send(json.dumps({
            "type": "subscribe",
            "channel": "processing_updates"
        }))

        # Receive messages
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            print(f"Received: {data}")


# Usage
asyncio.run(connect_websocket("your_access_token"))
```

### JavaScript WebSocket Client

```javascript
class WebSocketClient {
  constructor(baseUrl = 'ws://localhost:8000') {
    this.baseUrl = baseUrl;
    this.ws = null;
  }

  connect(accessToken) {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(`${this.baseUrl}/ws/connect`);

      this.ws.onopen = () => {
        // Send authentication
        this.ws.send(JSON.stringify({
          type: 'auth',
          token: accessToken
        }));
      };

      this.ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.type === 'auth_success') {
          resolve();
        } else {
          console.log('Message:', data);
        }
      };

      this.ws.onerror = (error) => {
        reject(error);
      };

      this.ws.onclose = () => {
        console.log('WebSocket closed');
      };
    });
  }

  send(message) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      throw new Error('WebSocket not connected');
    }
  }

  close() {
    if (this.ws) {
      this.ws.close();
    }
  }
}

// Usage
const wsClient = new WebSocketClient();
await wsClient.connect(accessToken);

// Subscribe to updates
wsClient.send({
  type: 'subscribe',
  channel: 'processing_updates'
});
```

---

## API Reference

### Quick Reference

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/auth/register` | POST | No | Register new user |
| `/api/auth/login` | POST | No | Login and get tokens |
| `/api/auth/token/refresh` | POST | Cookie | Refresh access token |
| `/api/auth/me` | GET | Yes | Get current user info |
| `/api/profile` | GET | Yes | Get user profile |
| `/api/profile/languages` | PUT | Yes | Update language preferences |
| `/api/vocabulary/library` | GET | Yes | Get vocabulary library |
| `/api/vocabulary/mark-known` | POST | Yes | Mark word status |
| `/api/vocabulary/stats` | GET | Yes | Get learning statistics |
| `/api/videos` | GET | Yes | List videos |
| `/api/videos/upload/{series}` | POST | Yes | Upload video |
| `/api/game/start` | POST | Yes | Start game session |
| `/api/game/answer` | POST | Yes | Submit answer |
| `/ws/connect` | WS | Yes | WebSocket connection |

For complete API documentation, visit:
- **Interactive docs**: http://localhost:8000/docs
- **Route documentation**: See enhanced docstrings in `api/routes/` modules

---

## Best Practices

### 1. Token Management

✅ **DO**:
- Store access token in memory (not localStorage)
- Store refresh token in HTTP-only cookie
- Implement automatic token refresh
- Handle 401 responses gracefully

❌ **DON'T**:
- Store tokens in localStorage (XSS risk)
- Share tokens between users
- Use tokens after logout
- Hardcode tokens in code

### 2. Error Handling

✅ **DO**:
- Check response status codes
- Parse error details
- Show user-friendly messages
- Log errors for debugging
- Implement retry logic for network errors

❌ **DON'T**:
- Ignore error responses
- Show raw error messages to users
- Retry indefinitely
- Assume requests always succeed

### 3. Performance

✅ **DO**:
- Use pagination for large datasets
- Implement request caching
- Batch operations when possible
- Use WebSockets for real-time updates
- Compress large requests

❌ **DON'T**:
- Fetch all data at once
- Poll frequently (use WebSockets)
- Send unnecessary requests
- Upload huge files without chunking

### 4. Security

✅ **DO**:
- Use HTTPS in production
- Validate input on client side
- Sanitize user-generated content
- Implement CORS properly
- Use secure password requirements

❌ **DON'T**:
- Send sensitive data in URLs
- Trust client-side validation alone
- Store passwords in plain text
- Disable SSL certificate validation
- Hard-code API keys

---

## Testing with Postman/Insomnia

### Postman Collection Setup

1. **Create Environment**:
   - `baseUrl`: `http://localhost:8000`
   - `accessToken`: (leave empty, will be set automatically)

2. **Pre-request Script** (for authenticated requests):
   ```javascript
   // Check if access token exists
   const accessToken = pm.environment.get('accessToken');
   if (accessToken) {
       pm.request.headers.add({
           key: 'Authorization',
           value: `Bearer ${accessToken}`
       });
   }
   ```

3. **Test Script** (for login request):
   ```javascript
   if (pm.response.code === 200) {
       const jsonData = pm.response.json();
       pm.environment.set('accessToken', jsonData.access_token);
   }
   ```

### Example Requests

Import these into Postman/Insomnia:

```json
{
  "name": "LangPlug API",
  "requests": [
    {
      "name": "Register",
      "method": "POST",
      "url": "{{baseUrl}}/api/auth/register",
      "body": {
        "username": "testuser",
        "email": "test@example.com",
        "password": "SecurePass123!"
      }
    },
    {
      "name": "Login",
      "method": "POST",
      "url": "{{baseUrl}}/api/auth/login",
      "body": {
        "username": "testuser",
        "password": "SecurePass123!"
      }
    },
    {
      "name": "Get Profile",
      "method": "GET",
      "url": "{{baseUrl}}/api/profile",
      "headers": {
        "Authorization": "Bearer {{accessToken}}"
      }
    }
  ]
}
```

---

## Related Documentation

- **[DEVELOPER_SETUP.md](DEVELOPER_SETUP.md)** - Development environment setup
- **[CONFIGURATION.md](CONFIGURATION.md)** - Configuration reference
- **[API Routes Documentation](../api/routes/)** - Detailed endpoint docs
- **[Interactive API Docs](http://localhost:8000/docs)** - OpenAPI/Swagger UI

---

**Document Version**: 1.0
**Last Updated**: 2025-10-03
**Maintained By**: Development Team

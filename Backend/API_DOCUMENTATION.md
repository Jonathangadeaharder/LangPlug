# LangPlug API Documentation

## Overview

LangPlug is a German language learning platform that helps users learn vocabulary through interactive video content. The backend provides REST APIs for authentication, vocabulary management, video processing, and learning progress tracking.

**Base URL:** `http://localhost:8000`

**FastAPI Interactive Docs:** `http://localhost:8000/docs`

---

## Authentication

All API endpoints (except `/health` and auth endpoints) require authentication via Bearer token.

### Register User

**POST** `/auth/register`

Creates a new user account.

**Request Body:**
```json
{
  "username": "string",
  "email": "string", 
  "password": "string"
}
```

**Response:**
```json
{
  "message": "User created successfully",
  "user_id": "string"
}
```

**Error Codes:**
- `400`: Username already exists
- `422`: Validation error (weak password, invalid email)

### Login

**POST** `/auth/login`

Authenticates user and returns access token.

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "token": "string",
  "user_id": "string",
  "expires_in": 86400
}
```

**Error Codes:**
- `401`: Invalid credentials
- `422`: Missing required fields

### Get Current User

**GET** `/auth/me`

Returns information about the currently authenticated user.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "user_id": "string",
  "username": "string",
  "email": "string",
  "created_at": "2025-09-07T12:00:00Z"
}
```

### Logout

**POST** `/auth/logout`

Invalidates the current session token.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "message": "Logout successful"
}
```

---

## Videos

Endpoints for managing video content and subtitles.

### Get Available Videos

**GET** `/videos`

Returns list of available video content.

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `category` (optional): Filter by video category
- `difficulty` (optional): Filter by difficulty level (A1, A2, B1, B2)

**Response:**
```json
[
  {
    "id": "string",
    "title": "string",
    "description": "string", 
    "path": "string",
    "duration": 1200,
    "difficulty_level": "A1",
    "category": "comedy",
    "has_subtitles": true,
    "thumbnail": "string"
  }
]
```

### Get Video Subtitles

**GET** `/videos/subtitles/{subtitle_path}`

Returns subtitle content for a specific video.

**Headers:**
```
Authorization: Bearer <token>
```

**Path Parameters:**
- `subtitle_path`: Path to subtitle file

**Response:**
```json
{
  "subtitles": [
    {
      "start_time": 1.5,
      "end_time": 3.2,
      "text": "Hallo, wie geht es dir?",
      "index": 1
    }
  ],
  "total_segments": 150,
  "language": "de"
}
```

### Stream Video

**GET** `/videos/stream/{video_path}`

Returns video stream with range support for progressive loading.

**Headers:**
```
Authorization: Bearer <token>
Range: bytes=0-1023 (optional)
```

**Response:** Video stream data with appropriate headers

---

## Vocabulary

Endpoints for vocabulary management and learning progress.

### Get Vocabulary Statistics

**GET** `/vocabulary/library/stats`

Returns overall vocabulary learning statistics for the user.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "total_words": 2500,
  "known_words": 1200,
  "learning_words": 300,
  "mastered_words": 900,
  "levels": {
    "A1": {
      "total": 500,
      "known": 450,
      "percentage": 90
    },
    "A2": {
      "total": 600,
      "known": 400,
      "percentage": 67
    }
  }
}
```

### Get Vocabulary by Level

**GET** `/vocabulary/library/{level}`

Returns vocabulary words for a specific CEFR level.

**Headers:**
```
Authorization: Bearer <token>
```

**Path Parameters:**
- `level`: CEFR level (A1, A2, B1, B2, C1, C2)

**Query Parameters:**
- `category` (optional): Word category filter
- `status` (optional): Learning status (known, learning, new)
- `limit` (optional): Number of words to return (default: 100)
- `offset` (optional): Pagination offset (default: 0)

**Response:**
```json
{
  "level": "A1",
  "words": [
    {
      "word": "hallo",
      "translation": "hello",
      "category": "greetings",
      "status": "known",
      "difficulty_score": 1,
      "frequency_rank": 15,
      "learned_at": "2025-09-05T10:30:00Z"
    }
  ],
  "total_count": 500,
  "known_count": 450,
  "pagination": {
    "limit": 100,
    "offset": 0,
    "has_next": true
  }
}
```

### Mark Word as Known/Unknown

**POST** `/vocabulary/mark-known`

Updates the learning status of a vocabulary word.

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "word": "string",
  "known": true
}
```

**Response:**
```json
{
  "message": "Word status updated successfully",
  "word": "hallo",
  "status": "known",
  "updated_at": "2025-09-07T12:00:00Z"
}
```

### Get Blocking Words for Video

**GET** `/vocabulary/blocking-words`

Returns unknown vocabulary words that appear in a specific video, which might block comprehension.

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `video_path`: Path to the video file
- `threshold` (optional): Minimum frequency threshold (default: 3)

**Response:**
```json
{
  "video_path": "string",
  "blocking_words": [
    {
      "word": "verstehen",
      "frequency": 8,
      "translation": "to understand",
      "contexts": [
        {
          "text": "Ich kann das nicht verstehen",
          "timestamp": 45.2
        }
      ]
    }
  ],
  "total_unknown": 15,
  "comprehension_score": 85.5
}
```

---

## Processing

Endpoints for video and audio processing tasks.

### Transcribe Video

**POST** `/process/transcribe`

Starts transcription process for a video file.

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "video_path": "string",
  "language": "de",
  "model": "whisper-base"
}
```

**Response:**
```json
{
  "task_id": "string",
  "status": "pending",
  "estimated_duration": 120,
  "message": "Transcription task started"
}
```

### Get Processing Progress

**GET** `/process/progress/{task_id}`

Returns the current status and progress of a processing task.

**Headers:**
```
Authorization: Bearer <token>
```

**Path Parameters:**
- `task_id`: Task identifier returned from processing request

**Response:**
```json
{
  "task_id": "string",
  "status": "processing",
  "progress": 65,
  "current_stage": "audio_extraction",
  "estimated_remaining": 45,
  "result": null,
  "error": null,
  "created_at": "2025-09-07T12:00:00Z",
  "updated_at": "2025-09-07T12:05:30Z"
}
```

**Status Values:**
- `pending`: Task is queued
- `processing`: Task is currently running
- `completed`: Task completed successfully
- `failed`: Task failed with error
- `cancelled`: Task was cancelled

### Get Processing Result

**GET** `/process/result/{task_id}`

Returns the final result of a completed processing task.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "task_id": "string",
  "status": "completed",
  "result": {
    "transcription": [
      {
        "start": 0.0,
        "end": 2.5,
        "text": "Hallo und willkommen"
      }
    ],
    "subtitle_file": "path/to/generated.srt",
    "word_count": 450,
    "duration": 300
  },
  "processing_time": 85
}
```

---

## Health & Debug

System health and debugging endpoints.

### Health Check

**GET** `/health`

Returns API health status. No authentication required.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-09-07T12:00:00Z",
  "version": "1.0.0",
  "database": "connected",
  "services": {
    "transcription": "available",
    "translation": "available",
    "vocabulary": "available"
  }
}
```

### Debug Information

**GET** `/debug/info`

Returns system information for debugging. Admin access only.

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Response:**
```json
{
  "system": {
    "python_version": "3.11.9",
    "platform": "Windows-10",
    "memory_usage": "256MB",
    "cpu_usage": "15%"
  },
  "database": {
    "status": "connected",
    "total_users": 150,
    "total_vocabulary": 15000,
    "last_backup": "2025-09-06T02:00:00Z"
  },
  "services": {
    "active_sessions": 25,
    "processing_queue": 3,
    "cache_hit_rate": 89.5
  }
}
```

---

## Error Handling

All API endpoints return errors in a consistent format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": "Password must be at least 8 characters",
    "timestamp": "2025-09-07T12:00:00Z",
    "request_id": "req_abc123"
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 422 | Request data validation failed |
| `AUTHENTICATION_ERROR` | 401 | Authentication required or invalid token |
| `AUTHORIZATION_ERROR` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `DUPLICATE_RESOURCE` | 409 | Resource already exists |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `SERVER_ERROR` | 500 | Internal server error |
| `SERVICE_UNAVAILABLE` | 503 | External service unavailable |

---

## Rate Limiting

API requests are rate limited to ensure fair usage:

- **Authentication endpoints**: 10 requests per minute per IP
- **General endpoints**: 100 requests per minute per user
- **Processing endpoints**: 5 requests per minute per user

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1694088000
```

---

## Data Models

### User
```typescript
interface User {
  user_id: string;
  username: string;
  email: string;
  created_at: string;
  last_login?: string;
}
```

### Video
```typescript
interface Video {
  id: string;
  title: string;
  description: string;
  path: string;
  duration: number; // seconds
  difficulty_level: "A1" | "A2" | "B1" | "B2" | "C1" | "C2";
  category: string;
  has_subtitles: boolean;
  thumbnail?: string;
}
```

### VocabularyWord
```typescript
interface VocabularyWord {
  word: string;
  translation: string;
  category: string;
  status: "new" | "learning" | "known" | "mastered";
  difficulty_score: number;
  frequency_rank: number;
  learned_at?: string;
}
```

### ProcessingTask
```typescript
interface ProcessingTask {
  task_id: string;
  status: "pending" | "processing" | "completed" | "failed" | "cancelled";
  progress: number; // 0-100
  current_stage: string;
  estimated_remaining: number; // seconds
  result?: any;
  error?: string;
  created_at: string;
  updated_at: string;
}
```

---

## WebSocket Support

Real-time updates are available via WebSocket for processing tasks:

**Connection:** `ws://localhost:8000/ws/processing`

**Authentication:** Include token in query parameter: `?token=<bearer_token>`

**Message Format:**
```json
{
  "type": "task_update",
  "task_id": "string",
  "status": "processing",
  "progress": 75,
  "current_stage": "transcription"
}
```

---

## SDKs and Examples

### Python Example
```python
import requests

# Setup
BASE_URL = "http://localhost:8000"
headers = {"Authorization": "Bearer <your_token>"}

# Get user vocabulary stats
response = requests.get(f"{BASE_URL}/vocabulary/library/stats", headers=headers)
stats = response.json()
print(f"Known words: {stats['known_words']}/{stats['total_words']}")

# Mark a word as known
data = {"word": "hallo", "known": True}
response = requests.post(f"{BASE_URL}/vocabulary/mark-known", json=data, headers=headers)
```

### JavaScript Example
```javascript
// Setup
const BASE_URL = 'http://localhost:8000';
const headers = { 'Authorization': `Bearer ${token}` };

// Get available videos
const response = await fetch(`${BASE_URL}/videos`, { headers });
const videos = await response.json();
console.log(`Found ${videos.length} videos`);

// Start video transcription
const transcribeData = {
  video_path: 'path/to/video.mp4',
  language: 'de'
};

const taskResponse = await fetch(`${BASE_URL}/process/transcribe`, {
  method: 'POST',
  headers: { ...headers, 'Content-Type': 'application/json' },
  body: JSON.stringify(transcribeData)
});
```

---

## Changelog

### Version 1.0.0 (2025-09-07)
- Initial API release
- Authentication system with JWT tokens
- Video streaming and subtitle management
- Vocabulary learning system with CEFR levels
- Audio/video processing pipeline
- Real-time WebSocket updates

---

For more information or support, please refer to the interactive API documentation at `http://localhost:8000/docs` when the server is running.
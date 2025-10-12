import { makeApi, Zodios, type ZodiosOptions } from '@zodios/core'
import { z } from 'zod'

const Body_auth_jwt_login_api_auth_login_post = z
  .object({
    grant_type: z.union([z.string(), z.null()]).optional(),
    username: z.string(),
    password: z.string(),
    scope: z.string().optional().default(''),
    client_id: z.union([z.string(), z.null()]).optional(),
    client_secret: z.union([z.string(), z.null()]).optional(),
  })
  .passthrough()
const BearerResponse = z.object({ access_token: z.string(), token_type: z.string() }).passthrough()
const ErrorModel = z.object({ detail: z.union([z.string(), z.record(z.string())]) }).passthrough()
const ValidationError = z
  .object({ loc: z.array(z.union([z.string(), z.number()])), msg: z.string(), type: z.string() })
  .passthrough()
const HTTPValidationError = z
  .object({ detail: z.array(ValidationError) })
  .partial()
  .passthrough()
const UserCreate = z
  .object({
    email: z.string().email(),
    password: z.string(),
    is_active: z.union([z.boolean(), z.null()]).optional().default(true),
    is_superuser: z.union([z.boolean(), z.null()]).optional().default(false),
    is_verified: z.union([z.boolean(), z.null()]).optional().default(false),
    username: z.string(),
  })
  .passthrough()
const UserRead = z
  .object({
    id: z.number().int(),
    email: z.string().email(),
    is_active: z.boolean().optional().default(true),
    is_superuser: z.boolean().optional().default(false),
    is_verified: z.boolean().optional().default(false),
    username: z.string(),
    created_at: z.string(),
    last_login: z.union([z.string(), z.null()]).optional(),
  })
  .passthrough()
const UserResponse = z
  .object({
    id: z.number().int(),
    username: z.string().min(3).max(50),
    email: z.string(),
    is_superuser: z.boolean(),
    is_active: z.boolean(),
    created_at: z.string(),
    last_login: z.union([z.string(), z.null()]).optional(),
  })
  .passthrough()
const TokenRefreshResponse = z
  .object({
    access_token: z.string(),
    refresh_token: z.string(),
    token_type: z.string().optional().default('bearer'),
    expires_in: z.number().int(),
  })
  .passthrough()
const VideoInfo = z
  .object({
    series: z.string().min(1).max(100),
    season: z.string().min(1).max(20),
    episode: z.string().min(1).max(20),
    title: z.string().min(1).max(200),
    path: z.string().min(1),
    has_subtitles: z.boolean(),
    duration: z.union([z.number(), z.null()]).optional(),
  })
  .passthrough()
const token = z.union([z.string(), z.null()]).optional()
const Body_upload_subtitle_api_videos_subtitle_upload_post = z
  .object({ subtitle_file: z.instanceof(File) })
  .passthrough()
const VocabularyWord = z.object({
  concept_id: z.union([z.string(), z.number(), z.string(), z.null()]).optional(),
  word: z.string().min(1).max(100),
  translation: z.union([z.string(), z.null()]).optional(),
  lemma: z.union([z.string(), z.null()]).optional(),
  difficulty_level: z.string().regex(/^(A1|A2|B1|B2|C1|C2)$/),
  semantic_category: z.union([z.string(), z.null()]).optional(),
  domain: z.union([z.string(), z.null()]).optional(),
  gender: z.union([z.string(), z.null()]).optional(),
  plural_form: z.union([z.string(), z.null()]).optional(),
  pronunciation: z.union([z.string(), z.null()]).optional(),
  notes: z.union([z.string(), z.null()]).optional(),
  known: z.boolean().optional().default(false),
})
const ProcessingStatus = z
  .object({
    status: z.string(),
    progress: z.number(),
    current_step: z.string(),
    message: z.string().optional().default(''),
    subtitle_path: z.string().optional().default(''),
  })
  .passthrough()
const Body_upload_video_generic_api_videos_upload_post = z
  .object({ video_file: z.instanceof(File) })
  .passthrough()
const Body_upload_video_to_series_api_videos_upload__series__post = z
  .object({ video_file: z.instanceof(File) })
  .passthrough()
const TranscribeRequest = z.object({ video_path: z.string().min(1) }).passthrough()
const FilterRequest = z.object({ video_path: z.string().min(1) }).passthrough()
const SelectiveTranslationRequest = z
  .object({ srt_path: z.string().min(1), known_words: z.array(z.string()) })
  .passthrough()
const ChunkProcessingRequest = z
  .object({
    video_path: z.string().min(1),
    start_time: z.number().gte(0),
    end_time: z.number().gt(0),
  })
  .passthrough()
const FullPipelineRequest = z
  .object({
    video_path: z.string().min(1),
    source_lang: z
      .string()
      .min(2)
      .max(5)
      .regex(/^[a-z]{2}(-[A-Z]{2})?$/)
      .optional()
      .default('de'),
    target_lang: z
      .string()
      .min(2)
      .max(5)
      .regex(/^[a-z]{2}(-[A-Z]{2})?$/)
      .optional()
      .default('en'),
  })
  .passthrough()
const MarkKnownRequest = z
  .object({
    concept_id: z.union([z.string(), z.null()]).optional(),
    word: z.union([z.string(), z.null()]).optional(),
    lemma: z.union([z.string(), z.null()]).optional(),
    language: z.string().optional().default('de'),
    known: z.boolean(),
  })
  .passthrough()
const SearchVocabularyRequest = z
  .object({
    search_term: z.string().min(1).max(100),
    language: z.string().optional().default('de'),
    limit: z.number().int().gte(1).lte(100).optional().default(20),
  })
  .passthrough()
const BulkMarkLevelRequest = z
  .object({
    level: z.string().regex(/^(A1|A2|B1|B2|C1|C2)$/),
    target_language: z.string().optional().default('de'),
    known: z.boolean(),
  })
  .passthrough()
const CreateVocabularyRequest = z
  .object({
    word: z.string().min(1).max(100),
    translation: z.string().min(1).max(200),
    difficulty_level: z.string().optional().default('beginner'),
    language: z.string().optional().default('de'),
  })
  .passthrough()
const AddCustomWordRequest = z
  .object({
    word: z.string().min(1).max(100),
    lemma: z.union([z.string(), z.null()]).optional(),
    language: z.string().optional().default('de'),
    translation: z.union([z.string(), z.null()]).optional(),
    part_of_speech: z.union([z.string(), z.null()]).optional(),
    gender: z.union([z.string(), z.null()]).optional(),
    notes: z.union([z.string(), z.null()]).optional(),
  })
  .passthrough()
const UserProfile = z
  .object({
    id: z.string(),
    username: z.string(),
    is_admin: z.boolean(),
    created_at: z.string(),
    last_login: z.union([z.string(), z.null()]).optional(),
    native_language: z.record(z.string()),
    target_language: z.record(z.string()),
    language_runtime: z.object({}).partial().passthrough(),
  })
  .passthrough()
const LanguagePreferences = z
  .object({ native_language: z.string(), target_language: z.string() })
  .passthrough()
const UserSettings = z
  .object({
    theme: z.union([z.string(), z.null()]).default('light'),
    notifications_enabled: z.union([z.boolean(), z.null()]).default(true),
    auto_play: z.union([z.boolean(), z.null()]).default(true),
    subtitle_size: z.union([z.string(), z.null()]).default('medium'),
    playback_speed: z.union([z.number(), z.null()]).default(1),
    vocabulary_difficulty: z.union([z.string(), z.null()]).default('intermediate'),
    daily_goal: z.union([z.number(), z.null()]).default(10),
    language_preferences: z.union([LanguagePreferences, z.null()]),
  })
  .partial()
  .passthrough()
const UserProgress = z
  .object({
    user_id: z.string(),
    total_videos_watched: z.number().int().optional().default(0),
    total_watch_time: z.number().optional().default(0),
    vocabulary_learned: z.number().int().optional().default(0),
    current_streak: z.number().int().optional().default(0),
    longest_streak: z.number().int().optional().default(0),
    level: z.string().optional().default('Beginner'),
    experience_points: z.number().int().optional().default(0),
    daily_goals_completed: z.number().int().optional().default(0),
    weekly_goals_completed: z.number().int().optional().default(0),
    last_activity: z.union([z.string(), z.null()]).optional(),
    achievements: z.array(z.string()).optional().default([]),
    learning_stats: z.object({}).partial().passthrough().optional().default({}),
  })
  .passthrough()
const DailyProgress = z
  .object({
    date: z.string(),
    videos_watched: z.number().int().optional().default(0),
    watch_time: z.number().optional().default(0),
    vocabulary_learned: z.number().int().optional().default(0),
    goals_completed: z.number().int().optional().default(0),
    experience_gained: z.number().int().optional().default(0),
  })
  .passthrough()
const GameType = z.enum(['vocabulary', 'listening', 'comprehension'])
const GameDifficulty = z.enum(['beginner', 'intermediate', 'advanced'])
const StartGameRequest = z
  .object({
    game_type: GameType,
    difficulty: GameDifficulty.optional(),
    video_id: z.union([z.string(), z.null()]).optional(),
    total_questions: z.number().int().gte(1).lte(50).optional().default(10),
  })
  .passthrough()
const GameSessionStatus = z.enum(['active', 'completed', 'paused', 'abandoned'])
const GameSession = z
  .object({
    session_id: z.string(),
    user_id: z.string(),
    game_type: z.union([GameType, z.string()]),
    difficulty: z.union([GameDifficulty, z.string()]).optional().default('intermediate'),
    video_id: z.union([z.string(), z.null()]).optional(),
    started_at: z.string().datetime({ offset: true }),
    completed_at: z.union([z.string(), z.null()]).optional(),
    status: z.union([GameSessionStatus, z.string()]).optional().default('active'),
    score: z.number().int().optional().default(0),
    max_score: z.number().int().optional().default(100),
    questions_answered: z.number().int().optional().default(0),
    correct_answers: z.number().int().optional().default(0),
    current_question: z.number().int().optional().default(0),
    total_questions: z.number().int().optional().default(10),
    session_data: z.object({}).partial().passthrough().optional(),
  })
  .passthrough()
const AnswerRequest = z
  .object({
    session_id: z.string(),
    question_id: z.string(),
    question_type: z.string().optional().default('multiple_choice'),
    user_answer: z.string(),
    correct_answer: z.union([z.string(), z.null()]).optional(),
    points: z.number().int().optional().default(10),
  })
  .passthrough()
const ParseSRTRequest = z.object({ content: z.string() }).passthrough()
const SRTSegmentResponse = z
  .object({
    index: z.number().int(),
    start_time: z.number(),
    end_time: z.number(),
    text: z.string(),
    original_text: z.string().optional().default(''),
    translation: z.string().optional().default(''),
  })
  .passthrough()
const ParseSRTResponse = z
  .object({
    segments: z.array(SRTSegmentResponse),
    total_segments: z.number().int(),
    duration: z.number(),
  })
  .passthrough()
const Body_parse_srt_file_api_srt_parse_file_post = z
  .object({ file: z.instanceof(File) })
  .passthrough()
const ConvertToSRTRequest = z.object({ segments: z.array(SRTSegmentResponse) }).passthrough()
const FrontendLogEntry = z
  .object({
    timestamp: z.string(),
    level: z.string(),
    category: z.string(),
    message: z.string(),
    data: z.unknown().optional(),
    error: z.union([z.string(), z.null()]).optional(),
    stack: z.union([z.string(), z.null()]).optional(),
    url: z.union([z.string(), z.null()]).optional(),
    userAgent: z.union([z.string(), z.null()]).optional(),
    userId: z.union([z.string(), z.null()]).optional(),
  })
  .passthrough()
const FrontendLogBatch = z.object({ logs: z.array(FrontendLogEntry) }).passthrough()
const log_frontend_entry_api_debug_frontend_logs_post_Body = z.union([
  FrontendLogEntry,
  FrontendLogBatch,
])

export const schemas = {
  Body_auth_jwt_login_api_auth_login_post,
  BearerResponse,
  ErrorModel,
  ValidationError,
  HTTPValidationError,
  UserCreate,
  UserRead,
  UserResponse,
  TokenRefreshResponse,
  VideoInfo,
  token,
  Body_upload_subtitle_api_videos_subtitle_upload_post,
  VocabularyWord,
  ProcessingStatus,
  Body_upload_video_generic_api_videos_upload_post,
  Body_upload_video_to_series_api_videos_upload__series__post,
  TranscribeRequest,
  FilterRequest,
  SelectiveTranslationRequest,
  ChunkProcessingRequest,
  FullPipelineRequest,
  MarkKnownRequest,
  SearchVocabularyRequest,
  BulkMarkLevelRequest,
  CreateVocabularyRequest,
  AddCustomWordRequest,
  UserProfile,
  LanguagePreferences,
  UserSettings,
  UserProgress,
  DailyProgress,
  GameType,
  GameDifficulty,
  StartGameRequest,
  GameSessionStatus,
  GameSession,
  AnswerRequest,
  ParseSRTRequest,
  SRTSegmentResponse,
  ParseSRTResponse,
  Body_parse_srt_file_api_srt_parse_file_post,
  ConvertToSRTRequest,
  FrontendLogEntry,
  FrontendLogBatch,
  log_frontend_entry_api_debug_frontend_logs_post_Body,
}

const endpoints = makeApi([
  {
    method: 'post',
    path: '/api/auth/login',
    alias: 'auth_jwt_login_api_auth_login_post',
    requestFormat: 'form-url',
    parameters: [
      {
        name: 'body',
        type: 'Body',
        schema: Body_auth_jwt_login_api_auth_login_post,
      },
    ],
    response: BearerResponse,
    errors: [
      {
        status: 400,
        description: `Bad Request`,
        schema: ErrorModel,
      },
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: 'post',
    path: '/api/auth/logout',
    alias: 'auth_jwt_logout_api_auth_logout_post',
    requestFormat: 'json',
    response: z.unknown(),
    errors: [
      {
        status: 401,
        description: `Missing token or inactive user.`,
        schema: z.void(),
      },
    ],
  },
  {
    method: 'get',
    path: '/api/auth/me',
    alias: 'auth_get_current_user_api_auth_me_get',
    description: `Get current authenticated user information.

This endpoint returns the profile information for the currently authenticated user.
Requires a valid JWT access token in the Authorization header.

**Authentication Required**: Yes

Returns:
    UserResponse: User profile information including:
        - id: Unique user identifier (UUID)
        - username: User&#x27;s username
        - email: User&#x27;s email address
        - is_superuser: Whether user has admin privileges
        - is_active: Whether user account is active
        - created_at: Account creation timestamp (ISO format)
        - last_login: Last login timestamp (ISO format, nullable)

Raises:
    HTTPException: 401 Unauthorized if token is invalid or missing

Example:
    &#x60;&#x60;&#x60;bash
    curl -H &quot;Authorization: Bearer &lt;token&gt;&quot; http://localhost:8000/api/auth/me
    &#x60;&#x60;&#x60;

    Response:
    &#x60;&#x60;&#x60;json
    {
        &quot;id&quot;: &quot;123e4567-e89b-12d3-a456-426614174000&quot;,
        &quot;username&quot;: &quot;johndoe&quot;,
        &quot;email&quot;: &quot;john@example.com&quot;,
        &quot;is_superuser&quot;: false,
        &quot;is_active&quot;: true,
        &quot;created_at&quot;: &quot;2025-10-03T10:00:00&quot;,
        &quot;last_login&quot;: &quot;2025-10-03T11:30:00&quot;
    }
    &#x60;&#x60;&#x60;`,
    requestFormat: 'json',
    response: UserResponse,
  },
  {
    method: 'post',
    path: '/api/auth/register',
    alias: 'register_register_api_auth_register_post',
    requestFormat: 'json',
    parameters: [
      {
        name: 'body',
        type: 'Body',
        schema: UserCreate,
      },
    ],
    response: UserRead,
    errors: [
      {
        status: 400,
        description: `Bad Request`,
        schema: ErrorModel,
      },
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: 'post',
    path: '/api/auth/token/refresh',
    alias: 'auth_refresh_token_api_auth_token_refresh_post',
    description: `Refresh access token with automatic token rotation

This endpoint exchanges a valid refresh token for:
1. A new access token (for API calls)
2. A new refresh token (rotated from old one)

Token Rotation Security:
- Each refresh token can only be used once
- If an old token is reused, it indicates theft and all tokens are revoked
- Rotation creates a &quot;family&quot; of tokens that are tracked together

The refresh token should be stored in an HTTP-only cookie for security.

Returns:
    TokenRefreshResponse: New access token and rotated refresh token

Raises:
    HTTPException: 401 if refresh token is invalid, expired, or reused (theft detected)

Security Note:
    If you receive a 401 error mentioning &quot;token reuse&quot;, all tokens have been
    revoked for security. The user must login again.`,
    requestFormat: 'json',
    response: TokenRefreshResponse,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: 'post',
    path: '/api/debug/frontend-logs',
    alias: 'log_frontend_entry_api_debug_frontend_logs_post',
    description: `Receive and process log entries from the frontend application.

Accepts either a single log entry or a batch of log entries from the frontend,
routing them to the backend logging system for centralized debugging and monitoring.
Supports standard log levels and includes contextual metadata.

**Authentication Required**: No

Args:
    payload (FrontendLogEntry | FrontendLogBatch): Log entry or batch with:
        - timestamp: ISO 8601 timestamp
        - level: Log level (&quot;debug&quot;, &quot;info&quot;, &quot;warn&quot;, &quot;error&quot;)
        - category: Log category (e.g., &quot;api&quot;, &quot;render&quot;, &quot;user-action&quot;)
        - message: Log message
        - data (optional): Structured log data
        - error (optional): Error message if applicable
        - stack (optional): Stack trace for errors
        - url (optional): Current page URL
        - userAgent (optional): Browser user agent
        - userId (optional): User identifier

Returns:
    dict: Acknowledgment with:
        - success: Always true
        - status: &quot;logged&quot;
        - count: Number of log entries processed (for batches)
        - timestamp: Timestamp of first log entry

Example (single entry):
    &#x60;&#x60;&#x60;bash
    curl -X POST &quot;http://localhost:8000/api/debug/frontend-logs&quot;           -H &quot;Content-Type: application/json&quot;           -d &#x27;{
        &quot;timestamp&quot;: &quot;2024-10-03T10:30:00.000Z&quot;,
        &quot;level&quot;: &quot;error&quot;,
        &quot;category&quot;: &quot;api&quot;,
        &quot;message&quot;: &quot;Failed to fetch vocabulary&quot;,
        &quot;error&quot;: &quot;Network request failed&quot;,
        &quot;userId&quot;: &quot;user-123&quot;
      }&#x27;
    &#x60;&#x60;&#x60;

Example (batch):
    &#x60;&#x60;&#x60;bash
    curl -X POST &quot;http://localhost:8000/api/debug/frontend-logs&quot;           -H &quot;Content-Type: application/json&quot;           -d &#x27;{
        &quot;logs&quot;: [
          {
            &quot;timestamp&quot;: &quot;2024-10-03T10:30:00.000Z&quot;,
            &quot;level&quot;: &quot;info&quot;,
            &quot;category&quot;: &quot;navigation&quot;,
            &quot;message&quot;: &quot;User navigated to vocabulary page&quot;
          },
          {
            &quot;timestamp&quot;: &quot;2024-10-03T10:30:05.000Z&quot;,
            &quot;level&quot;: &quot;debug&quot;,
            &quot;category&quot;: &quot;api&quot;,
            &quot;message&quot;: &quot;Fetching vocabulary library&quot;,
            &quot;data&quot;: {&quot;limit&quot;: 100, &quot;offset&quot;: 0}
          }
        ]
      }&#x27;
    &#x60;&#x60;&#x60;

Note:
    Log entries are written to the backend&#x27;s &quot;frontend&quot; logger and can be
    monitored alongside backend logs for comprehensive debugging.`,
    requestFormat: 'json',
    parameters: [
      {
        name: 'body',
        type: 'Body',
        schema: log_frontend_entry_api_debug_frontend_logs_post_Body,
      },
    ],
    response: z.unknown(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: 'get',
    path: '/api/debug/health',
    alias: 'debug_health_api_debug_health_get',
    description: `Debug health check endpoint`,
    requestFormat: 'json',
    response: z.unknown(),
  },
  {
    method: 'post',
    path: '/api/game/answer',
    alias: 'game_submit_answer_api_game_answer_post',
    description: `Submit an answer for a game question and receive immediate feedback.

Evaluates the user&#x27;s answer against the correct answer, updates score, and
automatically completes the session when all questions are answered.

**Authentication Required**: Yes

Args:
    answer_request (AnswerRequest): Answer submission with:
        - session_id (str): Game session identifier
        - question_id (str): Question identifier
        - user_answer (str): User&#x27;s submitted answer
        - correct_answer (str, optional): Expected correct answer
        - points (int): Points available for this question
    current_user (User): Authenticated user
    game_service (GameSessionService): Game session service

Returns:
    dict: Answer result with:
        - is_correct: Whether answer was correct
        - points_earned: Points awarded
        - current_score: Updated total score
        - questions_remaining: Remaining questions
        - session_completed: Whether session is finished

Raises:
    HTTPException: 404 if session or question not found
    HTTPException: 400 if question already answered or session not active
    HTTPException: 500 if answer processing fails

Example:
    &#x60;&#x60;&#x60;bash
    curl -X POST &quot;http://localhost:8000/api/game/answer&quot;           -H &quot;Authorization: Bearer &lt;token&gt;&quot;           -H &quot;Content-Type: application/json&quot;           -d &#x27;{
        &quot;session_id&quot;: &quot;abc-123&quot;,
        &quot;question_id&quot;: &quot;q1&quot;,
        &quot;user_answer&quot;: &quot;hola&quot;,
        &quot;points&quot;: 10
      }&#x27;
    &#x60;&#x60;&#x60;

    Response:
    &#x60;&#x60;&#x60;json
    {
        &quot;is_correct&quot;: true,
        &quot;points_earned&quot;: 10,
        &quot;current_score&quot;: 10,
        &quot;questions_remaining&quot;: 9,
        &quot;session_completed&quot;: false
    }
    &#x60;&#x60;&#x60;`,
    requestFormat: 'json',
    parameters: [
      {
        name: 'body',
        type: 'Body',
        schema: AnswerRequest,
      },
    ],
    response: z.unknown(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: 'get',
    path: '/api/game/session/:session_id',
    alias: 'game_get_session_api_game_session__session_id__get',
    description: `Get a specific game session

Args:
    session_id: Game session identifier
    current_user: Authenticated user
    game_service: Game session service

Returns:
    GameSession if found

Raises:
    HTTPException: 404 if session not found
    HTTPException: 500 if retrieval fails`,
    requestFormat: 'json',
    parameters: [
      {
        name: 'session_id',
        type: 'Path',
        schema: z.string(),
      },
    ],
    response: GameSession,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: 'get',
    path: '/api/game/sessions',
    alias: 'game_get_user_sessions_api_game_sessions_get',
    description: `Get user&#x27;s game sessions

Args:
    limit: Maximum number of sessions to return
    current_user: Authenticated user
    game_service: Game session service

Returns:
    List of GameSession objects

Raises:
    HTTPException: 500 if retrieval fails`,
    requestFormat: 'json',
    parameters: [
      {
        name: 'limit',
        type: 'Query',
        schema: z.number().int().optional().default(10),
      },
    ],
    response: z.array(GameSession),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: 'post',
    path: '/api/game/start',
    alias: 'game_start_session_api_game_start_post',
    description: `Start a new vocabulary game session for the current user.

Creates a new game session with generated questions based on game type and difficulty.
Supports vocabulary translation, listening comprehension, and general comprehension games.

**Authentication Required**: Yes

Args:
    game_request (StartGameRequest): Game configuration with:
        - game_type (GameType): &quot;vocabulary&quot;, &quot;listening&quot;, or &quot;comprehension&quot;
        - difficulty (GameDifficulty): &quot;beginner&quot;, &quot;intermediate&quot;, or &quot;advanced&quot;
        - video_id (str, optional): Associated video for context
        - total_questions (int): Number of questions (1-50, default: 10)
    current_user (User): Authenticated user
    game_service (GameSessionService): Game session service

Returns:
    GameSession: Created game session with:
        - session_id: Unique session identifier
        - game_type: Type of game
        - difficulty: Difficulty level
        - total_questions: Number of questions
        - status: &quot;active&quot;
        - session_data: Generated questions

Raises:
    HTTPException: 500 if session creation fails

Example:
    &#x60;&#x60;&#x60;bash
    curl -X POST &quot;http://localhost:8000/api/game/start&quot;           -H &quot;Authorization: Bearer &lt;token&gt;&quot;           -H &quot;Content-Type: application/json&quot;           -d &#x27;{
        &quot;game_type&quot;: &quot;vocabulary&quot;,
        &quot;difficulty&quot;: &quot;intermediate&quot;,
        &quot;total_questions&quot;: 15
      }&#x27;
    &#x60;&#x60;&#x60;

    Response:
    &#x60;&#x60;&#x60;json
    {
        &quot;session_id&quot;: &quot;abc-123-def&quot;,
        &quot;user_id&quot;: &quot;user-456&quot;,
        &quot;game_type&quot;: &quot;vocabulary&quot;,
        &quot;difficulty&quot;: &quot;intermediate&quot;,
        &quot;status&quot;: &quot;active&quot;,
        &quot;total_questions&quot;: 15,
        &quot;current_question&quot;: 0,
        &quot;score&quot;: 0,
        &quot;max_score&quot;: 150
    }
    &#x60;&#x60;&#x60;`,
    requestFormat: 'json',
    parameters: [
      {
        name: 'body',
        type: 'Body',
        schema: StartGameRequest,
      },
    ],
    response: GameSession,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: 'post',
    path: '/api/process/apply-selective-translations',
    alias: 'apply_selective_translations_api_process_apply_selective_translations_post',
    description: `Apply selective translations based on known words.
Re-filters subtitles to show only unknown words that need translation.`,
    requestFormat: 'json',
    parameters: [
      {
        name: 'body',
        type: 'Body',
        schema: SelectiveTranslationRequest,
      },
    ],
    response: z.unknown(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: 'post',
    path: '/api/process/chunk',
    alias: 'process_chunk_api_process_chunk_post',
    description: `Process a specific time-based chunk of video for vocabulary extraction and learning.

Extracts vocabulary from a defined time segment of a video, performing transcription,
translation, and vocabulary analysis on the specified chunk. Useful for focused
learning on specific video segments.

**Authentication Required**: Yes

Args:
    request (ChunkProcessingRequest): Chunk specification with:
        - video_path (str): Relative or absolute path to video file
        - start_time (float): Chunk start time in seconds (&gt;&#x3D; 0)
        - end_time (float): Chunk end time in seconds (&gt; start_time)
    background_tasks (BackgroundTasks): FastAPI background task manager
    current_user (User): Authenticated user
    task_progress (dict): Task progress tracking registry

Returns:
    dict: Task initiation response with:
        - task_id: Unique task identifier for progress tracking
        - status: &quot;started&quot;

Raises:
    HTTPException: 400 if chunk timing is invalid
    HTTPException: 404 if video file not found
    HTTPException: 500 if task initialization fails

Example:
    &#x60;&#x60;&#x60;bash
    curl -X POST &quot;http://localhost:8000/api/processing/chunk&quot;           -H &quot;Authorization: Bearer &lt;token&gt;&quot;           -H &quot;Content-Type: application/json&quot;           -d &#x27;{
        &quot;video_path&quot;: &quot;Learn German/S01E01.mp4&quot;,
        &quot;start_time&quot;: 120.0,
        &quot;end_time&quot;: 180.0
      }&#x27;
    &#x60;&#x60;&#x60;

    Response:
    &#x60;&#x60;&#x60;json
    {
        &quot;task_id&quot;: &quot;chunk_123_120_180_1234567890.123&quot;,
        &quot;status&quot;: &quot;started&quot;
    }
    &#x60;&#x60;&#x60;

Note:
    Use the returned task_id with /api/processing/progress/{task_id} to monitor
    chunk processing. Completed processing returns extracted vocabulary and
    generates chunk-specific subtitle segments.`,
    requestFormat: 'json',
    parameters: [
      {
        name: 'body',
        type: 'Body',
        schema: ChunkProcessingRequest,
      },
    ],
    response: z.unknown(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: 'post',
    path: '/api/process/filter-subtitles',
    alias: 'filter_subtitles_api_process_filter_subtitles_post',
    description: `Filter subtitle content based on user&#x27;s vocabulary knowledge level.

Initiates background processing to filter subtitles, highlighting unknown words
and applying vocabulary-based filtering according to user&#x27;s CEFR level and
known word list. Generates filtered subtitle file for adaptive learning.

**Authentication Required**: Yes

Args:
    request (FilterRequest): Filtering configuration with:
        - video_path (str): Relative or absolute path to video file
    background_tasks (BackgroundTasks): FastAPI background task manager
    current_user (User): Authenticated user
    task_progress (dict): Task progress tracking registry
    subtitle_processor (DirectSubtitleProcessor): Subtitle processing service

Returns:
    dict: Task initiation response with:
        - task_id: Unique task identifier for progress tracking
        - status: &quot;started&quot;

Raises:
    HTTPException: 422 if subtitle file not found
    HTTPException: 500 if task initialization fails

Example:
    &#x60;&#x60;&#x60;bash
    curl -X POST &quot;http://localhost:8000/api/processing/filter-subtitles&quot;           -H &quot;Authorization: Bearer &lt;token&gt;&quot;           -H &quot;Content-Type: application/json&quot;           -d &#x27;{
        &quot;video_path&quot;: &quot;Learn German/S01E01.mp4&quot;
      }&#x27;
    &#x60;&#x60;&#x60;

    Response:
    &#x60;&#x60;&#x60;json
    {
        &quot;task_id&quot;: &quot;filter_123_1234567890.123&quot;,
        &quot;status&quot;: &quot;started&quot;
    }
    &#x60;&#x60;&#x60;

Note:
    Use the returned task_id with /api/processing/progress/{task_id} to monitor
    filtering progress. Completed filtering generates a filtered SRT file with
    vocabulary annotations.`,
    requestFormat: 'json',
    parameters: [
      {
        name: 'body',
        type: 'Body',
        schema: z.object({ video_path: z.string().min(1) }).passthrough(),
      },
    ],
    response: z.unknown(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: 'post',
    path: '/api/process/full-pipeline',
    alias: 'full_pipeline_api_process_full_pipeline_post',
    description: `Run a full processing pipeline: Transcribe -&gt; Filter -&gt; Translate`,
    requestFormat: 'json',
    parameters: [
      {
        name: 'body',
        type: 'Body',
        schema: FullPipelineRequest,
      },
    ],
    response: z.unknown(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: 'get',
    path: '/api/process/progress/:task_id',
    alias: 'get_task_progress_api_process_progress__task_id__get',
    description: `Monitor progress of a background processing task.

Polls the status of an active background task (transcription, filtering, translation,
or full pipeline). Returns current progress percentage, status, and step information.

**Authentication Required**: Yes

Args:
    task_id (str): Unique task identifier from task initiation response
    current_user (User): Authenticated user
    task_progress (dict): Task progress tracking registry

Returns:
    ProcessingStatus: Progress information with:
        - status: &quot;processing&quot;, &quot;completed&quot;, &quot;error&quot;, or &quot;cancelled&quot;
        - progress: Percentage complete (0-100)
        - current_step: Description of current processing step
        - message: Detailed status message
        - vocabulary (optional): Extracted vocabulary (if applicable)
        - subtitle_path (optional): Generated subtitle path (if completed)
        - translation_path (optional): Translation file path (if applicable)

Raises:
    None (returns completed status for missing tasks)

Example:
    &#x60;&#x60;&#x60;bash
    curl -X GET &quot;http://localhost:8000/api/processing/progress/transcribe_123_1234567890.123&quot;           -H &quot;Authorization: Bearer &lt;token&gt;&quot;
    &#x60;&#x60;&#x60;

    Response (in progress):
    &#x60;&#x60;&#x60;json
    {
        &quot;status&quot;: &quot;processing&quot;,
        &quot;progress&quot;: 45.0,
        &quot;current_step&quot;: &quot;Transcribing audio segments&quot;,
        &quot;message&quot;: &quot;Processing segment 45 of 100&quot;
    }
    &#x60;&#x60;&#x60;

    Response (completed):
    &#x60;&#x60;&#x60;json
    {
        &quot;status&quot;: &quot;completed&quot;,
        &quot;progress&quot;: 100.0,
        &quot;current_step&quot;: &quot;Processing complete&quot;,
        &quot;message&quot;: &quot;Video transcribed successfully&quot;,
        &quot;subtitle_path&quot;: &quot;Learn German/S01E01.srt&quot;
    }
    &#x60;&#x60;&#x60;

Note:
    Frontend should poll this endpoint periodically (e.g., every 2 seconds)
    until status becomes &quot;completed&quot; or &quot;error&quot;. Missing tasks return
    completed status to prevent infinite polling.`,
    requestFormat: 'json',
    parameters: [
      {
        name: 'task_id',
        type: 'Path',
        schema: z.string(),
      },
    ],
    response: z.unknown(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: 'post',
    path: '/api/process/transcribe',
    alias: 'transcribe_video_api_process_transcribe_post',
    description: `Transcribe video audio to generate SRT subtitles using speech recognition.

Initiates background transcription task using Whisper or configured transcription
service. Validates video file format and existence before starting processing.

**Authentication Required**: Yes

Args:
    request (TranscribeRequest): Transcription request with:
        - video_path (str): Relative or absolute path to video file
    background_tasks (BackgroundTasks): FastAPI background task manager
    current_user (User): Authenticated user
    task_progress (dict): Task progress tracking registry

Returns:
    dict: Task initiation response with:
        - task_id: Unique task identifier for progress tracking
        - status: &quot;started&quot;

Raises:
    HTTPException: 404 if video file not found
    HTTPException: 422 if transcription service unavailable or invalid video format
    HTTPException: 500 if task initialization fails

Example:
    &#x60;&#x60;&#x60;bash
    curl -X POST &quot;http://localhost:8000/api/processing/transcribe&quot;           -H &quot;Authorization: Bearer &lt;token&gt;&quot;           -H &quot;Content-Type: application/json&quot;           -d &#x27;{
        &quot;video_path&quot;: &quot;Learn German/S01E01.mp4&quot;
      }&#x27;
    &#x60;&#x60;&#x60;

    Response:
    &#x60;&#x60;&#x60;json
    {
        &quot;task_id&quot;: &quot;transcribe_123_1234567890.123&quot;,
        &quot;status&quot;: &quot;started&quot;
    }
    &#x60;&#x60;&#x60;

Note:
    Use the returned task_id with /api/processing/progress/{task_id} to monitor
    transcription progress. Completed transcription generates an SRT file with
    the same name as the video file.`,
    requestFormat: 'json',
    parameters: [
      {
        name: 'body',
        type: 'Body',
        schema: z.object({ video_path: z.string().min(1) }).passthrough(),
      },
    ],
    response: z.unknown(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: 'get',
    path: '/api/profile',
    alias: 'profile_get_api_profile_get',
    description: `Retrieve the current user&#x27;s complete profile information.

Returns user account details, language preferences, and runtime configuration
for the user&#x27;s selected language pair.

**Authentication Required**: Yes

Args:
    current_user (User): Authenticated user from JWT token

Returns:
    UserProfile: Complete profile with:
        - id: User UUID
        - username: User&#x27;s username
        - is_admin: Administrator status
        - created_at: Account creation timestamp
        - last_login: Last login timestamp
        - native_language: Native language details (code, name, flag)
        - target_language: Learning language details (code, name, flag)
        - language_runtime: Runtime settings for language pair

Raises:
    HTTPException: 500 if profile retrieval fails

Example:
    &#x60;&#x60;&#x60;bash
    curl -X GET &quot;http://localhost:8000/api/profile&quot;           -H &quot;Authorization: Bearer &lt;token&gt;&quot;
    &#x60;&#x60;&#x60;

    Response:
    &#x60;&#x60;&#x60;json
    {
        &quot;id&quot;: &quot;user-123&quot;,
        &quot;username&quot;: &quot;learner01&quot;,
        &quot;is_admin&quot;: false,
        &quot;created_at&quot;: &quot;2024-01-15T10:30:00&quot;,
        &quot;last_login&quot;: &quot;2024-10-03T08:15:00&quot;,
        &quot;native_language&quot;: {
            &quot;code&quot;: &quot;en&quot;,
            &quot;name&quot;: &quot;English&quot;,
            &quot;flag&quot;: &quot;🇬🇧&quot;
        },
        &quot;target_language&quot;: {
            &quot;code&quot;: &quot;de&quot;,
            &quot;name&quot;: &quot;German&quot;,
            &quot;flag&quot;: &quot;🇩🇪&quot;
        },
        &quot;language_runtime&quot;: {
            &quot;transcription_model&quot;: &quot;whisper-large&quot;,
            &quot;translation_model&quot;: &quot;opus-en-de&quot;
        }
    }
    &#x60;&#x60;&#x60;`,
    requestFormat: 'json',
    response: UserProfile,
  },
  {
    method: 'get',
    path: '/api/profile/languages',
    alias: 'profile_get_supported_languages_api_profile_languages_get',
    description: `Get list of supported languages`,
    requestFormat: 'json',
    response: z.record(z.record(z.string())),
  },
  {
    method: 'put',
    path: '/api/profile/languages',
    alias: 'profile_update_languages_api_profile_languages_put',
    description: `Update user&#x27;s native and target language preferences.

Changes the user&#x27;s language learning configuration, updating both the native
language and target learning language. This affects subtitle processing,
translation models, and vocabulary filtering.

**Authentication Required**: Yes

Args:
    preferences (LanguagePreferences): Language configuration with:
        - native_language (str): Native language code (must be supported)
        - target_language (str): Target learning language code (must be supported)
    current_user (User): Authenticated user

Returns:
    dict: Update confirmation with:
        - success: Whether update succeeded
        - message: Success message
        - native_language: Updated native language details
        - target_language: Updated target language details
        - language_runtime: New runtime configuration

Raises:
    HTTPException: 400 if languages are invalid or identical
    HTTPException: 500 if update fails

Example:
    &#x60;&#x60;&#x60;bash
    curl -X PUT &quot;http://localhost:8000/api/profile/languages&quot;           -H &quot;Authorization: Bearer &lt;token&gt;&quot;           -H &quot;Content-Type: application/json&quot;           -d &#x27;{
        &quot;native_language&quot;: &quot;en&quot;,
        &quot;target_language&quot;: &quot;es&quot;
      }&#x27;
    &#x60;&#x60;&#x60;

    Response:
    &#x60;&#x60;&#x60;json
    {
        &quot;success&quot;: true,
        &quot;message&quot;: &quot;Language preferences updated successfully&quot;,
        &quot;native_language&quot;: {
            &quot;code&quot;: &quot;en&quot;,
            &quot;name&quot;: &quot;English&quot;,
            &quot;flag&quot;: &quot;🇬🇧&quot;
        },
        &quot;target_language&quot;: {
            &quot;code&quot;: &quot;es&quot;,
            &quot;name&quot;: &quot;Spanish&quot;,
            &quot;flag&quot;: &quot;🇪🇸&quot;
        },
        &quot;language_runtime&quot;: {
            &quot;transcription_model&quot;: &quot;whisper-large&quot;,
            &quot;translation_model&quot;: &quot;opus-en-es&quot;
        }
    }
    &#x60;&#x60;&#x60;`,
    requestFormat: 'json',
    parameters: [
      {
        name: 'body',
        type: 'Body',
        schema: LanguagePreferences,
      },
    ],
    response: z.object({}).partial().passthrough(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: 'get',
    path: '/api/profile/settings',
    alias: 'profile_get_settings_api_profile_settings_get',
    description: `Get user settings`,
    requestFormat: 'json',
    response: UserSettings,
  },
  {
    method: 'put',
    path: '/api/profile/settings',
    alias: 'profile_update_settings_api_profile_settings_put',
    description: `Update user settings`,
    requestFormat: 'json',
    parameters: [
      {
        name: 'body',
        type: 'Body',
        schema: UserSettings,
      },
    ],
    response: UserSettings,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: 'get',
    path: '/api/progress/daily',
    alias: 'progress_get_daily_api_progress_daily_get',
    description: `Get daily progress for the last N days`,
    requestFormat: 'json',
    parameters: [
      {
        name: 'days',
        type: 'Query',
        schema: z.number().int().optional().default(7),
      },
    ],
    response: z.array(DailyProgress),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: 'post',
    path: '/api/progress/update',
    alias: 'progress_update_user_api_progress_update_post',
    description: `Update user progress data`,
    requestFormat: 'json',
    parameters: [
      {
        name: 'body',
        type: 'Body',
        schema: z.object({}).partial().passthrough(),
      },
    ],
    response: z.unknown(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: 'get',
    path: '/api/progress/user',
    alias: 'progress_get_user_api_progress_user_get',
    description: `Retrieve comprehensive learning progress for the current user.

Returns cumulative learning statistics including videos watched, vocabulary learned,
learning streaks, experience points, and achievement tracking.

**Authentication Required**: Yes

Args:
    current_user (User): Authenticated user

Returns:
    UserProgress: Progress metrics with:
        - user_id: User identifier
        - total_videos_watched: Total videos completed
        - total_watch_time: Total watching time in minutes
        - vocabulary_learned: Number of words mastered
        - current_streak: Consecutive days of activity
        - longest_streak: Best streak achieved
        - level: Current proficiency level
        - experience_points: Total XP earned
        - daily_goals_completed: Goals completed today
        - weekly_goals_completed: Goals completed this week
        - last_activity: Timestamp of last activity
        - achievements: List of earned achievements
        - learning_stats: Additional statistics

Raises:
    HTTPException: 500 if progress retrieval fails

Example:
    &#x60;&#x60;&#x60;bash
    curl -X GET &quot;http://localhost:8000/api/progress/user&quot;           -H &quot;Authorization: Bearer &lt;token&gt;&quot;
    &#x60;&#x60;&#x60;

    Response:
    &#x60;&#x60;&#x60;json
    {
        &quot;user_id&quot;: &quot;user-123&quot;,
        &quot;total_videos_watched&quot;: 15,
        &quot;total_watch_time&quot;: 450.5,
        &quot;vocabulary_learned&quot;: 234,
        &quot;current_streak&quot;: 7,
        &quot;longest_streak&quot;: 14,
        &quot;level&quot;: &quot;Intermediate&quot;,
        &quot;experience_points&quot;: 1250,
        &quot;daily_goals_completed&quot;: 3,
        &quot;weekly_goals_completed&quot;: 15,
        &quot;last_activity&quot;: &quot;2024-10-03T10:30:00&quot;,
        &quot;achievements&quot;: [&quot;first_video&quot;, &quot;streak_7&quot;, &quot;vocab_100&quot;],
        &quot;learning_stats&quot;: {
            &quot;average_session_duration&quot;: 30.0,
            &quot;favorite_series&quot;: &quot;Learn German&quot;
        }
    }
    &#x60;&#x60;&#x60;`,
    requestFormat: 'json',
    response: UserProgress,
  },
  {
    method: 'post',
    path: '/api/srt/convert-to-srt',
    alias: 'convert_to_srt_api_srt_convert_to_srt_post',
    description: `Convert structured segment data back to SRT format.

Args:
    request: Segments to convert

Returns:
    SRT formatted content

Raises:
    HTTPException: If conversion fails`,
    requestFormat: 'json',
    parameters: [
      {
        name: 'body',
        type: 'Body',
        schema: ConvertToSRTRequest,
      },
    ],
    response: z.unknown(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: 'post',
    path: '/api/srt/parse',
    alias: 'parse_srt_content_api_srt_parse_post',
    description: `Parse SRT subtitle content and return structured segment data.

Converts raw SRT text format into structured JSON with parsed timestamps,
segment indices, and text content. This endpoint centralizes SRT parsing
logic on the backend, ensuring consistent parsing across the application.

**Authentication Required**: No

Args:
    request (ParseSRTRequest): Request with:
        - content (str): Raw SRT file content

Returns:
    ParseSRTResponse: Parsed data with:
        - segments: List of subtitle segments
            - index: Segment number
            - start_time: Start timestamp in seconds
            - end_time: End timestamp in seconds
            - text: Subtitle text
            - original_text: Original text (if available)
            - translation: Translation text (if available)
        - total_segments: Total number of segments
        - duration: Total video duration in seconds

Raises:
    HTTPException: 400 if SRT content is malformed or unparseable

Example:
    &#x60;&#x60;&#x60;bash
    curl -X POST &quot;http://localhost:8000/api/srt/parse&quot;           -H &quot;Content-Type: application/json&quot;           -d &#x27;{
        &quot;content&quot;: &quot;1\n00:00:00,000 --&gt; 00:00:05,000\nHallo!\n\n2\n00:00:05,500 --&gt; 00:00:10,000\nWie geht es dir?&quot;
      }&#x27;
    &#x60;&#x60;&#x60;

    Response:
    &#x60;&#x60;&#x60;json
    {
        &quot;segments&quot;: [
            {
                &quot;index&quot;: 1,
                &quot;start_time&quot;: 0.0,
                &quot;end_time&quot;: 5.0,
                &quot;text&quot;: &quot;Hallo!&quot;,
                &quot;original_text&quot;: &quot;&quot;,
                &quot;translation&quot;: &quot;&quot;
            },
            {
                &quot;index&quot;: 2,
                &quot;start_time&quot;: 5.5,
                &quot;end_time&quot;: 10.0,
                &quot;text&quot;: &quot;Wie geht es dir?&quot;,
                &quot;original_text&quot;: &quot;&quot;,
                &quot;translation&quot;: &quot;&quot;
            }
        ],
        &quot;total_segments&quot;: 2,
        &quot;duration&quot;: 10.0
    }
    &#x60;&#x60;&#x60;

Note:
    This endpoint should be used by frontend instead of client-side SRT parsing
    to ensure consistency and reduce code duplication.`,
    requestFormat: 'json',
    parameters: [
      {
        name: 'body',
        type: 'Body',
        schema: z.object({ content: z.string() }).passthrough(),
      },
    ],
    response: ParseSRTResponse,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: 'post',
    path: '/api/srt/parse-file',
    alias: 'parse_srt_file_api_srt_parse_file_post',
    description: `Parse an uploaded SRT file and return structured data.

Args:
    file: Uploaded SRT file

Returns:
    Parsed SRT segments with metadata

Raises:
    HTTPException: If file processing fails`,
    requestFormat: 'form-data',
    parameters: [
      {
        name: 'body',
        type: 'Body',
        schema: z.object({ file: z.instanceof(File) }).passthrough(),
      },
    ],
    response: z.unknown(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: 'get',
    path: '/api/srt/validate',
    alias: 'validate_srt_content_api_srt_validate_get',
    description: `Validate SRT content without full parsing.

Args:
    content: SRT content to validate

Returns:
    Validation result with issues found`,
    requestFormat: 'json',
    parameters: [
      {
        name: 'content',
        type: 'Query',
        schema: z.string(),
      },
    ],
    response: z.unknown(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: 'delete',
    path: '/api/test/cleanup',
    alias: 'cleanup_test_data_api_test_cleanup_delete',
    description: `Clean up test data created by e2e tests

Deletes all users and related data that match e2e test patterns:
- Users with emails matching e2e.*@langplug.com
- Users with usernames starting with e2euser_

**Authentication Required**: No (only available in debug mode)

Returns:
    dict: Cleanup summary with counts of deleted records`,
    requestFormat: 'json',
    response: z.unknown(),
  },
  {
    method: 'get',
    path: '/api/videos',
    alias: 'get_videos_api_videos_get',
    description: `Retrieve list of all available videos and series for the current user.

Scans the configured videos directory and returns metadata for all accessible
video files, including subtitle availability and episode information.

**Authentication Required**: Yes

Args:
    current_user (User): Authenticated user
    video_service (VideoService): Video service dependency

Returns:
    list[VideoInfo]: List of video metadata objects containing:
        - series: Series/show name
        - season: Season number
        - episode: Episode number
        - title: Episode title
        - path: Relative file path
        - has_subtitles: Whether subtitles exist
        - duration: Video duration in seconds

Raises:
    HTTPException: 500 if directory scanning fails

Example:
    &#x60;&#x60;&#x60;bash
    curl -X GET &quot;http://localhost:8000/api/videos&quot;           -H &quot;Authorization: Bearer &lt;token&gt;&quot;
    &#x60;&#x60;&#x60;

    Response:
    &#x60;&#x60;&#x60;json
    [
        {
            &quot;series&quot;: &quot;Learn German&quot;,
            &quot;season&quot;: &quot;1&quot;,
            &quot;episode&quot;: &quot;01&quot;,
            &quot;title&quot;: &quot;Introduction&quot;,
            &quot;path&quot;: &quot;Learn German/S01E01.mp4&quot;,
            &quot;has_subtitles&quot;: true,
            &quot;duration&quot;: 1200
        }
    ]
    &#x60;&#x60;&#x60;`,
    requestFormat: 'json',
    response: z.array(VideoInfo),
  },
  {
    method: 'get',
    path: '/api/videos/:series/:episode',
    alias: 'stream_video_api_videos__series___episode__get',
    description: `Stream video file - Requires authentication`,
    requestFormat: 'json',
    parameters: [
      {
        name: 'series',
        type: 'Path',
        schema: z.string(),
      },
      {
        name: 'episode',
        type: 'Path',
        schema: z.string(),
      },
      {
        name: 'token',
        type: 'Query',
        schema: token,
      },
      {
        name: 'authorization',
        type: 'Header',
        schema: token,
      },
    ],
    response: z.unknown(),
    errors: [
      {
        status: 401,
        description: `Invalid or missing authentication token`,
        schema: z.void(),
      },
      {
        status: 404,
        description: `Video file not accessible`,
        schema: z.void(),
      },
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
      {
        status: 500,
        description: `Error streaming video`,
        schema: z.void(),
      },
    ],
  },
  {
    method: 'get',
    path: '/api/videos/:video_id/status',
    alias: 'get_video_status_api_videos__video_id__status_get',
    description: `Get processing status for a video`,
    requestFormat: 'json',
    parameters: [
      {
        name: 'video_id',
        type: 'Path',
        schema: z.string(),
      },
    ],
    response: ProcessingStatus,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: 'get',
    path: '/api/videos/:video_id/vocabulary',
    alias: 'get_video_vocabulary_api_videos__video_id__vocabulary_get',
    description: `Get vocabulary words extracted from a video`,
    requestFormat: 'json',
    parameters: [
      {
        name: 'video_id',
        type: 'Path',
        schema: z.string(),
      },
    ],
    response: z.array(VocabularyWord),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: 'post',
    path: '/api/videos/scan',
    alias: 'scan_videos_api_videos_scan_post',
    description: `Scan videos directory for new videos - Requires authentication`,
    requestFormat: 'json',
    response: z.unknown(),
  },
  {
    method: 'post',
    path: '/api/videos/subtitle/upload',
    alias: 'upload_subtitle_api_videos_subtitle_upload_post',
    description: `Upload subtitle file for a video - Requires authentication
Uses FileSecurityValidator for secure file handling`,
    requestFormat: 'form-data',
    parameters: [
      {
        name: 'body',
        type: 'Body',
        schema: z.object({ subtitle_file: z.instanceof(File) }).passthrough(),
      },
      {
        name: 'video_path',
        type: 'Query',
        schema: z.string(),
      },
    ],
    response: z.unknown(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: 'get',
    path: '/api/videos/subtitles/:subtitle_path',
    alias: 'get_subtitles_api_videos_subtitles__subtitle_path__get',
    description: `Serve subtitle files (SRT format) for video playback.

Returns subtitle file content as plain text with UTF-8 encoding.
Validates file existence and applies security checks to prevent path traversal.

**Authentication Required**: Yes

Args:
    subtitle_path (str): Relative path to subtitle file
    current_user (User): Authenticated user
    video_service (VideoService): Video service dependency

Returns:
    FileResponse: SRT file content with UTF-8 encoding

Raises:
    HTTPException: 404 if subtitle file not found or invalid
    HTTPException: 500 if file serving fails

Example:
    &#x60;&#x60;&#x60;bash
    curl -X GET &quot;http://localhost:8000/api/videos/subtitles/Learn German/S01E01.srt&quot;           -H &quot;Authorization: Bearer &lt;token&gt;&quot;
    &#x60;&#x60;&#x60;

    Response: (plain text SRT content)
    &#x60;&#x60;&#x60;
    1
    00:00:00,000 --&gt; 00:00:05,000
    Hallo und willkommen!

    2
    00:00:05,500 --&gt; 00:00:10,000
    Heute lernen wir Deutsch.
    &#x60;&#x60;&#x60;`,
    requestFormat: 'json',
    parameters: [
      {
        name: 'subtitle_path',
        type: 'Path',
        schema: z.string(),
      },
    ],
    response: z.unknown(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: 'post',
    path: '/api/videos/upload',
    alias: 'upload_video_generic_api_videos_upload_post',
    description: `Upload a new video file (generic endpoint) - Requires authentication`,
    requestFormat: 'form-data',
    parameters: [
      {
        name: 'body',
        type: 'Body',
        schema: z.object({ video_file: z.instanceof(File) }).passthrough(),
      },
      {
        name: 'series',
        type: 'Query',
        schema: z.string().optional().default('Default'),
      },
    ],
    response: z.unknown(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: 'post',
    path: '/api/videos/upload/:series',
    alias: 'upload_video_to_series_api_videos_upload__series__post',
    description: `Upload a new video file to a series - Requires authentication
Uses FileSecurityValidator for secure file handling with path traversal prevention`,
    requestFormat: 'form-data',
    parameters: [
      {
        name: 'body',
        type: 'Body',
        schema: z.object({ video_file: z.instanceof(File) }).passthrough(),
      },
      {
        name: 'series',
        type: 'Path',
        schema: z.string(),
      },
    ],
    response: z.unknown(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: 'get',
    path: '/api/videos/user',
    alias: 'get_user_videos_api_videos_user_get',
    description: `Get videos for the current user (alias for get_available_videos)`,
    requestFormat: 'json',
    response: z.array(z.object({}).partial().passthrough()),
  },
  {
    method: 'post',
    path: '/api/vocabulary',
    alias: 'create_vocabulary_api_vocabulary_post',
    description: `Create test vocabulary word (primarily for E2E testing).

Maps difficulty levels to CEFR levels and creates a global vocabulary word.

Args:
    request: Vocabulary word details
    current_user: Authenticated user
    db: Database session

Returns:
    dict: Created vocabulary with id, word, translation, difficulty_level

Raises:
    HTTPException: 400 if creation fails`,
    requestFormat: 'json',
    parameters: [
      {
        name: 'body',
        type: 'Body',
        schema: CreateVocabularyRequest,
      },
    ],
    response: z.unknown(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: 'get',
    path: '/api/vocabulary/blocking-words',
    alias: 'get_blocking_words_api_vocabulary_blocking_words_get',
    description: `Get blocking words from SRT file`,
    requestFormat: 'json',
    parameters: [
      {
        name: 'video_path',
        type: 'Query',
        schema: z.string(),
      },
    ],
    response: z.unknown(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: 'delete',
    path: '/api/vocabulary/custom/:word_id',
    alias: 'delete_custom_word_api_vocabulary_custom__word_id__delete',
    description: `Delete a user-defined custom vocabulary word.

Users can only delete their own custom words. System vocabulary cannot be deleted.

Args:
    word_id: Database ID of the custom word
    current_user: Authenticated user
    vocabulary_service: Vocabulary service dependency

Returns:
    dict: Success message

Raises:
    HTTPException: 403 if word doesn&#x27;t belong to user or is system vocabulary
    HTTPException: 404 if word not found
    HTTPException: 500 if deletion fails`,
    requestFormat: 'json',
    parameters: [
      {
        name: 'word_id',
        type: 'Path',
        schema: z.number().int(),
      },
    ],
    response: z.unknown(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: 'post',
    path: '/api/vocabulary/custom/add',
    alias: 'add_custom_word_api_vocabulary_custom_add_post',
    description: `Add a custom user-defined vocabulary word to C2 level.

Allows users to add their own vocabulary words that aren&#x27;t in the system vocabulary.
Custom words are always classified as C2 level and are only visible to the user who created them.

Args:
    request: Custom word details
    current_user: Authenticated user
    vocabulary_service: Vocabulary service dependency

Returns:
    dict: Created word information including database ID

Raises:
    HTTPException: 400 if word already exists for this user
    HTTPException: 500 if creation fails`,
    requestFormat: 'json',
    parameters: [
      {
        name: 'body',
        type: 'Body',
        schema: AddCustomWordRequest,
      },
    ],
    response: z.unknown(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: 'get',
    path: '/api/vocabulary/languages',
    alias: 'get_supported_languages_api_vocabulary_languages_get',
    description: `Get list of supported languages`,
    requestFormat: 'json',
    response: z.unknown(),
  },
  {
    method: 'get',
    path: '/api/vocabulary/library',
    alias: 'get_vocabulary_library_api_vocabulary_library_get',
    description: `Retrieve paginated vocabulary library with optional CEFR level filtering.

Returns a paginated list of vocabulary words, optionally filtered by CEFR level,
with user-specific progress indicators showing which words are known.

**Authentication Required**: Yes

Args:
    language (str): Target language code (default: &quot;de&quot;)
    level (str, optional): CEFR level filter (A1, A2, B1, B2, C1, C2)
    limit (int): Maximum words to return (1-1000, default: 100)
    offset (int): Pagination offset (default: 0)
    current_user (User): Authenticated user
    db (AsyncSession): Database session

Returns:
    dict: Library data with:
        - words: List of vocabulary entries with known status
        - total_count: Total matching words
        - limit: Applied limit
        - offset: Applied offset

Raises:
    HTTPException: 500 if database query fails

Example:
    &#x60;&#x60;&#x60;bash
    curl -X GET &quot;http://localhost:8000/api/vocabulary/library?level&#x3D;A1&amp;limit&#x3D;50&quot;           -H &quot;Authorization: Bearer &lt;token&gt;&quot;
    &#x60;&#x60;&#x60;

    Response:
    &#x60;&#x60;&#x60;json
    {
        &quot;words&quot;: [
            {
                &quot;lemma&quot;: &quot;hallo&quot;,
                &quot;translation&quot;: &quot;hello&quot;,
                &quot;level&quot;: &quot;A1&quot;,
                &quot;is_known&quot;: true
            }
        ],
        &quot;total_count&quot;: 600,
        &quot;limit&quot;: 50,
        &quot;offset&quot;: 0
    }
    &#x60;&#x60;&#x60;`,
    requestFormat: 'json',
    parameters: [
      {
        name: 'language',
        type: 'Query',
        schema: z.string().optional().default('de'),
      },
      {
        name: 'level',
        type: 'Query',
        schema: token,
      },
      {
        name: 'limit',
        type: 'Query',
        schema: z.number().int().gte(1).lte(1000).optional().default(100),
      },
      {
        name: 'offset',
        type: 'Query',
        schema: z.number().int().gte(0).optional().default(0),
      },
    ],
    response: z.unknown(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: 'get',
    path: '/api/vocabulary/library/:level',
    alias: 'get_vocabulary_level_api_vocabulary_library__level__get',
    description: `Get vocabulary for a specific level`,
    requestFormat: 'json',
    parameters: [
      {
        name: 'level',
        type: 'Path',
        schema: z.string(),
      },
      {
        name: 'target_language',
        type: 'Query',
        schema: z.string().optional().default('de'),
      },
      {
        name: 'translation_language',
        type: 'Query',
        schema: z.string().optional().default('en'),
      },
      {
        name: 'limit',
        type: 'Query',
        schema: z.number().int().gte(1).lte(10000).optional().default(1000),
      },
      {
        name: 'offset',
        type: 'Query',
        schema: z.number().int().gte(0).optional().default(0),
      },
    ],
    response: z.unknown(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: 'post',
    path: '/api/vocabulary/library/bulk-mark',
    alias: 'bulk_mark_level_api_vocabulary_library_bulk_mark_post',
    description: `Mark all words in a level as known or unknown`,
    requestFormat: 'json',
    parameters: [
      {
        name: 'body',
        type: 'Body',
        schema: BulkMarkLevelRequest,
      },
    ],
    response: z.unknown(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: 'post',
    path: '/api/vocabulary/mark-known',
    alias: 'mark_word_known_api_vocabulary_mark_known_post',
    description: `Mark a vocabulary word as known or unknown for the current user.

Updates user&#x27;s vocabulary progress by marking a word as known (mastered)
or unknown (needs practice). Supports lookup by lemma, word form, or concept ID.

**Authentication Required**: Yes

Args:
    request (MarkKnownRequest): Request containing:
        - concept_id (str, optional): UUID of vocabulary concept
        - word (str, optional): The word text
        - lemma (str, optional): Base form of the word
        - language (str): Language code (default: &quot;de&quot;)
        - known (bool): Whether to mark as known
    current_user (User): Authenticated user
    db (AsyncSession): Database session

Returns:
    dict: Update result with:
        - success: Whether operation succeeded
        - concept_id: The vocabulary concept ID
        - known: The new known status
        - word: The word text
        - lemma: The word lemma
        - level: CEFR level

Raises:
    HTTPException: 500 if database update fails

Example:
    &#x60;&#x60;&#x60;bash
    curl -X POST &quot;http://localhost:8000/api/vocabulary/mark-known&quot;           -H &quot;Authorization: Bearer &lt;token&gt;&quot;           -H &quot;Content-Type: application/json&quot;           -d &#x27;{
        &quot;lemma&quot;: &quot;hallo&quot;,
        &quot;language&quot;: &quot;de&quot;,
        &quot;known&quot;: true
      }&#x27;
    &#x60;&#x60;&#x60;

    Response:
    &#x60;&#x60;&#x60;json
    {
        &quot;success&quot;: true,
        &quot;concept_id&quot;: &quot;abc-123&quot;,
        &quot;known&quot;: true,
        &quot;word&quot;: &quot;Hallo&quot;,
        &quot;lemma&quot;: &quot;hallo&quot;,
        &quot;level&quot;: &quot;A1&quot;
    }
    &#x60;&#x60;&#x60;`,
    requestFormat: 'json',
    parameters: [
      {
        name: 'body',
        type: 'Body',
        schema: MarkKnownRequest,
      },
    ],
    response: z.unknown(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: 'post',
    path: '/api/vocabulary/mark-known-lemma',
    alias: 'mark_word_known_by_lemma_api_vocabulary_mark_known_lemma_post',
    description: `Mark a word as known or unknown using lemma-based lookup (compatibility endpoint)`,
    requestFormat: 'json',
    parameters: [
      {
        name: 'body',
        type: 'Body',
        schema: MarkKnownRequest,
      },
    ],
    response: z.unknown(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: 'post',
    path: '/api/vocabulary/search',
    alias: 'search_vocabulary_api_vocabulary_search_post',
    description: `Search vocabulary by word or lemma`,
    requestFormat: 'json',
    parameters: [
      {
        name: 'body',
        type: 'Body',
        schema: SearchVocabularyRequest,
      },
    ],
    response: z.unknown(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: 'get',
    path: '/api/vocabulary/stats',
    alias: 'get_vocabulary_stats_api_vocabulary_stats_get',
    description: `Get comprehensive vocabulary learning statistics for the current user.

Returns detailed progress metrics including known/unknown word counts by CEFR level,
learning streaks, and overall proficiency metrics.

**Authentication Required**: Yes

Args:
    target_language (str): Target language code (default: &quot;de&quot;)
    translation_language (str): Translation language code (default: &quot;en&quot;)
    current_user (User): Authenticated user
    db (AsyncSession): Database session

Returns:
    VocabularyStats: Statistics including:
        - total_words: Total vocabulary size
        - known_words: Number of mastered words
        - by_level: Breakdown by CEFR level (A1-C2)
        - learning_streak: Consecutive days of practice
        - mastery_percentage: Overall proficiency score

Raises:
    HTTPException: 500 if statistics calculation fails

Example:
    &#x60;&#x60;&#x60;bash
    curl -X GET &quot;http://localhost:8000/api/vocabulary/stats?target_language&#x3D;de&amp;translation_language&#x3D;en&quot;           -H &quot;Authorization: Bearer &lt;token&gt;&quot;
    &#x60;&#x60;&#x60;

    Response:
    &#x60;&#x60;&#x60;json
    {
        &quot;total_words&quot;: 5000,
        &quot;known_words&quot;: 450,
        &quot;by_level&quot;: {
            &quot;A1&quot;: {&quot;total&quot;: 600, &quot;known&quot;: 200},
            &quot;A2&quot;: {&quot;total&quot;: 800, &quot;known&quot;: 150},
            &quot;B1&quot;: {&quot;total&quot;: 1000, &quot;known&quot;: 100}
        },
        &quot;mastery_percentage&quot;: 9.0
    }
    &#x60;&#x60;&#x60;`,
    requestFormat: 'json',
    parameters: [
      {
        name: 'target_language',
        type: 'Query',
        schema: z
          .string()
          .regex(/^[a-z]{2,3}$/)
          .optional()
          .default('de'),
      },
      {
        name: 'translation_language',
        type: 'Query',
        schema: z
          .string()
          .regex(/^[a-z]{2,3}$/)
          .optional()
          .default('en'),
      },
    ],
    response: z.unknown(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: 'get',
    path: '/api/vocabulary/test-data',
    alias: 'get_test_data_api_vocabulary_test_data_get',
    description: `Get test data for frontend testing`,
    requestFormat: 'json',
    response: z.unknown(),
  },
  {
    method: 'get',
    path: '/api/vocabulary/word-info/:word',
    alias: 'get_word_info_api_vocabulary_word_info__word__get',
    description: `Retrieve detailed information about a specific vocabulary word.

Looks up word metadata including lemma, CEFR level, translations, and usage examples
from the vocabulary database.

**Authentication Required**: No

Args:
    word (str): The word to look up
    language (str): Target language code (default: &quot;de&quot;)
    db (AsyncSession): Database session dependency

Returns:
    dict: Word information including:
        - word: The original word
        - lemma: Base form of the word
        - level: CEFR level (A1-C2)
        - translations: List of translations
        - examples: Usage examples

Raises:
    HTTPException: 404 if word not found in vocabulary database
    HTTPException: 500 if database query fails

Example:
    &#x60;&#x60;&#x60;bash
    curl -X GET &quot;http://localhost:8000/api/vocabulary/word-info/Hallo?language&#x3D;de&quot;
    &#x60;&#x60;&#x60;

    Response:
    &#x60;&#x60;&#x60;json
    {
        &quot;word&quot;: &quot;Hallo&quot;,
        &quot;lemma&quot;: &quot;hallo&quot;,
        &quot;level&quot;: &quot;A1&quot;,
        &quot;translations&quot;: [&quot;Hello&quot;, &quot;Hi&quot;],
        &quot;examples&quot;: [&quot;Hallo, wie geht es dir?&quot;]
    }
    &#x60;&#x60;&#x60;`,
    requestFormat: 'json',
    parameters: [
      {
        name: 'word',
        type: 'Path',
        schema: z.string(),
      },
      {
        name: 'language',
        type: 'Query',
        schema: z.string().optional().default('de'),
      },
    ],
    response: z.unknown(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: 'get',
    path: '/health',
    alias: 'health_check_health_get',
    description: `Health check endpoint`,
    requestFormat: 'json',
    response: z.unknown(),
  },
  {
    method: 'get',
    path: '/readiness',
    alias: 'readiness_check_readiness_get',
    description: `Readiness check endpoint - verifies that all services are initialized

Returns 200 when ready, 503 when still initializing`,
    requestFormat: 'json',
    response: z.unknown(),
  },
  {
    method: 'get',
    path: '/test',
    alias: 'test_endpoint_test_get',
    description: `Simple test endpoint`,
    requestFormat: 'json',
    response: z.unknown(),
  },
])

export const api = new Zodios(endpoints)

export function createApiClient(baseUrl: string, options?: ZodiosOptions) {
  return new Zodios(baseUrl, endpoints, options)
}

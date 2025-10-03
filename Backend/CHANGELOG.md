# Changelog

All notable changes to LangPlug Backend will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- Comprehensive documentation suite (Architecture, API, Testing, Deployment, Monitoring)
- CODE_STYLE.md with coding standards and best practices
- Enhanced docstrings for API routes and service layer

### Changed

### Deprecated

### Removed

### Fixed

### Security

---

## [0.1.0] - 2024-10-02

### Added
- Initial backend architecture with layered design
- JWT authentication with access and refresh tokens
- User registration and login endpoints
- Password hashing with Argon2
- Video upload and streaming functionality
- Subtitle generation and processing pipeline
- Vocabulary tracking and progress management
- AI-powered transcription using Whisper
- Translation services using OPUS-MT/NLLB
- Learning game sessions
- WebSocket support for real-time updates
- Database migrations with Alembic
- Comprehensive test suite (1,619 tests, 80% coverage)
- Pre-commit hooks with Ruff and Bandit
- CORS middleware configuration
- Health check endpoints
- Environment-based configuration
- Repository pattern for data access
- Strategy pattern for AI model selection

### Changed
- Migrated vocabulary system to lemma-based approach
- Updated password migration tracking

### Fixed
- API error handling and response standardization
- Player issues and subtitle synchronization
- Translation of all subtitle segments (not just vocabulary)

### Security
- Implemented Argon2 password hashing
- Added CSRF protection (planned)
- File upload security validation
- Rate limiting configuration (planned)
- SQL injection protection via parameterized queries

---

## Release Types

### Major Version (X.0.0)
- Breaking changes to API
- Database schema changes requiring migration
- Significant architecture refactoring
- Removal of deprecated features

### Minor Version (0.X.0)
- New features and functionality
- Non-breaking API changes
- Performance improvements
- New endpoints

### Patch Version (0.0.X)
- Bug fixes
- Security patches
- Documentation updates
- Minor improvements

---

## Change Categories

### Added
New features, endpoints, or functionality added to the project.

Examples:
- New API endpoint: `POST /api/vocabulary/bulk`
- New service: VocabularyStatsService
- New AI model support: Parakeet transcription

### Changed
Changes to existing functionality that don't break compatibility.

Examples:
- Improved transcription accuracy
- Updated error messages
- Enhanced logging format
- Performance optimization

### Deprecated
Features that will be removed in future versions (but still work).

Examples:
- Deprecated endpoint: `GET /api/old-vocabulary` (use `/api/vocabulary/words` instead)
- Deprecated configuration: `OLD_CONFIG_VAR` (use `NEW_CONFIG_VAR` instead)

### Removed
Features, endpoints, or functionality removed from the project.

Examples:
- Removed deprecated endpoint: `GET /api/old-vocabulary`
- Removed legacy authentication system
- Removed backward compatibility layer

### Fixed
Bug fixes and error corrections.

Examples:
- Fixed authentication token expiration bug
- Fixed video upload memory leak
- Fixed subtitle timing synchronization
- Resolved N+1 query problem in vocabulary service

### Security
Security improvements, vulnerability fixes, and security-related changes.

Examples:
- Fixed SQL injection vulnerability in vocabulary search
- Updated dependencies to patch security issues
- Implemented rate limiting to prevent abuse
- Added CSRF token validation

---

## Contribution Guidelines

When adding entries to the changelog:

1. **Add to [Unreleased] section** during development
2. **Use present tense**: "Add feature" not "Added feature"
3. **Be specific**: Include endpoint paths, function names, or component details
4. **Link to issues/PRs**: Reference GitHub issues when applicable
5. **Group related changes**: Organize by category (Added, Changed, etc.)
6. **User perspective**: Write for users/developers who will read the changelog

### Example Entry Format

```markdown
### Added
- New endpoint `POST /api/vocabulary/{word}/examples` for retrieving word usage examples
- Vocabulary spaced repetition algorithm (SRS) for optimized learning (#123)
- Export vocabulary to CSV functionality via `GET /api/vocabulary/export` (#456)

### Fixed
- Fixed memory leak in video processing pipeline when handling large files (#789)
- Resolved race condition in concurrent vocabulary updates (#234)

### Security
- Updated FastAPI to 0.104.0 to address CVE-2023-12345
```

---

## Release Process

### 1. Prepare Release

```bash
# Update version in pyproject.toml
# Move [Unreleased] changes to new version section
# Add release date
# Update version links at bottom of file
```

### 2. Create Release Commit

```bash
git add CHANGELOG.md pyproject.toml
git commit -m "chore: prepare release v0.2.0"
git tag v0.2.0
git push origin main --tags
```

### 3. Post-Release

```bash
# Create new [Unreleased] section
# Continue development
```

---

## Version History Links

[Unreleased]: https://github.com/langplug/backend/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/langplug/backend/releases/tag/v0.1.0

---

**Maintained By**: Development Team
**Last Updated**: 2025-10-03

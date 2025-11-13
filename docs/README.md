# LangPlug Documentation Index

Welcome to the LangPlug documentation. This index provides a comprehensive overview of all architectural guides, migration plans, and development resources.

## Table of Contents

- [Getting Started](#getting-started)
- [Architecture & Migration Guides](#architecture--migration-guides)
- [Development Guides](#development-guides)
- [Reports & Analysis](#reports--analysis)
- [Archive](#archive)

---

## Getting Started

### Essential Reading (Start Here)

1. **[CLAUDE.md](../CLAUDE.md)** - Project structure, core rules, and development standards
2. **[Phase 3 Summary](./guides/PHASE3_SUMMARY.md)** - Current architecture state and recent improvements
3. **[React Query Migration Guide](./guides/REACT_QUERY_MIGRATION.md)** - How to use React Query for server-side state
4. **[Nx Migration Guide](./guides/NX_MIGRATION_GUIDE.md)** - Monorepo setup and build caching

### Quick Reference

- **Frontend State Management**: Use React Query hooks (see [hooks/](../src/frontend/src/hooks/))
- **UI State**: Use Zustand stores (see [store/useVocabularyUIStore.ts](../src/frontend/src/store/useVocabularyUIStore.ts))
- **Running Tests**: `nx run-many --target=test --all`
- **Building Projects**: `nx run-many --target=build --all`
- **Affected Tests Only**: `nx affected --target=test`

---

## Architecture & Migration Guides

### Current Architecture (Phases 1-3)

#### Phase 1: Repository Reorganization + Nx Monorepo
- **[Nx Migration Guide](./guides/NX_MIGRATION_GUIDE.md)** (420 lines)
  - Monorepo setup with build caching
  - Task orchestration and parallel execution
  - CI/CD integration with nx affected
  - Benefits: 30-70% faster builds on repeated runs

#### Phase 2: React Query for Server-Side State
- **[React Query Migration Guide](./guides/REACT_QUERY_MIGRATION.md)** (420 lines)
  - Complete migration from Zustand to React Query for server state
  - All query hooks: `useWordsByLevel`, `useSearchWords`, `useUserProgress`, `useVocabularyStats`
  - All mutation hooks: `useMarkWord`, `useBulkMarkWords`
  - Automatic caching, refetching, and cache invalidation
  - Benefits: 87% reduction in store LOC, better separation of concerns

#### Phase 3: Component Migration Patterns
- **[Component Migration Examples](./guides/PHASE3_COMPONENT_MIGRATION_EXAMPLES.md)** (580 lines)
  - Real before/after examples (LearningPlayer, VocabularyLibrary)
  - Common patterns: conditional fetching, dependent queries, debounced search
  - Migration checklist and timeline
  - When NOT to use React Query (pure UI state)

- **[Phase 3 Summary](./guides/PHASE3_SUMMARY.md)** (450 lines)
  - Complete overview of Phases 1-3
  - Architecture decisions and rationale
  - Performance impact and success metrics
  - Validation and acceptance criteria

### Reference Implementation
- **[VocabularyStatsCard.example.tsx](../src/frontend/src/components/examples/VocabularyStatsCard.example.tsx)**
  - Real example component showing migration pattern
  - Before/after comparison with commentary
  - Demonstrates 96% boilerplate reduction

---

## Development Guides

### Backend

#### API & Services
- **[API Documentation](./architecture/API_DOCUMENTATION.md)** - Complete API reference
- **[Event System](./architecture/EVENT_SYSTEM_OVERVIEW.md)** - Event-driven architecture patterns
- **[NeMo Integration](./architecture/NEMO_INTEGRATION.md)** - NeMo ASR service integration
- **[Vocabulary Blocking Words](./architecture/VOCABULARY_BLOCKING_WORDS_ANALYSIS.md)** - Blocking words implementation

#### Data & Migrations
- **[Vocabulary Database Schema](./architecture/VOCABULARY_DATABASE_SCHEMA.md)** - Database design and relationships
- **[Migration Checklist (BERT)](./architecture/migration_checklist_bert_to_spacy.md)** - Example migration guide

### Frontend

#### State Management
- **Query Hooks Location**: `src/frontend/src/hooks/queries/`
  - `useVocabulary.ts` - Words, search, progress, stats
  - `useAuth.ts` - Authentication queries
  - `useGame.ts` - Game and blocking words

- **Mutation Hooks Location**: `src/frontend/src/hooks/mutations/`
  - `useVocabularyMutations.ts` - Mark words, bulk operations

- **UI Stores Location**: `src/frontend/src/store/`
  - `useVocabularyUIStore.ts` - Vocabulary UI state (level, language, search)
  - `useGameUIStore.ts` - Game UI state (subtitles, word index)
  - `useAuthStore.ts` - Auth UI state

#### Deprecated Stores (DO NOT USE for new components)
- ~~`useVocabularyStore.ts`~~ - Use React Query hooks instead
- ~~`useGameStore.ts`~~ - Use React Query hooks instead

### Testing

- **Backend Tests**: `cd src/backend && powershell.exe -Command ". api_venv/Scripts/activate; python -m pytest"`
- **Frontend Tests**: `cd src/frontend && npm test`
- **All Tests with Nx**: `nx run-many --target=test --all`
- **Affected Tests Only**: `nx affected --target=test`

---

## Reports & Analysis

### Recent Reports (2025)
Located in `docs/reports/`

#### Performance & Architecture
- **[Architecture Options Analysis](./reports/architecture_options_analysis_2025.md)** - Comparison of architecture patterns
- **[Nx Migration Implementation](./reports/nx_migration_implementation_report.md)** - Nx setup details
- **[React Query Migration](./reports/react_query_migration_report.md)** - Migration implementation

#### Feature Analysis
- **[CEFR Extraction Rules](./reports/CEFR_EXTRACTION_RULES_REPORT.md)** - Difficulty level extraction
- **[Known Words Filtering](./reports/known_words_filtering_analysis.md)** - Word filtering implementation
- **[NeMo Integration](./reports/NEMO_INTEGRATION_PLAN.md)** - NeMo ASR integration
- **[Vocabulary Migration](./reports/vocabulary_migration_verification.md)** - Migration verification

#### Planning Documents
- **[Audio Processing Improvements](./reports/audio_processing_improvements_2025.md)**
- **[Deployment Options](./reports/deployment_options_2025.md)**
- **[FastAPI Testing Strategy](./reports/fastapi_testing_strategy.md)**

### Completed Plans
Located in `docs/archive/plans/` (historical reference only)

---

## Archive

### Session Logs
Located in `docs/archive/sessions/` - Historical development session logs

### Legacy Documents
Located in `docs/archive/` - Old reports and plans kept for reference

---

## Key Architectural Decisions

### State Management Philosophy

**Server State (React Query):**
- API responses and cached data
- Automatic caching, refetching, and invalidation
- Loading and error states handled automatically
- Examples: vocabulary words, user progress, statistics

**Client State (Zustand):**
- Pure UI state: current level, search query, modal open/closed
- Local to the browser, not from API
- Examples: currentLevel, searchQuery, showSubtitles

**Local State (useState):**
- Ephemeral state: hover, animation flags
- Component-specific, doesn't need global access
- Examples: isHovered, isExpanded, inputValue

### Migration Strategy

**Approach:** Incremental, risk-averse
1. Create new React Query hooks alongside old stores
2. Add deprecation notices to old stores
3. Create comprehensive migration examples
4. Migrate simple components first to validate patterns
5. Gradually migrate complex components
6. Remove old stores only after all migrations complete

**Current Status:**
- Phase 1: ✅ Complete (Nx monorepo setup)
- Phase 2: ✅ Complete (React Query infrastructure)
- Phase 3: ✅ Complete (Migration patterns documented)
- Component Migration: 🔄 In Progress (incremental)

---

## Contributing

### Before Making Changes

1. Read [CLAUDE.md](../CLAUDE.md) for core development rules
2. Check [Phase 3 Summary](./guides/PHASE3_SUMMARY.md) for current architecture
3. Review relevant guide in this index
4. Follow migration patterns from [Component Migration Examples](./guides/PHASE3_COMPONENT_MIGRATION_EXAMPLES.md)

### When Adding New Components

- **For server data**: Use React Query hooks from `@/hooks`
- **For UI state**: Create minimal Zustand store or use local useState
- **Never**: Mix server data with UI state in the same store
- **Reference**: [VocabularyStatsCard.example.tsx](../src/frontend/src/components/examples/VocabularyStatsCard.example.tsx)

### When Migrating Existing Components

1. Identify state types (server vs UI)
2. Replace queries with React Query hooks
3. Replace mutations with mutation hooks
4. Move UI state to Zustand UI store or local useState
5. Remove manual loading/error states
6. Remove useEffects for data fetching
7. Test thoroughly
8. Follow [Migration Checklist](./guides/PHASE3_COMPONENT_MIGRATION_EXAMPLES.md#migration-checklist)

---

## Tools & Resources

### Development Tools

- **React Query DevTools**: Available in dev mode (bottom-left icon)
- **Nx Console**: VS Code extension for Nx commands
- **Nx Graph**: `nx graph` - Visualize project dependencies

### External Documentation

- [React Query Docs](https://tanstack.com/query/latest/docs/react/overview)
- [Nx Documentation](https://nx.dev/getting-started/intro)
- [Zustand Documentation](https://docs.pmnd.rs/zustand/getting-started/introduction)

---

## FAQ

### Q: When should I use React Query vs Zustand?
**A:** Use React Query for any data from the API (server state). Use Zustand only for pure UI state like current tab, modal open/closed, or local preferences.

### Q: How do I invalidate the cache after a mutation?
**A:** Mutation hooks like `useMarkWord` handle cache invalidation automatically. See [useVocabularyMutations.ts](../src/frontend/src/hooks/mutations/useVocabularyMutations.ts) for examples.

### Q: What if I need to share state across components?
**A:** If it's server data, React Query automatically shares the cache. If it's UI state, use a Zustand store (see [useVocabularyUIStore.ts](../src/frontend/src/store/useVocabularyUIStore.ts) as template).

### Q: How do I test components using React Query?
**A:** Wrap your component in `QueryClientProvider` with a test client. See [React Query Testing Docs](https://tanstack.com/query/latest/docs/react/guides/testing).

### Q: Can I still use the old Zustand stores?
**A:** They're deprecated but still functional. However, new components should use React Query hooks. See deprecation notices in the store files for migration guidance.

---

## Maintenance

**Last Updated:** 2025-11-13
**Current Version:** Phase 3 Complete (Nx + React Query + Migration Patterns)
**Next Steps:** Incremental component migration, optional Kubernetes deployment

**Document Owner:** Architecture Team
**Review Frequency:** After major architecture changes

---

## Directory Structure

```
docs/
├── architecture/     # Living architecture documentation
│   ├── API_DOCUMENTATION.md
│   ├── DDD_ARCHITECTURE_ANALYSIS.md
│   ├── DDD_COMPARISON.md
│   ├── EVENT_SYSTEM_OVERVIEW.md
│   ├── NEMO_INTEGRATION.md
│   ├── VOCABULARY_BLOCKING_WORDS_ANALYSIS.md
│   ├── VOCABULARY_DATABASE_SCHEMA.md
│   └── migration_checklist_bert_to_spacy.md
├── guides/           # Developer guides and migration patterns
│   ├── NX_MIGRATION_GUIDE.md
│   ├── PHASE3_COMPONENT_MIGRATION_EXAMPLES.md
│   ├── PHASE3_SUMMARY.md
│   └── REACT_QUERY_MIGRATION.md
├── reports/          # Point-in-time analysis and reports (38 files)
│   ├── architecture_options_analysis_2025.md
│   ├── nx_migration_implementation_report.md
│   ├── react_query_migration_report.md
│   └── [35 more reports...]
├── archive/          # Historical artifacts
│   ├── plans/        # Old planning documents
│   └── sessions/     # Development session summaries
└── README.md         # This file
```

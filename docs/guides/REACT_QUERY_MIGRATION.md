# React Query Migration Guide

This guide explains the Phase 2 migration from Zustand stores with custom caching to React Query for server-side state management.

## Summary of Changes

### What Changed

**Before (Zustand):**
- All state (server data + UI state) in Zustand stores
- ~200 LOC of custom caching logic
- Manual cache invalidation with timestamps
- Loading states managed manually
- Error handling scattered across components

**After (React Query + Zustand):**
- Server data managed by React Query hooks
- UI state in lightweight Zustand stores
- Automatic caching, refetching, and invalidation
- Built-in loading/error states
- Centralized error handling

### Files Added

```
src/frontend/src/
├── lib/
│   └── queryClient.ts              # React Query configuration
├── hooks/
│   ├── index.ts                   # Barrel exports
│   ├── queries/
│   │   ├── useVocabulary.ts       # Vocabulary queries
│   │   ├── useAuth.ts             # Auth queries
│   │   └── useGame.ts             # Game queries
│   └── mutations/
│       └── useVocabularyMutations.ts  # Vocabulary mutations
└── store/
    ├── useVocabularyUIStore.ts    # Vocabulary UI state only
    └── useGameUIStore.ts          # Game UI state only
```

### Files Modified

- `src/frontend/src/App.tsx` - Added QueryClientProvider
- `src/frontend/src/services/api-client.ts` - Kept functional, caching now handled by React Query

### Files to Deprecate (Components should stop using)

- `src/frontend/src/store/useVocabularyStore.ts` - Replace with hooks + UI store
- `src/frontend/src/store/useGameStore.ts` - Replace with hooks + UI store
- `src/frontend/src/store/useAuthStore.ts` - Keep for now (auth is special case)

---

## Migration Guide for Components

### Vocabulary Components

#### Old Pattern (Zustand)

```typescript
// Before
import { useVocabularyStore, useVocabularyWords } from '@/store/useVocabularyStore'

function VocabularyList() {
  const words = useVocabularyWords()
  const isLoading = useVocabularyStore(state => state.isLoading)
  const fetchWords = useVocabularyStore(state => state.fetchWordsByLevel)
  const markWord = useVocabularyStore(state => state.markWord)

  useEffect(() => {
    fetchWords('A1', 'de')
  }, [])

  return (
    <div>
      {isLoading && <Loading />}
      {words.map(word => (
        <WordCard
          key={word.id}
          word={word}
          onMark={(known) => markWord(word.id, known)}
        />
      ))}
    </div>
  )
}
```

#### New Pattern (React Query)

```typescript
// After
import { useWordsByLevel, useMarkWord } from '@/hooks'
import { useVocabularyUIStore } from '@/store/useVocabularyUIStore'

function VocabularyList() {
  const currentLevel = useVocabularyUIStore(state => state.currentLevel)
  const { data: words = [], isLoading } = useWordsByLevel(currentLevel, 'de')
  const markWordMutation = useMarkWord()

  return (
    <div>
      {isLoading && <Loading />}
      {words.map(word => (
        <WordCard
          key={word.id}
          word={word}
          onMark={(known) => markWordMutation.mutate({ vocabularyId: word.id, isKnown: known })}
        />
      ))}
    </div>
  )
}
```

**Key Changes:**
- ✅ No useEffect needed - React Query fetches automatically
- ✅ Loading state from useWordsByLevel hook
- ✅ Data destructured with default value
- ✅ Mutations use .mutate() method
- ✅ Cache automatically invalidated on mutation

---

### Search Components

#### Old Pattern

```typescript
// Before
import { useVocabularyStore } from '@/store/useVocabularyStore'

function SearchBar() {
  const searchQuery = useVocabularyStore(state => state.searchQuery)
  const setSearchQuery = useVocabularyStore(state => state.setSearchQuery)
  const searchWords = useVocabularyStore(state => state.searchWords)
  const results = useVocabularyStore(state => state.searchResults)
  const isSearching = useVocabularyStore(state => state.isSearching)

  const handleSearch = async (query: string) => {
    setSearchQuery(query)
    await searchWords(query, 'de', 20)
  }

  return <input onChange={(e) => handleSearch(e.target.value)} />
}
```

#### New Pattern

```typescript
// After
import { useSearchWords } from '@/hooks'
import { useVocabularyUIStore } from '@/store/useVocabularyUIStore'

function SearchBar() {
  const searchQuery = useVocabularyUIStore(state => state.searchQuery)
  const setSearchQuery = useVocabularyUIStore(state => state.setSearchQuery)
  const { data: results = [], isLoading: isSearching } = useSearchWords(searchQuery, 'de', 20)

  return (
    <input
      value={searchQuery}
      onChange={(e) => setSearchQuery(e.target.value)}
    />
  )
}
```

**Key Changes:**
- ✅ React Query automatically debounces (enabled only when query is non-empty)
- ✅ No manual search function needed
- ✅ Results update automatically when searchQuery changes
- ✅ Loading state from hook

---

### Statistics Components

#### Old Pattern

```typescript
// Before
import { useVocabularyStats } from '@/store/useVocabularyStore'

function StatsCard() {
  const stats = useVocabularyStats()
  const fetchStats = useVocabularyStore(state => state.fetchStats)

  useEffect(() => {
    fetchStats('de')
  }, [])

  if (!stats) return null

  return (
    <div>
      <p>Known: {stats.known_words}</p>
      <p>Unknown: {stats.unknown_words}</p>
    </div>
  )
}
```

#### New Pattern

```typescript
// After
import { useVocabularyStats } from '@/hooks'

function StatsCard() {
  const { data: stats, isLoading } = useVocabularyStats('de')

  if (isLoading) return <Loading />
  if (!stats) return null

  return (
    <div>
      <p>Known: {stats.known_words}</p>
      <p>Unknown: {stats.unknown_words}</p>
    </div>
  )
}
```

**Key Changes:**
- ✅ Automatic refetch on window focus (stats always fresh)
- ✅ Automatic refetch after marking words (cache invalidation)
- ✅ No manual fetchStats call needed

---

### Game Components

#### Old Pattern

```typescript
// Before
import { useGameStore } from '@/store/useGameStore'

function BlockingWordsView() {
  const currentWords = useGameStore(state => state.currentWords)
  const isProcessing = useGameStore(state => state.isProcessing)
  const loadWords = useGameStore(state => state.loadSegmentWords)

  useEffect(() => {
    loadWords(0)
  }, [])

  return (
    <div>
      {isProcessing && <Loading />}
      {currentWords.map(word => <WordCard word={word} />)}
    </div>
  )
}
```

#### New Pattern

```typescript
// After
import { useBlockingWords } from '@/hooks'
import { useGameUIStore } from '@/store/useGameUIStore'

function BlockingWordsView() {
  const gameSession = useGameUIStore(state => state.gameSession)
  const { data: currentWords = [], isLoading } = useBlockingWords(
    gameSession?.video_path || '',
    { enabled: !!gameSession }
  )

  return (
    <div>
      {isLoading && <Loading />}
      {currentWords.map(word => <WordCard word={word} />)}
    </div>
  )
}
```

**Key Changes:**
- ✅ Words cached per video_path
- ✅ Automatic refetch when switching videos
- ✅ Conditional fetching with `enabled` option

---

## Available Hooks

### Vocabulary Queries

```typescript
// Fetch words by CEFR level
const { data, isLoading, error } = useWordsByLevel('A1', 'de')

// Search words
const { data } = useSearchWords(searchQuery, 'de', 20)

// Get random words for practice
const { data } = useRandomWords('de', ['A1', 'A2'], 10)

// Get user progress for all words
const { data } = useUserProgress('de')

// Get vocabulary statistics
const { data } = useVocabularyStats('de')

// Get progress for specific word
const progress = useWordProgress(vocabularyId, 'de')

// Check if word is known
const isKnown = useIsWordKnown(vocabularyId, 'de')
```

### Vocabulary Mutations

```typescript
// Mark single word
const markWord = useMarkWord()
markWord.mutate({ vocabularyId: 123, isKnown: true, language: 'de' })

// Mark multiple words
const bulkMark = useBulkMarkWords()
bulkMark.mutate({ vocabularyIds: [1, 2, 3], isKnown: true, language: 'de' })

// Refresh all vocabulary data
const refresh = useRefreshVocabulary()
refresh()
```

### Game Queries

```typescript
// Get blocking words for video
const { data } = useBlockingWords('/path/to/video.mp4')
```

### Auth Queries

```typescript
// Get current user (auto-refreshes on window focus)
const { data: user } = useCurrentUser(isAuthenticated)
```

---

## React Query Features

### Automatic Refetching

```typescript
// Refetch on window focus (useful for stats)
const { data } = useVocabularyStats('de', {
  refetchOnWindowFocus: true,
})

// Refetch every 30 seconds
const { data } = useCurrentUser(true, {
  refetchInterval: 30000,
})
```

### Loading & Error States

```typescript
const { data, isLoading, isError, error, isFetching } = useWordsByLevel('A1')

// isLoading - true on initial fetch
// isFetching - true on any fetch (including background refetch)
// isError - true if query failed
// error - error object if query failed
```

### Optimistic Updates

```typescript
const markWord = useMarkWord({
  onMutate: async (variables) => {
    // Cancel outgoing refetches
    await queryClient.cancelQueries({ queryKey: queryKeys.progress.list('de') })

    // Snapshot previous value
    const previousProgress = queryClient.getQueryData(queryKeys.progress.list('de'))

    // Optimistically update UI
    queryClient.setQueryData(queryKeys.progress.list('de'), old => {
      // Update local cache immediately
      return updateProgress(old, variables)
    })

    // Return context for rollback
    return { previousProgress }
  },
  onError: (err, variables, context) => {
    // Rollback on error
    queryClient.setQueryData(queryKeys.progress.list('de'), context.previousProgress)
  },
})
```

### Cache Invalidation

```typescript
// Automatic invalidation (already configured in mutations)
const markWord = useMarkWord() // Auto-invalidates stats after mutation

// Manual invalidation
import { queryClient, queryKeys } from '@/lib/queryClient'

// Invalidate specific query
queryClient.invalidateQueries({ queryKey: queryKeys.vocabulary.list({ level: 'A1' }) })

// Invalidate all vocabulary queries
queryClient.invalidateQueries({ queryKey: queryKeys.vocabulary.all })

// Invalidate and refetch immediately
queryClient.invalidateQueries({
  queryKey: queryKeys.progress.stats('de'),
  refetchType: 'active',
})
```

### Dependent Queries

```typescript
// Query B depends on Query A
const { data: user } = useCurrentUser()
const { data: progress } = useUserProgress('de', {
  enabled: !!user, // Only fetch if user is loaded
})
```

---

## Testing with React Query

### Test Setup

```typescript
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'

// Create wrapper with query client
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false, // Disable retries in tests
        gcTime: 0, // Don't keep cache in tests
      },
    },
  })

  return ({ children }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}

// Test a query hook
test('fetches words by level', async () => {
  const { result } = renderHook(() => useWordsByLevel('A1'), {
    wrapper: createWrapper(),
  })

  await waitFor(() => expect(result.current.isSuccess).toBe(true))
  expect(result.current.data).toHaveLength(10)
})
```

### Mocking API Calls

```typescript
import { vi } from 'vitest'
import { api } from '@/services/api-client'

// Mock API responses
vi.spyOn(api.vocabulary, 'getByLevel').mockResolvedValue({
  data: [{ id: 1, word: 'Hallo', lemma: 'hallo', language: 'de', difficulty_level: 'A1' }],
  status: 200,
})
```

---

## React Query Devtools

The React Query Devtools are automatically enabled in development mode:

- Open devtools with the floating icon (bottom-left)
- View all queries and their states
- Inspect cache contents
- Manually refetch queries
- Clear cache
- View query timelines

---

## Performance Benefits

### Before (Zustand + Custom Caching)

```
First visit:
✅ Fetch words (1s) → Cache for 5 min

Switch to different level:
✅ Fetch new level (1s) → Cache for 5 min

Return to first level after 4 minutes:
✅ Serve from cache (instant)

Return to first level after 6 minutes:
❌ Cache expired → Fetch again (1s)
```

### After (React Query)

```
First visit:
✅ Fetch words (1s) → Cache with 5 min stale time

Switch to different level:
✅ Fetch new level (1s) → Cache

Return to first level after 4 minutes:
✅ Serve from cache (instant) → Background refetch

Return to first level after 6 minutes:
✅ Serve stale data (instant) → Background refetch

Mark word as known:
✅ Update cache optimistically (instant)
✅ Send mutation to server → Invalidate stats
```

**Improvements:**
- Stale-while-revalidate: Show cached data immediately, refetch in background
- Optimistic updates: UI updates instantly before server confirms
- Automatic invalidation: Stats refresh after marking words
- Parallel queries: Fetch words + progress + stats simultaneously

---

## Migration Checklist

### For Each Component

- [ ] Identify Zustand store usage
- [ ] Separate server data from UI state
- [ ] Replace fetch calls with useQuery hooks
- [ ] Replace mutations with useMutation hooks
- [ ] Remove manual loading state management
- [ ] Remove manual error handling (use hook states)
- [ ] Remove useEffect for initial fetches
- [ ] Update UI state to use new UI stores
- [ ] Test loading states
- [ ] Test error states
- [ ] Test cache invalidation

### Common Patterns

**Pattern 1: Remove useEffect for fetching**

```typescript
// Before
useEffect(() => {
  fetchWords()
}, [])

// After
const { data } = useWordsByLevel('A1') // Automatic
```

**Pattern 2: Replace manual loading states**

```typescript
// Before
const [isLoading, setIsLoading] = useState(false)
setIsLoading(true)
await fetchData()
setIsLoading(false)

// After
const { data, isLoading } = useQuery(...)
```

**Pattern 3: Optimistic mutations**

```typescript
// Before
markWord(id, true)
await fetchStats() // Manual refresh

// After
markWordMutation.mutate({ vocabularyId: id, isKnown: true })
// Stats auto-refresh via cache invalidation
```

---

## Troubleshooting

### Query Not Refetching

```typescript
// Check query key dependencies
queryKey: queryKeys.vocabulary.list({ level, language })

// Ensure dependencies are in query key
const { data } = useWordsByLevel(level, language) // ✅ Correct

// NOT like this:
const { data } = useWordsByLevel('A1') // ❌ Won't refetch when level changes
```

### Cache Not Invalidating

```typescript
// Ensure mutation invalidates correct keys
onSuccess: () => {
  queryClient.invalidateQueries({ queryKey: queryKeys.progress.all })
}

// Use specific keys for targeted invalidation
queryClient.invalidateQueries({ queryKey: queryKeys.progress.stats('de') })
```

### Slow Initial Load

```typescript
// Use prefetching for critical data
useEffect(() => {
  queryClient.prefetchQuery({
    queryKey: queryKeys.vocabulary.list({ level: 'A1', language: 'de' }),
    queryFn: () => api.vocabulary.getByLevel('A1', 'de'),
  })
}, [])
```

---

## Next Steps

1. **Migrate components incrementally**:
   - Start with simple read-only components
   - Move to components with mutations
   - End with complex components

2. **Monitor performance**:
   - Use React Query Devtools to inspect cache
   - Check network tab for unnecessary refetches
   - Adjust staleTime if needed

3. **Clean up old code**:
   - Remove old Zustand stores after migration complete
   - Remove custom caching from api-client.ts
   - Update documentation

---

## Resources

- [React Query Documentation](https://tanstack.com/query/latest/docs/react/overview)
- [React Query Devtools](https://tanstack.com/query/latest/docs/react/devtools)
- [Query Keys Guide](https://tkdodo.eu/blog/effective-react-query-keys)
- [Optimistic Updates](https://tanstack.com/query/latest/docs/react/guides/optimistic-updates)

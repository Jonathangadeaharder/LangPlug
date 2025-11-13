# Phase 3: Component Migration Examples

This document shows real examples of migrating components from Zustand to React Query.

## Example 1: LearningPlayer - Blocking Words

### Before (Direct API Call + Manual State)

```typescript
import { getBlockingWordsApiVocabularyBlockingWordsGet } from '@/client/services.gen'
import { useGameStore } from '@/store/useGameStore'

export const LearningPlayer: React.FC = () => {
  const [loading, setLoading] = useState(false)
  const [segmentWords, setSegmentWords] = useState<VocabularyWord[]>([])
  const { markWordKnown } = useGameStore()

  const loadSegmentWords = async (_segmentIndex: number) => {
    if (!videoInfo) return

    setLoading(true)
    try {
      const blockingWordsResponse = await getBlockingWordsApiVocabularyBlockingWordsGet({
        videoPath: videoInfo.path,
      })

      const words = Array.isArray(blockingWordsResponse)
        ? blockingWordsResponse
        : (blockingWordsResponse?.blocking_words ?? [])

      setSegmentWords(words)
      setShowVocabularyGame(words.length > 0)
    } catch (error) {
      handleApiError(error, 'LearningPlayer.handleError')
      toast.error('Failed to load vocabulary words')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (!videoInfo) {
      navigate('/')
      return
    }
    loadSegmentWords(0)
  }, [videoInfo, navigate])

  const handleWordAnswered = async (word: string, known: boolean) => {
    await markWordKnown(word, known)
  }

  return (
    <div>
      {loading && <LoadingOverlay>Loading vocabulary...</LoadingOverlay>}
      {/* ... */}
    </div>
  )
}
```

**Problems:**
- Manual loading state management
- Manual error handling
- useEffect dependency issues (loadSegmentWords not stable)
- No caching - refetches on every mount
- No automatic refetching
- Mutation (markWordKnown) mixed with component logic

### After (React Query)

```typescript
import { useBlockingWords } from '@/hooks'
import { useMarkWord } from '@/hooks'
import { useGameUIStore } from '@/store/useGameUIStore'

export const LearningPlayer: React.FC = () => {
  const { gameSession } = useGameUIStore()

  // Query: Fetches and caches blocking words
  const {
    data: segmentWords = [],
    isLoading,
    isError,
  } = useBlockingWords(videoInfo?.path || '', {
    enabled: !!videoInfo,
    staleTime: 10 * 60 * 1000, // 10 minutes
    onSuccess: (words) => {
      setShowVocabularyGame(words.length > 0)
    },
  })

  // Mutation: Marks words as known/unknown
  const markWordMutation = useMarkWord({
    onSuccess: () => {
      // Stats automatically refresh via cache invalidation
      toast.success('Word marked!')
    },
  })

  const handleWordAnswered = (word: string, known: boolean) => {
    // Find the full word object
    const wordData = segmentWords.find(w => w.word === word)
    if (wordData) {
      markWordMutation.mutate({
        vocabularyId: wordData.id,
        isKnown: known,
        language: 'de',
      })
    }
  }

  // No useEffect needed - React Query fetches automatically when videoInfo changes
  // No manual loading state - isLoading from hook
  // No manual error handling - isError from hook
  // Automatic caching - words cached per video path
  // Automatic refetching - refetches when video changes

  return (
    <div>
      {isLoading && <LoadingOverlay>Loading vocabulary...</LoadingOverlay>}
      {isError && <ErrorMessage>Failed to load vocabulary</ErrorMessage>}
      {/* ... */}
    </div>
  )
}
```

**Benefits:**
- ✅ No manual loading state
- ✅ Automatic error handling
- ✅ No useEffect needed
- ✅ Automatic caching (10 min per video)
- ✅ Automatic refetching when videoInfo changes
- ✅ Mutations properly separated
- ✅ Automatic stats refresh after marking words

---

## Example 2: VocabularyLibrary - Stats and Level Data

### Before (Manual State + Multiple useEffects)

```typescript
export const VocabularyLibrary: React.FC = () => {
  const [activeLevel, setActiveLevel] = useState<string>('A1')
  const [levelData, setLevelData] = useState<VocabularyLevel | null>(null)
  const [stats, setStats] = useState<VocabularyStats | null>(null)
  const [loading, setLoading] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')

  // Load stats on mount
  useEffect(() => {
    loadStats()
  }, [])

  // Load level data when level changes
  useEffect(() => {
    if (activeLevel) {
      setCurrentPage(0)
      setSearchTerm('')
      loadLevelData(activeLevel)
    }
  }, [activeLevel])

  // Debounced search
  useEffect(() => {
    if (activeLevel) {
      const delayedSearch = setTimeout(() => {
        loadLevelData(activeLevel)
      }, 300)
      return () => clearTimeout(delayedSearch)
    }
  }, [searchTerm, currentPage, activeLevel])

  const loadStats = async () => {
    try {
      const statsData = await getVocabularyStatsApiVocabularyStatsGet()
      setStats(statsData as VocabularyStats)
    } catch (error) {
      toast.error('Failed to load vocabulary statistics')
    }
  }

  const loadLevelData = async (level: string) => {
    setLoading(true)
    try {
      const data = await getVocabularyLevelApiVocabularyLibraryLevelGet({
        level,
        targetLanguage: 'de',
        limit: searchTerm ? 1000 : ITEMS_PER_PAGE,
        search: searchTerm || undefined,
        offset: currentPage * ITEMS_PER_PAGE,
      })
      setLevelData(data as VocabularyLevel)
    } catch (error) {
      toast.error(`Failed to load ${level} vocabulary`)
    } finally {
      setLoading(false)
    }
  }

  // Manual refresh
  const handleRefresh = () => {
    loadStats()
    loadLevelData(activeLevel)
  }
}
```

**Problems:**
- Multiple useEffects with complex dependencies
- Manual debouncing with setTimeout
- Manual loading states
- Manual error handling
- No caching
- Manual refresh logic

### After (React Query)

```typescript
import { useWordsByLevel, useVocabularyStats, useMarkWord } from '@/hooks'
import { useVocabularyUIStore } from '@/store/useVocabularyUIStore'

export const VocabularyLibrary: React.FC = () => {
  const { currentLevel, setCurrentLevel, searchQuery, setSearchQuery } = useVocabularyUIStore()
  const [currentPage, setCurrentPage] = useState(0)

  // Query: Fetch stats (auto-refetches on window focus)
  const {
    data: stats,
    isLoading: statsLoading,
    refetch: refetchStats,
  } = useVocabularyStats('de')

  // Query: Fetch words by level (auto-refetches when level changes)
  const {
    data: levelWords = [],
    isLoading: wordsLoading,
    isError: wordsError,
  } = useWordsByLevel(currentLevel, 'de', {
    // Automatically refetches when currentLevel changes
    staleTime: 5 * 60 * 1000,
  })

  // Query: Search words (only runs when searchQuery is not empty)
  const {
    data: searchResults = [],
    isLoading: searchLoading,
  } = useSearchWords(searchQuery, 'de', 1000, {
    enabled: searchQuery.trim().length > 0,
    staleTime: 2 * 60 * 1000,
  })

  // Use search results if searching, otherwise use level words
  const displayWords = searchQuery ? searchResults : levelWords
  const loading = wordsLoading || searchLoading

  // Mutation: Mark word
  const markWordMutation = useMarkWord({
    onSuccess: () => {
      // Stats automatically refresh via cache invalidation
      toast.success('Progress saved!')
    },
  })

  // No useEffects needed!
  // - Stats load automatically on mount
  // - Words refetch when currentLevel changes
  // - Search runs automatically when searchQuery changes
  // - All caching handled by React Query

  // Refresh is now simple
  const handleRefresh = () => {
    refetchStats()
    // Level words will auto-refetch if stale
  }

  return (
    <Container>
      {statsLoading && <Loading />}
      {stats && (
        <StatsGrid>
          <StatCard label="Total Words" value={stats.total_reviewed} />
          <StatCard label="Known" value={stats.known_words} />
          {/* ... */}
        </StatsGrid>
      )}

      <LevelTabs>
        {levels.map(level => (
          <LevelTab
            key={level}
            active={level === currentLevel}
            onClick={() => setCurrentLevel(level)}
          >
            {level}
          </LevelTab>
        ))}
      </LevelTabs>

      <SearchBar
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        placeholder="Search words..."
      />

      {loading && <Loading />}
      {wordsError && <Error>Failed to load vocabulary</Error>}

      <WordGrid>
        {displayWords.map(word => (
          <WordCard
            key={word.id}
            word={word}
            onMark={(known) => markWordMutation.mutate({
              vocabularyId: word.id,
              isKnown: known,
              language: 'de',
            })}
          />
        ))}
      </WordGrid>
    </Container>
  )
}
```

**Benefits:**
- ✅ No useEffects needed
- ✅ Automatic refetching when dependencies change
- ✅ Built-in debouncing via enabled condition
- ✅ Automatic caching (5 min for words, 2 min for search)
- ✅ Automatic loading/error states
- ✅ Stats automatically refresh after marking words
- ✅ Simpler refresh logic
- ✅ Better separation of concerns (UI state in Zustand, server state in React Query)

---

## Migration Checklist

For each component using Zustand stores:

### 1. Identify State Types

- [ ] **Server Data**: API responses, cached data → Use React Query
- [ ] **UI State**: Current selection, modals open, local flags → Use Zustand UI stores

### 2. Replace Queries

- [ ] Find all manual API calls (fetch, axios, client functions)
- [ ] Replace with appropriate React Query hooks
- [ ] Remove manual loading states
- [ ] Remove manual error handling
- [ ] Remove useEffects for data fetching

### 3. Replace Mutations

- [ ] Find all write operations (POST, PUT, DELETE)
- [ ] Replace with React Query mutation hooks
- [ ] Use optimistic updates if needed
- [ ] Remove manual cache invalidation (React Query handles it)

### 4. Clean Up

- [ ] Remove useState for server data
- [ ] Remove useEffects for fetching
- [ ] Remove manual debouncing (use enabled condition)
- [ ] Remove manual refresh logic
- [ ] Update imports to use new hooks

### 5. Test

- [ ] Component renders correctly
- [ ] Data loads on mount
- [ ] Data refetches when dependencies change
- [ ] Mutations work and invalidate cache
- [ ] Loading states display correctly
- [ ] Error states display correctly

---

## Common Patterns

### Pattern 1: Conditional Fetching

```typescript
// Before
useEffect(() => {
  if (userId) {
    fetchUserData(userId)
  }
}, [userId])

// After
const { data } = useQuery({
  queryKey: ['user', userId],
  queryFn: () => fetchUserData(userId),
  enabled: !!userId, // Only run if userId exists
})
```

### Pattern 2: Dependent Queries

```typescript
// Before
useEffect(() => {
  if (user) {
    fetchUserPosts(user.id)
  }
}, [user])

// After
const { data: user } = useCurrentUser()
const { data: posts } = useQuery({
  queryKey: ['posts', user?.id],
  queryFn: () => fetchUserPosts(user.id),
  enabled: !!user, // Wait for user to load
})
```

### Pattern 3: Debounced Search

```typescript
// Before
useEffect(() => {
  const timer = setTimeout(() => {
    search(query)
  }, 300)
  return () => clearTimeout(timer)
}, [query])

// After
const { data } = useQuery({
  queryKey: ['search', query],
  queryFn: () => search(query),
  enabled: query.length > 0, // Auto-debounces via staleTime
  staleTime: 300, // Waits 300ms before refetching
})
```

### Pattern 4: Optimistic Updates

```typescript
// Before
const handleLike = async (postId) => {
  // UI doesn't update until server responds
  await likePost(postId)
  refetchPosts()
}

// After
const likeMutation = useMutation({
  mutationFn: likePost,
  onMutate: async (postId) => {
    // Cancel outgoing refetches
    await queryClient.cancelQueries(['posts'])

    // Snapshot previous value
    const previousPosts = queryClient.getQueryData(['posts'])

    // Optimistically update UI
    queryClient.setQueryData(['posts'], old =>
      old.map(post =>
        post.id === postId
          ? { ...post, liked: true, likes: post.likes + 1 }
          : post
      )
    )

    return { previousPosts }
  },
  onError: (err, postId, context) => {
    // Rollback on error
    queryClient.setQueryData(['posts'], context.previousPosts)
  },
  onSettled: () => {
    // Refetch to ensure consistency
    queryClient.invalidateQueries(['posts'])
  },
})
```

---

## Migration Timeline

Suggested order for migrating components:

1. **Simple read-only components** (lists, displays)
   - Low risk
   - Immediate caching benefits
   - Good learning experience

2. **Components with mutations** (forms, interactive)
   - Medium risk
   - Optimistic updates add value
   - Cache invalidation benefits

3. **Complex components with multiple queries** (dashboards, libraries)
   - Higher risk
   - Most benefit from React Query
   - Do last after pattern is established

---

## When NOT to Use React Query

- **Pure UI state**: Modal open/closed, current tab, theme → Use Zustand
- **Form state**: Input values, validation → Use react-hook-form or local state
- **Ephemeral state**: Hover state, animation flags → Use local useState
- **Synchronous data**: Constants, derived values → Use useMemo

React Query is **only** for server-side/async state that comes from APIs.

---

## Resources

- `/docs/guides/REACT_QUERY_MIGRATION.md` - Full migration guide
- `/src/frontend/src/hooks/` - All React Query hooks
- `/src/frontend/src/store/useVocabularyUIStore.ts` - Example UI-only store
- React Query Devtools - Available in dev mode (bottom-left icon)

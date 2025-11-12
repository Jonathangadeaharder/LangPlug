/**
 * Auth query hooks using React Query
 * Note: Auth is special - we still use Zustand for token/user state management
 * because it needs to be synchronously available and persisted
 *
 * React Query is used here for:
 * - Session validation
 * - User data refetching
 * - Automatic session refresh on window focus
 */
import { useQuery, UseQueryOptions } from '@tanstack/react-query'
import { authGetCurrentUserApiAuthMeGet } from '@/client/services.gen'
import type { UserRead } from '@/client/types.gen'
import { queryKeys } from '@/lib/queryClient'

/**
 * Fetch current user data
 * This runs automatically when user is authenticated
 * and refetches on window focus to keep data fresh
 */
export const useCurrentUser = (
  enabled: boolean = true,
  options?: Omit<UseQueryOptions<UserRead>, 'queryKey' | 'queryFn'>
) => {
  return useQuery({
    queryKey: queryKeys.auth.user(),
    queryFn: async () => {
      return await authGetCurrentUserApiAuthMeGet()
    },
    enabled,
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: true, // Always check session on focus
    retry: false, // Don't retry auth failures
    ...options,
  })
}

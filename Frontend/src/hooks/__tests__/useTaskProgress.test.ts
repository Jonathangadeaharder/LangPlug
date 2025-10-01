import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useTaskProgress } from '../useTaskProgress';

vi.mock('@/client/services.gen', () => ({
  getTaskProgressApiProcessProgressTaskIdGet: vi.fn(),
}));

import { getTaskProgressApiProcessProgressTaskIdGet } from '@/client/services.gen';
const mockGetTaskProgress = vi.mocked(getTaskProgressApiProcessProgressTaskIdGet);

describe('useTaskProgress Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  describe('Initial State', () => {
    it('has correct initial state', () => {
      const { result } = renderHook(() => useTaskProgress());

      expect(result.current.progress).toBe(0);
      expect(result.current.status).toBe('idle');
      expect(result.current.error).toBeNull();
      expect(result.current.isComplete).toBe(false);
      expect(result.current.taskId).toBeNull();
    });
  });

  describe('Starting Task Monitoring', () => {
    it('starts monitoring a task successfully', async () => {
      const mockStatus = {
        taskId: 'task-123',
        status: 'processing' as const,
        progress: 25,
        message: 'Processing video...',
        current_step: 'transcribing'
      };

      mockGetTaskProgress.mockResolvedValue(mockStatus);

      const { result } = renderHook(() => useTaskProgress());

      act(() => {
        result.current.startMonitoring('task-123');
      });

      expect(result.current.taskId).toBe('task-123');
      expect(result.current.status).toBe('monitoring');

      // Fast-forward timer to trigger first poll
      await act(async () => {
        vi.advanceTimersByTime(2000);
      });

      expect(mockGetTaskProgress).toHaveBeenCalledWith({ taskId: 'task-123' });
      expect(result.current.progress).toBe(25);
      expect(result.current.status).toBe('processing');
    });

    it('handles task completion', async () => {
      const mockCompletedStatus = {
        taskId: 'task-123',
        status: 'completed' as const,
        progress: 100,
        current_step: 'complete',
        result: { videoId: 'video-456' }
      };

      mockGetTaskProgress.mockResolvedValue(mockCompletedStatus);

      const { result } = renderHook(() => useTaskProgress());

      act(() => {
        result.current.startMonitoring('task-123');
      });

      await act(async () => {
        vi.advanceTimersByTime(2000);
      });

      expect(result.current.progress).toBe(100);
      expect(result.current.status).toBe('completed');
      expect(result.current.isComplete).toBe(true);
      expect(result.current.result).toEqual({ videoId: 'video-456' });
    });

    it('handles task failure', async () => {
      const mockFailedStatus = {
        taskId: 'task-123',
        status: 'error' as const,
        progress: 50,
        current_step: 'failed',
        error: 'Processing failed: Invalid video format'
      };

      mockGetTaskProgress.mockResolvedValue(mockFailedStatus);

      const { result } = renderHook(() => useTaskProgress());

      act(() => {
        result.current.startMonitoring('task-123');
      });

      await act(async () => {
        vi.advanceTimersByTime(2000);
      });

      expect(result.current.status).toBe('failed');
      expect(result.current.error).toBe('Processing failed: Invalid video format');
      expect(result.current.isComplete).toBe(false);
    });

    it('handles API errors during monitoring', async () => {
      const apiError = new Error('Network error');
      mockGetTaskProgress.mockRejectedValue(apiError);

      const { result } = renderHook(() => useTaskProgress());

      act(() => {
        result.current.startMonitoring('task-123');
      });

      await act(async () => {
        vi.advanceTimersByTime(2000);
      });

      expect(result.current.status).toBe('error');
      expect(result.current.error).toBe('Network error');
    });
  });

  describe('Polling Behavior', () => {
    it('polls at regular intervals', async () => {
      const mockStatus = {
        taskId: 'task-123',
        status: 'processing' as const,
        progress: 25,
        current_step: 'transcribing'
      };

      mockGetTaskProgress.mockResolvedValue(mockStatus);

      const { result } = renderHook(() => useTaskProgress());

      act(() => {
        result.current.startMonitoring('task-123');
      });

      // First poll
      await act(async () => {
        vi.advanceTimersByTime(2000);
      });

      expect(mockGetTaskProgress).toHaveBeenCalledTimes(1);

      // Second poll
      await act(async () => {
        vi.advanceTimersByTime(2000);
      });

      expect(mockGetTaskProgress).toHaveBeenCalledTimes(2);

      // Third poll
      await act(async () => {
        vi.advanceTimersByTime(2000);
      });

      expect(mockGetTaskProgress).toHaveBeenCalledTimes(3);
    });

    it('stops polling when task completes', async () => {
      let callCount = 0;
      mockGetTaskProgress.mockImplementation((() => {
        callCount++;
        if (callCount === 1) {
          return Promise.resolve({
            taskId: 'task-123',
            status: 'processing' as const,
            progress: 50,
            current_step: 'transcribing'
          });
        } else {
          return Promise.resolve({
            taskId: 'task-123',
            status: 'completed' as const,
            progress: 100,
            current_step: 'complete'
          });
        }
      }) as any);

      const { result } = renderHook(() => useTaskProgress());

      act(() => {
        result.current.startMonitoring('task-123');
      });

      // First poll - processing
      await act(async () => {
        vi.advanceTimersByTime(2000);
      });

      expect(result.current.status).toBe('processing');

      // Second poll - completed
      await act(async () => {
        vi.advanceTimersByTime(2000);
      });

      expect(result.current.status).toBe('completed');

      // Third poll should not happen
      await act(async () => {
        vi.advanceTimersByTime(2000);
      });

      expect(mockGetTaskProgress).toHaveBeenCalledTimes(2);
    });
  });

  describe('Stop Monitoring', () => {
    it('stops monitoring when requested', async () => {
      const mockStatus = {
        taskId: 'task-123',
        status: 'processing' as const,
        progress: 25,
        current_step: 'transcribing'
      };

      mockGetTaskProgress.mockResolvedValue(mockStatus);

      const { result } = renderHook(() => useTaskProgress());

      act(() => {
        result.current.startMonitoring('task-123');
      });

      // First poll
      await act(async () => {
        vi.advanceTimersByTime(2000);
      });

      expect(mockGetTaskProgress).toHaveBeenCalledTimes(1);

      // Stop monitoring
      act(() => {
        result.current.stopMonitoring();
      });

      // Next poll should not happen
      await act(async () => {
        vi.advanceTimersByTime(2000);
      });

      expect(mockGetTaskProgress).toHaveBeenCalledTimes(1);
      expect(result.current.status).toBe('idle');
    });
  });

  describe('Reset', () => {
    it('resets to initial state', () => {
      const { result } = renderHook(() => useTaskProgress());

      // Set some state
      act(() => {
        result.current.startMonitoring('task-123');
      });

      expect(result.current.taskId).toBe('task-123');

      // Reset
      act(() => {
        result.current.reset();
      });

      expect(result.current.progress).toBe(0);
      expect(result.current.status).toBe('idle');
      expect(result.current.error).toBeNull();
      expect(result.current.isComplete).toBe(false);
      expect(result.current.taskId).toBeNull();
    });
  });

  describe('Cleanup', () => {
    it('cleans up timers on unmount', () => {
      const { result, unmount } = renderHook(() => useTaskProgress());

      act(() => {
        result.current.startMonitoring('task-123');
      });

      const clearIntervalSpy = vi.spyOn(global, 'clearInterval');

      unmount();

      expect(clearIntervalSpy).toHaveBeenCalled();
    });
  });
});

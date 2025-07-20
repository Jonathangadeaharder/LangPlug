/**
 * Performance Testing Utilities for State Management Comparison
 * 
 * This module provides tools to measure and compare performance between
 * React Context API and Zustand implementations.
 */

import { performance } from 'perf_hooks';

interface PerformanceMetrics {
  renderCount: number;
  totalRenderTime: number;
  averageRenderTime: number;
  memoryUsage?: number;
  stateUpdateTime: number;
  componentMountTime: number;
}

interface TestResult {
  contextAPI: PerformanceMetrics;
  zustand: PerformanceMetrics;
  improvement: {
    renderCountReduction: string;
    renderTimeImprovement: string;
    stateUpdateImprovement: string;
    memoryImprovement?: string;
  };
}

class PerformanceTracker {
  private metrics: PerformanceMetrics = {
    renderCount: 0,
    totalRenderTime: 0,
    averageRenderTime: 0,
    stateUpdateTime: 0,
    componentMountTime: 0,
  };

  private renderStartTime: number = 0;
  private stateUpdateStartTime: number = 0;
  private mountStartTime: number = 0;

  startRender(): void {
    this.renderStartTime = performance.now();
  }

  endRender(): void {
    const renderTime = performance.now() - this.renderStartTime;
    this.metrics.renderCount++;
    this.metrics.totalRenderTime += renderTime;
    this.metrics.averageRenderTime = this.metrics.totalRenderTime / this.metrics.renderCount;
  }

  startStateUpdate(): void {
    this.stateUpdateStartTime = performance.now();
  }

  endStateUpdate(): void {
    this.metrics.stateUpdateTime += performance.now() - this.stateUpdateStartTime;
  }

  startMount(): void {
    this.mountStartTime = performance.now();
  }

  endMount(): void {
    this.metrics.componentMountTime = performance.now() - this.mountStartTime;
  }

  getMetrics(): PerformanceMetrics {
    return { ...this.metrics };
  }

  reset(): void {
    this.metrics = {
      renderCount: 0,
      totalRenderTime: 0,
      averageRenderTime: 0,
      stateUpdateTime: 0,
      componentMountTime: 0,
    };
  }
}

// Global trackers for comparison
export const contextTracker = new PerformanceTracker();
export const zustandTracker = new PerformanceTracker();

/**
 * React Hook for tracking component renders
 */
export const useRenderTracker = (tracker: PerformanceTracker, componentName: string) => {
  React.useEffect(() => {
    tracker.startRender();
    return () => {
      tracker.endRender();
      if (__DEV__) {
        console.log(`${componentName} rendered - Total renders: ${tracker.getMetrics().renderCount}`);
      }
    };
  });
};

/**
 * Higher-order component for performance tracking
 */
export const withPerformanceTracking = <P extends object>(
  Component: React.ComponentType<P>,
  tracker: PerformanceTracker,
  componentName: string
) => {
  return React.memo((props: P) => {
    useRenderTracker(tracker, componentName);
    
    React.useEffect(() => {
      tracker.startMount();
      return () => {
        tracker.endMount();
      };
    }, []);

    return <Component {...props} />;
  });
};

/**
 * Simulate heavy state operations for testing
 */
export const simulateHeavyStateOperations = async (tracker: PerformanceTracker, operations: number = 100) => {
  for (let i = 0; i < operations; i++) {
    tracker.startStateUpdate();
    
    // Simulate state update work
    await new Promise(resolve => setTimeout(resolve, 1));
    
    tracker.endStateUpdate();
  }
};

/**
 * Generate performance comparison report
 */
export const generatePerformanceReport = (): TestResult => {
  const contextMetrics = contextTracker.getMetrics();
  const zustandMetrics = zustandTracker.getMetrics();

  const renderCountReduction = (
    ((contextMetrics.renderCount - zustandMetrics.renderCount) / contextMetrics.renderCount) * 100
  ).toFixed(1);

  const renderTimeImprovement = (
    ((contextMetrics.averageRenderTime - zustandMetrics.averageRenderTime) / contextMetrics.averageRenderTime) * 100
  ).toFixed(1);

  const stateUpdateImprovement = (
    ((contextMetrics.stateUpdateTime - zustandMetrics.stateUpdateTime) / contextMetrics.stateUpdateTime) * 100
  ).toFixed(1);

  return {
    contextAPI: contextMetrics,
    zustand: zustandMetrics,
    improvement: {
      renderCountReduction: `${renderCountReduction}%`,
      renderTimeImprovement: `${renderTimeImprovement}%`,
      stateUpdateImprovement: `${stateUpdateImprovement}%`,
    },
  };
};

/**
 * Log performance comparison to console
 */
export const logPerformanceComparison = () => {
  const report = generatePerformanceReport();
  
  console.group('🚀 State Management Performance Comparison');
  
  console.group('📊 Context API Metrics');
  console.log('Render Count:', report.contextAPI.renderCount);
  console.log('Average Render Time:', `${report.contextAPI.averageRenderTime.toFixed(2)}ms`);
  console.log('Total State Update Time:', `${report.contextAPI.stateUpdateTime.toFixed(2)}ms`);
  console.log('Component Mount Time:', `${report.contextAPI.componentMountTime.toFixed(2)}ms`);
  console.groupEnd();
  
  console.group('⚡ Zustand Metrics');
  console.log('Render Count:', report.zustand.renderCount);
  console.log('Average Render Time:', `${report.zustand.averageRenderTime.toFixed(2)}ms`);
  console.log('Total State Update Time:', `${report.zustand.stateUpdateTime.toFixed(2)}ms`);
  console.log('Component Mount Time:', `${report.zustand.componentMountTime.toFixed(2)}ms`);
  console.groupEnd();
  
  console.group('📈 Performance Improvements');
  console.log('Render Count Reduction:', report.improvement.renderCountReduction);
  console.log('Render Time Improvement:', report.improvement.renderTimeImprovement);
  console.log('State Update Improvement:', report.improvement.stateUpdateImprovement);
  console.groupEnd();
  
  console.groupEnd();
  
  return report;
};

/**
 * Reset all performance trackers
 */
export const resetPerformanceTrackers = () => {
  contextTracker.reset();
  zustandTracker.reset();
  console.log('🔄 Performance trackers reset');
};

/**
 * Benchmark function for automated testing
 */
export const runPerformanceBenchmark = async (testDuration: number = 5000) => {
  console.log(`🏁 Starting ${testDuration}ms performance benchmark...`);
  
  resetPerformanceTrackers();
  
  const startTime = performance.now();
  let operationCount = 0;
  
  // Simulate continuous state operations
  while (performance.now() - startTime < testDuration) {
    await simulateHeavyStateOperations(contextTracker, 10);
    await simulateHeavyStateOperations(zustandTracker, 10);
    operationCount++;
  }
  
  const report = logPerformanceComparison();
  
  console.log(`✅ Benchmark completed after ${operationCount} operation cycles`);
  
  return report;
};

/**
 * Memory usage tracking (React Native specific)
 */
export const trackMemoryUsage = () => {
  if (typeof global !== 'undefined' && global.performance && global.performance.memory) {
    return {
      usedJSHeapSize: global.performance.memory.usedJSHeapSize,
      totalJSHeapSize: global.performance.memory.totalJSHeapSize,
      jsHeapSizeLimit: global.performance.memory.jsHeapSizeLimit,
    };
  }
  return null;
};

/**
 * Export types for external usage
 */
export type { PerformanceMetrics, TestResult };

/**
 * Usage Examples:
 * 
 * // In a Context API component:
 * const MyContextComponent = withPerformanceTracking(
 *   MyComponent,
 *   contextTracker,
 *   'MyContextComponent'
 * );
 * 
 * // In a Zustand component:
 * const MyZustandComponent = withPerformanceTracking(
 *   MyComponent,
 *   zustandTracker,
 *   'MyZustandComponent'
 * );
 * 
 * // Run benchmark:
 * runPerformanceBenchmark(10000).then(report => {
 *   // Use report data
 * });
 * 
 * // Manual tracking:
 * contextTracker.startStateUpdate();
 * // ... perform state update
 * contextTracker.endStateUpdate();
 */
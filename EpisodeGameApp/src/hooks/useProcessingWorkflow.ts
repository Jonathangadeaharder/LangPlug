import { useState, useEffect, useCallback } from 'react';

export type ProcessingStage = 'idle' | 'transcription' | 'filtering' | 'translation' | 'complete' | 'error';

interface ProcessingStep {
  id: string;
  name: string;
  stage: ProcessingStage;
  progress: number;
  status: 'pending' | 'active' | 'completed' | 'error';
  message?: string;
  error?: string;
}

interface ProcessingResult {
  transcription?: string;
  filteredWords?: string[];
  translations?: Record<string, string>;
  metadata?: Record<string, any>;
}

interface UseProcessingWorkflowProps {
  onStageChange?: (stage: ProcessingStage) => void;
  onProgress?: (stage: ProcessingStage, progress: number) => void;
  onComplete?: (result: ProcessingResult) => void;
  onError?: (stage: ProcessingStage, error: string) => void;
  autoStart?: boolean;
}

interface UseProcessingWorkflowReturn {
  // Current state
  currentStage: ProcessingStage;
  overallProgress: number;
  isProcessing: boolean;
  isComplete: boolean;
  hasError: boolean;
  
  // Processing steps
  steps: ProcessingStep[];
  currentStep: ProcessingStep | null;
  
  // Results
  result: ProcessingResult;
  
  // Actions
  startProcessing: () => void;
  pauseProcessing: () => void;
  resumeProcessing: () => void;
  resetProcessing: () => void;
  skipCurrentStep: () => void;
  retryCurrentStep: () => void;
  
  // Manual step control
  updateStepProgress: (stepId: string, progress: number, message?: string) => void;
  completeStep: (stepId: string, data?: any) => void;
  failStep: (stepId: string, error: string) => void;
}

const initialSteps: ProcessingStep[] = [
  {
    id: 'transcription',
    name: 'Audio Transcription',
    stage: 'transcription',
    progress: 0,
    status: 'pending',
    message: 'Preparing to transcribe audio...',
  },
  {
    id: 'filtering',
    name: 'Content Filtering',
    stage: 'filtering',
    progress: 0,
    status: 'pending',
    message: 'Waiting for transcription...',
  },
  {
    id: 'translation',
    name: 'Translation Processing',
    stage: 'translation',
    progress: 0,
    status: 'pending',
    message: 'Waiting for filtering...',
  },
];

export const useProcessingWorkflow = ({
  onStageChange,
  onProgress,
  onComplete,
  onError,
  autoStart = false,
}: UseProcessingWorkflowProps = {}): UseProcessingWorkflowReturn => {
  const [currentStage, setCurrentStage] = useState<ProcessingStage>('idle');
  const [steps, setSteps] = useState<ProcessingStep[]>(initialSteps);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [result, setResult] = useState<ProcessingResult>({});
  
  const currentStep = steps.find(step => step.status === 'active') || null;
  const isComplete = currentStage === 'complete';
  const hasError = currentStage === 'error';
  
  // Calculate overall progress
  const overallProgress = Math.round(
    steps.reduce((total, step) => total + step.progress, 0) / steps.length
  );

  // Auto-start processing if enabled
  useEffect(() => {
    if (autoStart && currentStage === 'idle') {
      startProcessing();
    }
  }, [autoStart]);

  // Notify stage changes
  useEffect(() => {
    onStageChange?.(currentStage);
  }, [currentStage, onStageChange]);

  // Notify progress changes
  useEffect(() => {
    if (currentStep) {
      onProgress?.(currentStage, currentStep.progress);
    }
  }, [currentStage, currentStep?.progress, onProgress]);

  const updateStepProgress = useCallback((stepId: string, progress: number, message?: string) => {
    setSteps(prev => prev.map(step => 
      step.id === stepId 
        ? { ...step, progress: Math.max(0, Math.min(100, progress)), message }
        : step
    ));
  }, []);

  const completeStep = useCallback((stepId: string, data?: any) => {
    setSteps(prev => prev.map(step => 
      step.id === stepId 
        ? { ...step, progress: 100, status: 'completed' as const, message: 'Completed successfully' }
        : step
    ));
    
    // Update result with step data
    if (data) {
      setResult(prev => ({ ...prev, [stepId]: data }));
    }
    
    // Move to next step or complete
    const currentIndex = steps.findIndex(step => step.id === stepId);
    const nextStep = steps[currentIndex + 1];
    
    if (nextStep) {
      setSteps(prev => prev.map(step => 
        step.id === nextStep.id 
          ? { ...step, status: 'active' as const, message: 'Processing...' }
          : step
      ));
      setCurrentStage(nextStep.stage);
    } else {
      setCurrentStage('complete');
      setIsProcessing(false);
      onComplete?.(result);
    }
  }, [steps, result, onComplete]);

  const failStep = useCallback((stepId: string, error: string) => {
    setSteps(prev => prev.map(step => 
      step.id === stepId 
        ? { ...step, status: 'error' as const, error, message: `Error: ${error}` }
        : step
    ));
    setCurrentStage('error');
    setIsProcessing(false);
    onError?.(currentStage, error);
  }, [currentStage, onError]);

  const startProcessing = useCallback(() => {
    if (isProcessing && !isPaused) return;
    
    setIsProcessing(true);
    setIsPaused(false);
    
    if (currentStage === 'idle' || currentStage === 'error') {
      // Start from beginning
      setCurrentStage('transcription');
      setSteps(prev => prev.map((step, index) => ({
        ...step,
        progress: 0,
        status: index === 0 ? 'active' : 'pending',
        message: index === 0 ? 'Processing...' : step.message,
        error: undefined,
      })));
      setResult({});
    } else {
      // Resume from current step
      const activeStep = steps.find(step => step.status === 'active');
      if (activeStep) {
        setSteps(prev => prev.map(step => 
          step.id === activeStep.id 
            ? { ...step, message: 'Processing...' }
            : step
        ));
      }
    }
  }, [isProcessing, isPaused, currentStage, steps]);

  const pauseProcessing = useCallback(() => {
    setIsPaused(true);
    setSteps(prev => prev.map(step => 
      step.status === 'active' 
        ? { ...step, message: 'Paused...' }
        : step
    ));
  }, []);

  const resumeProcessing = useCallback(() => {
    if (!isProcessing) return;
    
    setIsPaused(false);
    setSteps(prev => prev.map(step => 
      step.status === 'active' 
        ? { ...step, message: 'Processing...' }
        : step
    ));
  }, [isProcessing]);

  const resetProcessing = useCallback(() => {
    setCurrentStage('idle');
    setIsProcessing(false);
    setIsPaused(false);
    setSteps(initialSteps);
    setResult({});
  }, []);

  const skipCurrentStep = useCallback(() => {
    if (!currentStep) return;
    
    completeStep(currentStep.id, null);
  }, [currentStep, completeStep]);

  const retryCurrentStep = useCallback(() => {
    if (!currentStep) return;
    
    setSteps(prev => prev.map(step => 
      step.id === currentStep.id 
        ? { ...step, progress: 0, status: 'active', message: 'Retrying...', error: undefined }
        : step
    ));
    
    if (currentStage === 'error') {
      setCurrentStage(currentStep.stage);
    }
  }, [currentStep, currentStage]);

  return {
    // Current state
    currentStage,
    overallProgress,
    isProcessing: isProcessing && !isPaused,
    isComplete,
    hasError,
    
    // Processing steps
    steps,
    currentStep,
    
    // Results
    result,
    
    // Actions
    startProcessing,
    pauseProcessing,
    resumeProcessing,
    resetProcessing,
    skipCurrentStep,
    retryCurrentStep,
    
    // Manual step control
    updateStepProgress,
    completeStep,
    failStep,
  };
};

// Helper function to simulate processing with delays
export const simulateProcessingStep = async (
  stepId: string,
  updateProgress: (progress: number, message?: string) => void,
  duration: number = 3000
): Promise<any> => {
  return new Promise((resolve, reject) => {
    let progress = 0;
    const interval = setInterval(() => {
      progress += Math.random() * 20;
      if (progress >= 100) {
        progress = 100;
        clearInterval(interval);
        updateProgress(100, 'Completed successfully');
        
        // Simulate different results based on step
        switch (stepId) {
          case 'transcription':
            resolve('This is a sample transcription of the audio content.');
            break;
          case 'filtering':
            resolve(['word1', 'word2', 'word3', 'word4', 'word5']);
            break;
          case 'translation':
            resolve({
              word1: 'palabra1',
              word2: 'palabra2',
              word3: 'palabra3',
              word4: 'palabra4',
              word5: 'palabra5',
            });
            break;
          default:
            resolve(null);
        }
      } else {
        updateProgress(progress, `Processing ${stepId}... ${Math.round(progress)}%`);
      }
    }, duration / 20);
  });
};

export default useProcessingWorkflow;
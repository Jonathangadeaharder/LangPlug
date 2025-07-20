import { useState, useEffect, useCallback } from 'react';

interface Question {
  id: string;
  text: string;
  options: string[];
  correctAnswer: number;
  explanation?: string;
}

interface GameStats {
  correct: number;
  incorrect: number;
  total: number;
  score: number;
  timeSpent: number;
}

interface UseGameLogicProps {
  questions: Question[];
  timeLimit?: number; // in seconds
  onGameComplete?: (stats: GameStats) => void;
  onQuestionAnswered?: (questionId: string, isCorrect: boolean) => void;
}

interface UseGameLogicReturn {
  // Current game state
  currentQuestionIndex: number;
  currentQuestion: Question | null;
  selectedAnswer: number | null;
  isAnswerSubmitted: boolean;
  isCorrect: boolean | null;
  gameStats: GameStats;
  
  // Timer state
  timeRemaining: number;
  isTimerActive: boolean;
  
  // Game status
  isGameComplete: boolean;
  isGameStarted: boolean;
  
  // Actions
  startGame: () => void;
  selectAnswer: (answerIndex: number) => void;
  submitAnswer: () => void;
  nextQuestion: () => void;
  skipQuestion: () => void;
  resetGame: () => void;
  pauseTimer: () => void;
  resumeTimer: () => void;
}

export const useGameLogic = ({
  questions,
  timeLimit = 300, // 5 minutes default
  onGameComplete,
  onQuestionAnswered,
}: UseGameLogicProps): UseGameLogicReturn => {
  // Game state
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null);
  const [isAnswerSubmitted, setIsAnswerSubmitted] = useState(false);
  const [isCorrect, setIsCorrect] = useState<boolean | null>(null);
  const [isGameStarted, setIsGameStarted] = useState(false);
  const [isGameComplete, setIsGameComplete] = useState(false);
  
  // Timer state
  const [timeRemaining, setTimeRemaining] = useState(timeLimit);
  const [isTimerActive, setIsTimerActive] = useState(false);
  const [startTime, setStartTime] = useState<number | null>(null);
  
  // Game statistics
  const [gameStats, setGameStats] = useState<GameStats>({
    correct: 0,
    incorrect: 0,
    total: 0,
    score: 0,
    timeSpent: 0,
  });

  const currentQuestion = questions[currentQuestionIndex] || null;

  // Timer effect
  useEffect(() => {
    let interval: NodeJS.Timeout;
    
    if (isTimerActive && timeRemaining > 0 && !isGameComplete) {
      interval = setInterval(() => {
        setTimeRemaining(prev => {
          if (prev <= 1) {
            completeGame();
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }
    
    return () => {
      if (interval) {
        clearInterval(interval);
      }
    };
  }, [isTimerActive, timeRemaining, isGameComplete]);

  const startGame = useCallback(() => {
    setIsGameStarted(true);
    setIsTimerActive(true);
    setStartTime(Date.now());
    setCurrentQuestionIndex(0);
    setSelectedAnswer(null);
    setIsAnswerSubmitted(false);
    setIsCorrect(null);
    setIsGameComplete(false);
    setGameStats({
      correct: 0,
      incorrect: 0,
      total: 0,
      score: 0,
      timeSpent: 0,
    });
  }, []);

  const selectAnswer = useCallback((answerIndex: number) => {
    if (!isAnswerSubmitted) {
      setSelectedAnswer(answerIndex);
    }
  }, [isAnswerSubmitted]);

  const submitAnswer = useCallback(() => {
    if (selectedAnswer === null || isAnswerSubmitted || !currentQuestion) {
      return;
    }

    const correct = selectedAnswer === currentQuestion.correctAnswer;
    setIsCorrect(correct);
    setIsAnswerSubmitted(true);
    
    // Update stats
    setGameStats(prev => ({
      ...prev,
      correct: prev.correct + (correct ? 1 : 0),
      incorrect: prev.incorrect + (correct ? 0 : 1),
      total: prev.total + 1,
      score: Math.round(((prev.correct + (correct ? 1 : 0)) / (prev.total + 1)) * 100),
    }));

    // Notify parent component
    onQuestionAnswered?.(currentQuestion.id, correct);
  }, [selectedAnswer, isAnswerSubmitted, currentQuestion, onQuestionAnswered]);

  const nextQuestion = useCallback(() => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(prev => prev + 1);
      setSelectedAnswer(null);
      setIsAnswerSubmitted(false);
      setIsCorrect(null);
    } else {
      completeGame();
    }
  }, [currentQuestionIndex, questions.length]);

  const skipQuestion = useCallback(() => {
    // Treat skip as incorrect answer
    setGameStats(prev => ({
      ...prev,
      incorrect: prev.incorrect + 1,
      total: prev.total + 1,
      score: Math.round((prev.correct / (prev.total + 1)) * 100),
    }));
    
    if (currentQuestion) {
      onQuestionAnswered?.(currentQuestion.id, false);
    }
    
    nextQuestion();
  }, [currentQuestion, nextQuestion, onQuestionAnswered]);

  const completeGame = useCallback(() => {
    setIsGameComplete(true);
    setIsTimerActive(false);
    
    const finalStats = {
      ...gameStats,
      timeSpent: startTime ? Math.round((Date.now() - startTime) / 1000) : 0,
    };
    
    setGameStats(finalStats);
    onGameComplete?.(finalStats);
  }, [gameStats, startTime, onGameComplete]);

  const resetGame = useCallback(() => {
    setCurrentQuestionIndex(0);
    setSelectedAnswer(null);
    setIsAnswerSubmitted(false);
    setIsCorrect(null);
    setIsGameStarted(false);
    setIsGameComplete(false);
    setTimeRemaining(timeLimit);
    setIsTimerActive(false);
    setStartTime(null);
    setGameStats({
      correct: 0,
      incorrect: 0,
      total: 0,
      score: 0,
      timeSpent: 0,
    });
  }, [timeLimit]);

  const pauseTimer = useCallback(() => {
    setIsTimerActive(false);
  }, []);

  const resumeTimer = useCallback(() => {
    if (!isGameComplete && timeRemaining > 0) {
      setIsTimerActive(true);
    }
  }, [isGameComplete, timeRemaining]);

  return {
    // Current game state
    currentQuestionIndex,
    currentQuestion,
    selectedAnswer,
    isAnswerSubmitted,
    isCorrect,
    gameStats,
    
    // Timer state
    timeRemaining,
    isTimerActive,
    
    // Game status
    isGameComplete,
    isGameStarted,
    
    // Actions
    startGame,
    selectAnswer,
    submitAnswer,
    nextQuestion,
    skipQuestion,
    resetGame,
    pauseTimer,
    resumeTimer,
  };
};

// Helper function to format time
export const formatTime = (seconds: number): string => {
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
};

// Helper function to generate sample questions
export const generateSampleQuestions = (count: number = 10): Question[] => {
  const sampleQuestions: Question[] = [
    {
      id: '1',
      text: 'What does "hello" mean in Spanish?',
      options: ['Adiós', 'Hola', 'Gracias', 'Por favor'],
      correctAnswer: 1,
      explanation: '"Hola" is the Spanish word for "hello".',
    },
    {
      id: '2',
      text: 'Which word means "thank you"?',
      options: ['De nada', 'Lo siento', 'Gracias', 'Perdón'],
      correctAnswer: 2,
      explanation: '"Gracias" means "thank you" in Spanish.',
    },
    {
      id: '3',
      text: 'How do you say "goodbye"?',
      options: ['Hola', 'Adiós', 'Buenos días', 'Buenas noches'],
      correctAnswer: 1,
      explanation: '"Adiós" is the Spanish word for "goodbye".',
    },
    {
      id: '4',
      text: 'What does "por favor" mean?',
      options: ['Thank you', 'Please', 'Excuse me', 'You\'re welcome'],
      correctAnswer: 1,
      explanation: '"Por favor" means "please" in Spanish.',
    },
    {
      id: '5',
      text: 'Which phrase means "good morning"?',
      options: ['Buenas tardes', 'Buenas noches', 'Buenos días', 'Hasta luego'],
      correctAnswer: 2,
      explanation: '"Buenos días" means "good morning" in Spanish.',
    },
  ];
  
  // Repeat and shuffle questions to reach desired count
  const questions = [];
  for (let i = 0; i < count; i++) {
    const baseQuestion = sampleQuestions[i % sampleQuestions.length];
    questions.push({
      ...baseQuestion,
      id: `${baseQuestion.id}_${i}`,
    });
  }
  
  return questions;
};

export default useGameLogic;
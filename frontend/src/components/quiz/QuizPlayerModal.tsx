import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  X, Clock, Award, CheckCircle2, XCircle, HelpCircle, 
  ArrowRight, ArrowLeft, RefreshCw, Sparkles, BookOpen 
} from 'lucide-react';

interface Question {
  id: string;
  question_text: string;
  question_type: string;
  options?: string[];
  concept_tag: string;
  points: number;
  order: number;
}

interface Quiz {
  id: string;
  course_id: string;
  title: string;
  description?: string;
  passing_score_percentage: number;
  time_limit_minutes?: number;
  is_ai_generated: boolean;
  questions: Question[];
}

interface AnswerFeedback {
  question_id: string;
  question_text: string;
  student_answer?: string;
  correct_answer: string;
  is_correct: boolean;
  explanation?: string;
  feedback?: string;
  concept_tag: string;
}

interface SubmissionResult {
  attempt_id: string;
  quiz_id: string;
  score_percentage: number;
  points_earned: number;
  total_points: number;
  passed: boolean;
  time_spent_seconds: number;
  answer_feedbacks: AnswerFeedback[];
}

interface QuizPlayerModalProps {
  quizId: string | null;
  isOpen: boolean;
  onClose: () => void;
  onQuizCompleted?: () => void;
}

export const QuizPlayerModal: React.FC<QuizPlayerModalProps> = ({
  quizId,
  isOpen,
  onClose,
  onQuizCompleted
}) => {
  const [quiz, setQuiz] = useState<Quiz | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<SubmissionResult | null>(null);
  const [timeSpentSeconds, setTimeSpentSeconds] = useState(0);

  useEffect(() => {
    if (isOpen && quizId) {
      setLoading(true);
      setError(null);
      setResult(null);
      setAnswers({});
      setCurrentIndex(0);
      setTimeSpentSeconds(0);

      const token = localStorage.getItem('token');
      const backendUrl = import.meta.env.VITE_API_BASE_URL || 'https://ai-doubt-backend.onrender.com';

      axios.get(`${backendUrl}/api/v1/quizzes/${quizId}`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      .then(res => {
        setQuiz(res.data);
        setLoading(false);
      })
      .catch(err => {
        setError(err.response?.data?.detail || 'Failed to load quiz');
        setLoading(false);
      });
    }
  }, [isOpen, quizId]);

  // Timer counter
  useEffect(() => {
    let timer: any;
    if (isOpen && quiz && !result) {
      timer = setInterval(() => {
        setTimeSpentSeconds(prev => prev + 1);
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [isOpen, quiz, result]);

  if (!isOpen || !quizId) return null;

  const handleOptionSelect = (questionId: string, option: string) => {
    setAnswers(prev => ({ ...prev, [questionId]: option }));
  };

  const handleSubmit = async () => {
    if (!quiz || submitting) return;
    setSubmitting(true);

    try {
      const token = localStorage.getItem('token');
      const backendUrl = import.meta.env.VITE_API_BASE_URL || 'https://ai-doubt-backend.onrender.com';

      const res = await axios.post(
        `${backendUrl}/api/v1/quizzes/${quiz.id}/submit`,
        {
          answers,
          time_spent_seconds: timeSpentSeconds
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      setResult(res.data);
      if (onQuizCompleted) onQuizCompleted();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to submit quiz attempt');
    } finally {
      setSubmitting(false);
    }
  };

  const formatTimer = (totalSeconds: number) => {
    const m = Math.floor(totalSeconds / 60);
    const s = totalSeconds % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4 overflow-y-auto">
      <div className="relative w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="p-5 bg-slate-950 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-indigo-600/20 border border-indigo-500/30 rounded-xl text-indigo-400">
              <Award className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                {quiz ? quiz.title : 'Assessment Quiz'}
                {quiz?.is_ai_generated && (
                  <span className="text-[10px] px-2 py-0.5 bg-indigo-950 text-indigo-300 border border-indigo-800 rounded-full font-medium flex items-center gap-1">
                    <Sparkles className="w-3 h-3" /> AI Generated
                  </span>
                )}
              </h2>
              {quiz?.description && <p className="text-xs text-slate-400 mt-0.5">{quiz.description}</p>}
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading && (
            <div className="flex flex-col items-center justify-center py-12 space-y-3 text-slate-400">
              <RefreshCw className="w-8 h-8 animate-spin text-indigo-500" />
              <p className="text-sm">Loading quiz questions...</p>
            </div>
          )}

          {error && (
            <div className="p-4 bg-rose-950/60 border border-rose-800/80 rounded-xl text-rose-300 text-sm text-center">
              {error}
            </div>
          )}

          {/* RESULTS VIEW */}
          {result && (
            <div className="space-y-6">
              {/* Score Banner */}
              <div className={`p-6 rounded-2xl border text-center ${
                result.passed
                  ? 'bg-emerald-950/60 border-emerald-500/40 text-emerald-300'
                  : 'bg-rose-950/60 border-rose-500/40 text-rose-300'
              }`}>
                <div className="flex justify-center mb-3">
                  {result.passed ? (
                    <CheckCircle2 className="w-12 h-12 text-emerald-400" />
                  ) : (
                    <XCircle className="w-12 h-12 text-rose-400" />
                  )}
                </div>
                <h3 className="text-2xl font-extrabold text-white">
                  {result.passed ? 'Quiz Passed!' : 'Needs Review'}
                </h3>
                <p className="text-3xl font-bold mt-2">
                  {result.score_percentage}%
                </p>
                <p className="text-xs mt-1 text-slate-400">
                  Earned {result.points_earned} of {result.total_points} points in {formatTimer(result.time_spent_seconds)}
                </p>
              </div>

              {/* Per Question Detailed Feedback */}
              <div className="space-y-4">
                <h4 className="text-sm font-semibold text-white flex items-center gap-2">
                  <BookOpen className="w-4 h-4 text-indigo-400" /> Detailed AI Answer Explanations
                </h4>
                {result.answer_feedbacks.map((fb, idx) => (
                  <div
                    key={fb.question_id}
                    className={`p-4 rounded-xl border text-xs leading-relaxed ${
                      fb.is_correct
                        ? 'bg-slate-900 border-emerald-500/30'
                        : 'bg-slate-900 border-rose-500/30'
                    }`}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <span className="font-semibold text-slate-200">
                        {idx + 1}. {fb.question_text}
                      </span>
                      <span className={`px-2 py-0.5 text-[10px] font-bold rounded ${
                        fb.is_correct ? 'bg-emerald-950 text-emerald-400' : 'bg-rose-950 text-rose-400'
                      }`}>
                        {fb.is_correct ? 'Correct' : 'Incorrect'}
                      </span>
                    </div>

                    <div className="space-y-1 text-slate-400">
                      <p><strong className="text-slate-300">Your Answer:</strong> {fb.student_answer || 'No Answer'}</p>
                      {!fb.is_correct && (
                        <p><strong className="text-emerald-400">Correct Answer:</strong> {fb.correct_answer}</p>
                      )}
                      {fb.explanation && (
                        <p className="mt-2 text-indigo-300 bg-indigo-950/40 p-2.5 rounded-lg border border-indigo-900/50">
                          <strong className="text-indigo-200">AI Explanation:</strong> {fb.explanation}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ACTIVE QUIZ QUESTION VIEW */}
          {quiz && !result && quiz.questions.length > 0 && (
            <div className="space-y-6">
              {/* Progress & Timer Bar */}
              <div className="flex items-center justify-between text-xs text-slate-400 pb-3 border-b border-slate-800">
                <span className="font-semibold text-indigo-400">
                  Question {currentIndex + 1} of {quiz.questions.length}
                </span>
                <div className="flex items-center space-x-2 text-slate-300">
                  <Clock className="w-4 h-4 text-indigo-400" />
                  <span className="font-mono">{formatTimer(timeSpentSeconds)}</span>
                </div>
              </div>

              {/* Current Question Display */}
              {(() => {
                const currentQ = quiz.questions[currentIndex];
                const selectedOpt = answers[currentQ.id] || '';

                return (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 bg-slate-800 text-slate-300 rounded border border-slate-700">
                        {currentQ.concept_tag}
                      </span>
                      <span className="text-xs text-slate-400">{currentQ.points} Point(s)</span>
                    </div>

                    <h3 className="text-base font-semibold text-white leading-snug">
                      {currentQ.question_text}
                    </h3>

                    {/* Options list */}
                    <div className="space-y-2.5 pt-2">
                      {(currentQ.options || ['True', 'False']).map((opt, oIdx) => (
                        <button
                          key={oIdx}
                          onClick={() => handleOptionSelect(currentQ.id, opt)}
                          className={`w-full p-3.5 rounded-xl border text-left text-xs font-medium transition-all flex items-center justify-between ${
                            selectedOpt === opt
                              ? 'bg-indigo-600/20 border-indigo-500 text-white shadow-md shadow-indigo-600/10'
                              : 'bg-slate-900 border-slate-800/80 text-slate-300 hover:border-slate-700 hover:bg-slate-800/60'
                          }`}
                        >
                          <span>{opt}</span>
                          <div className={`w-4 h-4 rounded-full border flex items-center justify-center ${
                            selectedOpt === opt ? 'border-indigo-400 bg-indigo-500' : 'border-slate-700'
                          }`}>
                            {selectedOpt === opt && <div className="w-1.5 h-1.5 bg-white rounded-full" />}
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                );
              })()}
            </div>
          )}
        </div>

        {/* Footer Navigation */}
        <div className="p-4 bg-slate-950 border-t border-slate-800 flex items-center justify-between">
          {!result && quiz && quiz.questions.length > 0 ? (
            <>
              <button
                onClick={() => setCurrentIndex(prev => Math.max(0, prev - 1))}
                disabled={currentIndex === 0}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-300 text-xs font-medium rounded-xl transition-colors flex items-center gap-1.5"
              >
                <ArrowLeft className="w-4 h-4" /> Previous
              </button>

              {currentIndex < quiz.questions.length - 1 ? (
                <button
                  onClick={() => setCurrentIndex(prev => Math.min(quiz.questions.length - 1, prev + 1))}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium rounded-xl transition-colors flex items-center gap-1.5"
                >
                  Next <ArrowRight className="w-4 h-4" />
                </button>
              ) : (
                <button
                  onClick={handleSubmit}
                  disabled={submitting}
                  className="px-5 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs font-semibold rounded-xl shadow-lg shadow-emerald-600/20 transition-colors flex items-center gap-1.5"
                >
                  {submitting ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" /> Evaluating...
                    </>
                  ) : (
                    <>
                      <CheckCircle2 className="w-4 h-4" /> Submit Quiz
                    </>
                  )}
                </button>
              )}
            </>
          ) : (
            <button
              onClick={onClose}
              className="w-full py-2.5 bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold rounded-xl transition-colors"
            >
              Close
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

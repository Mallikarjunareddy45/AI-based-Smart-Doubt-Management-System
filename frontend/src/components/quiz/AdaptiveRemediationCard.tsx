import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Target, AlertTriangle, CheckCircle2, BookOpen, 
  Sparkles, RefreshCw, ArrowRight 
} from 'lucide-react';

interface ConceptPerformance {
  concept_tag: string;
  total_questions: number;
  correct_answers: number;
  accuracy_percentage: number;
}

interface RecommendedLesson {
  lesson_id: string;
  title: string;
  lesson_type: string;
}

interface WeaknessData {
  student_id: string;
  course_id: string;
  total_attempts: number;
  overall_accuracy_percentage: number;
  concept_performance: ConceptPerformance[];
  weak_concepts: string[];
  recommended_lessons: RecommendedLesson[];
}

interface AdaptiveRemediationCardProps {
  courseId: string;
  onStartAdaptiveQuiz: (quizId: string) => void;
  onSelectLesson?: (lessonId: string) => void;
}

export const AdaptiveRemediationCard: React.FC<AdaptiveRemediationCardProps> = ({
  courseId,
  onStartAdaptiveQuiz,
  onSelectLesson
}) => {
  const [data, setData] = useState<WeaknessData | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  const fetchRemediation = async () => {
    try {
      const token = localStorage.getItem('token');
      const backendUrl = import.meta.env.VITE_API_BASE_URL || 'https://ai-doubt-backend.onrender.com';
      const res = await axios.get(`${backendUrl}/api/v1/quizzes/remediation/${courseId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setData(res.data);
    } catch (err) {
      console.error('Failed to fetch remediation analysis:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (courseId) fetchRemediation();
  }, [courseId]);

  const handleCreateAdaptivePractice = async () => {
    if (generating) return;
    setGenerating(true);

    try {
      const token = localStorage.getItem('token');
      const backendUrl = import.meta.env.VITE_API_BASE_URL || 'https://ai-doubt-backend.onrender.com';
      const res = await axios.post(`${backendUrl}/api/v1/quizzes/adaptive-practice/${courseId}`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (res.data?.id) {
        onStartAdaptiveQuiz(res.data.id);
      }
    } catch (err) {
      alert('Failed to generate adaptive practice session.');
    } finally {
      setGenerating(false);
    }
  };

  if (loading) {
    return (
      <div className="p-4 bg-slate-900 border border-slate-800 rounded-2xl animate-pulse text-xs text-slate-400">
        Loading adaptive weakness insights...
      </div>
    );
  }

  if (!data || data.total_attempts === 0) {
    return (
      <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-2xl text-xs text-slate-400 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-indigo-600/20 text-indigo-400 rounded-xl">
            <Target className="w-5 h-5" />
          </div>
          <div>
            <h4 className="font-semibold text-white">Adaptive Remediation Ready</h4>
            <p className="text-slate-400 text-[11px]">Complete course quizzes to unlock personalized AI weakness analysis.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-5 bg-gradient-to-br from-slate-900 via-slate-900 to-indigo-950/40 border border-slate-800 rounded-2xl shadow-xl space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 bg-indigo-600/20 border border-indigo-500/30 text-indigo-400 rounded-xl">
            <Target className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-1.5">
              Adaptive Weakness Analytics
              <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            </h3>
            <p className="text-[11px] text-slate-400">Based on {data.total_attempts} quiz attempts</p>
          </div>
        </div>

        <button
          onClick={handleCreateAdaptivePractice}
          disabled={generating}
          className="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-semibold rounded-xl shadow-lg shadow-indigo-600/20 transition-all border border-indigo-400/30 flex items-center gap-1.5"
        >
          {generating ? (
            <>
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              <span>Generating AI Quiz...</span>
            </>
          ) : (
            <>
              <Sparkles className="w-3.5 h-3.5" />
              <span>Start Adaptive AI Practice</span>
            </>
          )}
        </button>
      </div>

      {/* Accuracy Bar */}
      <div className="p-3 bg-slate-950/70 border border-slate-800/80 rounded-xl space-y-1.5">
        <div className="flex justify-between text-xs font-medium">
          <span className="text-slate-300">Overall Accuracy</span>
          <span className={data.overall_accuracy_percentage >= 70 ? 'text-emerald-400' : 'text-amber-400'}>
            {data.overall_accuracy_percentage}%
          </span>
        </div>
        <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${
              data.overall_accuracy_percentage >= 70 ? 'bg-emerald-500' : 'bg-amber-500'
            }`}
            style={{ width: `${Math.min(100, Math.max(0, data.overall_accuracy_percentage))}%` }}
          />
        </div>
      </div>

      {/* Concept Breakdown & Weaknesses */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
        {/* Concept Performance Badges */}
        <div className="p-3 bg-slate-950/50 border border-slate-800/60 rounded-xl space-y-2">
          <span className="font-semibold text-slate-300 block text-[11px] uppercase tracking-wider">
            Concept Mastery
          </span>
          <div className="space-y-1.5 max-h-32 overflow-y-auto pr-1">
            {data.concept_performance.map((cp, idx) => (
              <div key={idx} className="flex items-center justify-between text-[11px]">
                <span className="text-slate-400 truncate max-w-[150px]">{cp.concept_tag}</span>
                <span className={`px-1.5 py-0.5 rounded font-mono font-medium ${
                  cp.accuracy_percentage >= 70 ? 'bg-emerald-950 text-emerald-400' : 'bg-rose-950 text-rose-400'
                }`}>
                  {cp.accuracy_percentage}%
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Recommended Review Lessons */}
        <div className="p-3 bg-slate-950/50 border border-slate-800/60 rounded-xl space-y-2">
          <span className="font-semibold text-slate-300 block text-[11px] uppercase tracking-wider flex items-center gap-1">
            <BookOpen className="w-3 h-3 text-indigo-400" /> Recommended Review
          </span>
          {data.recommended_lessons.length > 0 ? (
            <div className="space-y-1.5">
              {data.recommended_lessons.map(les => (
                <button
                  key={les.lesson_id}
                  onClick={() => onSelectLesson && onSelectLesson(les.lesson_id)}
                  className="w-full p-2 bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded-lg text-left text-[11px] text-indigo-300 flex items-center justify-between transition-colors"
                >
                  <span className="truncate pr-2">{les.title}</span>
                  <ArrowRight className="w-3 h-3 shrink-0 text-indigo-400" />
                </button>
              ))}
            </div>
          ) : (
            <p className="text-[11px] text-slate-500">No review needed! High accuracy across all concepts.</p>
          )}
        </div>
      </div>
    </div>
  );
};

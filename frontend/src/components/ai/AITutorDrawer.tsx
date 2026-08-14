import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { 
  Bot, X, Send, Sparkles, Clock, AlertTriangle, BookOpen, 
  HelpCircle, ArrowRight, CheckCircle2, RefreshCw 
} from 'lucide-react';

interface Citation {
  lesson_id: string;
  lesson_title: string;
  section_title: string;
  chunk_type: string;
  timestamp_seconds?: number;
  snippet: string;
}

interface Message {
  id: string;
  sender: 'user' | 'ai';
  content: string;
  citations?: Citation[];
  confidence_score?: number;
  can_escalate?: boolean;
  was_escalated?: boolean;
}

interface AITutorDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  courseId: string;
  activeLessonId?: string | null;
  activeLessonTitle?: string | null;
  currentTimestampSeconds?: number | null;
  onJumpToTimestamp?: (seconds: number) => void;
}

export const AITutorDrawer: React.FC<AITutorDrawerProps> = ({
  isOpen,
  onClose,
  courseId,
  activeLessonId,
  activeLessonTitle,
  currentTimestampSeconds,
  onJumpToTimestamp
}) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      sender: 'ai',
      content: "Hello! I am your AI Tutor. Ask me any question about your course materials, notes, or current video lesson!",
      confidence_score: 1.0
    }
  ]);
  const [query, setQuery] = useState('');
  const [useTimestampContext, setUseTimestampContext] = useState(true);
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [escalatingId, setEscalatingId] = useState<string | null>(null);
  const [escalationSuccess, setEscalationSuccess] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
    }
  }, [messages, isOpen]);

  if (!isOpen) return null;

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || loading) return;

    const userPrompt = query.trim();
    setQuery('');

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      sender: 'user',
      content: userPrompt
    };

    setMessages(prev => [...prev, userMsg]);
    setLoading(true);

    try {
      const token = localStorage.getItem('token');
      const backendUrl = import.meta.env.VITE_API_BASE_URL || 'https://ai-doubt-backend.onrender.com';
      
      const payload = {
        course_id: courseId,
        query: userPrompt,
        lesson_id: activeLessonId || null,
        timestamp_seconds: useTimestampContext && currentTimestampSeconds !== null && currentTimestampSeconds !== undefined ? Math.floor(currentTimestampSeconds) : null,
        conversation_id: conversationId
      };

      const res = await axios.post(`${backendUrl}/api/v1/ai-tutor/chat`, payload, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (res.data) {
        if (!conversationId && res.data.conversation_id) {
          setConversationId(res.data.conversation_id);
        }

        const aiMsg: Message = {
          id: res.data.message_id || `ai-${Date.now()}`,
          sender: 'ai',
          content: res.data.answer,
          citations: res.data.citations || [],
          confidence_score: res.data.confidence_score,
          can_escalate: res.data.can_escalate
        };

        setMessages(prev => [...prev, aiMsg]);
      }
    } catch (err) {
      console.error('AI Tutor chat failed:', err);
      setMessages(prev => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          sender: 'ai',
          content: "Sorry, I ran into an issue retrieving course answers. Please try again.",
          confidence_score: 0.0
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleEscalate = async (messageId: string) => {
    setEscalatingId(messageId);
    try {
      const token = localStorage.getItem('token');
      const backendUrl = import.meta.env.VITE_API_BASE_URL || 'https://ai-doubt-backend.onrender.com';

      const res = await axios.post(`${backendUrl}/api/v1/ai-tutor/escalate`, { message_id: messageId }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (res.data) {
        setMessages(prev => prev.map(m => m.id === messageId ? { ...m, was_escalated: true } : m));
        setEscalationSuccess(`Question escalated to instructor! Doubt ID: ${res.data.question_id}`);
        setTimeout(() => setEscalationSuccess(null), 5000);
      }
    } catch (err) {
      console.error('Escalation failed:', err);
      alert('Failed to escalate question to instructor.');
    } finally {
      setEscalatingId(null);
    }
  };

  const formatTimestamp = (secs?: number) => {
    if (secs === undefined || secs === null) return null;
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <div className="fixed inset-y-0 right-0 w-full sm:w-96 bg-slate-900 border-l border-slate-800 shadow-2xl z-50 flex flex-col transition-all duration-300">
      {/* Drawer Header */}
      <div className="p-4 bg-slate-950 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-indigo-600/20 border border-indigo-500/30 rounded-xl text-indigo-400">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-semibold text-white text-sm flex items-center gap-1.5">
              AI Tutor Assistant
              <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            </h3>
            <p className="text-xs text-slate-400">RAG Vector Knowledge Base</p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Context Control Switch */}
      <div className="p-3 bg-slate-900/90 border-b border-slate-800/80 flex items-center justify-between text-xs">
        <div className="flex items-center space-x-2 text-slate-300">
          <Clock className="w-4 h-4 text-indigo-400" />
          <span>Video Timestamp Context</span>
          {currentTimestampSeconds !== null && currentTimestampSeconds !== undefined && (
            <span className="px-1.5 py-0.5 bg-indigo-950 text-indigo-300 border border-indigo-800 font-mono rounded">
              @{formatTimestamp(currentTimestampSeconds)}
            </span>
          )}
        </div>
        <label className="relative inline-flex items-center cursor-pointer">
          <input
            type="checkbox"
            checked={useTimestampContext}
            onChange={e => setUseTimestampContext(e.target.checked)}
            className="sr-only peer"
          />
          <div className="w-8 h-4 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-indigo-600"></div>
        </label>
      </div>

      {/* Escalation Alert Notification */}
      {escalationSuccess && (
        <div className="m-3 p-3 bg-emerald-950/80 border border-emerald-500/40 text-emerald-300 text-xs rounded-xl flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
          <span>{escalationSuccess}</span>
        </div>
      )}

      {/* Messages Body */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map(msg => (
          <div
            key={msg.id}
            className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'}`}
          >
            <div
              className={`max-w-[88%] p-3.5 rounded-2xl text-xs leading-relaxed ${
                msg.sender === 'user'
                  ? 'bg-indigo-600 text-white rounded-br-none shadow-md'
                  : 'bg-slate-800 border border-slate-700/80 text-slate-200 rounded-bl-none shadow-md'
              }`}
            >
              {msg.sender === 'ai' && msg.confidence_score !== undefined && (
                <div className="flex items-center justify-between mb-2 pb-1.5 border-b border-slate-700/60">
                  <span className="text-[10px] font-semibold tracking-wide uppercase text-indigo-400 flex items-center gap-1">
                    <Sparkles className="w-3 h-3" /> Grounded RAG Response
                  </span>
                  <span
                    className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${
                      msg.confidence_score >= 0.75
                        ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                        : msg.confidence_score >= 0.55
                        ? 'bg-amber-950 text-amber-400 border border-amber-800'
                        : 'bg-rose-950 text-rose-400 border border-rose-800'
                    }`}
                  >
                    {Math.round(msg.confidence_score * 100)}% Confidence
                  </span>
                </div>
              )}

              <div className="whitespace-pre-wrap">{msg.content}</div>

              {/* Citations list */}
              {msg.citations && msg.citations.length > 0 && (
                <div className="mt-3 pt-2.5 border-t border-slate-700/60 space-y-1.5">
                  <p className="text-[10px] font-semibold uppercase text-slate-400 flex items-center gap-1">
                    <BookOpen className="w-3 h-3" /> Source Citations ({msg.citations.length})
                  </p>
                  {msg.citations.map((cit, i) => (
                    <div
                      key={i}
                      className="p-2 bg-slate-900/80 border border-slate-800 rounded-lg flex items-start justify-between text-[11px] hover:border-slate-700 transition-colors"
                    >
                      <div className="pr-2">
                        <span className="font-medium text-slate-200 block">{cit.lesson_title}</span>
                        <span className="text-slate-400 text-[10px] block">{cit.section_title}</span>
                      </div>
                      {cit.timestamp_seconds !== undefined && cit.timestamp_seconds !== null && onJumpToTimestamp && (
                        <button
                          onClick={() => onJumpToTimestamp(cit.timestamp_seconds!)}
                          className="px-2 py-1 bg-indigo-950 hover:bg-indigo-900 border border-indigo-700 text-indigo-300 rounded text-[10px] flex items-center gap-1 shrink-0 transition-colors"
                        >
                          <Clock className="w-2.5 h-2.5" />
                          {formatTimestamp(cit.timestamp_seconds)}
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* Low confidence escalation trigger */}
              {msg.can_escalate && !msg.was_escalated && (
                <div className="mt-3 pt-2 border-t border-rose-900/40 flex flex-col space-y-2">
                  <div className="flex items-center gap-1.5 text-amber-400 text-[10px]">
                    <AlertTriangle className="w-3.5 h-3.5" />
                    <span>RAG confidence is low for this query.</span>
                  </div>
                  <button
                    onClick={() => handleEscalate(msg.id)}
                    disabled={escalatingId === msg.id}
                    className="w-full py-1.5 px-3 bg-rose-600/20 hover:bg-rose-600/30 border border-rose-500/40 text-rose-300 rounded-lg text-[11px] font-medium flex items-center justify-center gap-1.5 transition-colors disabled:opacity-50"
                  >
                    {escalatingId === msg.id ? (
                      <>
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                        <span>Escalating to Instructor...</span>
                      </>
                    ) : (
                      <>
                        <HelpCircle className="w-3.5 h-3.5" />
                        <span>Escalate to Instructor as Doubt</span>
                      </>
                    )}
                  </button>
                </div>
              )}

              {msg.was_escalated && (
                <div className="mt-2 text-[10px] text-emerald-400 flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" /> Escalated to course instructor.
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex items-center space-x-2 text-slate-400 text-xs p-2">
            <RefreshCw className="w-4 h-4 animate-spin text-indigo-400" />
            <span>Searching vector knowledge base...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Footer */}
      <form onSubmit={handleSend} className="p-3 bg-slate-950 border-t border-slate-800">
        <div className="relative flex items-center">
          <input
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder={
              useTimestampContext && currentTimestampSeconds !== null && currentTimestampSeconds !== undefined
                ? `Ask AI about video @ ${formatTimestamp(currentTimestampSeconds)}...`
                : "Ask AI Tutor about course content..."
            }
            className="w-full pl-3 pr-10 py-2.5 bg-slate-900 border border-slate-800 focus:border-indigo-500 rounded-xl text-xs text-slate-200 placeholder-slate-500 focus:outline-none transition-colors"
          />
          <button
            type="submit"
            disabled={!query.trim() || loading}
            className="absolute right-1.5 p-1.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white rounded-lg transition-colors"
          >
            <Send className="w-3.5 h-3.5" />
          </button>
        </div>
      </form>
    </div>
  );
};

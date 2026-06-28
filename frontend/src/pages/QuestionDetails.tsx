import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { useSocket } from '../context/SocketContext';
import { useAuth } from '../context/AuthContext';
import { Question, ChatMessage } from '../types';
import { motion } from 'framer-motion';
import { ArrowLeft, Send, MessageCircle, AlertCircle, CheckCircle } from 'lucide-react';

export const QuestionDetails: React.FC = () => {
  const { questionId } = useParams<{ questionId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { isConnected, sendMessage, registerListener } = useSocket();

  const [question, setQuestion] = useState<Question | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [typedMessage, setTypedMessage] = useState('');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  
  const chatBottomRef = useRef<HTMLDivElement | null>(null);

  // Auto scroll chat to bottom when new messages arrive
  const scrollToBottom = () => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    const fetchDetails = async () => {
      try {
        setIsLoading(true);
        // 1. Fetch doubt details
        const questionRes = await api.get<Question>(`/questions/${questionId}`);
        setQuestion(questionRes.data);
        
        // 2. Fetch chat history if mapped to a cluster
        if (questionRes.data.cluster_id) {
          const msgsRes = await api.get<ChatMessage[]>(
            `/questions/clusters/${questionRes.data.cluster_id}/messages`
          );
          setMessages(msgsRes.data);
        }
      } catch (err) {
        setError('Failed to load doubt details');
      } finally {
        setIsLoading(false);
      }
    };
    fetchDetails();
  }, [questionId]);

  useEffect(() => {
    if (!question || !question.cluster_id) return;

    // Join WebSocket cluster room
    sendMessage('join_room', { cluster_id: question.cluster_id });
    scrollToBottom();

    // Listen for real-time messages
    const unsubscribe = registerListener('new_message', (data) => {
      if (data.message.cluster_id === question.cluster_id) {
        setMessages((prev) => {
          // Check if message is already in list (prevent duplicate inserts)
          if (prev.some((m) => m.id === data.message.id)) return prev;
          return [...prev, data.message];
        });
      }
    });

    const unsubscribe2 = registerListener('cluster_resolved', (data) => {
      if (data.cluster_id === question.cluster_id) {
        setQuestion(prev => prev ? { ...prev, status: 'resolved' } : null);
      }
    });

    return () => {
      // Leave room on cleanup
      sendMessage('leave_room', { cluster_id: question.cluster_id });
      unsubscribe();
      unsubscribe2();
    };
  }, [question, sendMessage, registerListener]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!typedMessage.trim() || !question || !question.cluster_id) return;

    const messageText = typedMessage;
    setTypedMessage('');

    try {
      // Post message. Backend will save to database and broadcast to WS room.
      await api.post(`/questions/clusters/${question.cluster_id}/messages`, {
        content: messageText
      });
    } catch (err) {
      console.error('Failed to dispatch message');
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand-500 border-t-transparent" />
      </div>
    );
  }

  if (!question) {
    return (
      <div className="max-w-2xl mx-auto py-8 text-center text-slate-400">
        Question details could not be found.
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto py-4 flex flex-col gap-6 h-[calc(100vh-8rem)] page-transit">
      
      {/* Back Header */}
      <div className="flex items-center justify-between shrink-0">
        <button 
          onClick={() => navigate(-1)} 
          className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-700 font-semibold transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Dashboard
        </button>

        <span className={`px-2.5 py-1 rounded-full text-xs font-bold border uppercase ${
          question.status === 'resolved' 
            ? 'bg-emerald-50 text-emerald-600 border-emerald-200/50' 
            : 'bg-indigo-50 text-indigo-600 border-indigo-200/50'
        }`}>
          Status: {question.status}
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1 overflow-hidden">
        
        {/* Left Side: Question Summary details */}
        <div className="lg:col-span-1 bg-white rounded-3xl border border-slate-200/60 p-6 flex flex-col gap-4 overflow-y-auto shadow-sm">
          <div>
            <span className="text-[10px] text-brand-600 font-bold uppercase tracking-wider">Student Doubt</span>
            <h3 className="text-base font-bold text-slate-800 leading-snug mt-1">{question.title}</h3>
          </div>

          <div className="border-t border-slate-100 pt-4 flex flex-col gap-3">
            <h4 className="text-xs font-bold text-slate-400 uppercase">Description</h4>
            <p className="text-xs text-slate-500 leading-relaxed bg-slate-50/50 p-4 rounded-2xl border border-slate-100">
              {question.content}
            </p>
          </div>

          {/* Student Details (Tutor/Admin Only) */}
          {(user?.roles.map(r => r.name).includes('tutor') || user?.roles.map(r => r.name).includes('admin')) && (
            <div className="border-t border-slate-100 pt-4 flex flex-col gap-2">
              <h4 className="text-xs font-bold text-slate-400 uppercase">Student Details</h4>
              <div className="text-xs text-slate-600 flex flex-col gap-1 bg-slate-50 p-3 rounded-xl border border-slate-100">
                <span className="font-semibold text-slate-800">{question.student_name || 'Anonymous Student'}</span>
                <span className="text-slate-500">{question.student_email}</span>
              </div>
            </div>
          )}

          <div className="border-t border-slate-100 pt-4 mt-auto text-[10px] text-slate-400 flex flex-col gap-1.5">
            <span>Posted {new Date(question.created_at).toLocaleString()}</span>
            {question.priority_score > 0 && (
              <span>AI Priority Score: {question.priority_score.toFixed(1)}</span>
            )}
          </div>
        </div>

        {/* Right Side: Chat message thread */}
        <div className="lg:col-span-2 bg-white rounded-3xl border border-slate-200/60 flex flex-col overflow-hidden shadow-sm">
          
          {/* Thread Header */}
          <div className="p-4 border-b border-slate-100 bg-slate-50/20 flex items-center gap-2">
            <MessageCircle className="h-4.5 w-4.5 text-slate-400" />
            <h4 className="text-xs font-bold text-slate-700 uppercase">Clustered Discussion Thread</h4>
          </div>

          {/* Messages stream */}
          <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-4">
            {!question.cluster_id ? (
              <div className="flex flex-col items-center justify-center h-full text-center p-6 gap-2">
                <AlertCircle className="h-8 w-8 text-amber-500 animate-pulse" />
                <h5 className="font-semibold text-slate-800 text-sm">Processing Doubt</h5>
                <p className="text-xs text-slate-400 max-w-xs leading-relaxed">
                  Our background AI engine is currently generating vector embeddings to check for duplicates and assign a course tutor. Real-time sync will refresh shortly.
                </p>
              </div>
            ) : messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-slate-400 text-xs gap-1.5">
                <span>Doubt assigned to tutor.</span>
                <span>Type a message below to start the thread.</span>
              </div>
            ) : (
              messages.map((msg) => {
                const isMe = msg.sender_id === user?.id;
                return (
                  <div 
                    key={msg.id}
                    className={`flex flex-col max-w-[80%] ${isMe ? 'self-end items-end' : 'self-start items-start'}`}
                  >
                    <span className="text-[9px] text-slate-400 font-semibold mb-1 px-1">
                      {isMe ? 'You' : msg.sender_name || 'Course Assistant'}
                    </span>
                    <div 
                      className={`p-3.5 rounded-2xl text-xs leading-relaxed ${
                        isMe 
                          ? 'bg-brand-600 text-white rounded-tr-none shadow-md shadow-brand-600/10' 
                          : 'bg-slate-100 text-slate-800 rounded-tl-none'
                      }`}
                    >
                      {msg.content}
                    </div>
                    <span className="text-[8px] text-slate-400 mt-1 px-1">
                      {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                );
              })
            )}
            <div ref={chatBottomRef} />
          </div>

          {/* Chat message input */}
          {question.cluster_id && question.status !== 'resolved' && (
            <form onSubmit={handleSend} className="p-4 border-t border-slate-100 flex items-center gap-3">
              <input
                type="text"
                value={typedMessage}
                onChange={(e) => setTypedMessage(e.target.value)}
                placeholder="Type your reply..."
                className="flex-1 px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 text-xs bg-slate-50/50"
              />
              <button
                type="submit"
                className="h-10 w-10 rounded-xl bg-brand-600 hover:bg-brand-500 text-white flex items-center justify-center shrink-0 shadow-lg shadow-brand-600/15 transition-all active:scale-95"
              >
                <Send className="h-4 w-4" />
              </button>
            </form>
          )}

          {question.status === 'resolved' && (
            <div className="p-4 border-t border-slate-100 bg-emerald-50/30 text-emerald-700 text-xs flex items-center justify-center gap-2 font-semibold">
              <CheckCircle className="h-4 w-4 text-emerald-600" />
              This doubt has been marked as resolved.
            </div>
          )}
        </div>

      </div>
    </div>
  );
};
export default QuestionDetails;

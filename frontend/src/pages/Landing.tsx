import React from 'react';
import { Link } from 'react-router-dom';
import { GraduationCap, ArrowRight, HelpCircle, Layers, ShieldCheck, Zap } from 'lucide-react';

export const Landing: React.FC = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-950 text-white flex flex-col justify-between">
      {/* Header navbar branding */}
      <header className="max-w-7xl mx-auto w-full px-8 py-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-brand-500 to-indigo-500 flex items-center justify-center text-white shadow-md shadow-brand-500/20">
            <GraduationCap className="h-6 w-6" />
          </div>
          <div>
            <h1 className="font-semibold text-white leading-tight text-lg">DoubtAssist</h1>
            <span className="text-[10px] text-brand-400 font-semibold tracking-wider uppercase block -mt-0.5">AI Doubt Router</span>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <Link to="/login" className="text-slate-300 hover:text-white text-sm font-semibold transition-colors">
            Sign In
          </Link>
          <Link 
            to="/register" 
            className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-sm font-semibold shadow-lg shadow-brand-600/20 transition-all hover:-translate-y-0.5"
          >
            Sign Up
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <main className="max-w-5xl mx-auto w-full px-8 py-16 flex flex-col items-center text-center gap-8">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-semibold animate-pulse-subtle">
          <Zap className="h-3 w-3" />
          Powered by Sentence Transformers & pgvector
        </div>

        <h2 className="text-5xl md:text-6xl font-extrabold tracking-tight max-w-3xl leading-[1.1] font-sans">
          Route Course Doubts to the <span className="bg-clip-text text-transparent bg-gradient-to-r from-brand-400 via-indigo-400 to-violet-400">Right Tutor, Instantly</span>
        </h2>

        <p className="text-slate-400 max-w-xl text-base md:text-lg leading-relaxed">
          Automate student doubt management at scale. Group identical concerns dynamically, predict blocker urgency, and balance workloads among university course assistants.
        </p>

        <div className="flex flex-wrap items-center justify-center gap-4 mt-4">
          <Link 
            to="/login"
            className="px-6 py-3.5 rounded-xl bg-white text-slate-900 font-bold text-sm shadow-xl hover:bg-slate-100 transition-all flex items-center gap-2 group hover:-translate-y-0.5"
          >
            Access Workspace
            <ArrowRight className="h-4 w-4 group-hover:translate-x-1 transition-transform text-slate-900" />
          </Link>
          <Link 
            to="/register"
            className="px-6 py-3.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-semibold text-sm transition-all border border-slate-700/55 hover:-translate-y-0.5"
          >
            Create Student Profile
          </Link>
        </div>

        {/* Feature Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full mt-20">
          <div className="p-6 rounded-2xl bg-white/[0.03] border border-white/[0.06] text-left flex flex-col gap-3">
            <div className="h-10 w-10 rounded-lg bg-indigo-500/10 flex items-center justify-center text-indigo-400">
              <Layers className="h-5 w-5" />
            </div>
            <h3 className="font-semibold text-white">Semantic Clustering</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Detect duplicate questions and group related doubts using deep NLP sentence embeddings. Tutors resolve entire clusters with single answers.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-white/[0.03] border border-white/[0.06] text-left flex flex-col gap-3">
            <div className="h-10 w-10 rounded-lg bg-emerald-500/10 flex items-center justify-center text-emerald-400">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <h3 className="font-semibold text-white">Load-Balanced Routing</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Automatically assign doubts to tutors with the lowest active workload within the department, ensuring fast queue response times.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-white/[0.03] border border-white/[0.06] text-left flex flex-col gap-3">
            <div className="h-10 w-10 rounded-lg bg-rose-500/10 flex items-center justify-center text-rose-400">
              <HelpCircle className="h-5 w-5" />
            </div>
            <h3 className="font-semibold text-white">Urgency Prediction</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Scan doubt queries for system error blockers and time-sensitive keywords to push critical bugs to the top of the resolving queue.
            </p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="max-w-7xl mx-auto w-full px-8 py-6 text-center border-t border-white/[0.05] text-xs text-slate-500">
        &copy; {new Date().getFullYear()} DoubtAssist Platform. Built for large online university courses.
      </footer>
    </div>
  );
};
export default Landing;

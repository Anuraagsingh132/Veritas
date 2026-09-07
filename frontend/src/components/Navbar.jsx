import React from 'react';
import { 
  Layers, 
  Sparkles, 
  Search, 
  GitCompare, 
  FileText, 
  Key, 
  RotateCcw 
} from 'lucide-react';

export default function Navbar({ 
  activeTab, 
  setActiveTab, 
  stats, 
  status, 
  onOpenKeyModal, 
  onReseed 
}) {
  return (
    <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          
          {/* Logo / Brand */}
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setActiveTab('showcase')}>
            <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <Layers className="h-5 w-5 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-lg bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
                  Superjoin
                </span>
                <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-500/20 border border-indigo-500/40 text-indigo-300 font-medium">
                  Fact Knowledge Layer
                </span>
              </div>
              <p className="text-xs text-slate-400">VIT 2026 Engineering Assignment</p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="hidden md:flex space-x-1">
            <button
              onClick={() => setActiveTab('showcase')}
              className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'showcase'
                  ? 'bg-indigo-600/20 border border-indigo-500 text-indigo-300 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <Sparkles className="h-4 w-4 text-amber-400" />
              <span>4 Required Cases</span>
              <span className="ml-1 px-1.5 py-0.2 text-[10px] rounded bg-amber-500/20 text-amber-300 font-bold">
                EVAL
              </span>
            </button>

            <button
              onClick={() => setActiveTab('facts')}
              className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'facts'
                  ? 'bg-indigo-600/20 border border-indigo-500 text-indigo-300 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <Search className="h-4 w-4" />
              <span>Fact Explorer</span>
              {stats?.total_facts ? (
                <span className="ml-1 px-1.5 py-0.5 text-xs rounded-full bg-slate-800 text-slate-400">
                  {stats.total_facts}
                </span>
              ) : null}
            </button>

            <button
              onClick={() => setActiveTab('reconciliation')}
              className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'reconciliation'
                  ? 'bg-indigo-600/20 border border-indigo-500 text-indigo-300 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <GitCompare className="h-4 w-4" />
              <span>Cross-Doc Reconciliation</span>
              {stats?.total_relationships ? (
                <span className="ml-1 px-1.5 py-0.5 text-xs rounded-full bg-slate-800 text-slate-400">
                  {stats.total_relationships}
                </span>
              ) : null}
            </button>

            <button
              onClick={() => setActiveTab('documents')}
              className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'documents'
                  ? 'bg-indigo-600/20 border border-indigo-500 text-indigo-300 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <FileText className="h-4 w-4" />
              <span>PDFs & Ingestion</span>
              {stats?.total_documents ? (
                <span className="ml-1 px-1.5 py-0.5 text-xs rounded-full bg-slate-800 text-slate-400">
                  {stats.total_documents}
                </span>
              ) : null}
            </button>
          </nav>

          {/* Controls & API Key */}
          <div className="flex items-center space-x-3">
            <button
              onClick={onReseed}
              title="Reset to Ground Truth Starter Data"
              className="p-2 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
            >
              <RotateCcw className="h-4 w-4" />
            </button>

            <button
              onClick={onOpenKeyModal}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition ${
                status?.llm_available
                  ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                  : 'bg-amber-500/10 border-amber-500/30 text-amber-300'
              }`}
            >
              <Key className="h-3.5 w-3.5" />
              <span>{status?.llm_available ? 'Groq Active' : 'Configure LLM'}</span>
            </button>

            <div className="flex items-center space-x-1.5 pl-2 border-l border-slate-800 text-xs text-slate-400">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span className="hidden sm:inline">Engine Online</span>
            </div>
          </div>

        </div>
      </div>
    </header>
  );
}

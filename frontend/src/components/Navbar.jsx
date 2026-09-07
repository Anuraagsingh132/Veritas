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
    <header className="sticky top-0 z-40 border-b border-slate-800/80 bg-slate-950/85 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          
          {/* Logo / Brand Identity */}
          <button
            onClick={() => setActiveTab('showcase')}
            className="flex items-center space-x-3 text-left group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 rounded-xl p-1 -m-1 transition-all"
          >
            <div className="h-9 w-9 rounded-xl bg-slate-900 border border-slate-700/80 flex items-center justify-center text-indigo-400 group-hover:border-indigo-500/60 group-hover:text-indigo-300 transition-colors shadow-sm">
              <Layers className="h-4.5 w-4.5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-semibold text-base text-slate-100 group-hover:text-white transition-colors tracking-tight">
                  Superjoin
                </span>
                <span className="text-[11px] px-2 py-0.5 rounded-full bg-slate-800/80 border border-slate-700/70 text-slate-300 font-medium tracking-wide">
                  Fact Knowledge Layer
                </span>
              </div>
              <p className="text-[11px] text-slate-400 hidden sm:block">
                Epistemological Ground-Truth Engine
              </p>
            </div>
          </button>

          {/* Navigation Tabs */}
          <nav className="hidden md:flex items-center space-x-1" aria-label="Main Navigation">
            
            {/* Showcase Tab */}
            <button
              onClick={() => setActiveTab('showcase')}
              className={`flex items-center space-x-2 px-3 py-2 rounded-xl text-xs font-medium transition-colors ${
                activeTab === 'showcase'
                  ? 'bg-slate-800 text-slate-100 border border-slate-700 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
              }`}
            >
              <Sparkles className={`h-3.5 w-3.5 ${activeTab === 'showcase' ? 'text-amber-400' : 'text-slate-500'}`} />
              <span>4 Required Cases</span>
              <span className="px-1.5 py-0.2 text-[9px] rounded font-bold uppercase tracking-wider bg-amber-500/15 text-amber-300 border border-amber-500/30">
                EVAL
              </span>
            </button>

            {/* Fact Explorer Tab */}
            <button
              onClick={() => setActiveTab('facts')}
              className={`flex items-center space-x-2 px-3 py-2 rounded-xl text-xs font-medium transition-colors ${
                activeTab === 'facts'
                  ? 'bg-slate-800 text-slate-100 border border-slate-700 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
              }`}
            >
              <Search className={`h-3.5 w-3.5 ${activeTab === 'facts' ? 'text-indigo-400' : 'text-slate-500'}`} />
              <span>Fact Explorer</span>
              {stats?.total_facts !== undefined && (
                <span className="px-1.5 py-0.5 text-[10px] rounded-md bg-slate-900 text-slate-300 font-mono tabular-nums border border-slate-800">
                  {stats.total_facts}
                </span>
              )}
            </button>

            {/* Cross-Doc Reconciliation Tab */}
            <button
              onClick={() => setActiveTab('reconciliation')}
              className={`flex items-center space-x-2 px-3 py-2 rounded-xl text-xs font-medium transition-colors ${
                activeTab === 'reconciliation'
                  ? 'bg-slate-800 text-slate-100 border border-slate-700 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
              }`}
            >
              <GitCompare className={`h-3.5 w-3.5 ${activeTab === 'reconciliation' ? 'text-indigo-400' : 'text-slate-500'}`} />
              <span>Reconciliation Matrix</span>
              {stats?.total_relationships !== undefined && (
                <span className="px-1.5 py-0.5 text-[10px] rounded-md bg-slate-900 text-slate-300 font-mono tabular-nums border border-slate-800">
                  {stats.total_relationships}
                </span>
              )}
            </button>

            {/* PDFs & Ingestion Tab */}
            <button
              onClick={() => setActiveTab('documents')}
              className={`flex items-center space-x-2 px-3 py-2 rounded-xl text-xs font-medium transition-colors ${
                activeTab === 'documents'
                  ? 'bg-slate-800 text-slate-100 border border-slate-700 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
              }`}
            >
              <FileText className={`h-3.5 w-3.5 ${activeTab === 'documents' ? 'text-indigo-400' : 'text-slate-500'}`} />
              <span>PDF Documents</span>
              {stats?.total_documents !== undefined && (
                <span className="px-1.5 py-0.5 text-[10px] rounded-md bg-slate-900 text-slate-300 font-mono tabular-nums border border-slate-800">
                  {stats.total_documents}
                </span>
              )}
            </button>
          </nav>

          {/* Action Controls */}
          <div className="flex items-center space-x-2.5">
            
            {/* Reset / Reseed Button */}
            <button
              onClick={onReseed}
              aria-label="Reset knowledge layer to ground-truth starter dataset"
              title="Reset knowledge layer to ground-truth starter dataset"
              className="p-2 rounded-xl text-slate-400 hover:text-slate-200 hover:bg-slate-900 border border-transparent hover:border-slate-800 transition-colors focus-visible:ring-2 focus-visible:ring-indigo-500"
            >
              <RotateCcw className="h-4 w-4" />
            </button>

            {/* API Key Modal Trigger */}
            <button
              onClick={onOpenKeyModal}
              aria-label="Configure Groq LLM API Key"
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-medium border transition-colors focus-visible:ring-2 focus-visible:ring-indigo-500 ${
                status?.llm_available
                  ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/15'
                  : 'bg-amber-500/10 border-amber-500/30 text-amber-300 hover:bg-amber-500/15'
              }`}
            >
              <Key className="h-3.5 w-3.5" />
              <span>{status?.llm_available ? 'Groq Active' : 'Configure LLM'}</span>
            </button>

            {/* System Status Indicator */}
            <div className="hidden lg:flex items-center space-x-1.5 pl-2.5 border-l border-slate-800/80 text-xs text-slate-400">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              <span className="text-[11px] font-medium text-slate-300">Engine Online</span>
            </div>

          </div>

        </div>

        {/* Mobile Navigation Row */}
        <div className="md:hidden flex space-x-1 py-2 overflow-x-auto border-t border-slate-800/60 scrollbar-none">
          <button
            onClick={() => setActiveTab('showcase')}
            className={`px-2.5 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap ${
              activeTab === 'showcase' ? 'bg-slate-800 text-white' : 'text-slate-400'
            }`}
          >
            4 Cases
          </button>
          <button
            onClick={() => setActiveTab('facts')}
            className={`px-2.5 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap ${
              activeTab === 'facts' ? 'bg-slate-800 text-white' : 'text-slate-400'
            }`}
          >
            Fact Explorer ({stats?.total_facts || 0})
          </button>
          <button
            onClick={() => setActiveTab('reconciliation')}
            className={`px-2.5 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap ${
              activeTab === 'reconciliation' ? 'bg-slate-800 text-white' : 'text-slate-400'
            }`}
          >
            Reconciliation ({stats?.total_relationships || 0})
          </button>
          <button
            onClick={() => setActiveTab('documents')}
            className={`px-2.5 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap ${
              activeTab === 'documents' ? 'bg-slate-800 text-white' : 'text-slate-400'
            }`}
          >
            PDFs ({stats?.total_documents || 0})
          </button>
        </div>

      </div>
    </header>
  );
}

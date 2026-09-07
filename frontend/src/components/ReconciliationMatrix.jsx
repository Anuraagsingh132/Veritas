import React, { useState } from 'react';
import { 
  GitCompare, 
  CheckCircle2, 
  AlertTriangle, 
  Clock, 
  RefreshCw 
} from 'lucide-react';

export default function ReconciliationMatrix({ relationships, loading, onTriggerReconciliation }) {
  const [filterType, setFilterType] = useState('all');
  const [reconciling, setReconciling] = useState(false);

  const filterOptions = [
    { id: 'all', label: 'All Relationships' },
    { id: 'corroboration', label: 'Corroborations' },
    { id: 'genuine_contradiction', label: 'Genuine Contradictions' },
    { id: 'contextual_reconciliation', label: 'Contextual Reconciliations' },
  ];

  const filtered = relationships.filter(r => {
    if (filterType === 'all') return true;
    return r.relationship_type === filterType;
  });

  const handleRunReconcile = async () => {
    setReconciling(true);
    try {
      await onTriggerReconciliation();
    } finally {
      setReconciling(false);
    }
  };

  const getTypeBadge = (type) => {
    switch (type) {
      case 'corroboration':
        return {
          label: 'Corroboration',
          color: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400',
          icon: <CheckCircle2 className="h-4 w-4 text-emerald-400" />
        };
      case 'genuine_contradiction':
        return {
          label: 'Genuine Contradiction',
          color: 'bg-rose-500/10 border-rose-500/30 text-rose-400',
          icon: <AlertTriangle className="h-4 w-4 text-rose-400" />
        };
      case 'contextual_reconciliation':
      default:
        return {
          label: 'Contextual Reconciliation',
          color: 'bg-amber-500/10 border-amber-500/30 text-amber-400',
          icon: <Clock className="h-4 w-4 text-amber-400" />
        };
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      
      {/* Top Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex flex-wrap gap-2">
          {filterOptions.map(opt => (
            <button
              key={opt.id}
              onClick={() => setFilterType(opt.id)}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition ${
                filterType === opt.id
                  ? 'bg-indigo-600 text-white shadow'
                  : 'bg-slate-800/80 text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>

        <div className="flex items-center space-x-3">
          <span className="text-xs text-slate-400">
            {filtered.length} relationships
          </span>
          <button
            onClick={handleRunReconcile}
            disabled={reconciling}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium shadow transition disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${reconciling ? 'animate-spin' : ''}`} />
            <span>{reconciling ? 'Reconciling...' : 'Run Global Reconciliation'}</span>
          </button>
        </div>
      </div>

      {/* Relationships List */}
      {loading ? (
        <div className="flex justify-center py-20 text-slate-400">
          <div className="animate-spin h-8 w-8 border-2 border-indigo-500 border-t-transparent rounded-full mr-3"></div>
          <span>Comparing Cross-Document Facts...</span>
        </div>
      ) : filtered.length === 0 ? (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center text-slate-400">
          <GitCompare className="h-8 w-8 mx-auto mb-3 text-slate-600" />
          <p className="text-sm font-medium">No cross-document relationships match this filter.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filtered.map(rel => {
            const badge = getTypeBadge(rel.relationship_type);

            return (
              <div
                key={rel.id}
                className="bg-slate-900/90 border border-slate-800 hover:border-slate-700 rounded-2xl p-5 shadow-sm transition space-y-4"
              >
                {/* Header status */}
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/80 pb-3">
                  <span className={`flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-medium border ${badge.color}`}>
                    {badge.icon}
                    <span>{badge.label}</span>
                  </span>

                  {rel.context_difference && (
                    <span className="text-[11px] px-2.5 py-0.5 rounded-full bg-slate-800 text-indigo-300 border border-slate-700 font-mono">
                      Context Dimension: {rel.context_difference}
                    </span>
                  )}
                </div>

                {/* Side-by-side Facts */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Fact 1 */}
                  <div className="bg-slate-950/80 border border-slate-800/80 rounded-xl p-3.5 space-y-2">
                    <div className="flex items-center justify-between text-xs text-slate-400">
                      <span className="text-indigo-300 font-medium truncate max-w-[200px]" title={rel.fact_1.document_filename}>
                        {rel.fact_1.document_filename}
                      </span>
                      <span className="font-mono bg-slate-800 px-1.5 py-0.5 rounded text-[10px]">
                        p.{rel.fact_1.page_number}
                      </span>
                    </div>

                    <div className="text-xs font-semibold text-slate-200">
                      {rel.fact_1.subject}
                    </div>

                    <div className="flex items-baseline space-x-2">
                      <span className="text-lg font-bold text-white">
                        {rel.fact_1.value}
                      </span>
                      <span className="text-xs text-slate-400 font-medium">
                        {rel.fact_1.unit}
                      </span>
                      {rel.fact_1.temporal_context && (
                        <span className="text-[10px] text-indigo-300 bg-indigo-950/60 px-1.5 py-0.5 rounded">
                          {rel.fact_1.temporal_context}
                        </span>
                      )}
                    </div>

                    <div className="text-xs text-slate-400 italic bg-slate-900/80 p-2 rounded border border-slate-800/60">
                      "{rel.fact_1.exact_quote}"
                    </div>
                  </div>

                  {/* Fact 2 */}
                  <div className="bg-slate-950/80 border border-slate-800/80 rounded-xl p-3.5 space-y-2">
                    <div className="flex items-center justify-between text-xs text-slate-400">
                      <span className="text-purple-300 font-medium truncate max-w-[200px]" title={rel.fact_2.document_filename}>
                        {rel.fact_2.document_filename}
                      </span>
                      <span className="font-mono bg-slate-800 px-1.5 py-0.5 rounded text-[10px]">
                        p.{rel.fact_2.page_number}
                      </span>
                    </div>

                    <div className="text-xs font-semibold text-slate-200">
                      {rel.fact_2.subject}
                    </div>

                    <div className="flex items-baseline space-x-2">
                      <span className="text-lg font-bold text-white">
                        {rel.fact_2.value}
                      </span>
                      <span className="text-xs text-slate-400 font-medium">
                        {rel.fact_2.unit}
                      </span>
                      {rel.fact_2.temporal_context && (
                        <span className="text-[10px] text-purple-300 bg-purple-950/60 px-1.5 py-0.5 rounded">
                          {rel.fact_2.temporal_context}
                        </span>
                      )}
                    </div>

                    <div className="text-xs text-slate-400 italic bg-slate-900/80 p-2 rounded border border-slate-800/60">
                      "{rel.fact_2.exact_quote}"
                    </div>
                  </div>
                </div>

                {/* Reasoning Box */}
                <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 text-xs text-slate-300 leading-relaxed">
                  <span className="font-semibold text-indigo-400 mr-1.5">Reasoning:</span>
                  {rel.reasoning}
                </div>

              </div>
            );
          })}
        </div>
      )}

    </div>
  );
}

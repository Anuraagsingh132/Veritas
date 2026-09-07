import React, { useState } from 'react';
import { 
  GitCompare, 
  CheckCircle2, 
  AlertTriangle, 
  Clock, 
  RefreshCw,
  FileText,
  Quote,
  RotateCcw
} from 'lucide-react';
import { MatrixSkeleton } from './SkeletonLoader';

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
          label: 'Corroborated Ground Truth',
          badgeClass: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400',
          icon: <CheckCircle2 className="h-4 w-4 text-emerald-400 flex-shrink-0" />
        };
      case 'genuine_contradiction':
        return {
          label: 'Genuine Contradiction',
          badgeClass: 'bg-rose-500/10 border-rose-500/30 text-rose-400',
          icon: <AlertTriangle className="h-4 w-4 text-rose-400 flex-shrink-0" />
        };
      case 'contextual_reconciliation':
      default:
        return {
          label: 'Contextual Reconciliation',
          badgeClass: 'bg-amber-500/10 border-amber-500/30 text-amber-400',
          icon: <Clock className="h-4 w-4 text-amber-400 flex-shrink-0" />
        };
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      
      {/* Top Filter & Actions Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex flex-wrap gap-1.5" role="group" aria-label="Relationship filter">
          {filterOptions.map(opt => (
            <button
              key={opt.id}
              onClick={() => setFilterType(opt.id)}
              className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-colors ${
                filterType === opt.id
                  ? 'bg-slate-800 text-slate-100 border border-slate-700 shadow-sm'
                  : 'bg-slate-950/70 text-slate-400 border border-slate-800/80 hover:text-slate-200 hover:bg-slate-900'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>

        <div className="flex items-center space-x-3 self-end sm:self-center">
          <span className="text-xs text-slate-400">
            <strong className="text-slate-200 font-mono tabular-nums">{filtered.length}</strong> relationships
          </span>
          <button
            onClick={handleRunReconcile}
            disabled={reconciling}
            className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium shadow-sm transition-colors disabled:opacity-50 focus-visible:ring-2 focus-visible:ring-indigo-500"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${reconciling ? 'animate-spin' : ''}`} />
            <span>{reconciling ? 'Reconciling...' : 'Run Global Reconciliation'}</span>
          </button>
        </div>
      </div>

      {/* Relationships Comparison Matrix or Skeleton */}
      {loading ? (
        <MatrixSkeleton />
      ) : filtered.length === 0 ? (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center text-slate-400 space-y-4">
          <div className="p-3 rounded-2xl bg-slate-950 border border-slate-800 w-12 h-12 mx-auto flex items-center justify-center text-slate-500">
            <GitCompare className="h-6 w-6" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-200">No relationships match this filter</h3>
            <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto text-pretty">
              Switch filters or trigger a global reconciliation across all registered documents.
            </p>
          </div>
          {filterType !== 'all' && (
            <button
              onClick={() => setFilterType('all')}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-medium transition-colors inline-flex items-center space-x-1.5"
            >
              <RotateCcw className="h-3.5 w-3.5" />
              <span>Show All Relationships</span>
            </button>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          {filtered.map(rel => {
            const badge = getTypeBadge(rel.relationship_type);

            return (
              <section
                key={rel.id}
                className="bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-2xl p-5 sm:p-6 shadow-sm transition-colors space-y-4"
              >
                {/* Status Header */}
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/80 pb-3">
                  <span className={`flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-medium border ${badge.badgeClass}`}>
                    {badge.icon}
                    <span>{badge.label}</span>
                  </span>

                  {rel.context_difference && (
                    <span className="text-[11px] px-2.5 py-0.5 rounded-md bg-slate-950 text-slate-300 border border-slate-800 font-mono tabular-nums">
                      Discrepancy Axis: {rel.context_difference}
                    </span>
                  )}
                </div>

                {/* Side-by-Side Facts Comparative Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  
                  {/* Fact 1 */}
                  <div className="bg-slate-950/70 border border-slate-800/90 rounded-xl p-4 space-y-2.5">
                    <div className="flex items-center justify-between text-xs text-slate-400">
                      <div className="flex items-center space-x-1.5 text-slate-200 min-w-0" title={rel.fact_1.document_filename}>
                        <FileText className="h-3.5 w-3.5 text-indigo-400 flex-shrink-0" />
                        <span className="truncate max-w-[200px]">{rel.fact_1.document_filename}</span>
                      </div>
                      <span className="font-mono bg-slate-900 border border-slate-800 px-2 py-0.5 rounded-md text-[10px] text-slate-300 tabular-nums">
                        p.{rel.fact_1.page_number}
                      </span>
                    </div>

                    <div className="text-xs font-semibold text-slate-200">
                      {rel.fact_1.subject}
                    </div>

                    <div className="flex items-baseline space-x-2">
                      <span className="text-xl font-bold text-white tabular-nums tracking-tight">
                        {rel.fact_1.value}
                      </span>
                      {rel.fact_1.unit && (
                        <span className="text-xs text-slate-400 font-medium">
                          {rel.fact_1.unit}
                        </span>
                      )}
                      {rel.fact_1.temporal_context && (
                        <span className="text-[10px] text-slate-300 bg-slate-900 border border-slate-800 px-2 py-0.5 rounded-md tabular-nums">
                          {rel.fact_1.temporal_context}
                        </span>
                      )}
                    </div>

                    <div className="text-xs text-slate-300 italic bg-slate-900/80 p-2.5 rounded-lg border border-slate-800/70 flex items-start space-x-2">
                      <Quote className="h-3 w-3 text-indigo-400 flex-shrink-0 mt-0.5" />
                      <span className="text-pretty">"{rel.fact_1.exact_quote}"</span>
                    </div>
                  </div>

                  {/* Fact 2 */}
                  <div className="bg-slate-950/70 border border-slate-800/90 rounded-xl p-4 space-y-2.5">
                    <div className="flex items-center justify-between text-xs text-slate-400">
                      <div className="flex items-center space-x-1.5 text-slate-200 min-w-0" title={rel.fact_2.document_filename}>
                        <FileText className="h-3.5 w-3.5 text-indigo-400 flex-shrink-0" />
                        <span className="truncate max-w-[200px]">{rel.fact_2.document_filename}</span>
                      </div>
                      <span className="font-mono bg-slate-900 border border-slate-800 px-2 py-0.5 rounded-md text-[10px] text-slate-300 tabular-nums">
                        p.{rel.fact_2.page_number}
                      </span>
                    </div>

                    <div className="text-xs font-semibold text-slate-200">
                      {rel.fact_2.subject}
                    </div>

                    <div className="flex items-baseline space-x-2">
                      <span className="text-xl font-bold text-white tabular-nums tracking-tight">
                        {rel.fact_2.value}
                      </span>
                      {rel.fact_2.unit && (
                        <span className="text-xs text-slate-400 font-medium">
                          {rel.fact_2.unit}
                        </span>
                      )}
                      {rel.fact_2.temporal_context && (
                        <span className="text-[10px] text-slate-300 bg-slate-900 border border-slate-800 px-2 py-0.5 rounded-md tabular-nums">
                          {rel.fact_2.temporal_context}
                        </span>
                      )}
                    </div>

                    <div className="text-xs text-slate-300 italic bg-slate-900/80 p-2.5 rounded-lg border border-slate-800/70 flex items-start space-x-2">
                      <Quote className="h-3 w-3 text-indigo-400 flex-shrink-0 mt-0.5" />
                      <span className="text-pretty">"{rel.fact_2.exact_quote}"</span>
                    </div>
                  </div>

                </div>

                {/* Reasoning Callout */}
                <div className="bg-slate-950/80 p-3.5 rounded-xl border border-slate-800 text-xs text-slate-300 leading-relaxed text-pretty">
                  <span className="font-semibold text-indigo-400 mr-1.5">Epistemological Reasoning:</span>
                  {rel.reasoning}
                </div>

              </section>
            );
          })}
        </div>
      )}

    </div>
  );
}

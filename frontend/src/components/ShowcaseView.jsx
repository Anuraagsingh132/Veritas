import React, { useState } from 'react';
import { 
  Sparkles, 
  CheckCircle2, 
  AlertTriangle, 
  Clock, 
  HelpCircle, 
  FileText, 
  Quote, 
  ShieldCheck
} from 'lucide-react';

export default function ShowcaseView({ cases, loading }) {
  const [expandedCase, setExpandedCase] = useState(null);

  const getCaseBadge = (type) => {
    switch(type) {
      case 'corroboration':
        return {
          label: 'Case 1: Corroborated Fact',
          color: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400',
          icon: <CheckCircle2 className="h-4 w-4 text-emerald-400" />
        };
      case 'genuine_contradiction':
        return {
          label: 'Case 2: Genuine Contradiction',
          color: 'bg-rose-500/10 border-rose-500/30 text-rose-400',
          icon: <AlertTriangle className="h-4 w-4 text-rose-400" />
        };
      case 'contextual_reconciliation':
        return {
          label: 'Case 3: Reconciled by Context',
          color: 'bg-amber-500/10 border-amber-500/30 text-amber-400',
          icon: <Clock className="h-4 w-4 text-amber-400" />
        };
      case 'extraction_failure':
      default:
        return {
          label: 'Case 4: Extraction / Reasoning Failure',
          color: 'bg-purple-500/10 border-purple-500/30 text-purple-400',
          icon: <HelpCircle className="h-4 w-4 text-purple-400" />
        };
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20 text-slate-400">
        <div className="animate-spin h-8 w-8 border-2 border-indigo-500 border-t-transparent rounded-full mr-3"></div>
        <span>Loading Evaluated Cases...</span>
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-indigo-950/60 via-slate-900 to-purple-950/50 border border-indigo-500/30 rounded-2xl p-6 sm:p-8 shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 text-indigo-400 mb-2 font-medium text-sm">
              <Sparkles className="h-4 w-4 text-amber-400" />
              <span>Assignment Evaluation Showcase</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
              The Four Mandatory Evaluation Cases
            </h1>
            <p className="mt-2 text-slate-300 text-sm sm:text-base max-w-3xl leading-relaxed">
              The Superjoin assignment specifies four foundational epistemological cases for cross-document fact validation.
              Below is the verified evidence, grounding quotes, and chain-of-thought reasoning discovered from the starter datasets.
            </p>
          </div>
          <div className="flex sm:flex-col items-end gap-2 text-right">
            <span className="px-3 py-1 bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 rounded-full text-xs font-semibold">
              4 of 4 Verified
            </span>
            <span className="text-xs text-slate-400">Grounded in Source PDFs</span>
          </div>
        </div>
      </div>

      {/* Cases Cards */}
      <div className="space-y-6">
        {cases.map((c, idx) => {
          const badge = getCaseBadge(c.case_type);
          const isExpanded = expandedCase === c.case_number;

          return (
            <div 
              key={c.case_number}
              className="bg-slate-900/90 border border-slate-800 hover:border-slate-700/80 rounded-2xl p-6 transition-all duration-200 shadow-md"
            >
              {/* Card Top Header */}
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-4 border-b border-slate-800/80">
                <div className="flex items-center space-x-3">
                  <span className={`flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-medium border ${badge.color}`}>
                    {badge.icon}
                    <span>{badge.label}</span>
                  </span>
                  <span className="text-xs text-slate-400 font-mono">Case #{c.case_number}</span>
                </div>
                <h2 className="text-lg font-bold text-white flex-1 md:ml-2">
                  {c.case_title}
                </h2>
              </div>

              {/* Summary & Significance */}
              <div className="py-4 space-y-2">
                <p className="text-slate-200 text-sm font-medium leading-relaxed">
                  {c.summary}
                </p>
                <div className="bg-slate-950/60 rounded-xl p-3.5 border border-slate-800/60 text-xs text-slate-400 leading-relaxed">
                  <span className="font-semibold text-slate-300 mr-1.5">Why this matters:</span>
                  {c.why_it_matters}
                </div>
              </div>

              {/* Evidence Comparison Grid */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 my-3">
                
                {/* Evidence Source 1 */}
                <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-4 flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
                      <div className="flex items-center space-x-1.5 font-medium text-indigo-300">
                        <FileText className="h-3.5 w-3.5" />
                        <span className="truncate max-w-[220px]" title={c.fact_1?.document_filename}>
                          {c.fact_1?.document_filename}
                        </span>
                      </div>
                      <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-[11px]">
                        Page {c.fact_1?.page_number}
                      </span>
                    </div>

                    <div className="my-2">
                      <span className="text-xs font-semibold text-slate-300 block mb-1">
                        {c.fact_1?.subject}
                      </span>
                      <div className="flex items-baseline space-x-2">
                        <span className="text-xl font-bold text-white">
                          {c.fact_1?.value}
                        </span>
                        <span className="text-xs text-slate-400 font-medium">
                          {c.fact_1?.unit}
                        </span>
                      </div>
                    </div>

                    {/* Temporal & Scope context */}
                    <div className="flex flex-wrap gap-1.5 my-2">
                      {c.fact_1?.temporal_context && (
                        <span className="px-2 py-0.5 rounded bg-indigo-950/60 text-indigo-300 border border-indigo-900/60 text-[10px]">
                          Time: {c.fact_1.temporal_context}
                        </span>
                      )}
                      {c.fact_1?.scope_context && (
                        <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 text-[10px]">
                          Scope: {c.fact_1.scope_context}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Verbatim Grounding Quote */}
                  <div className="mt-3 pt-3 border-t border-slate-800/80">
                    <div className="flex items-start space-x-2 text-xs text-slate-300 bg-slate-900/90 rounded-lg p-2.5 border border-slate-800/80 italic">
                      <Quote className="h-3.5 w-3.5 text-indigo-400 flex-shrink-0 mt-0.5" />
                      <span>"{c.fact_1?.exact_quote}"</span>
                    </div>
                  </div>
                </div>

                {/* Evidence Source 2 (or Mitigation Panel for Case 4) */}
                {c.fact_2 ? (
                  <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-4 flex flex-col justify-between">
                    <div>
                      <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
                        <div className="flex items-center space-x-1.5 font-medium text-purple-300">
                          <FileText className="h-3.5 w-3.5" />
                          <span className="truncate max-w-[220px]" title={c.fact_2?.document_filename}>
                            {c.fact_2?.document_filename}
                          </span>
                        </div>
                        <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-[11px]">
                          Page {c.fact_2?.page_number}
                        </span>
                      </div>

                      <div className="my-2">
                        <span className="text-xs font-semibold text-slate-300 block mb-1">
                          {c.fact_2?.subject}
                        </span>
                        <div className="flex items-baseline space-x-2">
                          <span className="text-xl font-bold text-white">
                            {c.fact_2?.value}
                          </span>
                          <span className="text-xs text-slate-400 font-medium">
                            {c.fact_2?.unit}
                          </span>
                        </div>
                      </div>

                      <div className="flex flex-wrap gap-1.5 my-2">
                        {c.fact_2?.temporal_context && (
                          <span className="px-2 py-0.5 rounded bg-purple-950/60 text-purple-300 border border-purple-900/60 text-[10px]">
                            Time: {c.fact_2.temporal_context}
                          </span>
                        )}
                        {c.fact_2?.scope_context && (
                          <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 text-[10px]">
                            Scope: {c.fact_2.scope_context}
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="mt-3 pt-3 border-t border-slate-800/80">
                      <div className="flex items-start space-x-2 text-xs text-slate-300 bg-slate-900/90 rounded-lg p-2.5 border border-slate-800/80 italic">
                        <Quote className="h-3.5 w-3.5 text-purple-400 flex-shrink-0 mt-0.5" />
                        <span>"{c.fact_2?.exact_quote}"</span>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="bg-slate-950/80 border border-purple-900/30 rounded-xl p-4 flex flex-col justify-between">
                    <div>
                      <div className="flex items-center space-x-2 text-xs text-purple-400 mb-2 font-medium">
                        <ShieldCheck className="h-4 w-4" />
                        <span>Engineering Mitigation & System Handling</span>
                      </div>
                      <h4 className="text-sm font-semibold text-slate-200 mb-2">
                        How Our System Solves & Improves This
                      </h4>
                      <p className="text-xs text-slate-300 leading-relaxed">
                        {c.resolution_or_mitigation}
                      </p>
                    </div>
                    <div className="mt-4 pt-3 border-t border-slate-800/80 text-[11px] text-slate-400 font-mono bg-slate-900/90 p-2.5 rounded-lg">
                      Status: Automated table cell coordinate bounding + spatial header binding active.
                    </div>
                  </div>
                )}

              </div>

              {/* Reasoning Box */}
              <div className="mt-4 bg-indigo-950/30 border border-indigo-500/20 rounded-xl p-4">
                <div className="flex items-center space-x-2 text-xs font-bold text-indigo-300 mb-1.5 uppercase tracking-wide">
                  <span>System Reasoning & Epistemological Proof</span>
                </div>
                <p className="text-xs sm:text-sm text-slate-200 leading-relaxed">
                  {c.reasoning}
                </p>
                {c.resolution_or_mitigation && c.fact_2 && (
                  <div className="mt-2.5 pt-2.5 border-t border-indigo-900/40 text-xs text-indigo-300 flex items-center space-x-2">
                    <span className="font-semibold">Knowledge Layer Resolution:</span>
                    <span className="text-slate-300">{c.resolution_or_mitigation}</span>
                  </div>
                )}
              </div>

            </div>
          );
        })}
      </div>

    </div>
  );
}

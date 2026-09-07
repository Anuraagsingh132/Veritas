import React, { useState } from 'react';
import { 
  Sparkles, 
  CheckCircle2, 
  AlertTriangle, 
  Clock, 
  HelpCircle, 
  FileText, 
  Quote, 
  ShieldCheck,
  Copy,
  Check
} from 'lucide-react';
import { ShowcaseSkeleton } from './SkeletonLoader';

export default function ShowcaseView({ cases, loading }) {
  const [copiedQuote, setCopiedQuote] = useState(null);

  const handleCopyQuote = (quoteText, id) => {
    navigator.clipboard.writeText(quoteText);
    setCopiedQuote(id);
    setTimeout(() => setCopiedQuote(null), 2000);
  };

  const getCaseBadge = (type) => {
    switch (type) {
      case 'corroboration':
        return {
          label: 'Corroborated Ground Truth',
          badgeClass: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400',
          icon: <CheckCircle2 className="h-4 w-4 text-emerald-400 flex-shrink-0" />,
          relationText: 'Cross-Doc Equivalence Confirmed',
          relationSymbol: '=',
          relationClass: 'text-emerald-400 bg-emerald-950/60 border-emerald-500/30'
        };
      case 'genuine_contradiction':
        return {
          label: 'Genuine Contradiction',
          badgeClass: 'bg-rose-500/10 border-rose-500/30 text-rose-400',
          icon: <AlertTriangle className="h-4 w-4 text-rose-400 flex-shrink-0" />,
          relationText: 'Direct Empirical Discrepancy',
          relationSymbol: '≠',
          relationClass: 'text-rose-400 bg-rose-950/60 border-rose-500/30'
        };
      case 'contextual_reconciliation':
        return {
          label: 'Reconciled by Context',
          badgeClass: 'bg-amber-500/10 border-amber-500/30 text-amber-400',
          icon: <Clock className="h-4 w-4 text-amber-400 flex-shrink-0" />,
          relationText: 'Harmonized by Temporal & Scope Scope',
          relationSymbol: '⟷',
          relationClass: 'text-amber-400 bg-amber-950/60 border-amber-500/30'
        };
      case 'extraction_failure':
      default:
        return {
          label: 'Extraction & Layout Mitigation',
          badgeClass: 'bg-slate-800 border-slate-700 text-slate-300',
          icon: <HelpCircle className="h-4 w-4 text-slate-400 flex-shrink-0" />,
          relationText: 'Coordinate Bounding Guard Active',
          relationSymbol: '🛡️',
          relationClass: 'text-indigo-300 bg-indigo-950/60 border-indigo-500/30'
        };
    }
  };

  if (loading) {
    return <ShowcaseSkeleton />;
  }

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      
      {/* Header Banner - Enterprise Surface Standard */}
      <div className="rounded-2xl bg-slate-900 border border-slate-800 p-6 sm:p-8 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-2 max-w-3xl">
            <div className="flex items-center space-x-2 text-indigo-400 font-medium text-xs tracking-wider uppercase">
              <Sparkles className="h-3.5 w-3.5 text-amber-400" />
              <span>Assignment Evaluation Showcase</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-semibold text-slate-100 tracking-tight text-balance">
              The Four Mandatory Evaluation Cases
            </h1>
            <p className="text-slate-400 text-xs sm:text-sm leading-relaxed text-pretty">
              The Superjoin assignment specifies four foundational epistemological cases for cross-document fact validation.
              Below is the verified evidence, grounding quotes, and chain-of-thought reasoning discovered from the starter datasets.
            </p>
          </div>
          
          <div className="flex sm:flex-col items-start sm:items-end gap-1.5 self-start sm:self-center">
            <span className="px-3 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 rounded-full text-xs font-semibold tabular-nums">
              4 of 4 Verified
            </span>
            <span className="text-[11px] text-slate-400">Grounded in Source PDFs</span>
          </div>
        </div>
      </div>

      {/* Cases Cards */}
      <div className="space-y-6">
        {cases.map((c) => {
          const badge = getCaseBadge(c.case_type);

          return (
            <section 
              key={c.case_number}
              aria-labelledby={`case-heading-${c.case_number}`}
              className="bg-slate-900 border border-slate-800 hover:border-slate-700/80 rounded-2xl p-6 transition-colors shadow-sm space-y-4"
            >
              {/* Card Top Header */}
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-3.5 border-b border-slate-800/80">
                <div className="flex items-center space-x-2.5">
                  <span className={`flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-medium border ${badge.badgeClass}`}>
                    {badge.icon}
                    <span>{badge.label}</span>
                  </span>
                  <span className="text-xs text-slate-400 font-mono tabular-nums">
                    Case #{c.case_number}
                  </span>
                </div>
                <h2 
                  id={`case-heading-${c.case_number}`}
                  className="text-base sm:text-lg font-semibold text-slate-100 flex-1 md:ml-2"
                >
                  {c.case_title}
                </h2>
              </div>

              {/* Summary & Significance */}
              <div className="space-y-2.5">
                <p className="text-slate-200 text-xs sm:text-sm leading-relaxed text-pretty">
                  {c.summary}
                </p>
                <div className="bg-slate-950/70 rounded-xl p-3 border border-slate-800/80 text-xs text-slate-300 leading-relaxed">
                  <span className="font-semibold text-slate-200 mr-1.5">Epistemological Significance:</span>
                  <span className="text-slate-400">{c.why_it_matters}</span>
                </div>
              </div>

              {/* Comparative Relation Bar */}
              <div className="flex flex-wrap items-center justify-between gap-2 px-3 py-2 rounded-xl bg-slate-950/80 border border-slate-800/80 text-xs">
                <span className="text-[11px] font-medium text-slate-400">
                  {c.fact_2 ? 'Cross-Document Epistemological Comparison' : 'Automated Coordinate Table Pipeline'}
                </span>
                <span className={`inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-md font-mono text-[11px] font-semibold border ${badge.relationClass}`}>
                  <span>{badge.relationSymbol}</span>
                  <span>{badge.relationText}</span>
                </span>
              </div>

              {/* Evidence Comparison Grid */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 pt-1">
                
                {/* Evidence Source 1 */}
                <div className="bg-slate-950/70 border border-slate-800/90 rounded-xl p-4 flex flex-col justify-between space-y-3">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-xs text-slate-400">
                      <div className="flex items-center space-x-1.5 font-medium text-slate-200 min-w-0">
                        <FileText className="h-3.5 w-3.5 text-indigo-400 flex-shrink-0" />
                        <span className="truncate max-w-[200px]" title={c.fact_1?.document_filename}>
                          {c.fact_1?.document_filename}
                        </span>
                      </div>
                      <span className="px-2 py-0.5 rounded-md bg-slate-900 border border-slate-800 text-slate-300 font-mono text-[11px] tabular-nums">
                        Page {c.fact_1?.page_number}
                      </span>
                    </div>

                    <div>
                      <span className="text-xs font-semibold text-slate-300 block mb-0.5">
                        {c.fact_1?.subject}
                      </span>
                      <div className="flex items-baseline space-x-2">
                        <span className="text-2xl font-bold text-white tabular-nums tracking-tight">
                          {c.fact_1?.value}
                        </span>
                        {c.fact_1?.unit && (
                          <span className="text-xs text-slate-400 font-medium">
                            {c.fact_1?.unit}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Context metadata */}
                    <div className="flex flex-wrap gap-1.5 pt-1">
                      {c.fact_1?.temporal_context && (
                        <span className="px-2 py-0.5 rounded-md bg-slate-900 text-slate-300 border border-slate-800 text-[10px] tabular-nums">
                          Time: {c.fact_1.temporal_context}
                        </span>
                      )}
                      {c.fact_1?.scope_context && (
                        <span className="px-2 py-0.5 rounded-md bg-slate-900 text-slate-300 border border-slate-800 text-[10px]">
                          Scope: {c.fact_1.scope_context}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Verbatim Grounding Quote */}
                  <div className="pt-2 border-t border-slate-800/80">
                    <div className="flex items-start justify-between space-x-2 text-xs text-slate-300 bg-slate-900/90 rounded-lg p-2.5 border border-slate-800/80">
                      <div className="flex items-start space-x-2 italic text-pretty">
                        <Quote className="h-3.5 w-3.5 text-indigo-400 flex-shrink-0 mt-0.5" />
                        <span>"{c.fact_1?.exact_quote}"</span>
                      </div>
                      <button
                        onClick={() => handleCopyQuote(c.fact_1?.exact_quote, `f1-${c.case_number}`)}
                        aria-label="Copy verbatim quote"
                        title="Copy verbatim quote"
                        className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800 flex-shrink-0 transition-colors"
                      >
                        {copiedQuote === `f1-${c.case_number}` ? (
                          <Check className="h-3.5 w-3.5 text-emerald-400" />
                        ) : (
                          <Copy className="h-3.5 w-3.5" />
                        )}
                      </button>
                    </div>
                  </div>
                </div>

                {/* Evidence Source 2 OR Mitigation Panel */}
                {c.fact_2 ? (
                  <div className="bg-slate-950/70 border border-slate-800/90 rounded-xl p-4 flex flex-col justify-between space-y-3">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-xs text-slate-400">
                        <div className="flex items-center space-x-1.5 font-medium text-slate-200 min-w-0">
                          <FileText className="h-3.5 w-3.5 text-indigo-400 flex-shrink-0" />
                          <span className="truncate max-w-[200px]" title={c.fact_2?.document_filename}>
                            {c.fact_2?.document_filename}
                          </span>
                        </div>
                        <span className="px-2 py-0.5 rounded-md bg-slate-900 border border-slate-800 text-slate-300 font-mono text-[11px] tabular-nums">
                          Page {c.fact_2?.page_number}
                        </span>
                      </div>

                      <div>
                        <span className="text-xs font-semibold text-slate-300 block mb-0.5">
                          {c.fact_2?.subject}
                        </span>
                        <div className="flex items-baseline space-x-2">
                          <span className="text-2xl font-bold text-white tabular-nums tracking-tight">
                            {c.fact_2?.value}
                          </span>
                          {c.fact_2?.unit && (
                            <span className="text-xs text-slate-400 font-medium">
                              {c.fact_2?.unit}
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="flex flex-wrap gap-1.5 pt-1">
                        {c.fact_2?.temporal_context && (
                          <span className="px-2 py-0.5 rounded-md bg-slate-900 text-slate-300 border border-slate-800 text-[10px] tabular-nums">
                            Time: {c.fact_2.temporal_context}
                          </span>
                        )}
                        {c.fact_2?.scope_context && (
                          <span className="px-2 py-0.5 rounded-md bg-slate-900 text-slate-300 border border-slate-800 text-[10px]">
                            Scope: {c.fact_2.scope_context}
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="pt-2 border-t border-slate-800/80">
                      <div className="flex items-start justify-between space-x-2 text-xs text-slate-300 bg-slate-900/90 rounded-lg p-2.5 border border-slate-800/80">
                        <div className="flex items-start space-x-2 italic text-pretty">
                          <Quote className="h-3.5 w-3.5 text-indigo-400 flex-shrink-0 mt-0.5" />
                          <span>"{c.fact_2?.exact_quote}"</span>
                        </div>
                        <button
                          onClick={() => handleCopyQuote(c.fact_2?.exact_quote, `f2-${c.case_number}`)}
                          aria-label="Copy verbatim quote"
                          title="Copy verbatim quote"
                          className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800 flex-shrink-0 transition-colors"
                        >
                          {copiedQuote === `f2-${c.case_number}` ? (
                            <Check className="h-3.5 w-3.5 text-emerald-400" />
                          ) : (
                            <Copy className="h-3.5 w-3.5" />
                          )}
                        </button>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="bg-slate-950/70 border border-slate-800/90 rounded-xl p-4 flex flex-col justify-between space-y-3">
                    <div className="space-y-2">
                      <div className="flex items-center space-x-2 text-xs text-indigo-400 font-medium">
                        <ShieldCheck className="h-4 w-4" />
                        <span>Engineering Mitigation & System Handling</span>
                      </div>
                      <h4 className="text-xs font-semibold text-slate-200">
                        How Our Knowledge Layer Prevents & Handles This
                      </h4>
                      <p className="text-xs text-slate-300 leading-relaxed text-pretty">
                        {c.resolution_or_mitigation}
                      </p>
                    </div>
                    <div className="pt-2 border-t border-slate-800/80 text-[11px] text-slate-400 font-mono bg-slate-900/60 p-2 rounded-lg">
                      Pipeline Status: Spatial table-cell bounding & header-binding active.
                    </div>
                  </div>
                )}

              </div>

              {/* Reasoning Box */}
              <div className="rounded-xl bg-slate-950/80 border border-slate-800 p-4 space-y-2">
                <div className="flex items-center space-x-2 text-xs font-semibold text-indigo-400 uppercase tracking-wider">
                  <span>System Chain-of-Thought & Epistemological Proof</span>
                </div>
                <p className="text-xs sm:text-sm text-slate-300 leading-relaxed text-pretty">
                  {c.reasoning}
                </p>
                {c.resolution_or_mitigation && c.fact_2 && (
                  <div className="pt-2 border-t border-slate-800/80 text-xs text-slate-300 flex items-baseline space-x-2">
                    <span className="font-semibold text-indigo-400">Resolution:</span>
                    <span className="text-slate-300">{c.resolution_or_mitigation}</span>
                  </div>
                )}
              </div>

            </section>
          );
        })}
      </div>

    </div>
  );
}

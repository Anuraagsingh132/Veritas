import React, { useState, useEffect } from 'react';
import { 
  Search, 
  FileText, 
  Quote, 
  Calendar,
  X,
  Copy,
  Check,
  RotateCcw,
  SlidersHorizontal,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import { FactsGridSkeleton } from './SkeletonLoader';

const ITEMS_PER_PAGE = 18;

export default function FactExplorer({ facts, documents, loading }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedDoc, setSelectedDoc] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [activeQuoteModal, setActiveQuoteModal] = useState(null);
  const [copiedModalQuote, setCopiedModalQuote] = useState(false);

  // Close modal on ESC key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && activeQuoteModal) {
        setActiveQuoteModal(null);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [activeQuoteModal]);

  const categories = [
    { id: 'all', label: 'All Categories' },
    { id: 'financial', label: 'Financial' },
    { id: 'macroeconomic', label: 'Macroeconomic' },
    { id: 'corporate_governance', label: 'Corporate & Legal' },
    { id: 'operational', label: 'Operational' },
  ];

  const filteredFacts = facts.filter(f => {
    const matchQuery = !searchTerm || 
      f.subject.toLowerCase().includes(searchTerm.toLowerCase()) ||
      f.value.toLowerCase().includes(searchTerm.toLowerCase()) ||
      f.exact_quote.toLowerCase().includes(searchTerm.toLowerCase()) ||
      f.predicate.toLowerCase().includes(searchTerm.toLowerCase());

    const matchCat = selectedCategory === 'all' || f.category.toLowerCase() === selectedCategory;
    const matchDoc = selectedDoc === 'all' || f.document_id === selectedDoc;

    return matchQuery && matchCat && matchDoc;
  });

  const totalPages = Math.max(1, Math.ceil(filteredFacts.length / ITEMS_PER_PAGE));
  const paginatedFacts = filteredFacts.slice(
    (currentPage - 1) * ITEMS_PER_PAGE,
    currentPage * ITEMS_PER_PAGE
  );

  const handleCategoryChange = (catId) => {
    setSelectedCategory(catId);
    setCurrentPage(1);
  };

  const handleDocChange = (docId) => {
    setSelectedDoc(docId);
    setCurrentPage(1);
  };

  const handleSearchChange = (query) => {
    setSearchTerm(query);
    setCurrentPage(1);
  };

  const handleCopyQuote = (text) => {
    navigator.clipboard.writeText(text);
    setCopiedModalQuote(true);
    setTimeout(() => setCopiedModalQuote(false), 2000);
  };

  const handleResetFilters = () => {
    setSearchTerm('');
    setSelectedCategory('all');
    setSelectedDoc('all');
    setCurrentPage(1);
  };

  const handlePageChange = (newPage) => {
    setCurrentPage(newPage);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      
      {/* Search & Filter Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm space-y-4">
        <div className="flex flex-col md:flex-row gap-3">
          
          {/* Search Bar */}
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-3 h-4 w-4 text-slate-400 pointer-events-none" />
            <input
              type="text"
              placeholder="Search facts by subject, entity, metric value, or quote..."
              value={searchTerm}
              onChange={(e) => handleSearchChange(e.target.value)}
              className="w-full pl-10 pr-10 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-xs sm:text-sm text-slate-100 placeholder-slate-500 focus:border-indigo-500 transition-colors"
            />
            {searchTerm && (
              <button
                onClick={() => handleSearchChange('')}
                aria-label="Clear search query"
                className="absolute right-3 top-2.5 p-1 text-slate-400 hover:text-white rounded-lg transition-colors"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            )}
          </div>

          {/* Document Dropdown */}
          <div className="md:w-72">
            <select
              value={selectedDoc}
              onChange={(e) => handleDocChange(e.target.value)}
              aria-label="Filter by document"
              className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-xs sm:text-sm text-slate-200 focus:border-indigo-500 transition-colors"
            >
              <option value="all">All Documents ({documents?.length || 0})</option>
              {documents?.map(d => (
                <option key={d.id} value={d.id}>
                  {d.filename.length > 30 ? d.filename.substring(0, 30) + '...' : d.filename}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Category Pills & Count */}
        <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-slate-800/80">
          <div className="flex flex-wrap gap-1.5" role="group" aria-label="Filter categories">
            {categories.map(cat => (
              <button
                key={cat.id}
                onClick={() => handleCategoryChange(cat.id)}
                className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-colors ${
                  selectedCategory === cat.id
                    ? 'bg-slate-800 text-slate-100 border border-slate-700 shadow-sm'
                    : 'bg-slate-950/70 text-slate-400 border border-slate-800/80 hover:text-slate-200 hover:bg-slate-900'
                }`}
              >
                {cat.label}
              </button>
            ))}
          </div>

          <div className="flex items-center space-x-2 text-xs text-slate-400 self-center">
            <span>Showing <strong className="text-slate-200 font-mono tabular-nums">{filteredFacts.length}</strong> facts</span>
            {(searchTerm || selectedCategory !== 'all' || selectedDoc !== 'all') && (
              <button
                onClick={handleResetFilters}
                className="text-indigo-400 hover:text-indigo-300 text-xs font-medium transition-colors ml-2 flex items-center space-x-1"
              >
                <RotateCcw className="h-3 w-3" />
                <span>Reset</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Facts Grid or Skeleton */}
      {loading ? (
        <FactsGridSkeleton />
      ) : filteredFacts.length === 0 ? (
        /* Empty State with single clear next action */
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center text-slate-400 space-y-4">
          <div className="p-3 rounded-2xl bg-slate-950 border border-slate-800 w-12 h-12 mx-auto flex items-center justify-center text-slate-500">
            <SlidersHorizontal className="h-6 w-6" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-200">No facts matched your filters</h3>
            <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto text-pretty">
              Try modifying your search keywords or reset the active document and category filters.
            </p>
          </div>
          <button
            onClick={handleResetFilters}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-medium transition-colors inline-flex items-center space-x-1.5"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            <span>Clear Search Filters</span>
          </button>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {paginatedFacts.map(fact => (
              <article
                key={fact.id}
                className="bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-2xl p-5 flex flex-col justify-between transition-colors shadow-sm space-y-3 group"
              >
                <div className="space-y-2.5">
                  {/* Source & Page Indicator */}
                  <div className="flex items-center justify-between text-xs text-slate-400">
                    <div className="flex items-center space-x-1.5 text-slate-300 min-w-0" title={fact.document_filename}>
                      <FileText className="h-3.5 w-3.5 text-indigo-400 flex-shrink-0" />
                      <span className="truncate max-w-[180px]">{fact.document_filename || fact.document_id}</span>
                    </div>
                    <span className="px-2 py-0.5 rounded-md bg-slate-950 border border-slate-800 text-slate-300 font-mono text-[11px] tabular-nums">
                      p.{fact.page_number}
                    </span>
                  </div>

                  {/* Subject & Value Metric */}
                  <div>
                    <span className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold block mb-0.5">
                      {fact.category.replace('_', ' ')}
                    </span>
                    <h3 className="text-sm font-semibold text-slate-100 leading-snug">
                      {fact.subject}
                    </h3>
                    <div className="flex items-baseline space-x-2 mt-2">
                      <span className="text-2xl font-bold text-white tabular-nums tracking-tight">
                        {fact.value}
                      </span>
                      {fact.unit && (
                        <span className="text-xs font-medium text-slate-400">
                          {fact.unit}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Context Badges */}
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {fact.temporal_context && (
                      <span className="flex items-center space-x-1 px-2 py-0.5 rounded-md bg-slate-950 border border-slate-800 text-[10px] text-slate-300 tabular-nums">
                        <Calendar className="h-3 w-3 text-indigo-400 flex-shrink-0" />
                        <span>{fact.temporal_context}</span>
                      </span>
                    )}
                    {fact.scope_context && (
                      <span className="px-2 py-0.5 rounded-md bg-slate-950 border border-slate-800 text-[10px] text-slate-300">
                        {fact.scope_context}
                      </span>
                    )}
                  </div>
                </div>

                {/* Exact Verbatim Grounding Quote Snippet */}
                <div className="pt-3 border-t border-slate-800/80 space-y-2">
                  <div 
                    onClick={() => setActiveQuoteModal(fact)}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') setActiveQuoteModal(fact); }}
                    className="bg-slate-950/80 hover:bg-slate-950 p-2.5 rounded-xl border border-slate-800/80 text-xs text-slate-300 italic cursor-pointer transition-colors flex items-start space-x-2 focus-visible:ring-2 focus-visible:ring-indigo-500"
                  >
                    <Quote className="h-3.5 w-3.5 text-indigo-400 flex-shrink-0 mt-0.5" />
                    <span className="line-clamp-2 text-pretty">
                      "{fact.exact_quote}"
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-[11px] text-slate-400">
                    <span className="tabular-nums">Confidence: {(fact.confidence * 100).toFixed(0)}%</span>
                    <button 
                      onClick={() => setActiveQuoteModal(fact)}
                      className="text-indigo-400 hover:text-indigo-300 font-medium transition-colors"
                    >
                      View Grounding
                    </button>
                  </div>
                </div>

              </article>
            ))}
          </div>

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between pt-2 text-xs text-slate-400">
              <span className="tabular-nums">
                Showing <strong className="text-slate-200">{(currentPage - 1) * ITEMS_PER_PAGE + 1}</strong>–
                <strong className="text-slate-200">{Math.min(currentPage * ITEMS_PER_PAGE, filteredFacts.length)}</strong> of{' '}
                <strong className="text-slate-200">{filteredFacts.length}</strong>
              </span>

              <div className="flex items-center space-x-2">
                <button
                  onClick={() => handlePageChange(currentPage - 1)}
                  disabled={currentPage === 1}
                  aria-label="Previous page"
                  className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 hover:bg-slate-800 disabled:opacity-40 disabled:hover:bg-slate-900 text-slate-300 flex items-center space-x-1 transition-colors"
                >
                  <ChevronLeft className="h-3.5 w-3.5" />
                  <span>Prev</span>
                </button>

                <span className="px-3 py-1 rounded-lg bg-slate-950 border border-slate-800/80 font-mono text-[11px] tabular-nums text-slate-300">
                  {currentPage} / {totalPages}
                </span>

                <button
                  onClick={() => handlePageChange(currentPage + 1)}
                  disabled={currentPage === totalPages}
                  aria-label="Next page"
                  className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 hover:bg-slate-800 disabled:opacity-40 disabled:hover:bg-slate-900 text-slate-300 flex items-center space-x-1 transition-colors"
                >
                  <span>Next</span>
                  <ChevronRight className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          )}
        </>
      )}

      {/* Accessible Grounding Quote Modal */}
      {activeQuoteModal && (
        <div 
          className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-in fade-in duration-150"
          role="dialog"
          aria-modal="true"
          aria-labelledby="quote-modal-title"
          onClick={() => setActiveQuoteModal(null)}
        >
          <div 
            className="bg-slate-900 border border-slate-800 max-w-xl w-full rounded-2xl p-6 shadow-2xl space-y-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center space-x-2">
                <Quote className="h-4 w-4 text-indigo-400" />
                <h3 id="quote-modal-title" className="text-sm font-semibold text-white">
                  Verbatim Source Evidence Grounding
                </h3>
              </div>
              <button 
                onClick={() => setActiveQuoteModal(null)}
                aria-label="Close quote modal"
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span className="font-medium text-slate-300">{activeQuoteModal.document_filename}</span>
                <span className="font-mono bg-slate-950 border border-slate-800 px-2 py-0.5 rounded text-indigo-300 tabular-nums">
                  Page {activeQuoteModal.page_number}
                </span>
              </div>

              <div className="relative bg-slate-950 p-4 rounded-xl border border-slate-800 text-xs sm:text-sm text-slate-200 font-mono whitespace-pre-wrap leading-relaxed">
                "{activeQuoteModal.exact_quote}"
                <button
                  onClick={() => handleCopyQuote(activeQuoteModal.exact_quote)}
                  className="absolute right-3 top-3 p-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-white transition-colors"
                  title="Copy quote"
                >
                  {copiedModalQuote ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
                </button>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                <span className="text-slate-500 block mb-0.5">Extracted Subject</span>
                <span className="text-slate-200 font-medium">{activeQuoteModal.subject}</span>
              </div>
              <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                <span className="text-slate-500 block mb-0.5">Extracted Value</span>
                <span className="text-white font-bold tabular-nums">{activeQuoteModal.value} {activeQuoteModal.unit}</span>
              </div>
            </div>

            <div className="flex items-center justify-between text-[11px] text-slate-400 pt-2 border-t border-slate-800/80">
              <span>Fact ID: <span className="font-mono text-slate-300">{activeQuoteModal.id}</span></span>
              <button
                onClick={() => setActiveQuoteModal(null)}
                className="px-3.5 py-1.5 rounded-xl bg-slate-800 text-slate-200 hover:bg-slate-700 text-xs font-medium transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}

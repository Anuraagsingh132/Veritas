import React, { useState } from 'react';
import { 
  Search, 
  Filter, 
  FileText, 
  Quote, 
  Calendar, 
  Layers, 
  AlertCircle,
  ExternalLink,
  Check
} from 'lucide-react';

export default function FactExplorer({ facts, documents, loading }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedDoc, setSelectedDoc] = useState('all');
  const [activeQuoteModal, setActiveQuoteModal] = useState(null);

  const categories = [
    { id: 'all', label: 'All Categories' },
    { id: 'financial', label: 'Financial' },
    { id: 'macroeconomic', label: 'Macroeconomic' },
    { id: 'corporate_governance', label: 'Corporate & Legal' },
    { id: 'operational', label: 'Operational' },
  ];

  const filteredFacts = facts.filter(f => {
    // Search query
    const matchQuery = !searchTerm || 
      f.subject.toLowerCase().includes(searchTerm.toLowerCase()) ||
      f.value.toLowerCase().includes(searchTerm.toLowerCase()) ||
      f.exact_quote.toLowerCase().includes(searchTerm.toLowerCase()) ||
      f.predicate.toLowerCase().includes(searchTerm.toLowerCase());

    // Category filter
    const matchCat = selectedCategory === 'all' || f.category.toLowerCase() === selectedCategory;

    // Doc filter
    const matchDoc = selectedDoc === 'all' || f.document_id === selectedDoc;

    return matchQuery && matchCat && matchDoc;
  });

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      
      {/* Search & Filter Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg space-y-4">
        <div className="flex flex-col md:flex-row gap-3">
          
          {/* Search Bar */}
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-3 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search facts by subject, entity, number, or exact quote..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition"
            />
          </div>

          {/* Document Dropdown */}
          <div className="md:w-72">
            <select
              value={selectedDoc}
              onChange={(e) => setSelectedDoc(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-sm text-slate-300 focus:outline-none focus:border-indigo-500"
            >
              <option value="all">All Documents ({documents?.length || 0})</option>
              {documents?.map(d => (
                <option key={d.id} value={d.id}>
                  {d.filename.length > 32 ? d.filename.substring(0, 32) + '...' : d.filename}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Category Pills */}
        <div className="flex flex-wrap gap-2 pt-1 border-t border-slate-800/80">
          {categories.map(cat => (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                selectedCategory === cat.id
                  ? 'bg-indigo-600 text-white shadow'
                  : 'bg-slate-800/80 text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              {cat.label}
            </button>
          ))}
          <span className="text-xs text-slate-500 self-center ml-auto">
            Showing {filteredFacts.length} facts
          </span>
        </div>
      </div>

      {/* Facts Grid */}
      {loading ? (
        <div className="flex justify-center py-20 text-slate-400">
          <div className="animate-spin h-8 w-8 border-2 border-indigo-500 border-t-transparent rounded-full mr-3"></div>
          <span>Loading Facts...</span>
        </div>
      ) : filteredFacts.length === 0 ? (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center text-slate-400">
          <Search className="h-8 w-8 mx-auto mb-3 text-slate-600" />
          <p className="text-sm font-medium">No facts match your search criteria.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredFacts.map(fact => (
            <div
              key={fact.id}
              className="bg-slate-900/90 border border-slate-800 hover:border-indigo-500/50 rounded-2xl p-5 flex flex-col justify-between transition-all duration-200 shadow-sm hover:shadow-indigo-500/5 group"
            >
              <div>
                {/* Source Badge */}
                <div className="flex items-center justify-between text-xs text-slate-400 mb-3">
                  <div className="flex items-center space-x-1.5 text-indigo-400 truncate max-w-[200px]" title={fact.document_filename}>
                    <FileText className="h-3.5 w-3.5 flex-shrink-0" />
                    <span className="truncate">{fact.document_filename || fact.document_id}</span>
                  </div>
                  <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-[11px]">
                    p.{fact.page_number}
                  </span>
                </div>

                {/* Subject & Value */}
                <div className="mb-3">
                  <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold block mb-0.5">
                    {fact.category}
                  </span>
                  <h3 className="text-sm font-bold text-slate-100 leading-snug">
                    {fact.subject}
                  </h3>
                  <div className="flex items-baseline space-x-2 mt-2">
                    <span className="text-2xl font-black text-indigo-400">
                      {fact.value}
                    </span>
                    {fact.unit && (
                      <span className="text-xs font-semibold text-slate-400">
                        {fact.unit}
                      </span>
                    )}
                  </div>
                </div>

                {/* Context Badges */}
                <div className="flex flex-wrap gap-1.5 mb-3">
                  {fact.temporal_context && (
                    <span className="flex items-center space-x-1 px-2 py-0.5 rounded bg-indigo-950/70 border border-indigo-900/50 text-[11px] text-indigo-300">
                      <Calendar className="h-3 w-3" />
                      <span>{fact.temporal_context}</span>
                    </span>
                  )}
                  {fact.scope_context && (
                    <span className="px-2 py-0.5 rounded bg-slate-800/90 border border-slate-700/50 text-[11px] text-slate-300">
                      {fact.scope_context}
                    </span>
                  )}
                </div>
              </div>

              {/* Exact Verbatim Grounding Quote Snippet */}
              <div className="pt-3 border-t border-slate-800/80">
                <div 
                  onClick={() => setActiveQuoteModal(fact)}
                  className="bg-slate-950/80 hover:bg-slate-950 p-2.5 rounded-xl border border-slate-800/80 text-xs text-slate-300 italic cursor-pointer transition flex items-start space-x-2"
                >
                  <Quote className="h-3.5 w-3.5 text-indigo-400 flex-shrink-0 mt-0.5" />
                  <span className="line-clamp-2">
                    "{fact.exact_quote}"
                  </span>
                </div>
                <div className="flex items-center justify-between mt-2 text-[10px] text-slate-500">
                  <span>Confidence: {(fact.confidence * 100).toFixed(0)}%</span>
                  <span className="text-indigo-400/80 group-hover:text-indigo-400">Click quote for full evidence</span>
                </div>
              </div>

            </div>
          ))}
        </div>
      )}

      {/* Grounding Quote Modal */}
      {activeQuoteModal && (
        <div 
          className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          onClick={() => setActiveQuoteModal(null)}
        >
          <div 
            className="bg-slate-900 border border-slate-800 max-w-xl w-full rounded-2xl p-6 shadow-2xl space-y-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center space-x-2">
                <Quote className="h-4 w-4 text-indigo-400" />
                <span className="text-sm font-bold text-white">Verbatim Source Evidence Grounding</span>
              </div>
              <button 
                onClick={() => setActiveQuoteModal(null)}
                className="text-slate-400 hover:text-white text-xs px-2 py-1 rounded bg-slate-800"
              >
                Close
              </button>
            </div>

            <div>
              <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
                <span className="font-semibold text-slate-300">{activeQuoteModal.document_filename}</span>
                <span className="font-mono bg-slate-800 px-2 py-0.5 rounded text-indigo-300">
                  Page {activeQuoteModal.page_number}
                </span>
              </div>

              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-sm text-slate-200 font-mono whitespace-pre-wrap leading-relaxed">
                "{activeQuoteModal.exact_quote}"
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                <span className="text-slate-500 block">Extracted Subject:</span>
                <span className="text-slate-200 font-medium">{activeQuoteModal.subject}</span>
              </div>
              <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                <span className="text-slate-500 block">Extracted Value:</span>
                <span className="text-white font-bold">{activeQuoteModal.value} {activeQuoteModal.unit}</span>
              </div>
            </div>

            <div className="text-[11px] text-slate-400 text-right">
              Grounded Fact ID: <span className="font-mono text-slate-300">{activeQuoteModal.id}</span>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}

import React, { useState, useRef } from 'react';
import { 
  UploadCloud, 
  FileText, 
  Trash2, 
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  Loader2
} from 'lucide-react';
import { DocumentListSkeleton } from './SkeletonLoader';

export default function DocumentManager({ 
  documents, 
  loading, 
  onUploadSuccess, 
  onDeleteDocument,
  onRefresh
}) {
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = async (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFiles(e.dataTransfer.files);
    }
  };

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFiles(e.target.files);
    }
  };

  const handleFiles = async (files) => {
    const file = files[0];
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setUploadStatus({ type: 'error', text: 'Only PDF documents are supported for fact extraction.' });
      return;
    }

    setUploading(true);
    setUploadStatus({ type: 'info', text: `Ingesting "${file.name}" through PyMuPDF & LLM pipeline...` });

    try {
      await onUploadSuccess(file);
      setUploadStatus({ type: 'success', text: `Successfully processed "${file.name}"! Facts and relationships extracted.` });
      setTimeout(() => setUploadStatus(null), 5000);
    } catch (err) {
      setUploadStatus({ type: 'error', text: `Upload failed: ${err.message}` });
    } finally {
      setUploading(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      
      {/* Upload Zone */}
      <div 
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-2xl p-8 sm:p-12 text-center cursor-pointer transition-colors ${
          isDragging 
            ? 'border-indigo-500 bg-indigo-950/20 shadow-lg' 
            : 'border-slate-800 bg-slate-900/50 hover:border-slate-700 hover:bg-slate-900/80'
        }`}
      >
        <input 
          type="file" 
          ref={fileInputRef} 
          onChange={handleFileInput} 
          accept=".pdf" 
          className="hidden" 
        />
        
        <div className="flex flex-col items-center justify-center space-y-3">
          <div className="p-3.5 rounded-2xl bg-slate-800/80 border border-slate-700 text-indigo-400">
            <UploadCloud className="h-7 w-7" />
          </div>
          <div className="space-y-1">
            <h3 className="text-sm sm:text-base font-semibold text-slate-100">
              {uploading ? 'Ingesting PDF Document...' : 'Upload Ground-Truth PDF Document'}
            </h3>
            <p className="text-xs text-slate-400 max-w-md mx-auto leading-relaxed text-pretty">
              Drag and drop your PDF here, or click to browse. The pipeline performs text extraction, coordinate bounding, fact discovery, and cross-document reconciliation.
            </p>
          </div>

          {uploadStatus && (
            <div className={`mt-2 text-xs font-medium px-3.5 py-2 rounded-xl border flex items-center space-x-2 ${
              uploadStatus.type === 'error'
                ? 'bg-rose-950/60 border-rose-500/30 text-rose-300'
                : uploadStatus.type === 'success'
                  ? 'bg-emerald-950/60 border-emerald-500/30 text-emerald-300'
                  : 'bg-slate-950 border-slate-800 text-slate-300'
            }`}>
              {uploadStatus.type === 'success' && <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 flex-shrink-0" />}
              {uploadStatus.type === 'error' && <AlertCircle className="h-3.5 w-3.5 text-rose-400 flex-shrink-0" />}
              <span>{uploadStatus.text}</span>
            </div>
          )}
        </div>
      </div>

      {/* Registered Documents List */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-sm space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div className="flex items-center space-x-2.5">
            <FileText className="h-5 w-5 text-indigo-400" />
            <h2 className="text-sm sm:text-base font-semibold text-slate-100">Registered PDF Sources</h2>
            <span className="text-xs px-2 py-0.5 rounded-md bg-slate-950 border border-slate-800 text-slate-300 font-mono tabular-nums">
              {documents?.length || 0}
            </span>
          </div>

          <button
            onClick={onRefresh}
            aria-label="Refresh document status"
            className="p-1.5 text-slate-400 hover:text-white rounded-xl hover:bg-slate-800 border border-transparent hover:border-slate-700 transition-colors focus-visible:ring-2 focus-visible:ring-indigo-500"
            title="Refresh document status"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>

        {loading ? (
          <DocumentListSkeleton />
        ) : documents.length === 0 ? (
          <div className="text-center py-12 text-slate-400 text-xs sm:text-sm">
            No documents currently registered. Upload a PDF above to begin fact extraction.
          </div>
        ) : (
          <div className="divide-y divide-slate-800/60">
            {documents.map(doc => (
              <div 
                key={doc.id}
                className="py-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-slate-800/30 px-3 rounded-xl transition-colors"
              >
                <div className="flex items-start space-x-3.5 min-w-0">
                  <div className="p-2.5 rounded-xl bg-slate-800 text-indigo-400 mt-0.5 sm:mt-0 flex-shrink-0 border border-slate-700/60">
                    <FileText className="h-5 w-5" />
                  </div>
                  <div className="min-w-0 space-y-1">
                    <div className="flex items-center space-x-2 flex-wrap">
                      <h4 className="text-xs sm:text-sm font-semibold text-slate-100 truncate max-w-sm" title={doc.filename}>
                        {doc.filename}
                      </h4>
                      <span className={`text-[10px] px-2 py-0.5 rounded-md font-medium border flex items-center space-x-1 ${
                        doc.status === 'ready' 
                          ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' 
                          : doc.status === 'processing' 
                            ? 'bg-amber-500/10 text-amber-400 border-amber-500/30' 
                            : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                      }`}>
                        <span className={`h-1.5 w-1.5 rounded-full ${
                          doc.status === 'ready' ? 'bg-emerald-400' : doc.status === 'processing' ? 'bg-amber-400 animate-ping' : 'bg-rose-400'
                        }`} />
                        <span>{doc.status}</span>
                      </span>
                    </div>

                    <p className="text-xs text-slate-400 line-clamp-1 text-pretty">
                      {doc.summary || 'PDF document ingested into knowledge layer.'}
                    </p>

                    {doc.status === 'processing' ? (
                      <div className="pt-1.5 space-y-1.5 w-full max-w-md">
                        <div className="flex items-center justify-between text-[11px]">
                          <span className="text-amber-400 font-medium flex items-center space-x-1.5">
                            <Loader2 className="h-3 w-3 animate-spin text-amber-400 flex-shrink-0" />
                            <span className="truncate max-w-xs">{doc.current_step || 'Processing document...'}</span>
                          </span>
                          <span className="text-slate-200 font-mono tabular-nums font-semibold ml-2">
                            {doc.progress_pct || 10}%
                          </span>
                        </div>
                        <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden border border-slate-700/50">
                          <div 
                            className="bg-gradient-to-r from-amber-500 via-indigo-500 to-emerald-500 h-full rounded-full transition-all duration-300 ease-out"
                            style={{ width: `${Math.max(5, Math.min(100, doc.progress_pct || 10))}%` }}
                          />
                        </div>
                        <div className="flex items-center space-x-2 text-[10px] text-slate-400 font-mono tabular-nums">
                          <span>Processed {doc.processed_pages || 0} / {doc.total_pages || doc.page_count || '?'} target pages</span>
                          <span>•</span>
                          <span className="text-indigo-400 font-semibold">{doc.fact_count || 0} facts found</span>
                        </div>
                      </div>
                    ) : (
                      <div className="flex items-center space-x-3 text-[11px] text-slate-400 font-mono tabular-nums">
                        <span>{doc.page_count} pages</span>
                        <span>•</span>
                        <span>{formatFileSize(doc.filesize)}</span>
                        <span>•</span>
                        <span className="text-indigo-400 font-semibold">{doc.fact_count} facts extracted</span>
                      </div>
                    )}
                  </div>
                </div>

                <div className="flex items-center space-x-2 self-end sm:self-center flex-shrink-0">
                  <button
                    onClick={() => onDeleteDocument(doc.id)}
                    aria-label={`Remove document ${doc.filename}`}
                    className="p-2 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-xl transition-colors focus-visible:ring-2 focus-visible:ring-rose-500"
                    title="Remove document and purge facts"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

    </div>
  );
}

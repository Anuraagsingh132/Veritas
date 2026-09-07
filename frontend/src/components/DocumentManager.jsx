import React, { useState, useRef } from 'react';
import { 
  UploadCloud, 
  FileText, 
  CheckCircle, 
  Clock, 
  AlertCircle, 
  Trash2, 
  RefreshCw,
  Layers
} from 'lucide-react';

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
      alert('Please upload a valid PDF file.');
      return;
    }

    setUploading(true);
    setUploadStatus(`Uploading & ingesting ${file.name}...`);

    try {
      await onUploadSuccess(file);
      setUploadStatus(`Successfully processed ${file.name}! Facts and relationships extracted.`);
      setTimeout(() => setUploadStatus(null), 5000);
    } catch (err) {
      setUploadStatus(`Upload failed: ${err.message}`);
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
        className={`border-2 border-dashed rounded-2xl p-8 sm:p-12 text-center cursor-pointer transition-all duration-200 ${
          isDragging 
            ? 'border-indigo-400 bg-indigo-950/40 shadow-xl' 
            : 'border-slate-800 bg-slate-900/60 hover:border-slate-700 hover:bg-slate-900'
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
          <div className="p-4 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-400">
            <UploadCloud className="h-8 w-8 animate-bounce" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-white">
              {uploading ? 'Processing PDF Document...' : 'Upload Any New PDF Document'}
            </h3>
            <p className="text-xs text-slate-400 mt-1 max-w-md">
              Drag and drop your PDF here, or click to browse. The pipeline extracts text, discovers numerical and semantic facts, and reconciles against the knowledge layer.
            </p>
          </div>

          {uploadStatus && (
            <div className="mt-2 text-xs font-medium px-3 py-1.5 rounded-lg bg-indigo-950 border border-indigo-500/40 text-indigo-300">
              {uploadStatus}
            </div>
          )}
        </div>
      </div>

      {/* Documents List */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-lg space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div className="flex items-center space-x-2">
            <FileText className="h-5 w-5 text-indigo-400" />
            <h2 className="text-base font-bold text-white">Registered PDF Documents</h2>
            <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 font-mono">
              {documents?.length || 0}
            </span>
          </div>

          <button
            onClick={onRefresh}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition"
            title="Refresh document status"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>

        {loading ? (
          <div className="flex justify-center py-12 text-slate-400">
            <div className="animate-spin h-6 w-6 border-2 border-indigo-500 border-t-transparent rounded-full mr-2"></div>
            <span>Loading documents...</span>
          </div>
        ) : documents.length === 0 ? (
          <div className="text-center py-12 text-slate-400 text-sm">
            No documents currently registered. Upload a PDF above to start.
          </div>
        ) : (
          <div className="divide-y divide-slate-800/80">
            {documents.map(doc => (
              <div 
                key={doc.id}
                className="py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-slate-800/20 px-3 rounded-xl transition"
              >
                <div className="flex items-start space-x-3">
                  <div className="p-2.5 rounded-xl bg-slate-800 text-indigo-400 mt-1 sm:mt-0 flex-shrink-0">
                    <FileText className="h-5 w-5" />
                  </div>
                  <div>
                    <div className="flex items-center space-x-2">
                      <h4 className="text-sm font-semibold text-slate-100">
                        {doc.filename}
                      </h4>
                      <span className={`text-[10px] px-2 py-0.5 rounded font-medium ${
                        doc.status === 'ready' 
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' 
                          : doc.status === 'processing' 
                            ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' 
                            : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                      }`}>
                        {doc.status}
                      </span>
                    </div>

                    <p className="text-xs text-slate-400 mt-0.5 line-clamp-1">
                      {doc.summary || 'PDF document ingested into knowledge layer.'}
                    </p>

                    <div className="flex items-center space-x-4 mt-2 text-[11px] text-slate-500 font-mono">
                      <span>{doc.page_count} pages</span>
                      <span>•</span>
                      <span>{formatFileSize(doc.filesize)}</span>
                      <span>•</span>
                      <span className="text-indigo-400 font-semibold">{doc.fact_count} facts extracted</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-2 self-end sm:self-center">
                  <button
                    onClick={() => onDeleteDocument(doc.id)}
                    className="p-2 text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition"
                    title="Remove document"
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

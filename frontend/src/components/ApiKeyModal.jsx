import React, { useState, useEffect } from 'react';
import { Key, X, Eye, EyeOff, CheckCircle2, AlertCircle } from 'lucide-react';

export default function ApiKeyModal({ isOpen, onClose, onSaveKey, currentStatus }) {
  const [apiKey, setApiKey] = useState('');
  const [showKey, setShowKey] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState(null);

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleSave = async () => {
    if (!apiKey.trim()) {
      setMessage({ type: 'error', text: 'Please enter a valid Groq API key (starts with gsk_).' });
      return;
    }

    setSaving(true);
    try {
      await onSaveKey(apiKey);
      setMessage({ type: 'success', text: 'Groq API Key activated successfully!' });
      setTimeout(() => {
        setMessage(null);
        onClose();
      }, 1500);
    } catch (e) {
      setMessage({ type: 'error', text: `Failed to save: ${e.message}` });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div 
      className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-in fade-in duration-150"
      role="dialog"
      aria-modal="true"
      aria-labelledby="api-key-modal-title"
      onClick={onClose}
    >
      <div 
        className="bg-slate-900 border border-slate-800 max-w-md w-full rounded-2xl p-6 shadow-2xl space-y-4"
        onClick={(e) => e.stopPropagation()}
      >
        
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-xl bg-slate-800 text-indigo-400 border border-slate-700">
              <Key className="h-4 w-4" />
            </div>
            <h3 id="api-key-modal-title" className="text-sm font-semibold text-white">
              Configure Groq API Key
            </h3>
          </div>
          <button 
            onClick={onClose}
            aria-label="Close modal"
            className="p-1 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors focus-visible:ring-2 focus-visible:ring-indigo-500"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <p className="text-xs text-slate-400 leading-relaxed text-pretty">
          Power real-time cross-document fact extraction and reconciliation using <span className="text-indigo-300 font-mono font-medium">{currentStatus?.model || 'groq/compound-mini'}</span> on Groq's high-throughput inference engine (70K TPM).
        </p>

        <div className="space-y-1.5">
          <label htmlFor="groq-api-key-input" className="text-xs font-semibold text-slate-300 block">
            Groq API Key
          </label>
          <div className="relative">
            <input
              id="groq-api-key-input"
              type={showKey ? 'text' : 'password'}
              placeholder="gsk_..."
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              className="w-full pl-3.5 pr-10 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-xs sm:text-sm text-slate-100 placeholder-slate-600 focus:border-indigo-500 font-mono transition-colors"
            />
            <button
              type="button"
              onClick={() => setShowKey(!showKey)}
              aria-label={showKey ? 'Hide API key' : 'Show API key'}
              className="absolute right-3 top-2.5 p-1 text-slate-400 hover:text-white transition-colors"
            >
              {showKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
        </div>

        {message && (
          <div className={`text-xs p-3 rounded-xl border flex items-center space-x-2 ${
            message.type === 'success' 
              ? 'bg-emerald-950/60 border-emerald-500/30 text-emerald-300' 
              : 'bg-rose-950/60 border-rose-500/30 text-rose-300'
          }`}>
            {message.type === 'success' ? <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 flex-shrink-0" /> : <AlertCircle className="h-3.5 w-3.5 text-rose-400 flex-shrink-0" />}
            <span>{message.text}</span>
          </div>
        )}

        <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800/80 text-[11px] text-slate-400 space-y-1.5">
          <div className="flex justify-between items-center">
            <span>Current Status:</span>
            <span className={`px-2 py-0.5 rounded-md font-medium text-[10px] border ${
              currentStatus?.llm_available 
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' 
                : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
            }`}>
              {currentStatus?.llm_available ? 'Active & Ready' : 'Offline / Curated Fallback'}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span>Active Model:</span>
            <span className="font-mono text-indigo-400 font-medium">{currentStatus?.model || 'groq/compound-mini'}</span>
          </div>
          {currentStatus?.fallback_model && (
            <div className="flex justify-between items-center">
              <span>Fallback Model:</span>
              <span className="font-mono text-slate-400 text-[10px]">{currentStatus.fallback_model}</span>
            </div>
          )}
        </div>

        <div className="flex items-center justify-end space-x-2.5 pt-2">
          <button
            type="button"
            onClick={onClose}
            className="px-3.5 py-2 text-xs font-medium text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-xl transition-colors"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleSave}
            disabled={saving}
            className="px-4 py-2 text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl shadow-sm transition-colors disabled:opacity-50 focus-visible:ring-2 focus-visible:ring-indigo-500"
          >
            {saving ? 'Saving...' : 'Activate Key'}
          </button>
        </div>

      </div>
    </div>
  );
}

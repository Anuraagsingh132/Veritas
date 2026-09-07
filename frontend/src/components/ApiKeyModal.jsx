import React, { useState } from 'react';
import { Key, Check, ShieldAlert, X } from 'lucide-react';

export default function ApiKeyModal({ isOpen, onClose, onSaveKey, currentStatus }) {
  const [apiKey, setApiKey] = useState('');
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState(null);

  if (!isOpen) return null;

  const handleSave = async () => {
    if (!apiKey.trim()) {
      setMessage({ type: 'error', text: 'Please enter a valid API key string.' });
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
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 max-w-md w-full rounded-2xl p-6 shadow-2xl space-y-4">
        
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center space-x-2">
            <div className="p-1.5 rounded-lg bg-indigo-500/10 text-indigo-400">
              <Key className="h-4 w-4" />
            </div>
            <h3 className="text-sm font-bold text-white">Configure Groq API Key</h3>
          </div>
          <button 
            onClick={onClose}
            className="p-1 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <p className="text-xs text-slate-400 leading-relaxed">
          Provide your Groq API key to power live fact extraction and dynamic reconciliation using <span className="text-indigo-400 font-mono">llama-3.3-70b-versatile</span>.
        </p>

        <div>
          <label className="text-xs font-semibold text-slate-300 block mb-1.5">
            Groq API Key:
          </label>
          <input
            type="password"
            placeholder="gsk_..."
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-indigo-500 font-mono"
          />
        </div>

        {message && (
          <div className={`text-xs p-2.5 rounded-lg border ${
            message.type === 'success' 
              ? 'bg-emerald-950/60 border-emerald-500/40 text-emerald-300' 
              : 'bg-rose-950/60 border-rose-500/40 text-rose-300'
          }`}>
            {message.text}
          </div>
        )}

        <div className="bg-slate-950 p-3 rounded-xl border border-slate-800/80 text-[11px] text-slate-400 space-y-1">
          <div className="flex justify-between">
            <span>Current Status:</span>
            <span className={currentStatus?.llm_available ? 'text-emerald-400 font-semibold' : 'text-amber-400'}>
              {currentStatus?.llm_available ? 'Active' : 'Offline / Starter Knowledge Mode'}
            </span>
          </div>
          <div className="flex justify-between">
            <span>Active Model:</span>
            <span className="font-mono text-slate-300">{currentStatus?.model || 'llama-3.3-70b-versatile'}</span>
          </div>
        </div>

        <div className="flex items-center justify-end space-x-2 pt-2">
          <button
            onClick={onClose}
            className="px-3.5 py-2 text-xs font-medium text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-xl transition"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-4 py-2 text-xs font-medium bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl shadow transition disabled:opacity-50 flex items-center space-x-1.5"
          >
            {saving ? <span>Saving...</span> : <span>Activate Key</span>}
          </button>
        </div>

      </div>
    </div>
  );
}

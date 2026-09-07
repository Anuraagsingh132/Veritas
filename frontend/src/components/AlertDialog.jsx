import React, { useEffect } from 'react';
import { Trash2, RotateCcw, X } from 'lucide-react';

export default function AlertDialog({
  isOpen,
  title,
  description,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  intent = 'danger', // 'danger' | 'warning' | 'info'
  onConfirm,
  onCancel,
}) {
  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onCancel();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onCancel]);

  if (!isOpen) return null;

  const isDanger = intent === 'danger';

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-150"
      role="alertdialog"
      aria-modal="true"
      aria-labelledby="alert-dialog-title"
      aria-describedby="alert-dialog-description"
      onClick={onCancel}
    >
      <div
        className="w-full max-w-md rounded-2xl bg-slate-900 border border-slate-800 p-6 shadow-2xl space-y-4 scale-100 transition-all duration-150 ease-out"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start space-x-3.5">
          <div
            className={`p-2.5 rounded-xl flex-shrink-0 ${
              isDanger
                ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
            }`}
          >
            {isDanger ? (
              <Trash2 className="h-5 w-5" />
            ) : (
              <RotateCcw className="h-5 w-5" />
            )}
          </div>

          <div className="flex-1 min-w-0">
            <h3
              id="alert-dialog-title"
              className="text-base font-semibold text-slate-100 leading-snug"
            >
              {title}
            </h3>
            <p
              id="alert-dialog-description"
              className="mt-1.5 text-xs text-slate-400 leading-relaxed text-pretty"
            >
              {description}
            </p>
          </div>

          <button
            onClick={onCancel}
            aria-label="Close dialog"
            className="p-1 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="flex items-center justify-end space-x-2.5 pt-3 border-t border-slate-800/80">
          <button
            type="button"
            onClick={onCancel}
            className="px-3.5 py-2 text-xs font-medium rounded-xl text-slate-300 hover:text-white hover:bg-slate-800 transition-colors focus-visible:ring-2 focus-visible:ring-slate-400"
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            autoFocus
            onClick={onConfirm}
            className={`px-4 py-2 text-xs font-semibold rounded-xl text-white shadow-sm transition-all focus-visible:ring-2 ${
              isDanger
                ? 'bg-rose-600 hover:bg-rose-500 focus-visible:ring-rose-400 active:bg-rose-700'
                : 'bg-amber-600 hover:bg-amber-500 focus-visible:ring-amber-400 active:bg-amber-700'
            }`}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}

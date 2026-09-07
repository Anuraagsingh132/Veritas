import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import ShowcaseView from './components/ShowcaseView';
import FactExplorer from './components/FactExplorer';
import ReconciliationMatrix from './components/ReconciliationMatrix';
import DocumentManager from './components/DocumentManager';
import ApiKeyModal from './components/ApiKeyModal';
import AlertDialog from './components/AlertDialog';
import { 
  getStats, 
  getStatus, 
  getShowcaseCases, 
  getFacts, 
  getReconciliation, 
  getDocuments, 
  uploadDocument, 
  deleteDocument, 
  runReconciliation, 
  updateApiKey, 
  reseedData 
} from './api/client';

export default function App() {
  const [activeTab, setActiveTab] = useState('showcase'); // Default to 4 Required Cases
  const [stats, setStats] = useState(null);
  const [status, setStatus] = useState(null);
  const [showcaseCases, setShowcaseCases] = useState([]);
  const [facts, setFacts] = useState([]);
  const [relationships, setRelationships] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [keyModalOpen, setKeyModalOpen] = useState(false);

  // Accessible alert dialog state
  const [alertDialog, setAlertDialog] = useState({
    isOpen: false,
    title: '',
    description: '',
    confirmLabel: 'Confirm',
    intent: 'danger',
    onConfirm: () => {},
  });

  // Load all initial data
  const loadAllData = async () => {
    setLoading(true);
    try {
      const [statsData, statusData, casesData, factsData, relsData, docsData] = await Promise.all([
        getStats().catch(() => null),
        getStatus().catch(() => null),
        getShowcaseCases().catch(() => ({ cases: [] })),
        getFacts().catch(() => []),
        getReconciliation().catch(() => []),
        getDocuments().catch(() => [])
      ]);

      setStats(statsData);
      setStatus(statusData);
      setShowcaseCases(casesData.cases || []);
      setFacts(factsData);
      setRelationships(relsData);
      setDocuments(docsData);
    } catch (e) {
      console.error('Failed to load knowledge layer data:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAllData();
  }, []);

  // Auto-poll real-time progress while any document is in 'processing' state
  useEffect(() => {
    const isProcessing = documents.some(d => d.status === 'processing');
    if (!isProcessing) return;

    const interval = setInterval(async () => {
      try {
        const [docsData, statsData, factsData, relsData] = await Promise.all([
          getDocuments().catch(() => null),
          getStats().catch(() => null),
          getFacts().catch(() => null),
          getReconciliation().catch(() => null)
        ]);

        if (docsData) setDocuments(docsData);
        if (statsData) setStats(statsData);
        if (factsData) setFacts(factsData);
        if (relsData) setRelationships(relsData);
      } catch (err) {
        console.error('Silent progress poll error:', err);
      }
    }, 1200);

    return () => clearInterval(interval);
  }, [documents]);

  const handleUpload = async (file) => {
    await uploadDocument(file);
    // Refresh immediately so the newly uploaded file appears with its live progress bar
    const docs = await getDocuments().catch(() => []);
    setDocuments(docs);
  };

  // Replace raw window.confirm with accessible AlertDialog
  const handleDeleteRequest = (docId) => {
    const doc = documents.find(d => d.id === docId);
    const filename = doc ? doc.filename : 'this document';
    
    setAlertDialog({
      isOpen: true,
      title: 'Remove Document & Extracted Facts',
      description: `Are you sure you want to remove "${filename}"? All associated ground-truth facts and cross-document reconciliation links will be purged from the knowledge layer.`,
      confirmLabel: 'Delete Document',
      intent: 'danger',
      onConfirm: async () => {
        setAlertDialog(prev => ({ ...prev, isOpen: false }));
        await deleteDocument(docId);
        loadAllData();
      },
    });
  };

  const handleReseedRequest = () => {
    setAlertDialog({
      isOpen: true,
      title: 'Reset to Ground-Truth Dataset',
      description: 'This will reset the entire knowledge layer back to the curated 4 mandatory evaluation cases and starter PDFs. Any custom uploaded documents will be cleared.',
      confirmLabel: 'Reset Knowledge Layer',
      intent: 'warning',
      onConfirm: async () => {
        setAlertDialog(prev => ({ ...prev, isOpen: false }));
        await reseedData();
        loadAllData();
      },
    });
  };

  const handleTriggerReconcile = async () => {
    await runReconciliation();
    loadAllData();
  };

  const handleSaveKey = async (key) => {
    await updateApiKey(key);
    const updatedStatus = await getStatus();
    setStatus(updatedStatus);
  };

  return (
    <div className="min-h-dvh bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-indigo-500/30 selection:text-indigo-200">
      
      {/* Top Navbar */}
      <Navbar 
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        stats={stats}
        status={status}
        onOpenKeyModal={() => setKeyModalOpen(true)}
        onReseed={handleReseedRequest}
      />

      {/* Main Content Surface */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'showcase' && (
          <ShowcaseView cases={showcaseCases} loading={loading} />
        )}

        {activeTab === 'facts' && (
          <FactExplorer facts={facts} documents={documents} loading={loading} />
        )}

        {activeTab === 'reconciliation' && (
          <ReconciliationMatrix 
            relationships={relationships} 
            loading={loading}
            onTriggerReconciliation={handleTriggerReconcile}
          />
        )}

        {activeTab === 'documents' && (
          <DocumentManager 
            documents={documents} 
            loading={loading}
            onUploadSuccess={handleUpload}
            onDeleteDocument={handleDeleteRequest}
            onRefresh={loadAllData}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/60 py-6 text-xs text-slate-500 bg-slate-950/40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-2.5">
          <div className="flex items-center space-x-2">
            <span className="font-semibold text-slate-400">Superjoin Knowledge Layer</span>
            <span>•</span>
            <span>VIT 2026 Engineering Assignment</span>
          </div>
          <div className="flex items-center space-x-3 text-[11px] text-slate-500">
            <span>FastAPI</span>
            <span>•</span>
            <span>PyMuPDF</span>
            <span>•</span>
            <span>Groq LLaMA 3.3</span>
            <span>•</span>
            <span>React & Tailwind v4</span>
          </div>
        </div>
      </footer>

      {/* API Key Modal */}
      <ApiKeyModal 
        isOpen={keyModalOpen}
        onClose={() => setKeyModalOpen(false)}
        onSaveKey={handleSaveKey}
        currentStatus={status}
      />

      {/* Accessible Alert Dialog */}
      <AlertDialog 
        isOpen={alertDialog.isOpen}
        title={alertDialog.title}
        description={alertDialog.description}
        confirmLabel={alertDialog.confirmLabel}
        intent={alertDialog.intent}
        onConfirm={alertDialog.onConfirm}
        onCancel={() => setAlertDialog(prev => ({ ...prev, isOpen: false }))}
      />

    </div>
  );
}

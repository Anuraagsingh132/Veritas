import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import ShowcaseView from './components/ShowcaseView';
import FactExplorer from './components/FactExplorer';
import ReconciliationMatrix from './components/ReconciliationMatrix';
import DocumentManager from './components/DocumentManager';
import ApiKeyModal from './components/ApiKeyModal';
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

  const handleUpload = async (file) => {
    await uploadDocument(file);
    // Refresh data after brief processing
    setTimeout(loadAllData, 3000);
  };

  const handleDelete = async (docId) => {
    if (confirm('Are you sure you want to remove this document and its associated facts?')) {
      await deleteDocument(docId);
      loadAllData();
    }
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

  const handleReseed = async () => {
    if (confirm('Reset knowledge layer to curated ground-truth starter dataset?')) {
      await reseedData();
      loadAllData();
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      
      {/* Top Navbar */}
      <Navbar 
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        stats={stats}
        status={status}
        onOpenKeyModal={() => setKeyModalOpen(true)}
        onReseed={handleReseed}
      />

      {/* Main Content Area */}
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
            onDeleteDocument={handleDelete}
            onRefresh={loadAllData}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 py-6 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>Superjoin · Fact Knowledge Layer · VIT 2026</span>
          <span>PyMuPDF • Groq LLM • FastAPI • React</span>
        </div>
      </footer>

      {/* API Key Modal */}
      <ApiKeyModal 
        isOpen={keyModalOpen}
        onClose={() => setKeyModalOpen(false)}
        onSaveKey={handleSaveKey}
        currentStatus={status}
      />

    </div>
  );
}

import { useState, useEffect, useRef } from 'react';
import { listDocuments, uploadPDF } from '../lib/api';

interface Doc {
  id: string;
  name: string;
  filename: string;
  status: 'pending' | 'indexing' | 'ready' | 'failed';
  page_count: number;
  created_at: string;
  error_message?: string;
}

export function Sidebar() {
  const [docs, setDocs] = useState<Doc[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Fetch docs on mount and every 5s (polling for status changes)
  useEffect(() => {
    let cancelled = false;

    const fetchDocs = async () => {
      try {
        const data = await listDocuments();
        if (!cancelled) {
          setDocs(data);
          setLoading(false);
        }
      } catch (e: any) {
        if (!cancelled) {
          setError(e.message);
          setLoading(false);
        }
      }
    };

    fetchDocs();
    const interval = setInterval(fetchDocs, 5000);

    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setError('Only PDF files allowed');
      return;
    }

    setUploading(true);
    setError(null);

    try {
      const result = await uploadPDF(file);
      // Insert the new doc optimistically
      setDocs((prev) => [
        {
          id: result.doc_id,
          name: result.filename.replace(/\.pdf$/i, ''),
          filename: result.filename,
          status: 'pending',
          page_count: 0,
          created_at: new Date().toISOString(),
        },
        ...prev,
      ]);
      setSelectedId(result.doc_id);
    } catch (err: any) {
      setError(err.message || 'Upload failed');
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const statusBadge = (doc: Doc) => {
    if (doc.status === 'ready') {
      return (
        <span className="text-xs text-green-700 bg-green-100 px-2 py-0.5 rounded">
          {doc.page_count}p
        </span>
      );
    }
    if (doc.status === 'indexing') {
      return (
        <span className="text-xs text-yellow-700 bg-yellow-100 px-2 py-0.5 rounded flex items-center gap-1">
          <span className="animate-pulse">●</span> indexing
        </span>
      );
    }
    if (doc.status === 'failed') {
      return (
        <span className="text-xs text-red-700 bg-red-100 px-2 py-0.5 rounded">
          failed
        </span>
      );
    }
    return (
      <span className="text-xs text-gray-700 bg-gray-100 px-2 py-0.5 rounded flex items-center gap-1">
        <span className="animate-pulse">●</span> pending
      </span>
    );
  };

  return (
    <aside className="w-64 bg-gray-900 text-white flex flex-col h-screen">
      {/* Header */}
      <div className="p-4 border-b border-gray-800">
        <h1 className="text-lg font-bold">📄 AskAnyPDF</h1>
      </div>

      {/* Upload button */}
      <div className="p-4 border-b border-gray-800">
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          onChange={handleUpload}
          className="hidden"
          disabled={uploading}
        />
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium py-2 px-4 rounded-lg transition-colors"
        >
          {uploading ? '⏳ Uploading...' : '➕ Upload PDF'}
        </button>
        {error && (
          <div className="mt-2 text-xs text-red-300 bg-red-900/30 p-2 rounded">
            {error}
          </div>
        )}
      </div>

      {/* Document list */}
      <div className="flex-1 overflow-y-auto p-2">
        <div className="text-xs text-gray-400 px-2 py-2 uppercase tracking-wide">
          Documents ({docs.length})
        </div>

        {loading && (
          <div className="text-sm text-gray-400 px-2 py-2">Loading...</div>
        )}

        {!loading && docs.length === 0 && (
          <div className="text-sm text-gray-400 px-2 py-4 text-center">
            No documents yet.<br />
            Upload one to get started.
          </div>
        )}

        {docs.map((doc) => (
          <button
            key={doc.id}
            onClick={() => setSelectedId(doc.id)}
            className={`w-full text-left px-3 py-2 rounded-lg mb-1 transition-colors ${
              selectedId === doc.id
                ? 'bg-blue-600 text-white'
                : 'hover:bg-gray-800 text-gray-200'
            }`}
          >
            <div className="flex items-center justify-between gap-2">
              <span className="text-sm truncate flex-1" title={doc.name}>
                {doc.name}
              </span>
              {statusBadge(doc)}
            </div>
            {doc.status === 'failed' && doc.error_message && (
              <div className="text-xs text-red-300 mt-1 truncate" title={doc.error_message}>
                {doc.error_message}
              </div>
            )}
          </button>
        ))}
      </div>

      {/* Footer */}
      <div className="p-3 border-t border-gray-800 text-xs text-gray-500">
        Powered by MHier-RAG
      </div>
    </aside>
  );
}
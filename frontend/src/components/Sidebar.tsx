import { useState, useEffect, useRef, useCallback } from 'react';
import { listDocuments, uploadPDF, deleteDocument } from '../lib/api';
import { ProgressBar } from './ProgressBar';
import { supabase } from '../lib/supabase';

interface Doc {
  id: string;
  name: string;
  filename: string;
  status: 'pending' | 'indexing' | 'ready' | 'failed';
  page_count: number;
  created_at: string;
  error_message?: string;
  progress?: number;
}

interface SidebarProps {
  selectedId: string | null;
  onSelect: (id: string, name: string) => void;
  onDelete: (id: string) => void;
}

export function Sidebar({ selectedId, onSelect, onDelete }: SidebarProps) {
  const [docs, setDocs] = useState<Doc[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [signedOut, setSignedOut] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const deletedIdsRef = useRef<Set<string>>(new Set());

  const refreshDocs = useCallback(async () => {
    if (signedOut) return;

    try {
      const data: any[] = await listDocuments();
      const filtered = data.filter((d) => !deletedIdsRef.current.has(d.id));

      setDocs((prev) => {
        return filtered.map((fresh) => {
          const existing = prev.find((p) => p.id === fresh.id);
          const progress = (() => {
            if (fresh.status === 'ready') return 100;
            if (fresh.status === 'failed') return existing?.progress ?? 0;
            if (fresh.status === 'indexing') return Math.min(existing?.progress ?? 30, 95);
            return existing?.progress ?? 5;
          })();
          return { ...fresh, progress };
        });
      });
      setLoading(false);
      setError(null);
    } catch (e: any) {
      if (
        e.message?.includes('401') ||
        e.message?.includes('Not authenticated') ||
        e.message?.includes('Session expired')
      ) {
        console.warn('[auth] Session expired, signing out');
        setSignedOut(true);
        await supabase.auth.signOut();
        return;
      }
      setError(e.message);
      setLoading(false);
    }
  }, [signedOut]);

  useEffect(() => {
    refreshDocs();
    const interval = setInterval(refreshDocs, 3000);
    return () => clearInterval(interval);
  }, [refreshDocs]);

  useEffect(() => {
    const ticking = setInterval(() => {
      setDocs((prev) =>
        prev.map((d) => {
          if (d.status === 'indexing') {
            const current = d.progress ?? 30;
            const next = current + (95 - current) * 0.08;
            return { ...d, progress: Math.min(next, 95) };
          }
          return d;
        })
      );
    }, 2000);
    return () => clearInterval(ticking);
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

    const tempId = `temp-${Date.now()}`;
    const optimisticDoc: Doc = {
      id: tempId,
      name: file.name.replace(/\.pdf$/i, ''),
      filename: file.name,
      status: 'pending',
      page_count: 0,
      created_at: new Date().toISOString(),
      progress: 5,
    };
    setDocs((prev) => [optimisticDoc, ...prev]);

    try {
      const result = await uploadPDF(file);
      setDocs((prev) =>
        prev.map((d) =>
          d.id === tempId ? { ...d, id: result.doc_id, progress: 30 } : d
        )
      );
      await refreshDocs();
    } catch (err: any) {
      setError(err.message || 'Upload failed');
      setDocs((prev) => prev.filter((d) => d.id !== tempId));
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDelete = async (doc: Doc, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm(`Delete "${doc.name}"? This cannot be undone.`)) return;

    setDeletingId(doc.id);
    deletedIdsRef.current.add(doc.id);
    setDocs((prev) => prev.filter((d) => d.id !== doc.id));
    onDelete(doc.id);

    try {
      await deleteDocument(doc.id);
    } catch (err: any) {
      deletedIdsRef.current.delete(doc.id);
      setError(`Delete failed: ${err.message}`);
      await refreshDocs();
    } finally {
      setDeletingId(null);
    }
  };

  const statusBadge = (doc: Doc) => {
    if (doc.status === 'ready') {
      return (
        <span className="text-xs text-green-400 bg-green-900/40 px-2 py-0.5 rounded whitespace-nowrap">
          {doc.page_count}p
        </span>
      );
    }
    if (doc.status === 'indexing') {
      return (
        <span className="text-xs text-yellow-400 bg-yellow-900/40 px-2 py-0.5 rounded whitespace-nowrap">
          indexing
        </span>
      );
    }
    if (doc.status === 'failed') {
      return (
        <span className="text-xs text-red-400 bg-red-900/40 px-2 py-0.5 rounded whitespace-nowrap">
          failed
        </span>
      );
    }
    return (
      <span className="text-xs text-gray-400 bg-gray-800 px-2 py-0.5 rounded whitespace-nowrap">
        pending
      </span>
    );
  };

  return (
    <aside className="w-72 bg-gray-900 text-white flex flex-col h-screen flex-shrink-0">
      <div className="p-4 border-b border-gray-800 flex-shrink-0">
        <h1 className="text-lg font-bold">📄 AskAnyPDF</h1>
      </div>

      <div className="p-4 border-b border-gray-800 flex-shrink-0">
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

      <div className="flex-1 overflow-y-auto p-2">
        <div className="text-xs text-gray-400 px-2 py-2 uppercase tracking-wide">
          Documents ({docs.length})
        </div>

        {loading && <div className="text-sm text-gray-400 px-2 py-2">Loading...</div>}

        {!loading && docs.length === 0 && (
          <div className="text-sm text-gray-400 px-2 py-4 text-center">
            No documents yet.
            <br />
            Upload one to get started.
          </div>
        )}

        {docs.map((doc) => {
          const showProgress =
            doc.status === 'indexing' ||
            doc.status === 'pending' ||
            doc.status === 'failed';
          const isDeleting = deletingId === doc.id;

          return (
            <div
              key={doc.id}
              className={`group relative w-full text-left px-3 py-2 rounded-lg mb-1 transition-colors ${
                selectedId === doc.id && doc.status === 'ready'
                  ? 'bg-blue-600 text-white'
                  : doc.status === 'ready'
                  ? 'hover:bg-gray-800 text-gray-200 cursor-pointer'
                  : 'text-gray-400 opacity-90'
              } ${isDeleting ? 'opacity-50' : ''}`}
              onClick={() => doc.status === 'ready' && onSelect(doc.id, doc.name)}
              role={doc.status === 'ready' ? 'button' : undefined}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="text-sm truncate flex-1" title={doc.name}>
                  {doc.name}
                </span>
                {statusBadge(doc)}
                <button
                  onClick={(e) => handleDelete(doc, e)}
                  disabled={isDeleting}
                  className="opacity-0 group-hover:opacity-100 transition-opacity text-red-400 hover:text-red-300 disabled:opacity-50"
                  title="Delete document"
                  aria-label="Delete document"
                >
                  {isDeleting ? '⏳' : '🗑️'}
                </button>
              </div>
              {showProgress && (
                <div className="flex items-center gap-2 mt-1">
                  <ProgressBar progress={doc.progress ?? 0} status={doc.status} />
                  <span className="text-xs text-gray-400 w-8 text-right">
                    {Math.round(doc.progress ?? 0)}%
                  </span>
                </div>
              )}
              {doc.status === 'failed' && doc.error_message && (
                <div className="text-xs text-red-300 mt-1 truncate" title={doc.error_message}>
                  {doc.error_message}
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className="p-3 border-t border-gray-800 text-xs text-gray-500 flex-shrink-0">
        Powered by MHier-RAG
      </div>
    </aside>
  );
}
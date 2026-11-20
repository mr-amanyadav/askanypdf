import { useState } from 'react';
import { AuthProvider, useAuth } from './lib/AuthContext';
import { Login } from './pages/Login';
import { Sidebar } from './components/Sidebar';
import { ChatWindow } from './components/ChatWindow';

function AppContent() {
  const { user, loading, signOut } = useAuth();
  const [selectedDoc, setSelectedDoc] = useState<{ id: string; name: string } | null>(null);

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center">
        <div className="text-gray-500">Loading...</div>
      </div>
    );
  }

  if (!user) return <Login />;

  return (
    <div className="h-screen flex bg-gray-50 overflow-hidden">
      <Sidebar
        selectedId={selectedDoc?.id ?? null}
        onSelect={(id, name) => setSelectedDoc({ id, name })}
        onDelete={(id) => {
          if (selectedDoc?.id === id) setSelectedDoc(null);
        }}
      />
      <div className="flex-1 flex flex-col overflow-hidden min-w-0">
        {selectedDoc ? (
          <ChatWindow
            docId={selectedDoc.id}
            docName={selectedDoc.name}
            onBack={() => setSelectedDoc(null)}
          />
        ) : (
          <div className="flex-1 flex flex-col">
            <header className="bg-white border-b border-gray-200 px-6 py-3 flex-shrink-0">
              <div className="flex items-center justify-between">
                <h1 className="text-lg font-semibold text-gray-900">💬 Chat</h1>
                <div className="flex items-center gap-4">
                  <span className="text-sm text-gray-600">{user.email}</span>
                  <button
                    onClick={signOut}
                    className="text-sm text-gray-500 hover:text-gray-700"
                  >
                    Sign out
                  </button>
                </div>
              </div>
            </header>
            <div className="flex-1 flex items-center justify-center p-8 overflow-auto">
              <div className="text-center">
                <div className="text-6xl mb-4">📄</div>
                <h2 className="text-2xl font-semibold text-gray-900 mb-2">
                  Select a document
                </h2>
                <p className="text-gray-500">
                  Upload a PDF from the sidebar, or click an existing one to start chatting.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
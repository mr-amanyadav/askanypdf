import { AuthProvider, useAuth } from './lib/AuthContext';
import { Login } from './pages/Login';

function AppContent() {
  const { user, loading, signOut } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-500">Loading...</div>
      </div>
    );
  }

  if (!user) return <Login />;

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between max-w-7xl mx-auto">
          <h1 className="text-xl font-bold text-gray-900">📄 AskAnyPDF</h1>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">{user.email}</span>
            <button onClick={signOut} className="text-sm text-gray-500 hover:text-gray-700">
              Sign out
            </button>
          </div>
        </div>
      </header>
      <main className="max-w-7xl mx-auto p-6">
        <div className="bg-white rounded-xl shadow-sm p-8 text-center">
          <h2 className="text-2xl font-semibold text-gray-900 mb-2">
            ✅ Logged in as {user.email}
          </h2>
          <p className="text-gray-500">Next: document list + upload + chat</p>
        </div>
      </main>
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
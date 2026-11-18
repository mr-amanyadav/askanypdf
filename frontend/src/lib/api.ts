import { supabase } from './supabase';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function getAuthHeader(): Promise<{ Authorization: string }> {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  if (!token) throw new Error('Not authenticated');
  return { Authorization: `Bearer ${token}` };
}

export async function listDocuments() {
  const headers = await getAuthHeader();
  const res = await fetch(`${API_URL}/documents/`, { headers });
  if (!res.ok) throw new Error(`Failed: ${res.status}`);
  return res.json();
}

export async function uploadPDF(file: File) {
  const headers = await getAuthHeader();
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_URL}/documents/upload`, {
    method: 'POST',
    headers,
    body: formData,
  });
  if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
  return res.json();
}

export async function getDocument(docId: string) {
  const headers = await getAuthHeader();
  const res = await fetch(`${API_URL}/documents/${docId}`, { headers });
  if (!res.ok) throw new Error(`Failed: ${res.status}`);
  return res.json();
}

export async function deleteDocument(docId: string) {
  const headers = await getAuthHeader();
  const res = await fetch(`${API_URL}/documents/${docId}`, { method: 'DELETE', headers });
  if (!res.ok) throw new Error(`Delete failed: ${res.status}`);
  return res.json();
}

export { API_URL };
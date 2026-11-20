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
  const res = await fetch(`${API_URL}/documents/${docId}`, {
    method: 'DELETE',
    headers,
  });
  if (!res.ok) throw new Error(`Delete failed: ${res.status}`);
  return res.json();
}

export interface StreamEvent {
  type: 'token' | 'done' | 'error';
  content?: string;
  answer?: string;
  top_pages?: number[];
  num_candidates?: number;
  message?: string;
}

export async function* streamAnswer(
  docId: string,
  question: string
): AsyncGenerator<StreamEvent> {
  const headers = await getAuthHeader();
  const res = await fetch(`${API_URL}/query/ask`, {
    method: 'POST',
    headers: { ...headers, 'Content-Type': 'application/json' },
    body: JSON.stringify({ doc_id: docId, question }),
  });

  if (!res.ok || !res.body) {
    throw new Error(`Query failed: ${res.status}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (!line.startsWith('data: ')) continue;
      const json = line.slice(6).trim();
      if (!json) continue;
      try {
        yield JSON.parse(json) as StreamEvent;
      } catch {
        // ignore malformed lines
      }
    }
  }
}
export interface ChatMessage {
  id: string;
  chat_id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: { top_pages?: number[]; num_candidates?: number } | null;
  metadata?: any;
  created_at: string;
}

export async function getChatMessages(docId: string): Promise<ChatMessage[]> {
  const headers = await getAuthHeader();
  const res = await fetch(`${API_URL}/chats/${docId}/messages`, { headers });
  if (!res.ok) throw new Error(`Failed: ${res.status}`);
  return res.json();
}

export async function saveMessage(
  docId: string,
  role: 'user' | 'assistant',
  content: string,
  citations?: { top_pages: number[]; num_candidates: number } | null
): Promise<ChatMessage> {
  const headers = await getAuthHeader();
  const res = await fetch(`${API_URL}/chats/${docId}/messages`, {
    method: 'POST',
    headers: { ...headers, 'Content-Type': 'application/json' },
    body: JSON.stringify({ role, content, citations }),
  });
  if (!res.ok) throw new Error(`Save failed: ${res.status}`);
  return res.json();
}

export { API_URL };
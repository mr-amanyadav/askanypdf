import { useState, useRef, useEffect } from 'react';
import { streamAnswer } from '../lib/api';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  topPages?: number[];
  numCandidates?: number;
  streaming?: boolean;
}

interface Props {
  docId: string;
  docName: string;
}

export function ChatWindow({ docId, docName }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMessages([]);
    setInput('');
  }, [docId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const question = input.trim();
    if (!question || busy) return;

    setInput('');
    setBusy(true);

    setMessages((prev) => [
      ...prev,
      { role: 'user', content: question },
      { role: 'assistant', content: '', streaming: true },
    ]);

    try {
      let assistantContent = '';
      let topPages: number[] | undefined;
      let numCandidates: number | undefined;

      for await (const event of streamAnswer(docId, question)) {
        if (event.type === 'token' && event.content) {
          assistantContent += event.content;
          setMessages((prev) => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            updated[updated.length - 1] = { ...last, content: assistantContent };
            return updated;
          });
        } else if (event.type === 'done') {
          topPages = event.top_pages;
          numCandidates = event.num_candidates;
          setMessages((prev) => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            updated[updated.length - 1] = {
              ...last,
              streaming: false,
              topPages,
              numCandidates,
            };
            return updated;
          });
        } else if (event.type === 'error') {
          throw new Error(event.message || 'Stream error');
        }
      }
    } catch (err: any) {
      setMessages((prev) => {
        const updated = [...prev];
        const last = updated[updated.length - 1];
        updated[updated.length - 1] = {
          ...last,
          content: `❌ Error: ${err.message}`,
          streaming: false,
        };
        return updated;
      });
    } finally {
      setBusy(false);
    }
  };

  const formatMessage = (text: string) => {
    const parts = text.split(/(\*\*[^*]+\*\*)/g);
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i}>{part.slice(2, -2)}</strong>;
      }
      return <span key={i}>{part}</span>;
    });
  };

  return (
    <div className="flex-1 flex flex-col h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-gray-900">{docName}</h1>
          <p className="text-xs text-gray-500">Ask questions about this document</p>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto px-6 py-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-400 mt-16">
            <div className="text-5xl mb-3">💬</div>
            <p className="text-lg">Ask your first question</p>
            <p className="text-sm mt-2">Example: "What is this document about?"</p>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`mb-4 flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-3xl rounded-2xl px-4 py-3 ${
                msg.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white border border-gray-200 text-gray-900 shadow-sm'
              }`}
            >
              <div className="whitespace-pre-wrap text-sm leading-relaxed">
                {formatMessage(msg.content)}
                {msg.streaming && (
                  <span className="inline-block w-1.5 h-4 bg-gray-400 ml-0.5 animate-pulse" />
                )}
              </div>

              {msg.topPages && msg.topPages.length > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-200 text-xs text-gray-500">
                  <div className="flex flex-wrap gap-2">
                    <span className="font-medium">📄 Cited pages:</span>
                    {msg.topPages.slice(0, 5).map((p) => (
                      <span
                        key={p}
                        className="bg-gray-100 px-2 py-0.5 rounded font-mono"
                      >
                        p.{p}
                      </span>
                    ))}
                    {msg.numCandidates !== undefined && (
                      <span className="text-gray-400">({msg.numCandidates} candidates)</span>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={handleSubmit} className="bg-white border-t border-gray-200 px-6 py-4">
        <div className="flex gap-2 max-w-4xl mx-auto">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={busy ? 'Thinking...' : 'Ask a question about this document...'}
            disabled={busy}
            className="flex-1 px-4 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
          />
          <button
            type="submit"
            disabled={busy || !input.trim()}
            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium px-6 py-2.5 rounded-xl transition-colors"
          >
            {busy ? '⏳' : 'Ask'}
          </button>
        </div>
      </form>
    </div>
  );
}
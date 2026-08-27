import React, { useState } from 'react';
import { Sparkles, X, Send, Bot, User, Loader2, ArrowRight } from 'lucide-react';

export default function AICopilotModal({ isOpen, onClose, stats }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: `Hello! I am Lifeline Copilot, your autonomous fintech revenue intelligence assistant. I am actively monitoring your Razorpay payment failures, Groq AI interventions, and compliance stopping rules. How can I help you optimize recovery today?`
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const presetQuestions = [
    "What is our net recovery lift over blind retries?",
    "Why are transient bank outages handled differently than card expiration?",
    "How does our deterministic stopping rule protect against compliance penalties?",
    "Summarize current recovered vs lost revenue."
  ];

  const handleSend = async (questionText) => {
    const q = questionText || input;
    if (!q.trim() || loading) return;

    const userMsg = { role: 'user', content: q };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await fetch('/api/ai-copilot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: q })
      });
      const data = await res.json();
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: data.answer || "No response received." }
      ]);
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `Error communicating with AI engine: ${e.message}` }
      ]);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md">
      <div className="fintech-card w-full max-w-2xl rounded-2xl shadow-2xl border border-purple-500/30 flex flex-col h-[600px] overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-800 bg-slate-900/90">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-gradient-to-tr from-purple-600 to-indigo-600 text-white shadow-md shadow-purple-500/20">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-1.5 font-sans">
                Lifeline AI Copilot
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300 font-mono border border-purple-500/30">
                  Groq Intelligence
                </span>
              </h3>
              <p className="text-xs text-slate-400">Autonomous recovery insights & strategy consultant</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Chat History */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs">
          {messages.map((m, i) => (
            <div
              key={i}
              className={`flex items-start gap-3 ${
                m.role === 'user' ? 'flex-row-reverse' : ''
              }`}
            >
              <div
                className={`p-1.5 rounded-lg flex-shrink-0 ${
                  m.role === 'user'
                    ? 'bg-sky-600 text-white'
                    : 'bg-purple-600/20 text-purple-300 border border-purple-500/30'
                }`}
              >
                {m.role === 'user' ? <User className="w-3.5 h-3.5" /> : <Bot className="w-3.5 h-3.5 text-purple-300" />}
              </div>
              <div
                className={`p-3.5 rounded-2xl max-w-[84%] leading-relaxed ${
                  m.role === 'user'
                    ? 'bg-sky-600 text-white font-medium rounded-tr-none'
                    : 'bg-slate-900/90 text-slate-200 border border-slate-800 rounded-tl-none'
                }`}
              >
                {m.content}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex items-center gap-3">
              <div className="p-1.5 rounded-lg bg-purple-600/20 text-purple-300 border border-purple-500/30">
                <Bot className="w-3.5 h-3.5" />
              </div>
              <div className="p-3.5 rounded-2xl bg-slate-900/90 text-slate-400 border border-slate-800 flex items-center gap-2">
                <Loader2 className="w-3.5 h-3.5 animate-spin text-purple-400" />
                <span>Consulting Groq LLM inference...</span>
              </div>
            </div>
          )}
        </div>

        {/* Presets */}
        <div className="px-4 py-2 bg-slate-900/40 border-t border-slate-800 flex items-center gap-2 overflow-x-auto">
          {presetQuestions.map((pq, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(pq)}
              className="flex-shrink-0 px-2.5 py-1 rounded-lg bg-slate-800/60 hover:bg-purple-600/20 hover:text-purple-300 hover:border-purple-500/40 text-[11px] text-slate-400 border border-slate-700/60 transition-all flex items-center gap-1 font-sans"
            >
              <span>{pq}</span>
              <ArrowRight className="w-2.5 h-2.5" />
            </button>
          ))}
        </div>

        {/* Input bar */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="p-3 border-t border-slate-800 bg-slate-950 flex items-center gap-2"
        >
          <input
            type="text"
            placeholder="Ask about payment recovery, compliance stopping rules, or AI decisions..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            className="flex-1 px-4 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-purple-500 transition-colors"
          />
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="p-2.5 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white disabled:opacity-40 transition-all fintech-button"
          >
            <Send className="w-3.5 h-3.5" />
          </button>
        </form>

      </div>
    </div>
  );
}

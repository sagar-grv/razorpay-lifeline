import React, { useState, useEffect, useRef } from 'react';
import { Terminal, Trash2, Pause, Play, ChevronDown, ChevronUp, Copy, Check } from 'lucide-react';

export default function LiveTerminal({ isOpen, onClose }) {
  const [logs, setLogs] = useState([]);
  const [isPaused, setIsPaused] = useState(false);
  const [copied, setCopied] = useState(false);
  const terminalEndRef = useRef(null);

  useEffect(() => {
    // Fetch initial logs
    fetch('/api/logs')
      .then((res) => res.json())
      .then((initialLogs) => {
        if (Array.isArray(initialLogs)) setLogs(initialLogs);
      })
      .catch(() => {});

    // Open SSE stream
    const eventSource = new EventSource('/api/logs/stream');
    eventSource.onmessage = (event) => {
      if (isPaused) return;
      try {
        const logEntry = JSON.parse(event.data);
        setLogs((prev) => [...prev.slice(-150), logEntry]);
      } catch (e) {}
    };

    return () => {
      eventSource.close();
    };
  }, [isPaused]);

  useEffect(() => {
    if (!isPaused && terminalEndRef.current) {
      terminalEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, isPaused]);

  const handleCopyLogs = () => {
    const raw = logs.map((l) => `[${l.timestamp}] [${l.level}] ${l.message}`).join('\n');
    navigator.clipboard.writeText(raw);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!isOpen) return null;

  const getLevelColor = (level) => {
    switch (level) {
      case 'SUCCESS':
        return 'text-emerald-400 font-semibold';
      case 'WARN':
        return 'text-amber-400 font-semibold';
      case 'ERROR':
        return 'text-rose-400 font-bold';
      default:
        return 'text-cyan-400';
    }
  };

  return (
    <div className="glass-panel border-t border-slate-700/80 bg-[#070B14]/95 rounded-t-2xl shadow-2xl transition-all duration-300">
      {/* Terminal Title Bar */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-slate-900/80 border-b border-slate-800 rounded-t-2xl">
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 mr-2">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500/80" />
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500/80" />
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500/80" />
          </div>
          <Terminal className="w-3.5 h-3.5 text-blue-400" />
          <span className="text-xs font-mono font-semibold text-slate-200">
            Real-Time Engine Telemetry (Uvicorn / AI Agent Stream)
          </span>
          <span className="text-[10px] px-1.5 py-0.2 rounded bg-emerald-500/10 text-emerald-400 font-mono border border-emerald-500/20 animate-pulse">
            LIVE SSE
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsPaused(!isPaused)}
            className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
            title={isPaused ? "Resume Log Stream" : "Pause Log Stream"}
          >
            {isPaused ? <Play className="w-3.5 h-3.5 text-emerald-400" /> : <Pause className="w-3.5 h-3.5" />}
          </button>
          <button
            onClick={handleCopyLogs}
            className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
            title="Copy Logs"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
          </button>
          <button
            onClick={() => setLogs([])}
            className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-rose-400 transition-colors"
            title="Clear Logs"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={onClose}
            className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
            title="Close Terminal Drawer"
          >
            <ChevronDown className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Terminal Content Window */}
      <div className="h-60 overflow-y-auto p-4 font-mono text-xs text-slate-300 space-y-1 bg-black/40">
        {logs.length === 0 ? (
          <div className="text-slate-600 italic">Waiting for incoming engine telemetry...</div>
        ) : (
          logs.map((log, index) => (
            <div key={index} className="flex items-start gap-2 leading-relaxed">
              <span className="text-slate-500 select-none text-[10px] pt-0.5">{log.timestamp}</span>
              <span className={`text-[10px] uppercase font-bold select-none px-1 rounded bg-slate-900 border border-slate-800 ${getLevelColor(log.level)}`}>
                {log.level}
              </span>
              <span className="text-slate-300 break-all">{log.message}</span>
            </div>
          ))
        )}
        <div ref={terminalEndRef} />
      </div>
    </div>
  );
}

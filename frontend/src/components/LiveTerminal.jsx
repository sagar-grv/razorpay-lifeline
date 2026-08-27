import React, { useState, useEffect, useRef } from 'react';
import { Terminal, Trash2, Pause, Play, ChevronDown, Copy, Check, Filter, Search } from 'lucide-react';

export default function LiveTerminal({ isOpen, onClose }) {
  const [logs, setLogs] = useState([]);
  const [isPaused, setIsPaused] = useState(false);
  const [copied, setCopied] = useState(false);
  const [filterLevel, setFilterLevel] = useState('ALL');
  const [searchLog, setSearchLog] = useState('');
  const terminalEndRef = useRef(null);

  useEffect(() => {
    fetch('/api/logs')
      .then((res) => res.json())
      .then((initialLogs) => {
        if (Array.isArray(initialLogs)) setLogs(initialLogs);
      })
      .catch(() => {});

    const eventSource = new EventSource('/api/logs/stream');
    eventSource.onmessage = (event) => {
      if (isPaused) return;
      try {
        const logEntry = JSON.parse(event.data);
        setLogs((prev) => [...prev.slice(-200), logEntry]);
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

  const filteredLogs = logs.filter((l) => {
    const matchesLevel = filterLevel === 'ALL' || l.level === filterLevel;
    const matchesSearch = !searchLog || l.message.toLowerCase().includes(searchLog.toLowerCase());
    return matchesLevel && matchesSearch;
  });

  const getLevelBadge = (level) => {
    switch (level) {
      case 'SUCCESS':
        return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30';
      case 'WARN':
        return 'text-amber-400 bg-amber-500/10 border-amber-500/30';
      case 'ERROR':
        return 'text-rose-400 bg-rose-500/10 border-rose-500/30';
      default:
        return 'text-sky-400 bg-sky-500/10 border-sky-500/30';
    }
  };

  return (
    <div className="fintech-card border-t border-slate-700 bg-[#060910]/95 shadow-2xl transition-all duration-300">
      
      {/* Title Bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between px-4 py-2.5 bg-slate-900/90 border-b border-slate-800 rounded-t-2xl gap-2">
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 mr-2">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500/80" />
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500/80" />
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500/80" />
          </div>
          <Terminal className="w-3.5 h-3.5 text-sky-400" />
          <span className="text-xs font-mono font-semibold text-slate-200">
            Real-Time Engine Telemetry (FastAPI / Groq Stream)
          </span>
          <span className="text-[10px] px-1.5 py-0.2 rounded bg-emerald-500/10 text-emerald-400 font-mono border border-emerald-500/20 animate-pulse">
            LIVE SSE
          </span>
        </div>

        {/* Filter and Actions Bar */}
        <div className="flex items-center gap-2 w-full sm:w-auto justify-between sm:justify-end">
          {/* Level Filter */}
          <div className="flex items-center gap-1 text-[10px] font-mono bg-slate-950 p-1 rounded-lg border border-slate-800">
            {['ALL', 'INFO', 'SUCCESS', 'WARN', 'ERROR'].map((lvl) => (
              <button
                key={lvl}
                onClick={() => setFilterLevel(lvl)}
                className={`px-1.5 py-0.5 rounded ${
                  filterLevel === lvl ? 'bg-sky-600 text-white font-bold' : 'text-slate-400 hover:text-white'
                }`}
              >
                {lvl}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-1">
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
              title="Close Terminal"
            >
              <ChevronDown className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Terminal Content Window */}
      <div className="h-64 overflow-y-auto p-4 font-mono text-xs text-slate-300 space-y-1 bg-black/50">
        {filteredLogs.length === 0 ? (
          <div className="text-slate-600 italic">Waiting for incoming engine telemetry...</div>
        ) : (
          filteredLogs.map((log, index) => (
            <div key={index} className="flex items-start gap-2 leading-relaxed">
              <span className="text-slate-500 select-none text-[10px] pt-0.5">{log.timestamp}</span>
              <span className={`text-[9px] uppercase font-bold select-none px-1.5 py-0.2 rounded border ${getLevelBadge(log.level)}`}>
                {log.level}
              </span>
              <span className="text-slate-200 break-all">{log.message}</span>
            </div>
          ))
        )}
        <div ref={terminalEndRef} />
      </div>
    </div>
  );
}

import React, { useState } from 'react';
import { Activity, ShieldCheck, Copy, Check, Terminal, Sparkles, RefreshCw, Radio } from 'lucide-react';

export default function Header({ stats, onRefresh, isTerminalOpen, setIsTerminalOpen, onOpenCopilot, webhookUrl }) {
  const [copied, setCopied] = useState(false);

  const handleCopyWebhook = () => {
    navigator.clipboard.writeText(`${webhookUrl}/webhook/razorpay`);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <header className="sticky top-0 z-30 w-full border-b border-slate-800/80 bg-[#090D16]/80 backdrop-blur-xl px-4 lg:px-8 py-3.5">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        
        {/* Brand & Logo */}
        <div className="flex items-center gap-3">
          <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-cyan-500 shadow-lg shadow-blue-500/20 ring-1 ring-white/20">
            <Activity className="w-5 h-5 text-white animate-pulse" />
            <span className="absolute -top-1 -right-1 flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
            </span>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-1.5">
                Razorpay <span className="bg-gradient-to-r from-blue-400 via-cyan-300 to-indigo-300 bg-clip-text text-transparent">Lifeline</span>
              </h1>
              <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">
                v2.0 Autonomous
              </span>
            </div>
            <p className="text-xs text-slate-400">Autonomous AI Payment Recovery & Compliance Engine</p>
          </div>
        </div>

        {/* Center / Status info */}
        <div className="flex items-center gap-3 flex-wrap">
          {/* Active AI Model Badge */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900/80 border border-slate-700/60 shadow-inner">
            <Radio className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
            <span className="text-xs font-mono font-medium text-slate-300">
              {stats?.model_name || "Groq Inference Engine"}
            </span>
          </div>

          {/* Webhook Copy Pill */}
          <div className="hidden xl:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900/80 border border-slate-700/60 text-xs font-mono text-slate-300">
            <ShieldCheck className="w-3.5 h-3.5 text-blue-400" />
            <span className="truncate max-w-[220px]">{webhookUrl}/webhook/razorpay</span>
            <button
              onClick={handleCopyWebhook}
              className="ml-1 text-slate-400 hover:text-white transition-colors"
              title="Copy Razorpay Webhook URL"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            </button>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2">
          {/* AI Copilot Button */}
          <button
            onClick={onOpenCopilot}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white text-xs font-medium shadow-lg shadow-indigo-500/25 transition-all duration-200 active:scale-95 border border-purple-400/30"
          >
            <Sparkles className="w-3.5 h-3.5 text-purple-200" />
            <span>AI Copilot</span>
          </button>

          {/* Terminal Logs Toggle */}
          <button
            onClick={() => setIsTerminalOpen(!isTerminalOpen)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 border ${
              isTerminalOpen
                ? 'bg-blue-600/20 text-blue-400 border-blue-500/40 shadow-sm shadow-blue-500/20'
                : 'bg-slate-800/80 hover:bg-slate-700/80 text-slate-300 border-slate-700'
            }`}
          >
            <Terminal className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Live Logs</span>
          </button>

          {/* Refresh Button */}
          <button
            onClick={onRefresh}
            className="p-2 rounded-lg bg-slate-800/80 hover:bg-slate-700/80 text-slate-300 hover:text-white transition-all border border-slate-700"
            title="Refresh Data"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>

      </div>
    </header>
  );
}

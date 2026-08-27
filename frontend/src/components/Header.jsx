import React, { useState } from 'react';
import { Activity, ShieldCheck, Copy, Check, Terminal, Sparkles, RefreshCw, Command, Radio } from 'lucide-react';

export default function Header({ stats, onRefresh, isTerminalOpen, setIsTerminalOpen, onOpenCopilot, onOpenCmdk, webhookUrl }) {
  const [copied, setCopied] = useState(false);

  const handleCopyWebhook = () => {
    navigator.clipboard.writeText(`${webhookUrl}/webhook/razorpay`);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <header className="sticky top-0 z-30 w-full border-b border-slate-800/80 bg-[#060911]/90 backdrop-blur-2xl px-4 lg:px-8 py-3">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        
        {/* Brand & System Status */}
        <div className="flex items-center gap-3 w-full md:w-auto justify-between md:justify-start">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-9 h-9 rounded-xl bg-sky-600 shadow-md shadow-sky-600/20 border border-sky-400/30">
              <Activity className="w-4 h-4 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-base font-bold tracking-tight text-white">
                  Razorpay <span className="text-sky-400">Lifeline</span>
                </span>
                <span className="text-[9px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-sky-500/10 text-sky-400 border border-sky-500/20 font-numeric">
                  Autonomous Engine
                </span>
              </div>
              <p className="text-xs text-slate-400">Closed-Loop Recovery & Compliance Guard</p>
            </div>
          </div>

          {/* Mobile Cmd+K trigger */}
          <button
            onClick={() => onOpenCmdk(true)}
            className="md:hidden p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 tap-target"
          >
            <Command className="w-4 h-4" />
          </button>
        </div>

        {/* Center: Model & Webhook URL */}
        <div className="hidden md:flex items-center gap-2.5">
          {/* Active AI Model Badge */}
          <div className="flex items-center gap-2 px-3 py-1 rounded-lg bg-slate-900 border border-slate-800 text-xs font-numeric">
            <Radio className="w-3 h-3 text-emerald-400 animate-pulse" />
            <span className="text-slate-300 font-medium text-[11px]">
              {stats?.model_name || "Groq Llama-3 Engine"}
            </span>
          </div>

          {/* Webhook Copy Pill */}
          <div className="hidden lg:flex items-center gap-2 px-3 py-1 rounded-lg bg-slate-900 border border-slate-800 text-[11px] font-numeric text-slate-300">
            <ShieldCheck className="w-3.5 h-3.5 text-sky-400" />
            <span className="truncate max-w-[210px]">{webhookUrl}/webhook/razorpay</span>
            <button
              onClick={handleCopyWebhook}
              className="text-slate-400 hover:text-white transition-colors"
              title="Copy Webhook Endpoint"
            >
              {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
            </button>
          </div>

          {/* Cmd+K Quick Palette Trigger */}
          <button
            onClick={() => onOpenCmdk(true)}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-[11px] text-slate-400 hover:text-slate-200 transition-all font-numeric tap-target"
            title="Open Command Palette"
          >
            <Command className="w-3 h-3 text-slate-400" />
            <span>K</span>
          </button>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2 w-full md:w-auto justify-end">
          {/* AI Copilot Button */}
          <button
            onClick={onOpenCopilot}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold shadow-md shadow-purple-600/20 transition-all tap-target border border-purple-400/30"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>AI Copilot</span>
          </button>

          {/* Terminal Logs Toggle */}
          <button
            onClick={() => setIsTerminalOpen(!isTerminalOpen)}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all tap-target border ${
              isTerminalOpen
                ? 'bg-sky-500/20 text-sky-300 border-sky-500/40'
                : 'bg-slate-900 hover:bg-slate-800 text-slate-300 border-slate-800'
            }`}
          >
            <Terminal className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Telemetry</span>
          </button>

          {/* Refresh Button */}
          <button
            onClick={onRefresh}
            className="p-2 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white transition-all border border-slate-800 tap-target"
            title="Refresh Data"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>

      </div>
    </header>
  );
}

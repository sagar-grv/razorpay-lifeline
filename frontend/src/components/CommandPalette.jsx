import React, { useState, useEffect } from 'react';
import { Search, Sparkles, Terminal, Play, Zap, CreditCard, Smartphone, AlertCircle, ShieldAlert, X, ArrowRight } from 'lucide-react';

export default function CommandPalette({ isOpen, onClose, onOpenCopilot, onOpenTerminal, onSimulatePayment, onSimulateReply, onRunBatch }) {
  const [query, setQuery] = useState('');

  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        onClose(!isOpen);
      }
      if (e.key === 'Escape' && isOpen) {
        onClose(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const actions = [
    {
      id: 'copilot',
      title: 'Ask Lifeline AI Copilot',
      subtitle: 'Open conversational AI assistant for recovery analytics',
      icon: Sparkles,
      color: 'text-purple-400 bg-purple-500/10 border-purple-500/20',
      run: () => {
        onClose(false);
        onOpenCopilot();
      }
    },
    {
      id: 'logs',
      title: 'Open Real-Time Log Inspector',
      subtitle: 'View live streaming Uvicorn, HMAC & AI reasoning logs',
      icon: Terminal,
      color: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
      run: () => {
        onClose(false);
        onOpenTerminal();
      }
    },
    {
      id: 'sim_bank',
      title: 'Simulate: Bank Server Outage',
      subtitle: 'Triggers silent auto-retry (₹1,500)',
      icon: Zap,
      color: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
      run: () => {
        onClose(false);
        onSimulatePayment('bank_server_down', 1500, 'Bank Outage');
      }
    },
    {
      id: 'sim_card',
      title: 'Simulate: Card Expired',
      subtitle: 'Triggers Razorpay Link SMS (₹2,500)',
      icon: CreditCard,
      color: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
      run: () => {
        onClose(false);
        onSimulatePayment('card_expired', 2500, 'Card Expired');
      }
    },
    {
      id: 'sim_upi',
      title: 'Simulate: UPI PIN Blocked',
      subtitle: 'Triggers Nudge & Alternative App Link (₹5,000)',
      icon: Smartphone,
      color: 'text-purple-400 bg-purple-500/10 border-purple-500/20',
      run: () => {
        onClose(false);
        onSimulatePayment('upi_pin_blocked', 5000, 'UPI Blocked');
      }
    },
    {
      id: 'sim_funds',
      title: 'Simulate: Insufficient Funds',
      subtitle: 'Triggers Polite Salary Nudge + Link (₹1,200)',
      icon: AlertCircle,
      color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
      run: () => {
        onClose(false);
        onSimulatePayment('insufficient_funds', 1200, 'Insufficient Funds');
      }
    },
    {
      id: 'sim_stop',
      title: 'Simulate: Customer "STOP" Reply',
      subtitle: 'Tests deterministic compliance stopping rule (escalates to human)',
      icon: ShieldAlert,
      color: 'text-rose-400 bg-rose-500/10 border-rose-500/20',
      run: () => {
        onClose(false);
        onSimulateReply('STOP PLEASE', 'stop');
      }
    },
    {
      id: 'batch',
      title: 'Run 25-Payment Batch Simulation',
      subtitle: 'Dispatches synthetic failure volume across multiple codes',
      icon: Play,
      color: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20',
      run: () => {
        onClose(false);
        onRunBatch();
      }
    }
  ];

  const filtered = actions.filter((a) =>
    a.title.toLowerCase().includes(query.toLowerCase()) ||
    a.subtitle.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 p-4 bg-black/70 backdrop-blur-md">
      <div className="fintech-card w-full max-w-xl shadow-2xl border border-slate-700/80 overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        
        {/* Search input */}
        <div className="flex items-center px-4 py-3 border-b border-slate-800 bg-slate-900/90">
          <Search className="w-4 h-4 text-slate-400 mr-3" />
          <input
            type="text"
            autoFocus
            placeholder="Type a command or search action (e.g. 'simulate', 'logs', 'copilot')..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="flex-1 bg-transparent border-none text-xs text-white placeholder-slate-500 focus:outline-none"
          />
          <kbd className="px-2 py-0.5 text-[10px] font-mono rounded bg-slate-800 text-slate-400 border border-slate-700">
            ESC
          </kbd>
        </div>

        {/* Action List */}
        <div className="max-h-80 overflow-y-auto p-2 space-y-1">
          {filtered.length === 0 ? (
            <div className="py-8 text-center text-xs text-slate-500">
              No matching commands found.
            </div>
          ) : (
            filtered.map((action) => {
              const Icon = action.icon;
              return (
                <button
                  key={action.id}
                  onClick={action.run}
                  className="w-full flex items-center justify-between p-2.5 rounded-xl hover:bg-slate-800/80 text-left transition-all group"
                >
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg border ${action.color}`}>
                      <Icon className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-xs font-semibold text-white group-hover:text-blue-400 transition-colors">
                        {action.title}
                      </div>
                      <div className="text-[11px] text-slate-400">
                        {action.subtitle}
                      </div>
                    </div>
                  </div>
                  <ArrowRight className="w-3.5 h-3.5 text-slate-600 group-hover:text-slate-300 transition-colors" />
                </button>
              );
            })
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-2 bg-slate-950/80 border-t border-slate-800 flex items-center justify-between text-[11px] text-slate-500 font-mono">
          <span>Navigation: Use mouse or search</span>
          <span>Razorpay Lifeline Command Bar</span>
        </div>

      </div>
    </div>
  );
}

import React from 'react';
import { X, ExternalLink, Sparkles, MessageSquare, ShieldAlert, CheckCircle2, Clock, Smartphone, CreditCard } from 'lucide-react';

export default function PaymentDetailModal({ payment, onClose }) {
  if (!payment) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-md">
      <div className="glass-panel w-full max-w-lg rounded-2xl shadow-2xl border border-blue-500/30 overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-800 bg-slate-900/80">
          <div>
            <span className="text-[10px] uppercase font-bold tracking-wider text-blue-400 font-mono">
              Transaction Forensic Detail
            </span>
            <h3 className="text-base font-bold text-white font-mono">{payment.payment_id}</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4 text-xs">
          
          {/* Key attributes grid */}
          <div className="grid grid-cols-2 gap-3 p-3.5 rounded-xl bg-slate-900/60 border border-slate-800">
            <div>
              <span className="text-slate-400 block text-[10px] uppercase">Failed Amount</span>
              <span className="text-sm font-bold text-white font-mono">₹{payment.amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[10px] uppercase">Final Status</span>
              <span className={`inline-block font-semibold px-2 py-0.5 rounded text-[11px] mt-0.5 ${
                payment.final_status === 'RECOVERED' ? 'bg-emerald-500/20 text-emerald-300' :
                payment.final_status === 'ESCALATED' ? 'bg-amber-500/20 text-amber-300' : 'bg-rose-500/20 text-rose-300'
              }`}>
                {payment.final_status}
              </span>
            </div>
            <div>
              <span className="text-slate-400 block text-[10px] uppercase">Failure Reason</span>
              <span className="font-mono text-slate-200">{payment.failure_reason}</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[10px] uppercase">Customer Contact</span>
              <span className="font-mono text-slate-200">{payment.user_phone || "N/A"}</span>
            </div>
          </div>

          {/* AI Reasoning Box */}
          <div className="p-4 rounded-xl bg-purple-950/20 border border-purple-500/30 space-y-1.5">
            <div className="flex items-center justify-between text-purple-300 font-semibold">
              <span className="flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-purple-400" />
                AI Autonomous Strategy ({payment.ai_model_used || "Groq Engine"})
              </span>
              <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-purple-500/20 text-purple-200">
                {payment.action_taken || "AUTO_TRIAGE"}
              </span>
            </div>
            <p className="text-slate-300 leading-relaxed">
              {payment.ai_reasoning || "Autonomous error triage and recovery pipeline executed."}
            </p>
          </div>

          {/* Customer Reply & Intent */}
          {payment.user_reply && (
            <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
              <div className="flex items-center justify-between text-slate-400">
                <span className="flex items-center gap-1 text-[10px] uppercase font-semibold">
                  <MessageSquare className="w-3.5 h-3.5 text-amber-400" />
                  Inbound Customer Reply
                </span>
                <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-slate-800 text-amber-300">
                  Intent: {payment.user_reply_intent || "UNKNOWN"}
                </span>
              </div>
              <p className="text-white italic">"{payment.user_reply}"</p>
            </div>
          )}

        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/80 flex items-center justify-between">
          <span className="text-[11px] text-slate-500 font-mono">Logged: {payment.created_at || "Recent"}</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition-all"
          >
            Close
          </button>
        </div>

      </div>
    </div>
  );
}

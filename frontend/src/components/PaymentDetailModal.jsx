import React, { useState } from 'react';
import { X, Sparkles, MessageSquare, ExternalLink, Check, Copy, ShieldCheck, Code, ArrowRight } from 'lucide-react';

export default function PaymentDetailModal({ payment, onClose }) {
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');

  if (!payment) return null;

  const handleCopyId = () => {
    navigator.clipboard.writeText(payment.payment_id);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const rawJson = JSON.stringify(
    {
      event: 'payment.failed',
      payload: {
        payment: {
          entity: {
            id: payment.payment_id,
            amount: payment.amount * 100,
            currency: 'INR',
            status: 'failed',
            error_code: payment.failure_reason,
            error_description: payment.failure_reason,
            contact: payment.user_phone,
            created_at: Math.floor(Date.now() / 1000)
          }
        }
      },
      lifeline_recovery: {
        action: payment.action_taken,
        ai_model: payment.ai_model_used,
        ai_reasoning: payment.ai_reasoning,
        customer_intent: payment.user_reply_intent,
        final_status: payment.final_status
      }
    },
    null,
    2
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md">
      <div className="surface-panel w-full max-w-xl shadow-2xl border border-slate-700/80 overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-800 bg-slate-900/90">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] uppercase font-bold tracking-wider text-sky-400 font-numeric">
                Forensic Audit Trace
              </span>
              <span className="flex items-center gap-1 text-[10px] font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.2 rounded border border-emerald-500/20 font-numeric">
                <ShieldCheck className="w-3 h-3" /> HMAC Verified
              </span>
            </div>
            <div className="flex items-center gap-2 mt-1">
              <h3 className="text-base font-bold text-white font-numeric">{payment.payment_id}</h3>
              <button onClick={handleCopyId} className="text-slate-400 hover:text-white" title="Copy Payment ID">
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              </button>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Tab Toggle */}
        <div className="flex border-b border-slate-800 bg-slate-950/60 px-4 pt-2 gap-2 text-xs">
          <button
            onClick={() => setActiveTab('overview')}
            className={`pb-2 px-2 font-semibold transition-colors border-b-2 ${
              activeTab === 'overview' ? 'border-sky-500 text-white' : 'border-transparent text-slate-400 hover:text-white'
            }`}
          >
            Transaction Details
          </button>
          <button
            onClick={() => setActiveTab('json')}
            className={`pb-2 px-2 font-semibold transition-colors border-b-2 flex items-center gap-1.5 ${
              activeTab === 'json' ? 'border-sky-500 text-white' : 'border-transparent text-slate-400 hover:text-white'
            }`}
          >
            <Code className="w-3 h-3" />
            <span>Raw Webhook Payload</span>
          </button>
        </div>

        {/* Content */}
        {activeTab === 'overview' ? (
          <div className="p-6 space-y-4 text-xs">
            
            {/* Key attributes grid */}
            <div className="grid grid-cols-2 gap-3 p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 font-numeric">
              <div>
                <span className="text-slate-400 block text-[10px] uppercase">Failed Amount</span>
                <span className="text-sm font-bold text-white">₹{payment.amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px] uppercase">Settlement Outcome</span>
                <span className={`inline-block font-semibold px-2 py-0.5 rounded text-[11px] mt-0.5 ${
                  payment.final_status === 'RECOVERED' ? 'bg-emerald-500/20 text-emerald-300' :
                  payment.final_status === 'ESCALATED' ? 'bg-amber-500/20 text-amber-300' : 'bg-rose-500/20 text-rose-300'
                }`}>
                  {payment.final_status}
                </span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px] uppercase">Failure Reason</span>
                <span className="text-slate-200 text-[11px]">{payment.failure_reason}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px] uppercase">Customer Contact</span>
                <span className="text-slate-200">{payment.user_phone || "N/A"}</span>
              </div>
            </div>

            {/* AI Reasoning Box */}
            <div className="p-4 rounded-xl bg-purple-950/20 border border-purple-500/30 space-y-1.5">
              <div className="flex items-center justify-between text-purple-300 font-semibold">
                <span className="flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-purple-400" />
                  AI Autonomous Strategy ({payment.ai_model_used || "Groq Llama-3"})
                </span>
                <span className="text-[10px] font-numeric uppercase px-2 py-0.5 rounded bg-purple-500/20 text-purple-200">
                  {payment.action_taken || "AUTO_TRIAGE"}
                </span>
              </div>
              <p className="text-slate-300 leading-relaxed font-sans">
                {payment.ai_reasoning || "Autonomous error triage and recovery pipeline executed."}
              </p>
            </div>

            {/* Customer Reply & Intent */}
            {payment.user_reply && (
              <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
                <div className="flex items-center justify-between text-slate-400">
                  <span className="flex items-center gap-1 text-[10px] uppercase font-semibold">
                    <MessageSquare className="w-3.5 h-3.5 text-amber-400" />
                    Inbound Customer Response
                  </span>
                  <span className="font-numeric text-[10px] px-2 py-0.5 rounded bg-slate-800 text-amber-300">
                    Intent: {payment.user_reply_intent || "UNKNOWN"}
                  </span>
                </div>
                <p className="text-white italic">"{payment.user_reply}"</p>
              </div>
            )}

          </div>
        ) : (
          <div className="p-4">
            <pre className="p-3 rounded-lg bg-black/60 border border-slate-800 text-[11px] font-numeric text-slate-300 overflow-x-auto max-h-72">
              {rawJson}
            </pre>
          </div>
        )}

        {/* Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/90 flex items-center justify-between">
          <span className="text-[11px] text-slate-500 font-numeric">Timestamp: {payment.created_at || "Recent"}</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition-all tap-target"
          >
            Close Audit
          </button>
        </div>

      </div>
    </div>
  );
}

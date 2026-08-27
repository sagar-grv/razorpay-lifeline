import React, { useState } from 'react';
import { Play, Sparkles, Zap, Smartphone, CreditCard, AlertCircle, CheckCircle2, Loader2, MessageSquare, ShieldAlert } from 'lucide-react';

export default function SimulatorControls({ onSimulateSuccess }) {
  const [loadingAction, setLoadingAction] = useState(null);
  const [feedback, setFeedback] = useState(null);

  const showToast = (msg, type = 'success') => {
    setFeedback({ msg, type });
    setTimeout(() => setFeedback(null), 3500);
  };

  const handleSimulatePayment = async (reason, amount, label) => {
    setLoadingAction(reason);
    try {
      const res = await fetch('/api/simulate-payment', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          failure_reason: reason,
          amount_in_rupees: amount,
          phone: '+919876543210'
        })
      });
      const data = await res.json();
      showToast(`Simulated ${label} (${data.payment_id}) — Autonomous action dispatched!`);
      if (onSimulateSuccess) onSimulateSuccess();
    } catch (e) {
      showToast(`Simulation failed: ${e.message}`, 'error');
    } finally {
      setLoadingAction(null);
    }
  };

  const handleSimulateReply = async (content, label) => {
    setLoadingAction(label);
    try {
      const res = await fetch('/api/simulate-reply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          phone: '+919876543210',
          content: content
        })
      });
      const data = await res.json();
      showToast(`Simulated reply: "${content}" -> Intent: ${data.intent} (${data.payment_id})`);
      if (onSimulateSuccess) onSimulateSuccess();
    } catch (e) {
      showToast(`Reply simulation failed: ${e.message}`, 'error');
    } finally {
      setLoadingAction(null);
    }
  };

  const handleBatchTest = async () => {
    setLoadingAction('batch');
    try {
      await fetch('/api/batch-test', { method: 'POST' });
      showToast('25 synthetic webhook failures dispatched across multiple error codes!');
      if (onSimulateSuccess) setTimeout(onSimulateSuccess, 2000);
    } catch (e) {
      showToast(`Batch trigger failed: ${e.message}`, 'error');
    } finally {
      setLoadingAction(null);
    }
  };

  return (
    <div className="fintech-card p-6 relative">
      
      {/* Toast Feedback */}
      {feedback && (
        <div className={`absolute -top-3 right-6 z-20 flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-medium shadow-xl border animate-bounce ${
          feedback.type === 'error'
            ? 'bg-rose-950/90 text-rose-300 border-rose-700/80'
            : 'bg-emerald-950/90 text-emerald-300 border-emerald-700/80'
        }`}>
          <CheckCircle2 className="w-3.5 h-3.5" />
          <span>{feedback.msg}</span>
        </div>
      )}

      <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4 mb-4 pb-4 border-b border-slate-800">
        <div>
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-sky-400" />
            Interactive Testing Sandbox & Recovery Simulator
          </h3>
          <p className="text-xs text-slate-400">Trigger test webhook events or simulate inbound SMS replies with 1 click</p>
        </div>

        {/* Batch Test Button */}
        <button
          onClick={handleBatchTest}
          disabled={loadingAction === 'batch'}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-sky-600 to-blue-600 hover:from-sky-500 hover:to-blue-500 text-white text-xs font-semibold shadow-md shadow-sky-500/20 fintech-button disabled:opacity-50"
        >
          {loadingAction === 'batch' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5 fill-current" />}
          <span>Run 25-Payment Batch</span>
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
        
        {/* Trigger 1: Bank Down */}
        <button
          onClick={() => handleSimulatePayment('bank_server_down', 1500, 'Bank Outage')}
          disabled={loadingAction !== null}
          className="flex items-center justify-between p-3 rounded-xl bg-slate-900/80 border border-slate-800 hover:border-sky-500/40 hover:bg-slate-800/60 text-left fintech-button group"
        >
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-sky-500/10 text-sky-400 group-hover:bg-sky-500/20">
              <Zap className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs font-semibold text-white">Bank Server Down</div>
              <div className="text-[10px] text-slate-400 font-mono">Silent Retry (₹1,500)</div>
            </div>
          </div>
          {loadingAction === 'bank_server_down' && <Loader2 className="w-3.5 h-3.5 animate-spin text-sky-400" />}
        </button>

        {/* Trigger 2: Card Expired */}
        <button
          onClick={() => handleSimulatePayment('card_expired', 2500, 'Card Expired')}
          disabled={loadingAction !== null}
          className="flex items-center justify-between p-3 rounded-xl bg-slate-900/80 border border-slate-800 hover:border-amber-500/40 hover:bg-slate-800/60 text-left fintech-button group"
        >
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400 group-hover:bg-amber-500/20">
              <CreditCard className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs font-semibold text-white">Card Expired</div>
              <div className="text-[10px] text-slate-400 font-mono">SMS + RZP Link (₹2,500)</div>
            </div>
          </div>
          {loadingAction === 'card_expired' && <Loader2 className="w-3.5 h-3.5 animate-spin text-amber-400" />}
        </button>

        {/* Trigger 3: UPI PIN Blocked */}
        <button
          onClick={() => handleSimulatePayment('upi_pin_blocked', 5000, 'UPI Blocked')}
          disabled={loadingAction !== null}
          className="flex items-center justify-between p-3 rounded-xl bg-slate-900/80 border border-slate-800 hover:border-purple-500/40 hover:bg-slate-800/60 text-left fintech-button group"
        >
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-purple-500/10 text-purple-400 group-hover:bg-purple-500/20">
              <Smartphone className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs font-semibold text-white">UPI PIN Blocked</div>
              <div className="text-[10px] text-slate-400 font-mono">Nudge / Reset (₹5,000)</div>
            </div>
          </div>
          {loadingAction === 'upi_pin_blocked' && <Loader2 className="w-3.5 h-3.5 animate-spin text-purple-400" />}
        </button>

        {/* Trigger 4: Insufficient Funds */}
        <button
          onClick={() => handleSimulatePayment('insufficient_funds', 1200, 'Insufficient Funds')}
          disabled={loadingAction !== null}
          className="flex items-center justify-between p-3 rounded-xl bg-slate-900/80 border border-slate-800 hover:border-emerald-500/40 hover:bg-slate-800/60 text-left fintech-button group"
        >
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 group-hover:bg-emerald-500/20">
              <AlertCircle className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs font-semibold text-white">Insufficient Funds</div>
              <div className="text-[10px] text-slate-400 font-mono">Salary Nudge (₹1,200)</div>
            </div>
          </div>
          {loadingAction === 'insufficient_funds' && <Loader2 className="w-3.5 h-3.5 animate-spin text-emerald-400" />}
        </button>

      </div>

      {/* Compliance / Inbound Stopping Rule Triggers */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 p-3.5 rounded-xl bg-slate-950/70 border border-slate-800/80">
        <div className="flex items-center gap-2 text-xs text-slate-300">
          <MessageSquare className="w-4 h-4 text-amber-400" />
          <span className="font-medium">Simulate Inbound Customer SMS Reply:</span>
        </div>
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <button
            onClick={() => handleSimulateReply('STOP PLEASE', 'stop')}
            disabled={loadingAction !== null}
            className="flex-1 sm:flex-initial px-3 py-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 text-xs font-semibold flex items-center justify-center gap-1.5 fintech-button"
          >
            <ShieldAlert className="w-3.5 h-3.5" />
            <span>Simulate "STOP" (Opt-Out)</span>
          </button>
          <button
            onClick={() => handleSimulateReply('I will pay tomorrow morning after salary', 'promise')}
            disabled={loadingAction !== null}
            className="flex-1 sm:flex-initial px-3 py-1.5 rounded-lg bg-sky-500/10 hover:bg-sky-500/20 text-sky-400 border border-sky-500/30 text-xs font-semibold flex items-center justify-center gap-1.5 fintech-button"
          >
            <span>Simulate "Will Pay Tomorrow"</span>
          </button>
        </div>
      </div>

    </div>
  );
}

import React, { useState } from 'react';
import { ShieldCheck, Cpu, ShieldAlert, Send, CheckCircle2, ChevronRight, Activity, Zap, Smartphone, CreditCard, RefreshCw } from 'lucide-react';

export default function RecoveryPipelineVisualizer({ stats }) {
  const [activeStage, setActiveStage] = useState(null);

  const totalTxns = stats?.total_transactions || 0;
  const recoveredTxns = stats?.recovered_transactions || 0;
  const optOuts = stats?.opt_out_count || 0;
  const promises = stats?.promise_to_pay_count || 0;
  const totalAmount = stats?.total_amount || 0;
  const recoveredAmount = stats?.recovered_amount || 0;

  const stages = [
    {
      id: 'ingest',
      step: '01',
      title: 'Webhook Ingest',
      subtitle: 'HMAC-SHA256 Verified',
      icon: ShieldCheck,
      color: 'text-sky-400',
      bgBadge: 'bg-sky-500/10 border-sky-500/30',
      metric: `${totalTxns} Events`,
      detail: 'Every failed payment webhook is cryptographically verified with HMAC-SHA256 signature to guarantee zero spoofing.'
    },
    {
      id: 'triage',
      step: '02',
      title: 'AI Failure Triage',
      subtitle: 'On-Prem Llama 3.2 Inference',
      icon: Cpu,
      color: 'text-purple-400',
      bgBadge: 'bg-purple-500/10 border-purple-500/30',
      metric: `${totalTxns} Triaged`,
      detail: 'Local Llama maps the Razorpay failure reason to the right intervention and drafts the message.'
    },
    {
      id: 'compliance',
      step: '03',
      title: 'Compliance Guard',
      subtitle: 'Deterministic Stopping Rule',
      icon: ShieldAlert,
      color: 'text-amber-400',
      bgBadge: 'bg-amber-500/10 border-amber-500/30',
      metric: `${optOuts + promises} Halts/Delays`,
      detail: 'Strict compliance engine detects opt-out replies ("STOP") and halts outreach immediately. Detects "promise-to-pay" and reschedules reminders.'
    },
    {
      id: 'action',
      step: '04',
      title: 'Autonomous Action',
      subtitle: 'Multimodal Intervention',
      icon: Send,
      color: 'text-blue-400',
      bgBadge: 'bg-blue-500/10 border-blue-500/30',
      metric: `${totalTxns - optOuts} Dispatches`,
      detail: 'Generates live Razorpay payment links (rzp.io) and dispatches empathetic Hinglish SMS or schedules silent auto-retries.'
    },
    {
      id: 'settlement',
      step: '05',
      title: 'Merchant Settlement',
      subtitle: 'Net Revenue Recovered',
      icon: CheckCircle2,
      color: 'text-emerald-400',
      bgBadge: 'bg-emerald-500/10 border-emerald-500/30',
      metric: `₹${recoveredAmount.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`,
      detail: 'Closed-loop confirmation via payment_link.paid webhooks logs recovered revenue directly into merchant settlement.'
    }
  ];

  return (
    <div className="surface-panel p-5 sm:p-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 mb-5 pb-4 border-b border-slate-800">
        <div>
          <h2 className="text-sm font-semibold text-white tracking-tight flex items-center gap-2">
            <Activity className="w-4 h-4 text-sky-400" />
            Autonomous Recovery Pipeline Architecture
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Closed-loop transaction routing from failure webhook to merchant settlement
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-numeric px-2.5 py-1 rounded-md bg-slate-900 text-slate-300 border border-slate-800">
            Engine Latency: ~140ms
          </span>
        </div>
      </div>

      {/* 5-Stage Visual Circuit */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
        {stages.map((st, i) => {
          const Icon = st.icon;
          const isSelected = activeStage === st.id;

          return (
            <div
              key={st.id}
              onClick={() => setActiveStage(isSelected ? null : st.id)}
              className={`p-4 rounded-xl transition-all cursor-pointer tap-target relative border ${
                isSelected
                  ? 'bg-slate-900 border-sky-500/60 shadow-lg shadow-sky-500/10'
                  : 'bg-slate-900/50 hover:bg-slate-900/90 border-slate-800/80 hover:border-slate-700'
              }`}
            >
              {/* Top Row: Step & Icon */}
              <div className="flex items-center justify-between mb-3">
                <span className="text-[10px] font-numeric font-bold text-slate-500">{st.step}</span>
                <div className={`p-2 rounded-lg border ${st.bgBadge} ${st.color}`}>
                  <Icon className="w-4 h-4" />
                </div>
              </div>

              {/* Title & Subtitle */}
              <div className="text-xs font-bold text-white mb-0.5">{st.title}</div>
              <div className="text-[11px] text-slate-400 mb-3">{st.subtitle}</div>

              {/* Dynamic Live Metric */}
              <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between">
                <span className="text-[11px] font-numeric font-semibold text-slate-200">{st.metric}</span>
                <span className={`text-[10px] font-medium ${st.color}`}>Active</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Expanded Stage Explanation */}
      {activeStage && (
        <div className="mt-4 p-4 rounded-xl bg-slate-950/80 border border-sky-500/30 text-xs text-slate-300 animate-in fade-in duration-150 flex items-start gap-3">
          <div className="p-1.5 rounded bg-sky-500/10 text-sky-400 flex-shrink-0 mt-0.5">
            <Activity className="w-3.5 h-3.5" />
          </div>
          <div>
            <div className="font-semibold text-white mb-0.5">
              {stages.find((s) => s.id === activeStage)?.title} Specification:
            </div>
            <div className="leading-relaxed">
              {stages.find((s) => s.id === activeStage)?.detail}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

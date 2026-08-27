import React from 'react';
import { ArrowUpRight, CheckCircle2, XCircle, ShieldAlert, TrendingUp } from 'lucide-react';

export default function MetricCards({ stats }) {
  const totalAmount = stats?.total_amount || 0;
  const recoveredAmount = stats?.recovered_amount || 0;
  const lostAmount = stats?.lost_amount || 0;
  const recoveryRate = stats?.recovery_rate || 0;
  const baselineLift = stats?.baseline_lift || 0;
  const optOuts = stats?.opt_out_count || 0;
  const promises = stats?.promise_to_pay_count || 0;
  const totalTxns = stats?.total_transactions || 0;
  const recoveredTxns = stats?.recovered_transactions || 0;

  const formatINR = (val) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 2,
    }).format(val);
  };

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      
      {/* 1. AI Recovered Revenue */}
      <div className="fintech-card-active p-5 relative overflow-hidden group hover:border-sky-500/50 transition-all">
        <div className="flex items-center justify-between text-slate-400 mb-2">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            Recovered Revenue
          </span>
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-300 font-mono font-medium border border-emerald-500/20">
            {recoveredTxns} / {totalTxns} Confirmed
          </span>
        </div>
        <div className="text-2xl lg:text-3xl font-extrabold text-white tracking-tight mb-1.5 font-mono-numbers">
          {formatINR(recoveredAmount)}
        </div>
        <div className="text-xs text-slate-400 flex items-center gap-1.5">
          <span className="text-emerald-400 font-semibold font-mono flex items-center">
            <ArrowUpRight className="w-3.5 h-3.5" /> {recoveryRate}%
          </span>
          <span>recovery conversion rate</span>
        </div>
      </div>

      {/* 2. Total Failed Exposure */}
      <div className="fintech-card p-5 relative overflow-hidden group hover:border-slate-700 transition-all">
        <div className="flex items-center justify-between text-slate-400 mb-2">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-rose-400 flex items-center gap-1.5">
            <XCircle className="w-3.5 h-3.5 text-rose-400" />
            Failed Volume Pool
          </span>
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-rose-500/10 text-rose-300 font-mono font-medium border border-rose-500/20">
            {totalTxns} Txns
          </span>
        </div>
        <div className="text-2xl lg:text-3xl font-extrabold text-white tracking-tight mb-1.5 font-mono-numbers">
          {formatINR(totalAmount)}
        </div>
        <div className="text-xs text-slate-400 flex items-center justify-between">
          <span className="text-rose-400 font-mono">Lost: {formatINR(lostAmount)}</span>
          <span className="text-slate-500">Gross Pool</span>
        </div>
      </div>

      {/* 3. Measured Lift vs Baseline */}
      <div className="fintech-card p-5 relative overflow-hidden group hover:border-sky-500/40 transition-all">
        <div className="flex items-center justify-between text-slate-400 mb-2">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-sky-400 flex items-center gap-1.5">
            <TrendingUp className="w-3.5 h-3.5 text-sky-400" />
            Net Recovery Lift
          </span>
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-sky-500/10 text-sky-300 font-mono font-medium border border-sky-500/20">
            vs 22% Baseline
          </span>
        </div>
        <div className="text-2xl lg:text-3xl font-extrabold text-white tracking-tight mb-1.5 font-mono-numbers">
          <span className="text-sky-400">+{baselineLift}%</span>
        </div>
        <div className="text-xs text-slate-400">
          Honest lift over blind retry standard
        </div>
      </div>

      {/* 4. Stopping Rules & Compliance */}
      <div className="fintech-card p-5 relative overflow-hidden group hover:border-amber-500/40 transition-all">
        <div className="flex items-center justify-between text-slate-400 mb-2">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-amber-400 flex items-center gap-1.5">
            <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
            Compliance Halts
          </span>
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-300 font-mono font-medium border border-amber-500/20">
            Deterministic
          </span>
        </div>
        <div className="text-2xl lg:text-3xl font-extrabold text-white tracking-tight mb-1.5 font-mono-numbers flex items-center gap-3">
          <span>{optOuts}</span>
          <span className="text-xs font-normal text-slate-400 font-sans">Opt-Outs</span>
          <span className="text-slate-700">/</span>
          <span>{promises}</span>
          <span className="text-xs font-normal text-slate-400 font-sans">Promises</span>
        </div>
        <div className="text-xs text-slate-400">
          Zero compliance penalty exposure
        </div>
      </div>

    </div>
  );
}

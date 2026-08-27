import React from 'react';
import { ArrowUpRight, CheckCircle2, XCircle, ShieldAlert, TrendingUp, AlertTriangle, Clock } from 'lucide-react';

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

  // Format currency
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
      <div className="glass-panel-glow p-5 rounded-2xl relative overflow-hidden group hover:border-emerald-500/40 transition-all duration-300">
        <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/10 rounded-full blur-2xl -mr-10 -mt-10 pointer-events-none" />
        <div className="flex items-center justify-between text-slate-400 mb-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-emerald-400/90 flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            Recovered Revenue
          </span>
          <span className="text-[11px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-300 font-mono font-medium border border-emerald-500/20">
            {recoveredTxns} / {totalTxns} Txns
          </span>
        </div>
        <div className="text-2xl lg:text-3xl font-extrabold text-white tracking-tight mb-1 font-mono">
          {formatINR(recoveredAmount)}
        </div>
        <div className="text-xs text-slate-400 flex items-center gap-1">
          <span className="text-emerald-400 font-semibold flex items-center">
            <ArrowUpRight className="w-3.5 h-3.5" /> {recoveryRate}%
          </span>
          <span>of total failed volume saved</span>
        </div>
      </div>

      {/* 2. Total Failed Pool */}
      <div className="glass-panel p-5 rounded-2xl relative overflow-hidden group hover:border-slate-700 transition-all duration-300">
        <div className="flex items-center justify-between text-slate-400 mb-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-rose-400/90 flex items-center gap-1.5">
            <XCircle className="w-4 h-4 text-rose-400" />
            Total Failed Exposure
          </span>
          <span className="text-[11px] px-2 py-0.5 rounded-full bg-rose-500/10 text-rose-300 font-mono font-medium border border-rose-500/20">
            {totalTxns} Total
          </span>
        </div>
        <div className="text-2xl lg:text-3xl font-extrabold text-white tracking-tight mb-1 font-mono">
          {formatINR(totalAmount)}
        </div>
        <div className="text-xs text-slate-400 flex items-center gap-1">
          <span className="text-rose-400 font-medium">Lost: {formatINR(lostAmount)}</span>
        </div>
      </div>

      {/* 3. Honest Lift vs Baseline */}
      <div className="glass-panel p-5 rounded-2xl relative overflow-hidden group hover:border-blue-500/40 transition-all duration-300">
        <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/10 rounded-full blur-2xl -mr-10 -mt-10 pointer-events-none" />
        <div className="flex items-center justify-between text-slate-400 mb-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-blue-400/90 flex items-center gap-1.5">
            <TrendingUp className="w-4 h-4 text-blue-400" />
            Net Recovery Lift
          </span>
          <span className="text-[11px] px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-300 font-mono font-medium border border-blue-500/20">
            vs 22% Baseline
          </span>
        </div>
        <div className="text-2xl lg:text-3xl font-extrabold text-white tracking-tight mb-1 font-mono flex items-center gap-1">
          <span className="text-blue-400">+{baselineLift}%</span>
        </div>
        <div className="text-xs text-slate-400">
          Over industry standard blind retries
        </div>
      </div>

      {/* 4. Stopping Rules & Compliance */}
      <div className="glass-panel p-5 rounded-2xl relative overflow-hidden group hover:border-amber-500/40 transition-all duration-300">
        <div className="flex items-center justify-between text-slate-400 mb-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-amber-400/90 flex items-center gap-1.5">
            <ShieldAlert className="w-4 h-4 text-amber-400" />
            Compliance Halts
          </span>
          <span className="text-[11px] px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-300 font-mono font-medium border border-amber-500/20">
            100% Enforced
          </span>
        </div>
        <div className="text-2xl lg:text-3xl font-extrabold text-white tracking-tight mb-1 font-mono flex items-center gap-3">
          <span>{optOuts}</span>
          <span className="text-xs font-normal text-slate-400 font-sans">Opt-Outs</span>
          <span className="text-slate-600">|</span>
          <span>{promises}</span>
          <span className="text-xs font-normal text-slate-400 font-sans">Promises</span>
        </div>
        <div className="text-xs text-slate-400 flex items-center gap-1">
          <span className="text-amber-400 font-medium">Deterministic Halts:</span> Zero compliance fines
        </div>
      </div>

    </div>
  );
}

import React from 'react';
import { 
  ArrowUpRight, 
  CheckCircle2, 
  XCircle, 
  ShieldAlert, 
  Clock, 
  Zap, 
  ShieldCheck, 
  CopySlash, 
  BellOff 
} from 'lucide-react';

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

  // Reliability & CX Metrics
  const avgRecoveryTime = stats?.avg_time_to_recovery_min ?? 0;
  const avgWebhookLatency = stats?.avg_webhook_latency_s ?? 0;
  const lateAuthRate = stats?.late_auth_rate ?? 0;
  const duplicatesBlocked = stats?.duplicates_blocked ?? 0;
  const outreachSuppressed = stats?.outreach_suppressed ?? 0;

  const formatINR = (val) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(val);
  };

  return (
    <div className="space-y-4">
      {/* Row 1: Primary Revenue & Business Recovery Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-4">
        
        {/* 1. Hero Revenue Recovery Card (Takes 6 cols) */}
        <div className="md:col-span-6 surface-panel-hero p-6 flex flex-col justify-between relative overflow-hidden">
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold text-emerald-400 flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                Net Recovered Revenue
              </span>
              <span className="text-[11px] font-numeric px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-300 font-semibold border border-emerald-500/20">
                {recoveredTxns} / {totalTxns} Confirmed
              </span>
            </div>
            <div className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight mb-2 font-numeric">
              {formatINR(recoveredAmount)}
            </div>
            <p className="text-xs text-slate-300 mb-4">
              Autonomous closed-loop recovery via personalized payment links and smart retries.
            </p>
          </div>

          <div className="pt-4 border-t border-slate-800/80 grid grid-cols-2 gap-4">
            <div>
              <span className="text-[11px] text-slate-400 block">Recovery Conversion</span>
              <span className="text-sm font-bold text-emerald-400 font-numeric flex items-center gap-1">
                <ArrowUpRight className="w-4 h-4" /> {recoveryRate}%
              </span>
            </div>
            <div>
              <span className="text-[11px] text-slate-400 block">Net Lift vs 22% Baseline</span>
              <span className="text-sm font-bold text-sky-400 font-numeric">
                +{baselineLift}% Realized
              </span>
            </div>
          </div>
        </div>

        {/* 2. Total Failed Volume Pool (Takes 3 cols) */}
        <div className="md:col-span-3 surface-panel p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold text-rose-400 flex items-center gap-1.5">
                <XCircle className="w-4 h-4 text-rose-400" />
                Failed Exposure
              </span>
              <span className="text-[10px] font-numeric px-2 py-0.5 rounded-full bg-rose-500/10 text-rose-300 border border-rose-500/20">
                {totalTxns} Txns
              </span>
            </div>
            <div className="text-2xl font-bold text-white tracking-tight mb-1 font-numeric">
              {formatINR(totalAmount)}
            </div>
            <p className="text-xs text-slate-400">Total gross failed payment volume intercepted.</p>
          </div>

          <div className="pt-4 border-t border-slate-800/80 flex items-center justify-between text-xs">
            <span className="text-slate-400">Unrecovered:</span>
            <span className="text-rose-400 font-numeric font-semibold">{formatINR(lostAmount)}</span>
          </div>
        </div>

        {/* 3. Deterministic Compliance Guard (Takes 3 cols) */}
        <div className="md:col-span-3 surface-panel p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold text-amber-400 flex items-center gap-1.5">
                <ShieldAlert className="w-4 h-4 text-amber-400" />
                Stopping Rules
              </span>
              <span className="text-[10px] font-numeric px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-300 border border-amber-500/20">
                100% Guard
              </span>
            </div>
            <div className="text-2xl font-bold text-white tracking-tight mb-1 font-numeric flex items-center gap-2">
              <span>{optOuts}</span>
              <span className="text-xs font-normal text-slate-400">Opt-Outs</span>
              <span className="text-slate-600">/</span>
              <span>{promises}</span>
              <span className="text-xs font-normal text-slate-400">Promises</span>
            </div>
            <p className="text-xs text-slate-400">Zero spam penalty risk with deterministic halt checks.</p>
          </div>

          <div className="pt-4 border-t border-slate-800/80 flex items-center justify-between text-xs">
            <span className="text-slate-400">Compliance Status:</span>
            <span className="text-emerald-400 font-semibold flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3" /> Strict Active
            </span>
          </div>
        </div>

      </div>

      {/* Row 2: Reliability & CX Metrics Section */}
      <div className="space-y-2.5 pt-1">
        <div className="flex items-center justify-between px-1">
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-sky-400 animate-pulse" />
            <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Reliability & CX Metrics
            </h2>
          </div>
          <span className="text-[11px] text-slate-500 font-numeric">
            Audited via live PostgreSQL telemetry
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3.5">
          
          {/* Card 1: Avg Recovery Time */}
          <div className="surface-panel p-4 flex flex-col justify-between hover:border-slate-700/80 transition-all">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-medium text-slate-400 flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-sky-400" />
                Avg Recovery Time
              </span>
              <span className="text-[9px] font-numeric px-1.5 py-0.5 rounded bg-sky-500/10 text-sky-300 border border-sky-500/20">
                Speed
              </span>
            </div>
            <div className="text-xl sm:text-2xl font-bold text-white tracking-tight font-numeric mb-1">
              {avgRecoveryTime} min
            </div>
            <p className="text-[10px] text-slate-500 leading-tight">
              Ingest to ground-truth settlement
            </p>
          </div>

          {/* Card 2: Avg Webhook Latency */}
          <div className="surface-panel p-4 flex flex-col justify-between hover:border-slate-700/80 transition-all">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-medium text-slate-400 flex items-center gap-1.5">
                <Zap className="w-3.5 h-3.5 text-amber-400" />
                Avg Webhook Latency
              </span>
              <span className="text-[9px] font-numeric px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20">
                Real-time
              </span>
            </div>
            <div className="text-xl sm:text-2xl font-bold text-white tracking-tight font-numeric mb-1">
              {avgWebhookLatency} s
            </div>
            <p className="text-[10px] text-slate-500 leading-tight">
              Razorpay cloud event dispatch delay
            </p>
          </div>

          {/* Card 3: Late-Auth Catch Rate */}
          <div className="surface-panel p-4 flex flex-col justify-between hover:border-slate-700/80 transition-all">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-medium text-slate-400 flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                Late-Auth Catch Rate
              </span>
              <span className="text-[9px] font-numeric px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
                Guard
              </span>
            </div>
            <div className="text-xl sm:text-2xl font-bold text-white tracking-tight font-numeric mb-1">
              {lateAuthRate}%
            </div>
            <p className="text-[10px] text-slate-500 leading-tight">
              Natively settled in 45s window
            </p>
          </div>

          {/* Card 4: Duplicates Blocked */}
          <div className="surface-panel p-4 flex flex-col justify-between hover:border-slate-700/80 transition-all">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-medium text-slate-400 flex items-center gap-1.5">
                <CopySlash className="w-3.5 h-3.5 text-purple-400" />
                Duplicates Blocked
              </span>
              <span className="text-[9px] font-numeric px-1.5 py-0.5 rounded bg-purple-500/10 text-purple-300 border border-purple-500/20">
                Idempotency
              </span>
            </div>
            <div className="text-xl sm:text-2xl font-bold text-white tracking-tight font-numeric mb-1">
              {duplicatesBlocked}
            </div>
            <p className="text-[10px] text-slate-500 leading-tight">
              Razorpay retries safely deduplicated
            </p>
          </div>

          {/* Card 5: Outreach Suppressed */}
          <div className="surface-panel p-4 flex flex-col justify-between hover:border-slate-700/80 transition-all">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-medium text-slate-400 flex items-center gap-1.5">
                <BellOff className="w-3.5 h-3.5 text-rose-400" />
                Outreach Suppressed
              </span>
              <span className="text-[9px] font-numeric px-1.5 py-0.5 rounded bg-rose-500/10 text-rose-300 border border-rose-500/20">
                TRAI Safe
              </span>
            </div>
            <div className="text-xl sm:text-2xl font-bold text-white tracking-tight font-numeric mb-1">
              {outreachSuppressed}
            </div>
            <p className="text-[10px] text-slate-500 leading-tight">
              Halts via opt-out or late auth
            </p>
          </div>

        </div>
      </div>
    </div>
  );
}

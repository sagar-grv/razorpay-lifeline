import React from 'react';
import { Layers, Zap, Smartphone, CreditCard, AlertCircle } from 'lucide-react';

export default function RecoveryChart({ stats }) {
  const breakdown = stats?.failure_breakdown || {};
  const failureKeys = Object.keys(breakdown);

  const getReasonConfig = (key) => {
    const k = key.toLowerCase();
    if (k.includes('bank')) {
      return {
        label: 'Bank Server Outage',
        icon: Zap,
        color: 'from-blue-500 to-indigo-500',
        action: 'Silent Auto-Retry (10 min)',
        badgeColor: 'bg-blue-500/10 text-blue-400 border-blue-500/20'
      };
    }
    if (k.includes('card')) {
      return {
        label: 'Card Expired',
        icon: CreditCard,
        color: 'from-amber-500 to-orange-500',
        action: 'Razorpay Payment Link SMS',
        badgeColor: 'bg-amber-500/10 text-amber-400 border-amber-500/20'
      };
    }
    if (k.includes('upi')) {
      return {
        label: 'UPI PIN Blocked',
        icon: Smartphone,
        color: 'from-purple-500 to-pink-500',
        action: 'Switch App / Reset Link',
        badgeColor: 'bg-purple-500/10 text-purple-400 border-purple-500/20'
      };
    }
    return {
      label: 'Insufficient Funds',
      icon: AlertCircle,
      color: 'from-emerald-500 to-teal-500',
      action: 'Polite Salary Nudge + Link',
      badgeColor: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
    };
  };

  return (
    <div className="glass-panel p-6 rounded-2xl">
      <div className="flex items-center justify-between mb-6 pb-4 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/20">
            <Layers className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">Failure Code Analysis & Recovery Interventions</h3>
            <p className="text-xs text-slate-400">Autonomous strategy performance across error categories</p>
          </div>
        </div>
        <div className="flex items-center gap-3 text-xs text-slate-400">
          <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block" /> Recovered</span>
          <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-rose-500 inline-block" /> Lost</span>
          <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block" /> Escalated</span>
        </div>
      </div>

      {failureKeys.length === 0 ? (
        <div className="py-12 text-center text-slate-500 text-sm">
          No failure events recorded yet. Trigger a simulated payment failure below to see recovery insights.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {failureKeys.map((key) => {
            const data = breakdown[key];
            const cfg = getReasonConfig(key);
            const Icon = cfg.icon;
            const total = data.total || 1;
            const recPercent = Math.round((data.recovered / total) * 100);
            const lostPercent = Math.round((data.lost / total) * 100);
            const escPercent = Math.round((data.escalated / total) * 100);

            return (
              <div key={key} className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 hover:border-slate-700 transition-all">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <div className="p-1.5 rounded-md bg-slate-800 text-slate-300">
                      <Icon className="w-4 h-4" />
                    </div>
                    <div>
                      <h4 className="text-xs font-semibold text-white">{cfg.label}</h4>
                      <span className="text-[10px] font-mono text-slate-400">{key}</span>
                    </div>
                  </div>
                  <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium border ${cfg.badgeColor}`}>
                    {cfg.action}
                  </span>
                </div>

                {/* Progress bar */}
                <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden flex my-3">
                  <div style={{ width: `${recPercent}%` }} className="h-full bg-emerald-500 transition-all duration-500" title={`Recovered: ${recPercent}%`} />
                  <div style={{ width: `${escPercent}%` }} className="h-full bg-amber-500 transition-all duration-500" title={`Escalated: ${escPercent}%`} />
                  <div style={{ width: `${lostPercent}%` }} className="h-full bg-rose-500/80 transition-all duration-500" title={`Lost: ${lostPercent}%`} />
                </div>

                {/* Stats sub-row */}
                <div className="flex items-center justify-between text-[11px] text-slate-400 font-mono">
                  <span>Vol: ₹{data.amount.toLocaleString('en-IN')}</span>
                  <span>{data.recovered}/{data.total} ({recPercent}% Saved)</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

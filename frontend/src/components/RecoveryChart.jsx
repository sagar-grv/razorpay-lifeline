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
        action: 'Silent Auto-Retry (10 min)',
        badgeColor: 'bg-blue-500/10 text-blue-400 border-blue-500/30'
      };
    }
    if (k.includes('card')) {
      return {
        label: 'Card Expired',
        icon: CreditCard,
        action: 'Razorpay Payment Link SMS',
        badgeColor: 'bg-amber-500/10 text-amber-400 border-amber-500/30'
      };
    }
    if (k.includes('upi')) {
      return {
        label: 'UPI PIN Blocked',
        icon: Smartphone,
        action: 'Switch App / Reset Link',
        badgeColor: 'bg-purple-500/10 text-purple-400 border-purple-500/30'
      };
    }
    return {
      label: 'Insufficient Funds',
      icon: AlertCircle,
      action: 'Polite Salary Nudge + Link',
      badgeColor: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
    };
  };

  return (
    <div className="surface-panel p-5 sm:p-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-6 pb-4 border-b border-slate-800">
        <div>
          <h3 className="text-sm font-semibold text-white">Error Code Taxonomy & Recovery Performance</h3>
          <p className="text-xs text-slate-400 mt-0.5">Autonomous operational strategy breakdown across failure classifications</p>
        </div>
        <div className="flex items-center gap-4 text-xs font-numeric text-slate-400">
          <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-emerald-500" /> Recovered</span>
          <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-amber-500" /> Escalated</span>
          <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-rose-500" /> Lost</span>
        </div>
      </div>

      {failureKeys.length === 0 ? (
        <div className="py-12 text-center text-slate-500 text-xs font-numeric">
          No failure events recorded in database yet. Use the Simulator Controls to dispatch synthetic events.
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
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2.5">
                    <div className="p-2 rounded-lg bg-slate-800 text-slate-200">
                      <Icon className="w-4 h-4" />
                    </div>
                    <div>
                      <h4 className="text-xs font-semibold text-white">{cfg.label}</h4>
                      <span className="text-[10px] font-numeric text-slate-400">{key}</span>
                    </div>
                  </div>
                  <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium border font-numeric ${cfg.badgeColor}`}>
                    {cfg.action}
                  </span>
                </div>

                {/* Progress bar */}
                <div className="w-full h-2 rounded-full bg-slate-800/80 overflow-hidden flex my-3">
                  <div style={{ width: `${recPercent}%` }} className="h-full bg-emerald-500 transition-all duration-500" />
                  <div style={{ width: `${escPercent}%` }} className="h-full bg-amber-500 transition-all duration-500" />
                  <div style={{ width: `${lostPercent}%` }} className="h-full bg-rose-500 transition-all duration-500" />
                </div>

                {/* Stats row */}
                <div className="flex items-center justify-between text-[11px] text-slate-400 font-numeric">
                  <span>Exposure: ₹{data.amount.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</span>
                  <span className="text-slate-200 font-semibold">{data.recovered}/{data.total} ({recPercent}% Recovered)</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

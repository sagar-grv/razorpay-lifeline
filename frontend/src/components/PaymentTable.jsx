import React, { useState } from 'react';
import { Search, Filter, ExternalLink, CheckCircle2, XCircle, ShieldAlert, Sparkles, MessageSquare, ArrowRight } from 'lucide-react';

export default function PaymentTable({ payments, onSelectPayment }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('ALL');

  const filtered = payments.filter((p) => {
    const matchesSearch =
      p.payment_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (p.user_phone && p.user_phone.includes(searchTerm)) ||
      (p.failure_reason && p.failure_reason.toLowerCase().includes(searchTerm.toLowerCase()));
    
    const matchesFilter = filterStatus === 'ALL' || p.final_status === filterStatus;
    return matchesSearch && matchesFilter;
  });

  const getStatusBadge = (status) => {
    switch (status) {
      case 'RECOVERED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <CheckCircle2 className="w-3.5 h-3.5" /> RECOVERED
          </span>
        );
      case 'LOST':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <XCircle className="w-3.5 h-3.5" /> LOST
          </span>
        );
      case 'ESCALATED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <ShieldAlert className="w-3.5 h-3.5" /> ESCALATED
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-500/10 text-slate-400 border border-slate-500/20">
            PENDING
          </span>
        );
    }
  };

  return (
    <div className="glass-panel p-6 rounded-2xl">
      
      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 mb-6 pb-4 border-b border-slate-800">
        <div>
          <h3 className="text-sm font-semibold text-white">Immutable PostgreSQL Audit Ledger</h3>
          <p className="text-xs text-slate-400">Complete forensic trail of failure telemetry, AI reasoning, and compliance stops</p>
        </div>

        <div className="flex items-center gap-3 w-full md:w-auto flex-wrap">
          {/* Search */}
          <div className="relative flex-1 md:w-64">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search ID, phone, reason..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 rounded-xl bg-slate-900/80 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
            />
          </div>

          {/* Filter Pills */}
          <div className="flex items-center gap-1 p-1 rounded-xl bg-slate-900/80 border border-slate-800 text-xs">
            {['ALL', 'RECOVERED', 'LOST', 'ESCALATED'].map((st) => (
              <button
                key={st}
                onClick={() => setFilterStatus(st)}
                className={`px-2.5 py-1 rounded-lg font-medium transition-all ${
                  filterStatus === st
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {st}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="text-[11px] uppercase tracking-wider text-slate-400 bg-slate-900/40 border-b border-slate-800">
            <tr>
              <th className="py-3 px-4 font-semibold">Payment ID</th>
              <th className="py-3 px-4 font-semibold">Amount</th>
              <th className="py-3 px-4 font-semibold">Failure Reason</th>
              <th className="py-3 px-4 font-semibold">Action Taken</th>
              <th className="py-3 px-4 font-semibold">Customer Reply & Intent</th>
              <th className="py-3 px-4 font-semibold text-right">Final Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-sans">
            {filtered.length === 0 ? (
              <tr>
                <td colSpan="6" className="py-12 text-center text-slate-500">
                  No payment records found matching criteria.
                </td>
              </tr>
            ) : (
              filtered.map((item) => (
                <tr
                  key={item.payment_id}
                  onClick={() => onSelectPayment && onSelectPayment(item)}
                  className="hover:bg-slate-800/40 cursor-pointer transition-colors group"
                >
                  {/* Payment ID */}
                  <td className="py-3 px-4">
                    <div className="font-mono font-medium text-white group-hover:text-blue-400 transition-colors">
                      {item.payment_id}
                    </div>
                    <div className="text-[10px] text-slate-500 font-mono">{item.user_phone || "Guest"}</div>
                  </td>

                  {/* Amount */}
                  <td className="py-3 px-4 font-mono font-bold text-white">
                    ₹{item.amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </td>

                  {/* Failure Reason */}
                  <td className="py-3 px-4">
                    <span className="px-2 py-0.5 rounded-md bg-slate-800 text-slate-300 font-mono text-[11px] border border-slate-700/60">
                      {item.failure_reason}
                    </span>
                  </td>

                  {/* Action Taken & AI Reasoning preview */}
                  <td className="py-3 px-4 max-w-[260px]">
                    <div className="font-semibold text-slate-200 flex items-center gap-1.5">
                      <Sparkles className="w-3 h-3 text-cyan-400" />
                      <span>{item.action_taken || "AUTO_TRIAGE"}</span>
                    </div>
                    {item.ai_reasoning && (
                      <p className="text-[11px] text-slate-400 truncate mt-0.5" title={item.ai_reasoning}>
                        {item.ai_reasoning}
                      </p>
                    )}
                  </td>

                  {/* Customer Reply & Intent */}
                  <td className="py-3 px-4">
                    {item.user_reply ? (
                      <div>
                        <div className="text-[11px] text-slate-300 flex items-center gap-1">
                          <MessageSquare className="w-3 h-3 text-slate-400" />
                          <span className="italic">"{item.user_reply}"</span>
                        </div>
                        {item.user_reply_intent === 'OPT_OUT' && (
                          <span className="inline-block mt-0.5 text-[9px] font-bold px-1.5 py-0.2 rounded bg-rose-500/20 text-rose-400 border border-rose-500/30">
                            STOPPING RULE HALT
                          </span>
                        )}
                        {item.user_reply_intent === 'PROMISE_TO_PAY' && (
                          <span className="inline-block mt-0.5 text-[9px] font-bold px-1.5 py-0.2 rounded bg-blue-500/20 text-blue-400 border border-blue-500/30">
                            PROMISE TO PAY
                          </span>
                        )}
                      </div>
                    ) : (
                      <span className="text-[11px] text-slate-600 italic">No reply</span>
                    )}
                  </td>

                  {/* Final Status */}
                  <td className="py-3 px-4 text-right">
                    {getStatusBadge(item.final_status)}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

    </div>
  );
}

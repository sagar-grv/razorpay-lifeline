import React, { useState } from 'react';
import { Search, CheckCircle2, XCircle, ShieldAlert, Sparkles, MessageSquare, ArrowUpRight } from 'lucide-react';

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

  const getCount = (st) => {
    if (st === 'ALL') return payments.length;
    return payments.filter((p) => p.final_status === st).length;
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'RECOVERED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-numeric">
            <CheckCircle2 className="w-3 h-3" /> RECOVERED
          </span>
        );
      case 'LOST':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md text-[11px] font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20 font-numeric">
            <XCircle className="w-3 h-3" /> LOST
          </span>
        );
      case 'ESCALATED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md text-[11px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20 font-numeric">
            <ShieldAlert className="w-3 h-3" /> ESCALATED
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md text-[11px] font-semibold bg-slate-500/10 text-slate-400 border border-slate-500/20 font-numeric">
            PENDING
          </span>
        );
    }
  };

  return (
    <div className="surface-panel p-5 sm:p-6">
      
      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 mb-6 pb-4 border-b border-slate-800">
        <div>
          <h3 className="text-sm font-semibold text-white">Forensic Audit Ledger</h3>
          <p className="text-xs text-slate-400 mt-0.5">Immutable record of webhook triggers, AI reasoning traces, and compliance halts</p>
        </div>

        <div className="flex items-center gap-3 w-full md:w-auto flex-wrap">
          {/* Search */}
          <div className="relative flex-1 md:w-64">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              placeholder="Search payment ID, phone, code..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500 transition-colors"
            />
          </div>

          {/* Filter Pills with Counts */}
          <div className="flex items-center gap-1 p-1 rounded-lg bg-slate-900 border border-slate-800 text-xs">
            {['ALL', 'RECOVERED', 'LOST', 'ESCALATED'].map((st) => (
              <button
                key={st}
                onClick={() => setFilterStatus(st)}
                className={`px-2.5 py-1 rounded font-medium transition-all flex items-center gap-1.5 ${
                  filterStatus === st
                    ? 'bg-sky-600 text-white font-semibold'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <span>{st}</span>
                <span className="text-[10px] font-numeric opacity-80">({getCount(st)})</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="text-[10px] uppercase tracking-wider text-slate-400 bg-slate-900/60 border-b border-slate-800 font-numeric">
            <tr>
              <th className="py-3 px-4 font-semibold">Payment ID</th>
              <th className="py-3 px-4 font-semibold">Failed Amount</th>
              <th className="py-3 px-4 font-semibold">Failure Reason</th>
              <th className="py-3 px-4 font-semibold">Autonomous Intervention</th>
              <th className="py-3 px-4 font-semibold">Customer Response</th>
              <th className="py-3 px-4 font-semibold text-right">Final Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {filtered.length === 0 ? (
              <tr>
                <td colSpan="6" className="py-12 text-center text-slate-500 font-numeric text-xs">
                  No payment records found matching the active filter criteria.
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
                  <td className="py-3.5 px-4">
                    <div className="font-numeric font-semibold text-white group-hover:text-sky-400 transition-colors flex items-center gap-1.5">
                      <span>{item.payment_id}</span>
                      <ArrowUpRight className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity text-sky-400" />
                    </div>
                    <div className="text-[10px] text-slate-500 font-numeric">{item.user_phone || "Guest"}</div>
                  </td>

                  {/* Amount */}
                  <td className="py-3.5 px-4 font-numeric font-bold text-white">
                    ₹{item.amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </td>

                  {/* Failure Reason */}
                  <td className="py-3.5 px-4">
                    <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-numeric text-[11px] border border-slate-700/60">
                      {item.failure_reason}
                    </span>
                  </td>

                  {/* Action Taken & AI Reasoning preview */}
                  <td className="py-3.5 px-4 max-w-[260px]">
                    <div className="font-semibold text-slate-200 flex items-center gap-1.5">
                      <Sparkles className="w-3.5 h-3.5 text-sky-400" />
                      <span>{item.action_taken || "AUTO_TRIAGE"}</span>
                    </div>
                    {item.ai_reasoning && (
                      <p className="text-[11px] text-slate-400 truncate mt-0.5" title={item.ai_reasoning}>
                        {item.ai_reasoning}
                      </p>
                    )}
                  </td>

                  {/* Customer Reply & Intent */}
                  <td className="py-3.5 px-4">
                    {item.user_reply ? (
                      <div>
                        <div className="text-[11px] text-slate-300 flex items-center gap-1">
                          <MessageSquare className="w-3 h-3 text-slate-400" />
                          <span className="italic">"{item.user_reply}"</span>
                        </div>
                        {item.user_reply_intent === 'OPT_OUT' && (
                          <span className="inline-block mt-0.5 text-[9px] font-bold px-1.5 py-0.2 rounded bg-rose-500/20 text-rose-400 border border-rose-500/30 font-numeric">
                            STOPPING RULE HALT
                          </span>
                        )}
                        {item.user_reply_intent === 'PROMISE_TO_PAY' && (
                          <span className="inline-block mt-0.5 text-[9px] font-bold px-1.5 py-0.2 rounded bg-sky-500/20 text-sky-400 border border-sky-500/30 font-numeric">
                            PROMISE TO PAY
                          </span>
                        )}
                      </div>
                    ) : (
                      <span className="text-[11px] text-slate-600 italic">No reply</span>
                    )}
                  </td>

                  {/* Final Status */}
                  <td className="py-3.5 px-4 text-right">
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

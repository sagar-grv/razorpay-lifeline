import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import MetricCards from './components/MetricCards';
import RecoveryChart from './components/RecoveryChart';
import SimulatorControls from './components/SimulatorControls';
import PaymentTable from './components/PaymentTable';
import LiveTerminal from './components/LiveTerminal';
import AICopilotModal from './components/AICopilotModal';
import PaymentDetailModal from './components/PaymentDetailModal';
import { Sparkles, Terminal, ArrowUpRight, Activity } from 'lucide-react';

export default function App() {
  const [stats, setStats] = useState(null);
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isTerminalOpen, setIsTerminalOpen] = useState(false);
  const [isCopilotOpen, setIsCopilotOpen] = useState(false);
  const [selectedPayment, setSelectedPayment] = useState(null);
  const [webhookUrl, setWebhookUrl] = useState('http://localhost:8000');

  const fetchData = async () => {
    try {
      const [statsRes, paymentsRes, ngrokRes] = await Promise.all([
        fetch('/api/stats').then((r) => r.json()),
        fetch('/api/payments').then((r) => r.json()),
        fetch('/api/ngrok-info').then((r) => r.json()).catch(() => ({ public_url: 'http://localhost:8000' })),
      ]);
      setStats(statsRes);
      setPayments(paymentsRes);
      if (ngrokRes?.public_url) setWebhookUrl(ngrokRes.public_url);
    } catch (err) {
      console.error('Error fetching dashboard telemetry:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 4000); // Poll every 4 seconds
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-[#090D16] text-slate-100 flex flex-col selection:bg-blue-600 selection:text-white">
      
      {/* Navigation Header */}
      <Header
        stats={stats}
        onRefresh={fetchData}
        isTerminalOpen={isTerminalOpen}
        setIsTerminalOpen={setIsTerminalOpen}
        onOpenCopilot={() => setIsCopilotOpen(true)}
        webhookUrl={webhookUrl}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 lg:px-8 py-6 space-y-6 pb-28">
        
        {/* Metric Cards Grid */}
        <MetricCards stats={stats} />

        {/* Simulator & Sandbox Action Bar */}
        <SimulatorControls onSimulateSuccess={fetchData} />

        {/* Charts & Breakdown Grid */}
        <div className="grid grid-cols-1 gap-6">
          <RecoveryChart stats={stats} />
        </div>

        {/* Audit Ledger Table */}
        <PaymentTable
          payments={payments}
          onSelectPayment={(payment) => setSelectedPayment(payment)}
        />

      </main>

      {/* Bottom Sticky Floating Live Terminal Bar */}
      <div className="fixed bottom-0 left-0 right-0 z-40 max-w-7xl mx-auto px-4 lg:px-8 pointer-events-none">
        <div className="pointer-events-auto">
          {isTerminalOpen ? (
            <LiveTerminal isOpen={isTerminalOpen} onClose={() => setIsTerminalOpen(false)} />
          ) : (
            <div className="flex justify-end pb-3">
              <button
                onClick={() => setIsTerminalOpen(true)}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-900/90 hover:bg-slate-800 text-slate-300 hover:text-white text-xs font-mono font-medium border border-slate-700 shadow-2xl backdrop-blur-lg transition-all active:scale-95 group"
              >
                <Terminal className="w-3.5 h-3.5 text-blue-400 group-hover:text-cyan-300" />
                <span>Open Live Engine Logs</span>
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              </button>
            </div>
          )}
        </div>
      </div>

      {/* AI Copilot Drawer Modal */}
      <AICopilotModal
        isOpen={isCopilotOpen}
        onClose={() => setIsCopilotOpen(false)}
        stats={stats}
      />

      {/* Payment Detail Modal */}
      <PaymentDetailModal
        payment={selectedPayment}
        onClose={() => setSelectedPayment(null)}
      />

    </div>
  );
}

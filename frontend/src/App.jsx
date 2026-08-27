import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import MetricCards from './components/MetricCards';
import RecoveryPipelineVisualizer from './components/RecoveryPipelineVisualizer';
import RecoveryChart from './components/RecoveryChart';
import SimulatorControls from './components/SimulatorControls';
import PaymentTable from './components/PaymentTable';
import LiveTerminal from './components/LiveTerminal';
import AICopilotModal from './components/AICopilotModal';
import PaymentDetailModal from './components/PaymentDetailModal';
import CommandPalette from './components/CommandPalette';
import { Terminal } from 'lucide-react';

export default function App() {
  const [stats, setStats] = useState(null);
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isTerminalOpen, setIsTerminalOpen] = useState(false);
  const [isCopilotOpen, setIsCopilotOpen] = useState(false);
  const [isCmdkOpen, setIsCmdkOpen] = useState(false);
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
    const interval = setInterval(fetchData, 4000);
    return () => clearInterval(interval);
  }, []);

  const handleSimulatePayment = async (reason, amount, label) => {
    try {
      await fetch('/api/simulate-payment', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          failure_reason: reason,
          amount_in_rupees: amount,
          phone: '+919876543210'
        })
      });
      fetchData();
    } catch (e) {}
  };

  const handleSimulateReply = async (content, label) => {
    try {
      await fetch('/api/simulate-reply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          phone: '+919876543210',
          content: content
        })
      });
      fetchData();
    } catch (e) {}
  };

  const handleRunBatch = async () => {
    try {
      await fetch('/api/batch-test', { method: 'POST' });
      setTimeout(fetchData, 2000);
    } catch (e) {}
  };

  return (
    <div className="min-h-screen bg-[#060911] text-slate-100 flex flex-col selection:bg-sky-500 selection:text-white">
      
      {/* Navigation Header */}
      <Header
        stats={stats}
        onRefresh={fetchData}
        isTerminalOpen={isTerminalOpen}
        setIsTerminalOpen={setIsTerminalOpen}
        onOpenCopilot={() => setIsCopilotOpen(true)}
        onOpenCmdk={setIsCmdkOpen}
        webhookUrl={webhookUrl}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 lg:px-8 py-6 space-y-6 pb-28">
        
        {/* Metric Cards Grid (Asymmetric) */}
        <MetricCards stats={stats} />

        {/* Signature Element: Interactive Autonomous Recovery Pipeline */}
        <RecoveryPipelineVisualizer stats={stats} />

        {/* Interactive Testing Sandbox */}
        <SimulatorControls onSimulateSuccess={fetchData} />

        {/* Error Code Breakdown Grid */}
        <RecoveryChart stats={stats} />

        {/* Forensic Audit Ledger Table */}
        <PaymentTable
          payments={payments}
          onSelectPayment={(payment) => setSelectedPayment(payment)}
        />

      </main>

      {/* Bottom Floating Live Telemetry Tray */}
      <div className="fixed bottom-0 left-0 right-0 z-40 max-w-7xl mx-auto px-4 lg:px-8 pointer-events-none">
        <div className="pointer-events-auto">
          {isTerminalOpen ? (
            <LiveTerminal isOpen={isTerminalOpen} onClose={() => setIsTerminalOpen(false)} />
          ) : (
            <div className="flex justify-end pb-3">
              <button
                onClick={() => setIsTerminalOpen(true)}
                className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white text-xs font-numeric font-medium border border-slate-700/80 shadow-2xl backdrop-blur-xl transition-all tap-target"
              >
                <Terminal className="w-3.5 h-3.5 text-sky-400" />
                <span>Engine Telemetry</span>
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Command Palette (Cmd+K) */}
      <CommandPalette
        isOpen={isCmdkOpen}
        onClose={setIsCmdkOpen}
        onOpenCopilot={() => setIsCopilotOpen(true)}
        onOpenTerminal={() => setIsTerminalOpen(true)}
        onSimulatePayment={handleSimulatePayment}
        onSimulateReply={handleSimulateReply}
        onRunBatch={handleRunBatch}
      />

      {/* AI Copilot Drawer Modal */}
      <AICopilotModal
        isOpen={isCopilotOpen}
        onClose={() => setIsCopilotOpen(false)}
        stats={stats}
      />

      {/* Forensic Transaction Detail Modal */}
      <PaymentDetailModal
        payment={selectedPayment}
        onClose={() => setSelectedPayment(null)}
      />

    </div>
  );
}

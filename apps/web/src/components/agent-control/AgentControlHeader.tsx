'use client';

import React from 'react';
import { useAuth } from '@/components/auth/AuthProvider';
import { useRunAgentWorkflow } from '@/lib/queries/useOpportunityOs';
import { useAgentControlStore } from './useAgentControlStore';
import {
  Activity,
  Radio,
  RotateCcw,
  ShieldCheck,
  AlertTriangle,
  Clock,
  Layers,
  Search,
  Play,
} from 'lucide-react';

export function AgentControlHeader() {
  const { user } = useAuth();
  const runWorkflow = useRunAgentWorkflow();
  const {
    metrics,
    streamingSpeed,
    isStreaming,
    statusFilter,
    searchQuery,
    checkpointerBackend,
    sseConnected,
    setStreamingSpeed,
    toggleStreaming,
    setStatusFilter,
    setSearchQuery,
    resetCamera,
    setActiveSessionId,
    setCommandLog,
  } = useAgentControlStore();

  const handleLaunchRun = async () => {
    try {
      const res = await runWorkflow.mutateAsync({
        query: 'Find eligible software & ML internships and prepare tailored application',
        workflowType: 'full_pipeline',
      });
      setActiveSessionId(res.sessionId);
      setCommandLog(
        `LangGraph (${res.checkpointerBackend}) ran to '${res.status}': ${res.message}`
      );
    } catch (err) {
      setCommandLog(err instanceof Error ? err.message : 'Failed to launch autonomous workflow.');
    }
  };

  return (
    <div className="border-b border-white/[0.08] bg-[#070A11] px-4 sm:px-6 py-3.5 space-y-3">
      {/* Top Row: Page Title, Operational Status & Telemetry Controls */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        {/* Brand & Purpose */}
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.2)]">
            <Radio className="h-4 w-4 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2.5">
              <h1 className="text-base font-bold tracking-tight text-white font-sans">
                NexteRaS Agent Control Center
              </h1>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-cyan-950/80 text-cyan-300 border border-cyan-800/60 font-semibold flex items-center gap-1.5">
                <span className="h-1.5 w-1.5 rounded-full bg-cyan-400 animate-pulse" />
                Live System
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5 font-sans">
              Monitor agent activity, communication and workflow execution.
            </p>
          </div>
        </div>

        {/* Right Telemetry Controls (Cadence & Streaming State) */}
        <div className="flex items-center gap-2">
          {/* Cadence Speed */}
          <div className="flex items-center p-0.5 rounded-lg border border-white/[0.08] bg-[#0B0F1A] text-xs font-mono">
            {(['high', 'med', 'low', 'paused'] as const).map((speed) => (
              <button
                key={speed}
                type="button"
                onClick={() => setStreamingSpeed(speed)}
                className={`px-2.5 py-1 rounded uppercase tracking-wider text-[10px] font-semibold transition ${
                  streamingSpeed === speed
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {speed}
              </button>
            ))}
          </div>

          {/* Streaming Pulse Indicator */}
          <button
            type="button"
            onClick={toggleStreaming}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-mono transition ${
              isStreaming
                ? 'border-emerald-500/40 bg-emerald-950/30 text-emerald-300'
                : 'border-slate-800 bg-slate-900/60 text-slate-400'
            }`}
          >
            <span
              className={`h-2 w-2 rounded-full ${
                isStreaming ? 'bg-emerald-400 animate-ping' : 'bg-slate-500'
              }`}
            />
            <span>{isStreaming ? 'STREAMING ACTIVE' : 'STREAM PAUSED'}</span>
          </button>

          {/* Launch Autonomous LangGraph Pipeline */}
          {user && (
            <button
              type="button"
              disabled={runWorkflow.isPending}
              onClick={() => void handleLaunchRun()}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-cyan-500/50 bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-200 text-xs font-mono font-semibold transition disabled:opacity-50"
            >
              <Play className="h-3.5 w-3.5" />
              <span>{runWorkflow.isPending ? 'RUNNING GRAPH...' : 'LAUNCH PIPELINE'}</span>
            </button>
          )}

          <span className="hidden xl:inline-flex items-center px-2.5 py-1 rounded-lg border border-white/[0.08] bg-[#0B0F1A] text-[10px] font-mono text-slate-300">
            DB: {checkpointerBackend} {sseConnected ? '• SSE' : ''}
          </span>

          {/* Reset Camera View */}
          <button
            type="button"
            onClick={resetCamera}
            className="p-1.5 rounded-lg border border-white/[0.08] bg-[#0B0F1A] hover:bg-white/[0.05] text-slate-400 hover:text-white transition"
            title="Reset Network Graph Camera"
          >
            <RotateCcw className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      {/* Metric Counters Bar (Clickable Filter Shortcuts) */}
      <div className="flex flex-wrap items-center justify-between gap-3 pt-1 text-xs font-mono">
        <div className="flex flex-wrap items-center gap-2">
          {/* Total Agents */}
          <button
            type="button"
            onClick={() => setStatusFilter('all')}
            className={`px-3 py-1.5 rounded-lg border transition flex items-center gap-1.5 ${
              statusFilter === 'all'
                ? 'border-cyan-500/50 bg-cyan-950/40 text-cyan-300'
                : 'border-white/[0.07] bg-white/[0.02] text-slate-300 hover:border-white/20'
            }`}
          >
            <Layers className="h-3.5 w-3.5 text-cyan-400" />
            <span>TOTAL AGENTS:</span>
            <span className="font-bold text-white">{metrics.totalAgents}</span>
          </button>

          {/* Active Agents */}
          <button
            type="button"
            onClick={() => setStatusFilter(statusFilter === 'active' ? 'all' : 'active')}
            className={`px-3 py-1.5 rounded-lg border transition flex items-center gap-1.5 ${
              statusFilter === 'active'
                ? 'border-emerald-500/60 bg-emerald-950/50 text-emerald-300 shadow-[0_0_12px_rgba(16,185,129,0.2)]'
                : 'border-white/[0.07] bg-white/[0.02] text-slate-300 hover:border-white/20'
            }`}
          >
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>ACTIVE:</span>
            <span className="font-bold text-emerald-400">{metrics.activeCount}</span>
          </button>

          {/* Busy Agents */}
          <button
            type="button"
            onClick={() => setStatusFilter(statusFilter === 'busy' ? 'all' : 'busy')}
            className={`px-3 py-1.5 rounded-lg border transition flex items-center gap-1.5 ${
              statusFilter === 'busy'
                ? 'border-violet-500/60 bg-violet-950/50 text-violet-300 shadow-[0_0_12px_rgba(139,92,246,0.2)]'
                : 'border-white/[0.07] bg-white/[0.02] text-slate-300 hover:border-white/20'
            }`}
          >
            <Activity className="h-3.5 w-3.5 text-violet-400" />
            <span>BUSY:</span>
            <span className="font-bold text-violet-400">{metrics.busyCount}</span>
          </button>

          {/* Idle Agents */}
          <button
            type="button"
            onClick={() => setStatusFilter(statusFilter === 'idle' ? 'all' : 'idle')}
            className={`px-3 py-1.5 rounded-lg border transition flex items-center gap-1.5 ${
              statusFilter === 'idle'
                ? 'border-blue-500/60 bg-blue-950/50 text-blue-300'
                : 'border-white/[0.07] bg-white/[0.02] text-slate-300 hover:border-white/20'
            }`}
          >
            <Clock className="h-3.5 w-3.5 text-blue-400" />
            <span>IDLE:</span>
            <span className="font-bold text-blue-300">{metrics.idleCount}</span>
          </button>

          {/* Awaiting Approval */}
          <button
            type="button"
            onClick={() => setStatusFilter(statusFilter === 'awaiting_approval' ? 'all' : 'awaiting_approval')}
            className={`px-3 py-1.5 rounded-lg border transition flex items-center gap-1.5 ${
              statusFilter === 'awaiting_approval'
                ? 'border-amber-500/60 bg-amber-950/50 text-amber-300 shadow-[0_0_12px_rgba(245,158,11,0.25)]'
                : 'border-white/[0.07] bg-white/[0.02] text-slate-300 hover:border-white/20'
            }`}
          >
            <ShieldCheck className="h-3.5 w-3.5 text-amber-400" />
            <span>APPROVALS:</span>
            <span className="font-bold text-amber-400">{metrics.pendingApprovals} PENDING</span>
          </button>

          {/* Failed / Degraded */}
          <button
            type="button"
            onClick={() => setStatusFilter(statusFilter === 'failed' ? 'all' : 'failed')}
            className={`px-3 py-1.5 rounded-lg border transition flex items-center gap-1.5 ${
              statusFilter === 'failed'
                ? 'border-red-500/60 bg-red-950/50 text-red-300'
                : 'border-white/[0.07] bg-white/[0.02] text-slate-300 hover:border-white/20'
            }`}
          >
            <AlertTriangle className="h-3.5 w-3.5 text-red-400" />
            <span>FAILED:</span>
            <span className="font-bold text-red-400">{metrics.failedCount}</span>
          </button>
        </div>

        {/* Search Input Filter */}
        <div className="relative min-w-[220px]">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search agent or tool..."
            className="w-full rounded-lg border border-white/[0.08] bg-[#0A0D16] pl-8 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:border-cyan-500/50 focus:outline-none font-mono"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[10px] text-slate-400 hover:text-white"
            >
              ✕
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

'use client';

import React, { useState } from 'react';
import { useAuth } from '@/components/auth/AuthProvider';
import { useCommandAgentSession, useRunAgentWorkflow } from '@/lib/queries/useOpportunityOs';
import { useAgentControlStore } from './useAgentControlStore';
import {
  Cpu,
  Play,
  Pause,
  Zap,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Shield,
  Layers,
  Wrench,
  Terminal,
  Activity,
  ExternalLink,
} from 'lucide-react';
import { Phase5IntegrationSurface } from './Phase5IntegrationSurface';

export function AgentInspector() {
  const { user } = useAuth();
  const runWorkflow = useRunAgentWorkflow();
  const commandMutation = useCommandAgentSession();
  const {
    agents,
    activeSessionId,
    selectedAgentId,
    selectAgent,
    pauseAgent,
    resumeAgent,
    triggerAgentTask,
    setActiveSessionId,
    setCommandLog,
  } = useAgentControlStore();

  const [activeTab, setActiveTab] = useState<'inspector' | 'surface'>('inspector');

  const selectedAgent = agents.find((a) => a.id === selectedAgentId) || agents[0];

  const handleDispatchSelected = async () => {
    triggerAgentTask(selectedAgent.id, 'Dispatching workflow...');
    if (!user) return;
    try {
      const wfType =
        selectedAgent.category === 'discovery'
          ? 'discovery'
          : selectedAgent.category === 'resume'
          ? 'resume_tailoring'
          : 'full_pipeline';
      const res = await runWorkflow.mutateAsync({
        query: `${selectedAgent.name}: ${selectedAgent.role}`,
        workflowType: wfType,
      });
      setActiveSessionId(res.sessionId);
      setCommandLog(`[${selectedAgent.code}] Dispatched (${res.status}): ${res.message}`);
    } catch (err) {
      setCommandLog(err instanceof Error ? err.message : 'Agent dispatch failed');
    }
  };

  const handlePauseResume = async (action: 'pause' | 'resume') => {
    if (action === 'pause') pauseAgent(selectedAgent.id);
    else resumeAgent(selectedAgent.id);
    if (user && activeSessionId) {
      try {
        const res = await commandMutation.mutateAsync({
          sessionId: activeSessionId,
          action,
        });
        setCommandLog(res.reply);
      } catch (err) {
        setCommandLog(err instanceof Error ? err.message : 'Command failed');
      }
    }
  };

  return (
    <div className="flex flex-col h-full border-l border-white/[0.08] bg-[#07090F] overflow-hidden text-xs">
      {/* 1. Inspector Navigation Tabs */}
      <div className="flex items-center border-b border-white/[0.08] bg-[#080C14] text-xs font-mono">
        <button
          type="button"
          onClick={() => setActiveTab('inspector')}
          className={`flex-1 py-3 text-center uppercase tracking-wider font-semibold border-b-2 transition ${
            activeTab === 'inspector'
              ? 'border-cyan-400 text-cyan-300 bg-white/[0.03]'
              : 'border-transparent text-slate-400 hover:text-white'
          }`}
        >
          Agent Inspector
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('surface')}
          className={`flex-1 py-3 text-center uppercase tracking-wider font-semibold border-b-2 transition ${
            activeTab === 'surface'
              ? 'border-cyan-400 text-cyan-300 bg-white/[0.03]'
              : 'border-transparent text-slate-400 hover:text-white'
          }`}
        >
          Integrations
        </button>
      </div>

      {activeTab === 'surface' ? (
        <Phase5IntegrationSurface />
      ) : (
        <div className="flex-1 overflow-y-auto p-4 space-y-5 custom-scrollbar">
          {/* 2. Agent Identity Card */}
          <div className="p-4 rounded-xl border border-white/[0.08] bg-[#0A0E1A] space-y-3">
            <div className="flex items-center justify-between">
              <span className="px-2 py-0.5 rounded font-mono text-[10px] bg-cyan-950 text-cyan-300 border border-cyan-800 font-bold">
                {selectedAgent.code}
              </span>
              <span
                className={`px-2 py-0.5 rounded-full text-[10px] font-mono uppercase font-semibold flex items-center gap-1 ${
                  selectedAgent.status === 'active'
                    ? 'bg-emerald-950/80 text-emerald-300 border border-emerald-800/60'
                    : selectedAgent.status === 'busy'
                    ? 'bg-violet-950/80 text-violet-300 border border-violet-800/60'
                    : selectedAgent.status === 'awaiting_approval'
                    ? 'bg-amber-950/80 text-amber-300 border border-amber-800/60'
                    : 'bg-slate-900 text-slate-400 border border-slate-800'
                }`}
              >
                <span className="h-1.5 w-1.5 rounded-full bg-current" />
                {selectedAgent.status}
              </span>
            </div>

            <div>
              <h3 className="text-sm font-bold text-white tracking-tight">{selectedAgent.name}</h3>
              <p className="text-[11px] font-mono text-cyan-400/90 mt-0.5">{selectedAgent.role}</p>
            </div>

            <p className="text-[11px] text-slate-300 leading-relaxed border-t border-white/[0.06] pt-2">
              {selectedAgent.description}
            </p>

            <div className="flex items-center justify-between pt-1 text-[10px] font-mono text-slate-400">
              <span>TIER:</span>
              <span className="text-slate-200 font-semibold">{selectedAgent.implementationTier}</span>
            </div>
          </div>

          {/* 3. Operational Action Controls (Real Interactive Actions) */}
          <div className="space-y-2">
            <div className="text-[10px] font-mono uppercase tracking-wider text-slate-500 font-semibold">
              OPERATIONAL CONTROLS
            </div>

            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => void handleDispatchSelected()}
                disabled={selectedAgent.status === 'busy' || runWorkflow.isPending}
                className="py-2 px-3 rounded-lg bg-cyan-500/15 hover:bg-cyan-500/25 border border-cyan-500/40 text-cyan-300 font-semibold text-[11px] font-mono flex items-center justify-center gap-1.5 transition disabled:opacity-50"
              >
                <Zap className="h-3.5 w-3.5" />
                <span>{runWorkflow.isPending ? 'Running...' : 'Run Agent'}</span>
              </button>

              {selectedAgent.status === 'idle' ? (
                <button
                  type="button"
                  onClick={() => void handlePauseResume('resume')}
                  className="py-2 px-3 rounded-lg bg-emerald-500/15 hover:bg-emerald-500/25 border border-emerald-500/40 text-emerald-300 font-semibold text-[11px] font-mono flex items-center justify-center gap-1.5 transition"
                >
                  <Play className="h-3.5 w-3.5" />
                  <span>Resume</span>
                </button>
              ) : (
                <button
                  type="button"
                  onClick={() => void handlePauseResume('pause')}
                  className="py-2 px-3 rounded-lg bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] text-slate-300 font-semibold text-[11px] font-mono flex items-center justify-center gap-1.5 transition"
                >
                  <Pause className="h-3.5 w-3.5 text-amber-400" />
                  <span>Pause Agent</span>
                </button>
              )}
            </div>

            {selectedAgent.currentTask && (
              <div className="p-2.5 rounded-lg border border-white/[0.06] bg-[#0A0D16] text-[11px] font-mono flex items-start gap-2">
                <Activity className="h-3.5 w-3.5 text-cyan-400 shrink-0 mt-0.5 animate-pulse" />
                <div className="space-y-0.5">
                  <div className="text-[9px] text-slate-500 uppercase tracking-wider">CURRENT STATE</div>
                  <div className="text-slate-300">{selectedAgent.currentTask}</div>
                </div>
              </div>
            )}
          </div>

          {/* 4. Telemetry Metrics */}
          <div className="p-3 rounded-xl border border-white/[0.06] bg-[#080B14] space-y-2">
            <div className="text-[10px] font-mono uppercase tracking-wider text-slate-500 font-semibold">
              EXECUTION TELEMETRY
            </div>

            <div className="grid grid-cols-3 gap-2 text-center text-xs font-mono">
              <div className="p-2 rounded bg-white/[0.02] border border-white/[0.05]">
                <div className="text-[9px] text-slate-500">RUNS</div>
                <div className="text-white font-bold mt-0.5">{selectedAgent.executionCount}</div>
              </div>
              <div className="p-2 rounded bg-white/[0.02] border border-white/[0.05]">
                <div className="text-[9px] text-slate-500">SUCCESS</div>
                <div className="text-emerald-400 font-bold mt-0.5">{selectedAgent.successRate}%</div>
              </div>
              <div className="p-2 rounded bg-white/[0.02] border border-white/[0.05]">
                <div className="text-[9px] text-slate-500">LATENCY</div>
                <div className="text-cyan-400 font-bold mt-0.5">{selectedAgent.avgLatencyMs}ms</div>
              </div>
            </div>
          </div>

          {/* 5. Tools & Capabilities */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-[10px] font-mono uppercase tracking-wider text-slate-500 font-semibold">
              <span>ACCESS TOOLS ({selectedAgent.tools.length})</span>
              <Wrench className="h-3 w-3" />
            </div>

            <div className="flex flex-wrap gap-1.5">
              {selectedAgent.tools.map((t) => (
                <span
                  key={t}
                  className="px-2 py-1 rounded-md text-[10px] font-mono bg-white/[0.03] text-slate-300 border border-white/[0.07] hover:border-cyan-500/40 hover:text-cyan-300 transition"
                >
                  {t}()
                </span>
              ))}
            </div>
          </div>

          {/* 6. Capabilities List */}
          <div className="space-y-2">
            <div className="text-[10px] font-mono uppercase tracking-wider text-slate-500 font-semibold">
              SYSTEM CAPABILITIES
            </div>

            <div className="space-y-1 text-[11px] text-slate-300">
              {selectedAgent.capabilities.map((c, i) => (
                <div key={i} className="flex items-start gap-2">
                  <span className="text-cyan-400 mt-1">•</span>
                  <span>{c}</span>
                </div>
              ))}
            </div>
          </div>

          {/* 7. Connected Network Entities (Clickable to jump focus) */}
          <div className="space-y-2">
            <div className="text-[10px] font-mono uppercase tracking-wider text-slate-500 font-semibold">
              CONNECTED AGENTS ({selectedAgent.connectedAgentIds.length})
            </div>

            <div className="space-y-1.5">
              {selectedAgent.connectedAgentIds.map((cId) => {
                const target = agents.find((a) => a.id === cId);
                if (!target) return null;

                return (
                  <button
                    key={cId}
                    type="button"
                    onClick={() => selectAgent(cId)}
                    className="w-full p-2 rounded-lg border border-white/[0.06] bg-white/[0.02] hover:bg-white/[0.06] hover:border-cyan-500/40 flex items-center justify-between text-left transition group"
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-mono text-cyan-400 font-bold">[{target.code}]</span>
                      <span className="text-[11px] text-slate-300 group-hover:text-white font-medium">
                        {target.name}
                      </span>
                    </div>
                    <ArrowRight className="h-3.5 w-3.5 text-slate-600 group-hover:text-cyan-400 group-hover:translate-x-0.5 transition" />
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

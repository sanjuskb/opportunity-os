'use client';

import React from 'react';
import { useAgentControlStore } from './useAgentControlStore';
import { AgentNode } from './types';
import { ArrowRight, CheckCircle2, Clock, Activity, ShieldCheck, AlertTriangle } from 'lucide-react';

interface AgentInventoryViewProps {
  onClose?: () => void;
}

export function AgentInventoryView({ onClose }: AgentInventoryViewProps) {
  const {
    agents,
    selectedAgentId,
    categoryFilter,
    statusFilter,
    searchQuery,
    selectAgent,
  } = useAgentControlStore();

  const filteredAgents = agents.filter((a) => {
    if (categoryFilter !== 'all' && a.category !== categoryFilter) return false;
    if (statusFilter !== 'all' && a.status !== statusFilter) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      return (
        a.name.toLowerCase().includes(q) ||
        a.code.toLowerCase().includes(q) ||
        a.role.toLowerCase().includes(q)
      );
    }
    return true;
  });

  return (
    <div className="p-4 sm:p-6 space-y-4 font-mono text-xs text-slate-300">
      <div className="flex items-center justify-between pb-3 border-b border-white/[0.08]">
        <div>
          <h2 className="text-sm font-bold text-white uppercase tracking-wider">
            STRUCTURED AGENT INVENTORY ({filteredAgents.length})
          </h2>
          <p className="text-[11px] text-slate-400">
            Bidirectional synchronization: selecting any agent updates the network graph and inspector.
          </p>
        </div>
        {onClose && (
          <button
            type="button"
            onClick={onClose}
            className="px-3 py-1 rounded-lg border border-white/10 hover:bg-white/[0.06] text-white transition text-xs"
          >
            Switch to Graph View
          </button>
        )}
      </div>

      {/* Structured Table */}
      <div className="overflow-x-auto rounded-xl border border-white/[0.08] bg-[#070A12]">
        <table className="w-full text-left text-xs">
          <thead className="bg-[#0B0F1A] text-[10px] uppercase tracking-wider text-slate-400 border-b border-white/[0.06]">
            <tr>
              <th className="py-3 px-4">CODE</th>
              <th className="py-3 px-4">AGENT NAME & ROLE</th>
              <th className="py-3 px-4">CATEGORY</th>
              <th className="py-3 px-4">STATUS</th>
              <th className="py-3 px-4">SUCCESS</th>
              <th className="py-3 px-4">LATENCY</th>
              <th className="py-3 px-4">LINKS</th>
              <th className="py-3 px-4">CURRENT STATE</th>
              <th className="py-3 px-4 text-right">ACTION</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/[0.04]">
            {filteredAgents.map((agent) => {
              const isSelected = selectedAgentId === agent.id;
              return (
                <tr
                  key={agent.id}
                  onClick={() => selectAgent(agent.id)}
                  className={`cursor-pointer transition ${
                    isSelected
                      ? 'bg-cyan-950/40 text-white'
                      : 'hover:bg-white/[0.02] text-slate-300'
                  }`}
                >
                  <td className="py-3 px-4 font-bold text-cyan-400">[{agent.code}]</td>
                  <td className="py-3 px-4">
                    <div className="font-semibold text-white">{agent.name}</div>
                    <div className="text-[10px] text-slate-400">{agent.role}</div>
                  </td>
                  <td className="py-3 px-4 uppercase text-[10px] text-slate-400">{agent.category}</td>
                  <td className="py-3 px-4">
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] uppercase font-semibold inline-flex items-center gap-1 ${
                        agent.status === 'active'
                          ? 'bg-emerald-950/80 text-emerald-300 border border-emerald-800/60'
                          : agent.status === 'busy'
                          ? 'bg-violet-950/80 text-violet-300 border border-violet-800/60'
                          : agent.status === 'awaiting_approval'
                          ? 'bg-amber-950/80 text-amber-300 border border-amber-800/60'
                          : 'bg-slate-900 text-slate-400 border border-slate-800'
                      }`}
                    >
                      <span className="h-1.5 w-1.5 rounded-full bg-current" />
                      {agent.status}
                    </span>
                  </td>
                  <td className="py-3 px-4 font-bold text-emerald-400">{agent.successRate}%</td>
                  <td className="py-3 px-4 text-cyan-300">{agent.avgLatencyMs}ms</td>
                  <td className="py-3 px-4 text-slate-400">{agent.connectedAgentIds.length} peers</td>
                  <td className="py-3 px-4 text-[11px] text-slate-300 max-w-[220px] truncate">
                    {agent.currentTask || 'Idle'}
                  </td>
                  <td className="py-3 px-4 text-right">
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        selectAgent(agent.id);
                        if (onClose) onClose();
                      }}
                      className="px-2.5 py-1 rounded bg-white/[0.04] hover:bg-cyan-500/20 hover:text-cyan-300 border border-white/[0.08] text-[10px] transition inline-flex items-center gap-1"
                    >
                      <span>Focus</span>
                      <ArrowRight className="h-3 w-3" />
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

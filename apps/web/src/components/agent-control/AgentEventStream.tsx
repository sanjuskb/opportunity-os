'use client';

import React, { useState } from 'react';
import { useAgentControlStore } from './useAgentControlStore';
import { EventSeverity } from './types';
import {
  Activity,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  ShieldCheck,
  Zap,
  Filter,
  Check,
} from 'lucide-react';

export function AgentEventStream() {
  const {
    events,
    workflows,
    metrics,
    selectAgent,
    approvePendingAction,
    rejectPendingAction,
  } = useAgentControlStore();

  const [severityFilter, setSeverityFilter] = useState<EventSeverity | 'all'>('all');

  const filteredEvents = events.filter((ev) => {
    if (severityFilter === 'all') return true;
    return ev.severity === severityFilter;
  });

  const activePipeline = workflows[0]; // Primary pipeline

  return (
    <div className="flex flex-col h-full border-r border-white/[0.08] bg-[#07090F] overflow-hidden text-xs">
      {/* 1. Event Stream Header */}
      <div className="p-3.5 border-b border-white/[0.08] bg-[#080C14] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity className="h-4 w-4 text-cyan-400 animate-pulse" />
          <span className="font-mono text-xs font-bold uppercase tracking-wider text-white">
            EVENT STREAM
          </span>
          <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-cyan-950/70 text-cyan-300 border border-cyan-800/60">
            {events.length}
          </span>
        </div>

        {/* Severity Filter */}
        <div className="flex items-center gap-1 text-[10px] font-mono">
          <button
            type="button"
            onClick={() => setSeverityFilter('all')}
            className={`px-1.5 py-0.5 rounded transition ${
              severityFilter === 'all'
                ? 'bg-white/10 text-white font-semibold'
                : 'text-slate-500 hover:text-slate-300'
            }`}
          >
            ALL
          </button>
          <button
            type="button"
            onClick={() => setSeverityFilter('warning')}
            className={`px-1.5 py-0.5 rounded transition ${
              severityFilter === 'warning'
                ? 'bg-amber-950 text-amber-300 font-semibold'
                : 'text-slate-500 hover:text-amber-400'
            }`}
          >
            GATES
          </button>
          <button
            type="button"
            onClick={() => setSeverityFilter('success')}
            className={`px-1.5 py-0.5 rounded transition ${
              severityFilter === 'success'
                ? 'bg-emerald-950 text-emerald-300 font-semibold'
                : 'text-slate-500 hover:text-emerald-400'
            }`}
          >
            OK
          </button>
        </div>
      </div>

      {/* 2. Scrollable Events Feed */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2.5 max-h-[380px] custom-scrollbar">
        {filteredEvents.length === 0 ? (
          <div className="py-12 text-center text-slate-500 font-mono text-xs">
            No events match current filter.
          </div>
        ) : (
          filteredEvents.map((ev) => {
            const isApproval = ev.type === 'approval_required';
            return (
              <div
                key={ev.id}
                onClick={() => selectAgent(ev.sourceAgentId)}
                className={`p-2.5 rounded-xl border transition-all duration-200 cursor-pointer space-y-1.5 ${
                  isApproval
                    ? 'border-amber-500/40 bg-amber-950/20 hover:border-amber-500/70 shadow-[0_0_15px_rgba(245,158,11,0.1)]'
                    : 'border-white/[0.06] bg-white/[0.02] hover:border-white/15 hover:bg-white/[0.04]'
                }`}
              >
                {/* Event Meta Line */}
                <div className="flex items-center justify-between text-[10px] font-mono">
                  <div className="flex items-center gap-1.5">
                    <span
                      className={`h-1.5 w-1.5 rounded-full ${
                        ev.severity === 'error'
                          ? 'bg-red-400 animate-ping'
                          : ev.severity === 'warning'
                          ? 'bg-amber-400'
                          : ev.severity === 'success'
                          ? 'bg-emerald-400'
                          : 'bg-cyan-400'
                      }`}
                    />
                    <span className="font-semibold text-slate-300">[{ev.sourceAgentCode}]</span>
                    <span className="text-slate-400 truncate max-w-[130px]">{ev.sourceAgentName}</span>
                  </div>
                  <span className="text-slate-500 font-mono">{ev.timestamp}</span>
                </div>

                {/* Event Description */}
                <p className="text-[11px] text-slate-300 leading-snug">{ev.description}</p>

                {/* Interactive Human Approval Buttons */}
                {isApproval && (
                  <div className="pt-1.5 flex items-center gap-2">
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        approvePendingAction();
                      }}
                      className="flex-1 py-1 px-2 rounded-lg bg-emerald-500/20 hover:bg-emerald-500/30 border border-emerald-500/50 text-emerald-300 font-semibold text-[10px] flex items-center justify-center gap-1 transition"
                    >
                      <Check className="h-3 w-3" /> Approve Dispatch
                    </button>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        rejectPendingAction();
                      }}
                      className="py-1 px-2 rounded-lg bg-red-500/20 hover:bg-red-500/30 border border-red-500/40 text-red-300 font-semibold text-[10px] transition"
                    >
                      Abort
                    </button>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* 3. Telemetry Counters Bar (Matches VORTEX reference) */}
      <div className="p-3 border-t border-b border-white/[0.08] bg-[#060910] space-y-2">
        <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
          <span className="font-semibold uppercase tracking-wider text-slate-300">TELEMETRY COUNTERS</span>
          <span className="text-cyan-400">LIVE SENSORS</span>
        </div>
        <div className="grid grid-cols-2 gap-2 text-[11px] font-mono">
          <div className="p-2 rounded-lg border border-white/[0.06] bg-white/[0.02]">
            <div className="text-[10px] text-slate-500">EVENT VELOCITY</div>
            <div className="text-sm font-bold text-white mt-0.5">{metrics.eventsPerMinute} ev/min</div>
          </div>
          <div className="p-2 rounded-lg border border-white/[0.06] bg-white/[0.02]">
            <div className="text-[10px] text-slate-500">SYSTEM LATENCY</div>
            <div className="text-sm font-bold text-cyan-400 mt-0.5">{metrics.avgLatencyMs} ms</div>
          </div>
        </div>
      </div>

      {/* 4. Active Workflow Pipeline / Quality Stages (Matches VORTEX reference) */}
      <div className="p-3 bg-[#05070B] space-y-2.5 flex-1 overflow-y-auto">
        <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
          <span className="font-semibold uppercase tracking-wider text-slate-300">QUALITY STAGES</span>
          <span className="text-violet-400">{activePipeline.stages.length} Steps</span>
        </div>

        <div className="text-[11px] font-medium text-slate-400 truncate">
          {activePipeline.name}
        </div>

        <div className="space-y-1.5 pt-1">
          {activePipeline.stages.map((stage, idx) => (
            <div
              key={stage.name}
              onClick={() => selectAgent(stage.agentId)}
              className="flex items-center justify-between p-2 rounded-lg border border-white/[0.05] bg-white/[0.01] hover:bg-white/[0.04] transition cursor-pointer text-[11px] font-mono"
            >
              <div className="flex items-center gap-2">
                <span className="text-[10px] text-slate-500">0{idx + 1}</span>
                <span
                  className={
                    stage.status === 'active'
                      ? 'text-amber-400 font-semibold'
                      : stage.status === 'completed'
                      ? 'text-slate-200'
                      : 'text-slate-500'
                  }
                >
                  {stage.name}
                </span>
              </div>

              <div>
                {stage.status === 'completed' && (
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                )}
                {stage.status === 'active' && (
                  <span className="flex h-2 w-2 rounded-full bg-amber-400 animate-ping" />
                )}
                {stage.status === 'pending' && (
                  <span className="text-[10px] text-slate-600">PENDING</span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

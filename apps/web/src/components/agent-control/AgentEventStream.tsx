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
  Check,
  Clock,
  Radio,
  BarChart2,
  GitBranch,
  Layers,
  ChevronRight,
  RefreshCw,
  XCircle,
  TrendingUp,
} from 'lucide-react';

export function AgentEventStream() {
  const {
    events,
    workflows,
    metrics,
    activeWorkflowId,
    setActiveWorkflowId,
    selectAgent,
    approvePendingAction,
    rejectPendingAction,
  } = useAgentControlStore();

  const [activeTab, setActiveTab] = useState<'events' | 'telemetry' | 'workflows'>('events');
  const [severityFilter, setSeverityFilter] = useState<EventSeverity | 'all'>('all');

  const filteredEvents = events.filter((ev) => {
    if (severityFilter === 'all') return true;
    return ev.severity === severityFilter;
  });

  const selectedWorkflow =
    workflows.find((w) => w.id === activeWorkflowId) || workflows[0];

  return (
    <div className="flex flex-col h-full border-r border-white/[0.08] bg-[#07090F] overflow-hidden text-xs">
      {/* 1. Horizontal Tab Navigation Bar */}
      <div className="flex items-center border-b border-white/[0.08] bg-[#080C14] shrink-0">
        <button
          type="button"
          onClick={() => setActiveTab('events')}
          className={`flex-1 py-2.5 px-1 text-center text-[11px] font-mono font-semibold uppercase tracking-wider border-b-2 transition relative flex items-center justify-center gap-1 ${
            activeTab === 'events'
              ? 'border-cyan-400 text-cyan-300 bg-white/[0.03]'
              : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-white/[0.01]'
          }`}
        >
          <span>Events</span>
          <span
            className={`px-1.5 py-0.2 rounded text-[10px] font-mono transition ${
              activeTab === 'events'
                ? 'bg-cyan-950 text-cyan-400 border border-cyan-800/80 font-bold'
                : 'bg-white/5 text-slate-500 border border-white/5'
            }`}
          >
            {events.length}
          </span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('telemetry')}
          className={`flex-1 py-2.5 px-1 text-center text-[11px] font-mono font-semibold uppercase tracking-wider border-b-2 transition relative flex items-center justify-center gap-1 ${
            activeTab === 'telemetry'
              ? 'border-cyan-400 text-cyan-300 bg-white/[0.03]'
              : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-white/[0.01]'
          }`}
        >
          <span>Telemetry</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('workflows')}
          className={`flex-1 py-2.5 px-1 text-center text-[11px] font-mono font-semibold uppercase tracking-wider border-b-2 transition relative flex items-center justify-center gap-1 ${
            activeTab === 'workflows'
              ? 'border-cyan-400 text-cyan-300 bg-white/[0.03]'
              : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-white/[0.01]'
          }`}
        >
          <span>Workflows</span>
          <span
            className={`px-1.5 py-0.2 rounded text-[10px] font-mono transition ${
              activeTab === 'workflows'
                ? 'bg-violet-950 text-violet-300 border border-violet-800/80 font-bold'
                : 'bg-white/5 text-slate-500 border border-white/5'
            }`}
          >
            {workflows.length}
          </span>
        </button>
      </div>

      {/* 2. TAB CONTENT (Only one visible at a time, uses full panel with independent internal scroll) */}

      {/* ─── TAB 1: EVENTS ─── */}
      {activeTab === 'events' && (
        <div className="flex-1 flex flex-col overflow-hidden min-h-0">
          {/* Severity Filter Subheader */}
          <div className="px-3 py-2 border-b border-white/[0.06] bg-[#060910] flex items-center justify-between shrink-0">
            <div className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-cyan-400 animate-pulse" />
              <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider">
                Live Event Stream
              </span>
            </div>

            <div className="flex items-center gap-1 text-[10px] font-mono">
              <button
                type="button"
                onClick={() => setSeverityFilter('all')}
                className={`px-2 py-0.5 rounded transition ${
                  severityFilter === 'all'
                    ? 'bg-white/10 text-white font-semibold'
                    : 'text-slate-500 hover:text-slate-300'
                }`}
              >
                All
              </button>
              <button
                type="button"
                onClick={() => setSeverityFilter('warning')}
                className={`px-2 py-0.5 rounded transition ${
                  severityFilter === 'warning'
                    ? 'bg-amber-950/80 text-amber-300 font-semibold border border-amber-800/60'
                    : 'text-slate-500 hover:text-amber-400'
                }`}
              >
                Gates
              </button>
              <button
                type="button"
                onClick={() => setSeverityFilter('success')}
                className={`px-2 py-0.5 rounded transition ${
                  severityFilter === 'success'
                    ? 'bg-emerald-950/80 text-emerald-300 font-semibold border border-emerald-800/60'
                    : 'text-slate-500 hover:text-emerald-400'
                }`}
              >
                OK
              </button>
              <button
                type="button"
                onClick={() => setSeverityFilter('error')}
                className={`px-2 py-0.5 rounded transition ${
                  severityFilter === 'error'
                    ? 'bg-red-950/80 text-red-300 font-semibold border border-red-800/60'
                    : 'text-slate-500 hover:text-red-400'
                }`}
              >
                Errors
              </button>
            </div>
          </div>

          {/* Scrollable Events List */}
          <div className="flex-1 overflow-y-auto p-3 space-y-2.5 custom-scrollbar min-h-0">
            {filteredEvents.length === 0 ? (
              <div className="py-16 text-center text-slate-500 font-mono text-xs space-y-2">
                <p>No events match the selected filter.</p>
                <button
                  type="button"
                  onClick={() => setSeverityFilter('all')}
                  className="px-2.5 py-1 rounded bg-white/5 hover:bg-white/10 text-slate-300 text-[10px] transition"
                >
                  Reset Filter
                </button>
              </div>
            ) : (
              filteredEvents.map((ev) => {
                const isApproval = ev.type === 'approval_required';
                return (
                  <div
                    key={ev.id}
                    onClick={() => selectAgent(ev.sourceAgentId)}
                    className={`p-3 rounded-xl border transition-all duration-200 cursor-pointer space-y-2 ${
                      isApproval
                        ? 'border-amber-500/50 bg-amber-950/20 hover:border-amber-500/80 shadow-[0_0_15px_rgba(245,158,11,0.12)]'
                        : 'border-white/[0.06] bg-white/[0.02] hover:border-white/15 hover:bg-white/[0.04]'
                    }`}
                  >
                    {/* Event Meta Line */}
                    <div className="flex items-center justify-between text-[10px] font-mono">
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <span
                          className={`h-1.5 w-1.5 rounded-full shrink-0 ${
                            ev.severity === 'error'
                              ? 'bg-red-400 animate-ping'
                              : ev.severity === 'warning'
                              ? 'bg-amber-400'
                              : ev.severity === 'success'
                              ? 'bg-emerald-400'
                              : 'bg-cyan-400'
                          }`}
                        />
                        <span className="font-semibold text-cyan-300">[{ev.sourceAgentCode}]</span>
                        <span className="text-slate-300 font-medium truncate max-w-[140px]">
                          {ev.sourceAgentName}
                        </span>
                      </div>
                      <span className="text-slate-500 font-mono">{ev.timestamp}</span>
                    </div>

                    {/* Target Agent / Handoff Direction if present */}
                    {ev.targetAgentName && (
                      <div className="flex items-center gap-1 text-[10px] font-mono text-slate-400 pl-3">
                        <ArrowRight className="h-3 w-3 text-cyan-400 shrink-0" />
                        <span>Target:</span>
                        <span className="text-slate-200 truncate">{ev.targetAgentName}</span>
                      </div>
                    )}

                    {/* Event Description */}
                    <p className="text-[11px] text-slate-300 leading-relaxed">{ev.description}</p>

                    {/* Interactive Human Approval Buttons */}
                    {isApproval && (
                      <div className="pt-2 flex items-center gap-2 border-t border-amber-500/20">
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            approvePendingAction();
                          }}
                          className="flex-1 py-1.5 px-2.5 rounded-lg bg-emerald-500/20 hover:bg-emerald-500/30 border border-emerald-500/50 text-emerald-300 font-semibold text-[10px] flex items-center justify-center gap-1.5 transition"
                        >
                          <Check className="h-3 w-3" /> Approve Dispatch
                        </button>
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            rejectPendingAction();
                          }}
                          className="py-1.5 px-2.5 rounded-lg bg-red-500/20 hover:bg-red-500/30 border border-red-500/40 text-red-300 font-semibold text-[10px] transition"
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
        </div>
      )}

      {/* ─── TAB 2: TELEMETRY ─── */}
      {activeTab === 'telemetry' && (
        <div className="flex-1 overflow-y-auto p-3.5 space-y-4 custom-scrollbar min-h-0">
          {/* Subheader */}
          <div className="flex items-center justify-between pb-2 border-b border-white/[0.06]">
            <div>
              <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-white">
                System Telemetry
              </h4>
              <p className="text-[10px] text-slate-400">Live operational throughput & latency</p>
            </div>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-cyan-950 text-cyan-300 border border-cyan-800/60 font-semibold">
              Live Feed
            </span>
          </div>

          {/* Primary Metric Cards */}
          <div className="grid grid-cols-2 gap-2.5">
            {/* Event Velocity */}
            <div className="p-3 rounded-xl border border-white/[0.08] bg-[#0A0E1A] space-y-1.5">
              <div className="flex items-center justify-between text-[10px] font-mono text-slate-400">
                <span>EVENT VELOCITY</span>
                <Activity className="h-3.5 w-3.5 text-cyan-400" />
              </div>
              <div className="text-lg font-bold font-mono text-white">
                {metrics.eventsPerMinute} <span className="text-xs font-normal text-slate-400">ev/min</span>
              </div>
              {/* Mini Sparkline Visualization */}
              <div className="flex items-end gap-1 h-5 pt-1">
                {[40, 65, 55, 80, 70, 95, 85].map((h, i) => (
                  <div
                    key={i}
                    style={{ height: `${h}%` }}
                    className="flex-1 rounded-sm bg-cyan-500/30 hover:bg-cyan-400 transition"
                  />
                ))}
              </div>
            </div>

            {/* System Latency */}
            <div className="p-3 rounded-xl border border-white/[0.08] bg-[#0A0E1A] space-y-1.5">
              <div className="flex items-center justify-between text-[10px] font-mono text-slate-400">
                <span>SYSTEM LATENCY</span>
                <Zap className="h-3.5 w-3.5 text-emerald-400" />
              </div>
              <div className="text-lg font-bold font-mono text-emerald-400">
                {metrics.avgLatencyMs} <span className="text-xs font-normal text-slate-400">ms</span>
              </div>
              <div className="text-[10px] font-mono text-slate-500 pt-1 flex items-center gap-1">
                <CheckCircle2 className="h-3 w-3 text-emerald-400 shrink-0" />
                <span>&lt; 100ms Target (SLA 99.9%)</span>
              </div>
            </div>
          </div>

          {/* Agent Workforce Execution Distribution */}
          <div className="p-3.5 rounded-xl border border-white/[0.08] bg-[#0A0E1A] space-y-3">
            <div className="flex items-center justify-between text-[10px] font-mono uppercase tracking-wider text-slate-400">
              <span>Workforce Status Distribution</span>
              <span className="text-white font-bold">{metrics.totalAgents} Agents</span>
            </div>

            {/* Multi-segment distribution bar */}
            <div className="h-2.5 rounded-full overflow-hidden bg-slate-800 flex">
              <div
                style={{ width: `${(metrics.activeCount / metrics.totalAgents) * 100}%` }}
                className="bg-emerald-400"
                title={`Active: ${metrics.activeCount}`}
              />
              <div
                style={{ width: `${(metrics.busyCount / metrics.totalAgents) * 100}%` }}
                className="bg-violet-400"
                title={`Busy: ${metrics.busyCount}`}
              />
              <div
                style={{ width: `${(metrics.idleCount / metrics.totalAgents) * 100}%` }}
                className="bg-blue-400"
                title={`Idle: ${metrics.idleCount}`}
              />
              <div
                style={{ width: `${(metrics.failedCount / metrics.totalAgents) * 100}%` }}
                className="bg-red-400"
                title={`Failed: ${metrics.failedCount}`}
              />
            </div>

            {/* Metric breakdown badges */}
            <div className="grid grid-cols-2 gap-2 text-[11px] font-mono pt-1">
              <div className="flex items-center justify-between p-2 rounded-lg bg-white/[0.02] border border-white/[0.04]">
                <div className="flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-emerald-400" />
                  <span className="text-slate-300">Active</span>
                </div>
                <span className="font-bold text-white">{metrics.activeCount}</span>
              </div>

              <div className="flex items-center justify-between p-2 rounded-lg bg-white/[0.02] border border-white/[0.04]">
                <div className="flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-violet-400" />
                  <span className="text-slate-300">Busy</span>
                </div>
                <span className="font-bold text-white">{metrics.busyCount}</span>
              </div>

              <div className="flex items-center justify-between p-2 rounded-lg bg-white/[0.02] border border-white/[0.04]">
                <div className="flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-blue-400" />
                  <span className="text-slate-300">Idle</span>
                </div>
                <span className="font-bold text-white">{metrics.idleCount}</span>
              </div>

              <div className="flex items-center justify-between p-2 rounded-lg bg-white/[0.02] border border-white/[0.04]">
                <div className="flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-amber-400" />
                  <span className="text-slate-300">Approvals</span>
                </div>
                <span className="font-bold text-amber-300">{metrics.pendingApprovals}</span>
              </div>
            </div>
          </div>

          {/* Operational Quality & Success Rates */}
          <div className="p-3.5 rounded-xl border border-white/[0.08] bg-[#0A0E1A] space-y-3">
            <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold">
              Quality & Verification Health
            </div>

            <div className="space-y-2 text-[11px] font-mono">
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Execution Success Rate</span>
                <span className="text-emerald-400 font-bold">99.8%</span>
              </div>
              <div className="h-1.5 rounded-full bg-slate-800 overflow-hidden">
                <div className="h-full bg-emerald-400 rounded-full" style={{ width: '99.8%' }} />
              </div>

              <div className="flex items-center justify-between pt-1">
                <span className="text-slate-400">NLI Fact Grounding Score</span>
                <span className="text-cyan-400 font-bold">100.0%</span>
              </div>
              <div className="h-1.5 rounded-full bg-slate-800 overflow-hidden">
                <div className="h-full bg-cyan-400 rounded-full" style={{ width: '100%' }} />
              </div>
            </div>
          </div>

          {/* Demonstration Notice */}
          <div className="p-2.5 rounded-lg border border-white/[0.06] bg-white/[0.015] text-[10px] font-mono text-slate-500 leading-relaxed">
            Note: Demonstrational telemetry synchronized with local state machine.
          </div>
        </div>
      )}

      {/* ─── TAB 3: WORKFLOWS ─── */}
      {activeTab === 'workflows' && (
        <div className="flex-1 flex flex-col overflow-hidden min-h-0">
          {/* Workflow Selector Bar */}
          <div className="p-3 border-b border-white/[0.06] bg-[#060910] space-y-2 shrink-0">
            <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
              <span className="font-bold uppercase tracking-wider text-slate-300">
                ACTIVE WORKFLOW PIPELINE
              </span>
              <span className="text-violet-400 font-semibold">
                {selectedWorkflow.stages.length} Steps
              </span>
            </div>

            {/* Workflow Pipeline Pills */}
            <div className="flex flex-wrap gap-1.5">
              {workflows.map((wf) => (
                <button
                  key={wf.id}
                  type="button"
                  onClick={() => setActiveWorkflowId(wf.id)}
                  className={`px-2 py-1 rounded-lg text-[10px] font-mono transition text-left ${
                    activeWorkflowId === wf.id
                      ? 'bg-violet-950 text-violet-300 border border-violet-700/80 font-bold'
                      : 'bg-white/[0.03] hover:bg-white/[0.06] text-slate-400 border border-white/[0.06]'
                  }`}
                >
                  {wf.id === 'wf-app-submit'
                    ? 'Application Pipeline'
                    : wf.id === 'wf-discovery'
                    ? 'Opportunity Ingestion'
                    : wf.id === 'wf-resume-tailor'
                    ? 'Resume Tailoring'
                    : 'Voice Interview'}
                </button>
              ))}
            </div>
          </div>

          {/* Selected Workflow Execution Details */}
          <div className="flex-1 overflow-y-auto p-3.5 space-y-4 custom-scrollbar min-h-0">
            {/* Header Card */}
            <div className="p-3.5 rounded-xl border border-white/[0.08] bg-[#0A0E1A] space-y-2">
              <div className="flex items-center justify-between">
                <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-violet-950 text-violet-300 border border-violet-800/80 font-bold">
                  {selectedWorkflow.id}
                </span>
                <span className="flex items-center gap-1.5 text-[10px] font-mono text-amber-300 font-semibold">
                  <span className="h-1.5 w-1.5 rounded-full bg-amber-400 animate-pulse" />
                  IN PROGRESS
                </span>
              </div>

              <h4 className="text-xs font-bold text-white tracking-tight">
                {selectedWorkflow.name}
              </h4>

              <div className="text-[10px] font-mono text-slate-400 border-t border-white/[0.05] pt-1.5">
                <span className="text-slate-500">Trigger:</span> {selectedWorkflow.trigger}
              </div>
            </div>

            {/* Clean Vertical Timeline of Stages */}
            <div className="space-y-1">
              <div className="text-[10px] font-mono uppercase tracking-wider text-slate-500 font-semibold px-1 pb-1">
                EXECUTION STAGES ({selectedWorkflow.stages.length})
              </div>

              <div className="relative pl-3 space-y-2 border-l border-white/[0.08] ml-2">
                {selectedWorkflow.stages.map((stage, idx) => {
                  const isCompleted = stage.status === 'completed';
                  const isActive = stage.status === 'active';
                  const isPending = stage.status === 'pending';

                  return (
                    <div
                      key={stage.name}
                      onClick={() => selectAgent(stage.agentId)}
                      className={`relative p-2.5 rounded-xl border transition-all cursor-pointer group ${
                        isActive
                          ? 'border-amber-500/50 bg-amber-950/20 shadow-[0_0_12px_rgba(245,158,11,0.1)]'
                          : isCompleted
                          ? 'border-white/[0.06] bg-white/[0.02] hover:border-white/15 hover:bg-white/[0.04]'
                          : 'border-white/[0.03] bg-white/[0.01] opacity-75'
                      }`}
                    >
                      {/* Timeline Node Marker on the left border */}
                      <span
                        className={`absolute -left-[19px] top-4 h-2.5 w-2.5 rounded-full border-2 transition ${
                          isCompleted
                            ? 'bg-emerald-400 border-emerald-950'
                            : isActive
                            ? 'bg-amber-400 border-amber-950 animate-ping'
                            : 'bg-slate-700 border-slate-900'
                        }`}
                      />

                      <div className="flex items-center justify-between text-[11px] font-mono">
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] text-slate-500 font-bold">
                            0{idx + 1}
                          </span>
                          <span
                            className={`font-semibold ${
                              isActive
                                ? 'text-amber-300'
                                : isCompleted
                                ? 'text-slate-200'
                                : 'text-slate-500'
                            }`}
                          >
                            {stage.name}
                          </span>
                        </div>

                        <div>
                          {isCompleted && (
                            <span className="flex items-center gap-1 text-[10px] font-mono text-emerald-400 font-medium">
                              <CheckCircle2 className="h-3.5 w-3.5" />
                              <span>{stage.timestamp || 'Done'}</span>
                            </span>
                          )}
                          {isActive && (
                            <span className="px-2 py-0.5 rounded-full text-[9px] font-mono bg-amber-950 text-amber-300 border border-amber-800/80 font-bold">
                              ACTIVE
                            </span>
                          )}
                          {isPending && (
                            <span className="text-[10px] font-mono text-slate-600">
                              PENDING
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Associated Agent Pill */}
                      <div className="mt-1 flex items-center gap-1.5 text-[10px] font-mono text-slate-400">
                        <span className="text-cyan-400 font-semibold">[{stage.agentCode}]</span>
                        <span className="text-slate-500 group-hover:text-slate-300 transition">
                          Click to focus in network
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

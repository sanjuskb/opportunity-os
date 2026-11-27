'use client';

import React, { useState } from 'react';
import { useAuth } from '@/components/auth/AuthProvider';
import { useCommandAgentSession, useRunAgentWorkflow } from '@/lib/queries/useOpportunityOs';
import { useAgentControlStore } from './useAgentControlStore';
import { Terminal, CornerDownLeft } from 'lucide-react';

export function AgentCommandBar() {
  const { user } = useAuth();
  const { commandLog, activeSessionId, dispatchUserCommand, setActiveSessionId, setCommandLog } =
    useAgentControlStore();
  const commandMutation = useCommandAgentSession();
  const runWorkflow = useRunAgentWorkflow();
  const [inputVal, setInputVal] = useState('');

  const executeTextCommand = async (rawText: string) => {
    const trimmed = rawText.trim();
    if (!trimmed) return;
    dispatchUserCommand(trimmed);

    const lower = trimmed.toLowerCase();
    const isFilterKeyword = ['failed', 'error', 'approval', 'gate', 'pending', 'reset', 'clear'].includes(lower);
    if (!user || isFilterKeyword) return;

    if (lower.startsWith('run ') || lower.startsWith('discover ')) {
      try {
        const res = await runWorkflow.mutateAsync({
          query: trimmed.replace(/^(run|discover)\s+/i, ''),
          workflowType: lower.startsWith('discover ') ? 'discovery' : 'full_pipeline',
        });
        setActiveSessionId(res.sessionId);
        setCommandLog(`Launched session ${res.sessionId.slice(0, 8)} (${res.status}): ${res.message}`);
      } catch (err) {
        setCommandLog(err instanceof Error ? err.message : 'Workflow dispatch failed.');
      }
      return;
    }

    if (activeSessionId) {
      try {
        const res = await commandMutation.mutateAsync({
          sessionId: activeSessionId,
          action: lower === 'pause' ? 'pause' : lower === 'resume' ? 'resume' : 'query',
          command: trimmed,
        });
        setCommandLog(res.reply);
      } catch (err) {
        setCommandLog(err instanceof Error ? err.message : 'Operator query failed.');
      }
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputVal.trim()) return;
    void executeTextCommand(inputVal);
    setInputVal('');
  };

  const SHORTCUTS = [
    { label: 'Run ML Internship Pipeline', query: 'run backend & ML internship matching' },
    { label: 'Filter Failed Agents', query: 'failed' },
    { label: 'Inspect Approval Gate', query: 'approval' },
    { label: 'Pause Session', query: 'pause' },
    { label: 'Reset Network View', query: 'reset' },
  ];

  return (
    <div className="border-t border-white/[0.08] bg-[#070A11] p-3 sm:px-6 space-y-2">
      {commandLog && (
        <div className="text-[11px] font-mono text-cyan-300 bg-cyan-950/30 border border-cyan-800/50 px-3 py-1.5 rounded-lg flex items-center justify-between gap-2">
          <span className="truncate">{commandLog}</span>
          <span className="text-[10px] text-slate-500 font-sans shrink-0">Command executed</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="flex items-center gap-3">
        <div className="flex items-center gap-2 pl-2 text-xs font-mono font-bold text-slate-400">
          <Terminal className="h-4 w-4 text-cyan-400" />
          <span className="tracking-wider uppercase">QUERY</span>
        </div>

        <div className="flex-1 relative flex items-center">
          <input
            type="text"
            value={inputVal}
            onChange={(e) => setInputVal(e.target.value)}
            placeholder="Type 'run <goal>' to launch LangGraph, ask about active session state, or filter nodes."
            className="w-full rounded-xl border border-white/[0.09] bg-[#0A0E18] px-4 py-2 text-xs text-white placeholder-slate-500 font-mono focus:border-cyan-500/60 focus:outline-none focus:ring-1 focus:ring-cyan-500/30 transition shadow-inner"
          />
        </div>

        <button
          type="submit"
          disabled={runWorkflow.isPending || commandMutation.isPending}
          className="px-5 py-2 rounded-xl bg-gradient-to-r from-cyan-400 to-sky-400 hover:from-cyan-300 hover:to-sky-300 text-slate-950 font-bold text-xs font-mono uppercase tracking-wider transition shadow-[0_0_15px_rgba(6,182,212,0.3)] flex items-center gap-1.5 disabled:opacity-50"
        >
          <span>{runWorkflow.isPending ? 'RUNNING' : 'EXECUTE'}</span>
          <CornerDownLeft className="h-3.5 w-3.5" />
        </button>
      </form>

      <div className="flex flex-wrap items-center gap-2 pt-0.5 text-[10px] font-mono">
        <span className="text-slate-500 uppercase tracking-wider">SUGGESTED DISPATCHES:</span>
        {SHORTCUTS.map((chip) => (
          <button
            key={chip.label}
            type="button"
            onClick={() => void executeTextCommand(chip.query)}
            className="px-2 py-0.5 rounded-md border border-white/[0.06] bg-white/[0.02] text-slate-400 hover:text-cyan-300 hover:border-cyan-500/40 transition"
          >
            {chip.label}
          </button>
        ))}
      </div>
    </div>
  );
}

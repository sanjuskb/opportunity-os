'use client';

import React from 'react';
import { useAgentControlStore } from './useAgentControlStore';
import { AgentCategory } from './types';

export function AgentCategoryFilterPills() {
  const { categoryFilter, setCategoryFilter, activeWorkflowId, dispatchUserCommand } = useAgentControlStore();

  const CATEGORIES: { id: AgentCategory | 'all'; label: string; prefix: string; color: string }[] = [
    { id: 'all', label: 'ALL ARCHITECTURE', prefix: 'A', color: 'border-cyan-500/40 text-cyan-300' },
    { id: 'orchestration', label: 'ORCHESTRATION', prefix: 'O', color: 'border-cyan-500/40 text-cyan-400' },
    { id: 'discovery', label: 'DISCOVERY', prefix: 'D', color: 'border-blue-500/40 text-blue-400' },
    { id: 'verification', label: 'VERIFICATION', prefix: 'V', color: 'border-emerald-500/40 text-emerald-400' },
    { id: 'resume', label: 'RESUME INTEL', prefix: 'R', color: 'border-violet-500/40 text-violet-400' },
    { id: 'execution', label: 'EXECUTION & SANDBOX', prefix: 'E', color: 'border-amber-500/40 text-amber-400' },
    { id: 'voice', label: 'VOICE & INTERVIEW', prefix: 'S', color: 'border-pink-500/40 text-pink-400' },
  ];

  const WORKFLOW_PRESETS = [
    { label: 'APPLICATION PIPELINE', query: 'approval' },
    { label: 'OPPORTUNITY DISCOVERY', query: 'discovery' },
    { label: 'ATS RESUME FLOW', query: 'resume' },
    { label: 'VOICE INTERACTION', query: 'voice' },
    { label: 'RESET VIEW', query: 'reset' },
  ];

  return (
    <div className="border-b border-white/[0.06] bg-[#06080E] px-4 sm:px-6 py-2.5 space-y-2">
      {/* Top Row: Category Architecture Pills */}
      <div className="flex flex-wrap items-center gap-2">
        {CATEGORIES.map((cat) => {
          const isActive = categoryFilter === cat.id;
          return (
            <button
              key={cat.id}
              type="button"
              onClick={() => setCategoryFilter(cat.id)}
              className={`flex items-center gap-1.5 px-3 py-1 rounded text-[11px] font-mono uppercase tracking-wider transition ${
                isActive
                  ? `bg-white/[0.08] ${cat.color} font-bold shadow-sm ring-1 ring-white/10`
                  : 'bg-white/[0.02] border border-white/[0.06] text-slate-400 hover:text-slate-200 hover:border-white/10'
              }`}
            >
              <span className="opacity-60">[{cat.prefix}]</span>
              <span>{cat.label}</span>
            </button>
          );
        })}
      </div>

      {/* Second Row: Quick Workflow Inspector Shortcuts */}
      <div className="flex flex-wrap items-center gap-2 pt-0.5">
        <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500 mr-1">
          ACTIVE WORKFLOWS:
        </span>
        {WORKFLOW_PRESETS.map((wf) => (
          <button
            key={wf.label}
            type="button"
            onClick={() => dispatchUserCommand(wf.query)}
            className="px-2.5 py-0.5 rounded text-[10px] font-mono uppercase tracking-wider bg-white/[0.03] hover:bg-white/[0.07] border border-white/[0.07] text-slate-400 hover:text-cyan-300 transition"
          >
            {wf.label}
          </button>
        ))}
      </div>
    </div>
  );
}

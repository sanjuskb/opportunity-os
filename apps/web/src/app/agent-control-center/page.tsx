'use client';

import React, { useState } from 'react';
import { DashboardLayout } from '../../components/dashboard/DashboardLayout';
import { AgentControlHeader } from '../../components/agent-control/AgentControlHeader';
import { AgentCategoryFilterPills } from '../../components/agent-control/AgentCategoryFilterPills';
import { AgentNetworkGraph } from '../../components/agent-control/AgentNetworkGraph';
import { AgentEventStream } from '../../components/agent-control/AgentEventStream';
import { AgentInspector } from '../../components/agent-control/AgentInspector';
import { AgentCommandBar } from '../../components/agent-control/AgentCommandBar';
import { AgentInventoryView } from '../../components/agent-control/AgentInventoryView';
import { Network, Table, PanelLeftClose, PanelLeftOpen, PanelRightClose, PanelRightOpen } from 'lucide-react';

export default function AgentControlCenterPage() {
  const [viewMode, setViewMode] = useState<'graph' | 'inventory'>('graph');
  const [mobileTab, setMobileTab] = useState<'network' | 'events' | 'inspector'>('network');
  const [leftPanelOpen, setLeftPanelOpen] = useState(true);
  const [rightPanelOpen, setRightPanelOpen] = useState(true);

  return (
    <DashboardLayout>
      <div className="flex flex-col h-[calc(100vh-5.5rem)] max-h-[960px] bg-[#05070B] text-slate-100 overflow-hidden border border-white/[0.08] rounded-2xl m-2 sm:m-3 shadow-2xl">
        {/* 1. Master Control Header with VORTEX Telemetry Bar */}
        <AgentControlHeader />

        {/* 2. Category Architecture & Quick Workflow Filter Pills */}
        <div className="flex flex-wrap items-center justify-between border-b border-white/[0.06] bg-[#06080E] px-3 sm:px-4 py-1.5 gap-2 shrink-0">
          <div className="flex-1 min-w-[280px]">
            <AgentCategoryFilterPills />
          </div>

          {/* View Toggles & Panel Controls */}
          <div className="flex items-center gap-2 shrink-0">
            {/* Panel Collapse Toggles (Desktop only) */}
            <div className="hidden xl:flex items-center gap-1 p-1 rounded-lg border border-white/[0.08] bg-[#0A0D16] text-[11px] font-mono text-slate-400">
              <button
                type="button"
                onClick={() => setLeftPanelOpen(!leftPanelOpen)}
                className={`p-1.5 rounded hover:text-white transition ${
                  leftPanelOpen ? 'bg-cyan-500/20 text-cyan-300' : 'text-slate-500'
                }`}
                title={leftPanelOpen ? 'Collapse Event Stream' : 'Expand Event Stream'}
              >
                {leftPanelOpen ? <PanelLeftClose className="h-3.5 w-3.5" /> : <PanelLeftOpen className="h-3.5 w-3.5" />}
              </button>
              <button
                type="button"
                onClick={() => setRightPanelOpen(!rightPanelOpen)}
                className={`p-1.5 rounded hover:text-white transition ${
                  rightPanelOpen ? 'bg-cyan-500/20 text-cyan-300' : 'text-slate-500'
                }`}
                title={rightPanelOpen ? 'Collapse Inspector' : 'Expand Inspector'}
              >
                {rightPanelOpen ? <PanelRightClose className="h-3.5 w-3.5" /> : <PanelRightOpen className="h-3.5 w-3.5" />}
              </button>
            </div>

            {/* Graph vs Inventory View Switcher */}
            <div className="flex items-center p-1 rounded-lg border border-white/[0.08] bg-[#0A0D16] text-[11px] font-mono">
              <button
                type="button"
                onClick={() => setViewMode('graph')}
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded transition ${
                  viewMode === 'graph'
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-semibold'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <Network className="h-3.5 w-3.5" />
                <span>Graph</span>
              </button>
              <button
                type="button"
                onClick={() => setViewMode('inventory')}
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded transition ${
                  viewMode === 'inventory'
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-semibold'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <Table className="h-3.5 w-3.5" />
                <span>Inventory</span>
              </button>
            </div>
          </div>
        </div>

        {/* Mobile Viewport Tab Switcher (Visible only < 1024px) */}
        <div className="flex lg:hidden border-b border-white/[0.08] bg-[#090C16] text-xs font-mono shrink-0">
          <button
            type="button"
            onClick={() => setMobileTab('network')}
            className={`flex-1 py-2 text-center font-semibold border-b-2 transition ${
              mobileTab === 'network'
                ? 'border-cyan-400 text-cyan-300 bg-white/[0.03]'
                : 'border-transparent text-slate-400'
            }`}
          >
            Network Graph
          </button>
          <button
            type="button"
            onClick={() => setMobileTab('events')}
            className={`flex-1 py-2 text-center font-semibold border-b-2 transition ${
              mobileTab === 'events'
                ? 'border-cyan-400 text-cyan-300 bg-white/[0.03]'
                : 'border-transparent text-slate-400'
            }`}
          >
            Events Stream
          </button>
          <button
            type="button"
            onClick={() => setMobileTab('inspector')}
            className={`flex-1 py-2 text-center font-semibold border-b-2 transition ${
              mobileTab === 'inspector'
                ? 'border-cyan-400 text-cyan-300 bg-white/[0.03]'
                : 'border-transparent text-slate-400'
            }`}
          >
            Inspector
          </button>
        </div>

        {/* 3. Main Central Studio Space */}
        {viewMode === 'inventory' ? (
          <div className="flex-1 overflow-y-auto min-h-0">
            <AgentInventoryView onClose={() => setViewMode('graph')} />
          </div>
        ) : (
          <div className="flex-1 flex overflow-hidden relative min-h-0">
            {/* Left Column: Event Stream & Telemetry Counters */}
            <div
              className={`shrink-0 transition-all duration-300 z-10 h-full overflow-hidden ${
                leftPanelOpen ? 'w-72 xl:w-80' : 'w-0 hidden'
              } ${mobileTab === 'events' ? 'block w-full' : 'hidden lg:block'}`}
            >
              <AgentEventStream />
            </div>

            {/* Center Column: Interactive Autonomous Agent Graph Canvas */}
            <div
              className={`flex-1 flex flex-col relative overflow-hidden h-full min-h-0 min-w-0 ${
                mobileTab === 'network' ? 'block' : 'hidden lg:flex'
              }`}
            >
              <AgentNetworkGraph className="flex-1 w-full h-full" />
            </div>

            {/* Right Column: Agent Inspector & Phase 5 Integration Surface */}
            <div
              className={`shrink-0 transition-all duration-300 z-10 h-full overflow-hidden ${
                rightPanelOpen ? 'w-80 xl:w-88' : 'w-0 hidden'
              } ${mobileTab === 'inspector' ? 'block w-full' : 'hidden lg:block'}`}
            >
              <AgentInspector />
            </div>
          </div>
        )}

        {/* 4. Bottom Grounded Query & Command Bar */}
        <div className="shrink-0">
          <AgentCommandBar />
        </div>
      </div>
    </DashboardLayout>
  );
}

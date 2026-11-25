'use client';

import React, { useState } from 'react';
import { useAgentControlStore } from './useAgentControlStore';
import {
  Server,
  Database,
  Cloud,
  CheckCircle2,
  Clock,
  Radio,
  Upload,
  FileText,
  FileCode,
  ShieldCheck,
  RefreshCw,
} from 'lucide-react';

export function Phase5IntegrationSurface() {
  const { addEvent, triggerAgentTask } = useAgentControlStore();
  const [lastRefreshed, setLastRefreshed] = useState('3s ago');

  const CONNECTORS = [
    { name: 'LangGraph State Engine', code: 'M91', status: 'RUNNING', color: 'text-emerald-400' },
    { name: 'Gemini Live Voice WS', code: 'M92', status: 'STREAMING', color: 'text-cyan-400' },
    { name: 'Supabase DB & Auth', code: 'M93', status: 'CONNECTED', color: 'text-emerald-400' },
    { name: 'Olostep Scraper Engine', code: 'M94', status: 'RUNNING', color: 'text-emerald-400' },
    { name: 'Crustdata Enrichment API', code: 'M95', status: 'CONNECTED', color: 'text-blue-400' },
    { name: 'DigiLocker NAD Gateway', code: 'M96', status: 'STANDBY', color: 'text-slate-400' },
    { name: 'Playwright Chromium Sandbox', code: 'M97', status: 'STANDBY', color: 'text-slate-400' },
    { name: 'BGE Vector Indexer', code: 'M98', status: 'RUNNING', color: 'text-emerald-400' },
    { name: 'NLI Entailment Classifier', code: 'M99', status: 'RUNNING', color: 'text-emerald-400' },
  ];

  const handleSimulateUpload = (docType: string) => {
    addEvent({
      sourceAgentId: 'agent-supervisor',
      sourceAgentName: 'Supervisor Intent Agent',
      sourceAgentCode: 'M01',
      type: 'task_started',
      description: `Ingested ${docType}. Routing payload to Resume Intelligence Agent for extraction.`,
      severity: 'info',
    });
    triggerAgentTask('agent-resume', `Parsing uploaded ${docType}`);
  };

  return (
    <div className="p-4 space-y-5 flex-1 overflow-y-auto custom-scrollbar text-xs font-mono">
      {/* Surface Header */}
      <div className="flex items-center justify-between pb-3 border-b border-white/[0.08]">
        <div>
          <div className="text-xs font-bold text-white uppercase tracking-wider">
            SERVICE INTEGRATIONS
          </div>
          <div className="text-[10px] text-slate-500">Active Service Bridges • Updated {lastRefreshed}</div>
        </div>

        <button
          type="button"
          onClick={() => setLastRefreshed('Just now')}
          className="p-1.5 rounded-lg border border-white/[0.08] hover:bg-white/[0.05] text-slate-400 hover:text-white transition"
          title="Refresh surface"
        >
          <RefreshCw className="h-3 w-3" />
        </button>
      </div>

      {/* Surface Quick Action Buttons (Matches VORTEX reference) */}
      <div className="grid grid-cols-3 gap-1.5 text-[10px]">
        <button
          type="button"
          onClick={() => handleSimulateUpload('Mock Student Marksheet')}
          className="p-2 rounded-lg border border-white/[0.08] bg-white/[0.02] hover:bg-white/[0.06] text-slate-300 text-center transition"
        >
          SYNC NAD
        </button>
        <button
          type="button"
          onClick={() => handleSimulateUpload('Campus Placement Feed')}
          className="p-2 rounded-lg border border-white/[0.08] bg-white/[0.02] hover:bg-white/[0.06] text-slate-300 text-center transition"
        >
          CONNECT CAL
        </button>
        <button
          type="button"
          onClick={() => handleSimulateUpload('WebSocket Heartbeat')}
          className="p-2 rounded-lg border border-cyan-500/30 bg-cyan-950/20 text-cyan-300 text-center transition"
        >
          PING WS
        </button>
      </div>

      {/* Connectors Table (Matches VORTEX layout) */}
      <div className="space-y-1.5">
        <div className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">
          ACTIVE SERVICE BRIDGES
        </div>

        <div className="space-y-1">
          {CONNECTORS.map((conn) => (
            <div
              key={conn.name}
              className="p-2 rounded-lg border border-white/[0.05] bg-white/[0.015] flex items-center justify-between"
            >
              <div className="flex items-center gap-2">
                <span className="text-[10px] text-slate-500 font-bold">[{conn.code}]</span>
                <span className="text-[11px] text-slate-300 truncate max-w-[150px]">{conn.name}</span>
              </div>
              <span className={`text-[10px] font-bold ${conn.color}`}>{conn.status}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Upload & Route Ingestion Simulator (Matches VORTEX reference) */}
      <div className="p-3.5 rounded-xl border border-white/[0.08] bg-[#0A0D16] space-y-3">
        <div className="flex items-center justify-between text-[10px] uppercase tracking-wider text-slate-400">
          <span>UPLOAD & ROUTE PIPELINE</span>
          <Upload className="h-3.5 w-3.5 text-cyan-400" />
        </div>

        <div className="grid grid-cols-3 gap-1.5 text-[10px]">
          <button
            type="button"
            onClick={() => handleSimulateUpload('Career Passport JSON')}
            className="p-2 rounded-lg border border-white/[0.08] bg-white/[0.03] hover:border-cyan-500/40 text-slate-300 text-center transition"
          >
            PASSPORT
          </button>
          <button
            type="button"
            onClick={() => handleSimulateUpload('Resume PDF')}
            className="p-2 rounded-lg border border-white/[0.08] bg-white/[0.03] hover:border-cyan-500/40 text-slate-300 text-center transition"
          >
            UPLOAD PDF
          </button>
          <button
            type="button"
            onClick={() => handleSimulateUpload('Opportunity Posting')}
            className="p-2 rounded-lg border border-white/[0.08] bg-white/[0.03] hover:border-cyan-500/40 text-slate-300 text-center transition"
          >
            JOB POST
          </button>
        </div>

        <div className="p-3 rounded-lg border border-dashed border-white/10 text-center text-[10px] text-slate-500">
          Drag & drop artifact to dispatch into neural pipeline
        </div>
      </div>
    </div>
  );
}

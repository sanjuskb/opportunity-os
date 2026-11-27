'use client';

import React, { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { RefreshCw, ShieldCheck } from 'lucide-react';
import { useAuth } from '@/components/auth/AuthProvider';
import {
  QUERY_KEYS,
  useAgentSessions,
  useBrowserLogs,
  useDecideApproval,
  usePendingApprovals,
} from '@/lib/queries/useOpportunityOs';
import { BrowserScreenshotPreview } from './BrowserScreenshotPreview';
import { useAgentControlStore } from './useAgentControlStore';

export function Phase5IntegrationSurface() {
  const { user, apiClient } = useAuth();
  const qc = useQueryClient();
  const [lastRefreshed, setLastRefreshed] = useState('Live');
  const [actionMsg, setActionMsg] = useState<string | null>(null);
  const { checkpointerBackend, sseConnected } = useAgentControlStore();

  const { data: mlHealth } = useQuery({
    queryKey: ['mlHealth'],
    queryFn: () => apiClient.getMlHealth(),
    enabled: Boolean(user),
    retry: false,
  });
  const { data: sessions } = useAgentSessions();
  const { data: browserLogs } = useBrowserLogs();
  const { data: pendingApprovals } = usePendingApprovals();
  const decideMutation = useDecideApproval();

  const handleRefresh = () => {
    setLastRefreshed(new Date().toLocaleTimeString());
    void qc.invalidateQueries({ queryKey: QUERY_KEYS.agentSessions });
    void qc.invalidateQueries({ queryKey: QUERY_KEYS.browserLogs });
    void qc.invalidateQueries({ queryKey: QUERY_KEYS.approvals });
    void qc.invalidateQueries({ queryKey: ['mlHealth'] });
  };

  const handleDecision = async (approvalId: string, approved: boolean, executeSubmission = false) => {
    try {
      const res = await decideMutation.mutateAsync({ approvalId, approved, executeSubmission });
      setActionMsg(
        `Decision '${res.status}' saved${res.workflowResumed ? ` • LangGraph resumed (${res.resumedStage})` : ''}`
      );
    } catch (err) {
      setActionMsg(err instanceof Error ? err.message : 'Approval update failed');
    }
  };

  const latestShotLog = (browserLogs ?? []).find((l) => Boolean(l.screenshotUrl));

  const connectors = [
    {
      name: 'LangGraph + PostgresSaver',
      code: 'M02',
      status: `${checkpointerBackend.toUpperCase()}${sseConnected ? ' • SSE' : ''}`,
      color: 'text-emerald-300',
    },
    {
      name: 'ML Intelligence Subsystem',
      code: 'M06',
      status: mlHealth?.ml_available ? 'READY' : 'API ONLINE',
      color: 'text-emerald-400',
    },
    { name: 'Gemini Live Voice WS', code: 'M13', status: user ? 'AUTHENTICATED' : 'STANDBY', color: 'text-cyan-400' },
    { name: 'Playwright Logs Recorded', code: 'M12', status: `${(browserLogs ?? []).length} EVENTS`, color: 'text-blue-400' },
    { name: 'Agent Sessions Recorded', code: 'M01', status: `${(sessions ?? []).length} SESSIONS`, color: 'text-slate-300' },
  ];

  return (
    <div className="p-4 space-y-5 flex-1 overflow-y-auto custom-scrollbar text-xs font-mono">
      <div className="flex items-center justify-between pb-3 border-b border-white/[0.08]">
        <div>
          <div className="text-xs font-bold text-white uppercase tracking-wider">LIVE LANGGRAPH &amp; GATES</div>
          <div className="text-[10px] text-slate-500">PostgreSQL Checkpoint Telemetry • {lastRefreshed}</div>
        </div>

        <button
          type="button"
          onClick={handleRefresh}
          className="p-1.5 rounded-lg border border-white/[0.08] hover:bg-white/[0.05] text-slate-400 hover:text-white transition"
          title="Refresh live telemetry"
        >
          <RefreshCw className="h-3 w-3" />
        </button>
      </div>

      {actionMsg && (
        <div className="p-2 rounded-lg border border-cyan-500/40 bg-cyan-950/30 text-[10px] text-cyan-200">
          {actionMsg}
        </div>
      )}

      <div className="space-y-1.5">
        <div className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">SYSTEM BRIDGES</div>
        <div className="space-y-1">
          {connectors.map((conn) => (
            <div
              key={conn.name}
              className="p-2 rounded-lg border border-white/[0.05] bg-white/[0.015] flex items-center justify-between"
            >
              <div className="flex items-center gap-2">
                <span className="text-[10px] text-slate-500 font-bold">[{conn.code}]</span>
                <span className="text-[11px] text-slate-300 truncate max-w-[140px]">{conn.name}</span>
              </div>
              <span className={`text-[10px] font-bold ${conn.color}`}>{conn.status}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="space-y-2">
        <div className="text-[10px] text-amber-400 uppercase tracking-wider font-semibold flex items-center gap-1">
          <ShieldCheck className="h-3.5 w-3.5" />
          <span>PENDING HUMAN APPROVALS ({(pendingApprovals ?? []).length})</span>
        </div>
        {(pendingApprovals ?? []).length === 0 ? (
          <div className="p-3 rounded-lg border border-white/[0.06] text-[10px] text-slate-500">
            No pending portal submission approvals.
          </div>
        ) : (
          (pendingApprovals ?? []).map((apr) => (
            <div key={apr.id} className="p-2.5 rounded-lg border border-amber-500/30 bg-amber-950/20 space-y-2">
              <div className="text-[11px] text-white font-semibold">{apr.actionType}</div>
              <div className="flex gap-1.5">
                <button
                  type="button"
                  disabled={decideMutation.isPending}
                  onClick={() => void handleDecision(apr.id, true, true)}
                  className="flex-1 py-1 rounded bg-emerald-600 text-white text-[10px] font-bold hover:bg-emerald-500 disabled:opacity-50"
                >
                  APPROVE &amp; RESUME
                </button>
                <button
                  type="button"
                  disabled={decideMutation.isPending}
                  onClick={() => void handleDecision(apr.id, false, false)}
                  className="flex-1 py-1 rounded bg-rose-900 text-rose-200 text-[10px] font-bold hover:bg-rose-800 disabled:opacity-50"
                >
                  REJECT
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {latestShotLog && <BrowserScreenshotPreview logId={latestShotLog.id} label="Latest Playwright Capture" />}
    </div>
  );
}

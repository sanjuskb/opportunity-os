'use client';

import { useEffect } from 'react';
import type { AgentEventRecord } from '@opportunity-os/shared-types';
import { useAuth } from '@/components/auth/AuthProvider';
import {
  useAgentSessionDetail,
  useAgentSessions,
  useBrowserLogs,
  usePendingApprovals,
} from '@/lib/queries/useOpportunityOs';
import { useAgentControlStore } from './useAgentControlStore';

export function AgentLiveBridge() {
  const { user, session, apiClient } = useAuth();
  const { data: sessions } = useAgentSessions();
  const activeSessionId = useAgentControlStore((s) => s.activeSessionId);
  const effectiveSessionId = activeSessionId ?? sessions?.[0]?.id ?? null;

  const { data: sessionDetail } = useAgentSessionDetail(effectiveSessionId);
  const { data: pendingApprovals } = usePendingApprovals();
  const { data: browserLogs } = useBrowserLogs();

  const syncLiveTelemetry = useAgentControlStore((s) => s.syncLiveTelemetry);
  const appendLiveSseEvent = useAgentControlStore((s) => s.appendLiveSseEvent);
  const setSseConnected = useAgentControlStore((s) => s.setSseConnected);

  useEffect(() => {
    if (!user) return;
    syncLiveTelemetry({
      sessions: sessions ?? [],
      events: sessionDetail?.events ?? [],
      pendingApprovals: pendingApprovals ?? [],
      browserLogs: browserLogs ?? [],
    });
  }, [user, sessions, sessionDetail, pendingApprovals, browserLogs, syncLiveTelemetry]);

  useEffect(() => {
    const token = session?.access_token;
    const isSessionActive = sessionDetail?.session?.isActive;
    if (!user || !token || !effectiveSessionId || !isSessionActive) {
      setSseConnected(false);
      return;
    }

    const controller = new AbortController();
    let cancelled = false;

    async function connectSse() {
      try {
        const url = apiClient.getAgentSessionStreamUrl(effectiveSessionId!, false);
        const resp = await fetch(url, {
          headers: { Authorization: `Bearer ${token}` },
          signal: controller.signal,
        });
        if (!resp.ok || !resp.body) {
          setSseConnected(false);
          return;
        }
        setSseConnected(true);
        const reader = resp.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        while (!cancelled) {
          const { value, done } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const frames = buffer.split('\n\n');
          buffer = frames.pop() ?? '';
          for (const frame of frames) {
            if (!frame.includes('event: agent_event')) continue;
            const dataLine = frame
              .split('\n')
              .find((l) => l.startsWith('data: '));
            if (!dataLine) continue;
            try {
              const parsed = JSON.parse(dataLine.slice(6)) as AgentEventRecord;
              appendLiveSseEvent(parsed);
            } catch {
              // ignore malformed chunk
            }
          }
        }
      } catch {
        // aborted on cleanup or network reconnect
      } finally {
        if (!cancelled) setSseConnected(false);
      }
    }

    void connectSse();
    return () => {
      cancelled = true;
      controller.abort();
      setSseConnected(false);
    };
  }, [user, session?.access_token, effectiveSessionId, sessionDetail?.session?.isActive, apiClient, appendLiveSseEvent, setSseConnected]);

  return null;
}

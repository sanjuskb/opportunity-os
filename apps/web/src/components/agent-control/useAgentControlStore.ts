'use client';

import { create } from 'zustand';
import type {
  AgentEventRecord,
  AgentSessionRecord,
  ApprovalRequest,
  BrowserExecutionLogRecord,
} from '@opportunity-os/shared-types';
import {
  AgentCategory,
  AgentConnection,
  AgentEvent,
  AgentNode,
  AgentStatus,
  SystemTelemetryMetrics,
  WorkflowPipeline,
} from './types';
import { INITIAL_AGENTS, INITIAL_CONNECTIONS, INITIAL_EVENTS, SAMPLE_WORKFLOW_PIPELINES } from './agentData';

interface LiveTelemetryPayload {
  sessions: AgentSessionRecord[];
  events: AgentEventRecord[];
  pendingApprovals: ApprovalRequest[];
  browserLogs: BrowserExecutionLogRecord[];
}

interface AgentControlState {
  agents: AgentNode[];
  connections: AgentConnection[];
  events: AgentEvent[];
  workflows: WorkflowPipeline[];
  liveSessions: AgentSessionRecord[];
  activeSessionId: string | null;
  pendingApprovals: ApprovalRequest[];
  browserLogs: BrowserExecutionLogRecord[];
  checkpointerBackend: string;
  sseConnected: boolean;

  selectedAgentId: string | null;
  hoveredAgentId: string | null;
  categoryFilter: AgentCategory | 'all';
  statusFilter: AgentStatus | 'all';
  searchQuery: string;
  streamingSpeed: 'high' | 'med' | 'low' | 'paused';
  isStreaming: boolean;
  zoom: number;
  pan: { x: number; y: number };
  activeWorkflowId: string;
  commandQuery: string;
  commandLog: string | null;
  metrics: SystemTelemetryMetrics;

  // Actions
  setActiveWorkflowId: (id: string) => void;
  setActiveSessionId: (id: string | null) => void;
  setSseConnected: (connected: boolean) => void;
  setCommandLog: (msg: string | null) => void;
  selectAgent: (id: string | null) => void;
  hoverAgent: (id: string | null) => void;
  setCategoryFilter: (cat: AgentCategory | 'all') => void;
  setStatusFilter: (status: AgentStatus | 'all') => void;
  setSearchQuery: (query: string) => void;
  setStreamingSpeed: (speed: 'high' | 'med' | 'low' | 'paused') => void;
  toggleStreaming: () => void;
  setZoom: (zoom: number) => void;
  setPan: (pan: { x: number; y: number }) => void;
  resetCamera: () => void;
  pauseAgent: (id: string) => void;
  resumeAgent: (id: string) => void;
  triggerAgentTask: (id: string, taskName?: string) => void;
  dispatchUserCommand: (command: string) => void;
  addEvent: (event: Omit<AgentEvent, 'id' | 'timestamp'>) => void;
  syncLiveTelemetry: (data: LiveTelemetryPayload) => void;
  appendLiveSseEvent: (rawEvent: AgentEventRecord) => void;
  approvePendingAction: () => void;
  rejectPendingAction: () => void;
}

const NODE_ID_ALIASES: Record<string, string> = {
  playwright_runner: 'agent-playwright',
  human_approval_gate: 'agent-approval-gate',
  'agent-supervisor': 'agent-supervisor',
  'agent-workflow-engine': 'agent-workflow-engine',
  'agent-discovery': 'agent-discovery',
  'agent-dedup-vector': 'agent-dedup-vector',
  'agent-monitor': 'agent-monitor',
  'agent-eligibility': 'agent-eligibility',
  'agent-resume': 'agent-resume',
  'agent-nli-verifier': 'agent-nli-verifier',
  'agent-form-mapper': 'agent-form-mapper',
  'agent-approval-gate': 'agent-approval-gate',
  'agent-playwright': 'agent-playwright',
  'agent-mock-interview': 'agent-mock-interview',
};

function mapBackendEvent(
  ev: AgentEventRecord,
  agents: AgentNode[],
  pendingCount: number
): AgentEvent {
  const mappedId = NODE_ID_ALIASES[ev.nodeName] || 'agent-supervisor';
  const node = agents.find((a) => a.id === mappedId) ?? agents[0];
  const et = ev.eventType;
  let severity: AgentEvent['severity'] = 'info';
  let type: AgentEvent['type'] = 'tool_invoked';
  if (et.includes('approval_requested')) {
    severity = pendingCount > 0 ? 'warning' : 'info';
    type = pendingCount > 0 ? 'approval_required' : 'task_completed';
  } else if (et.includes('approval_granted') || et.includes('completed') || et.includes('submitted')) {
    severity = 'success';
    type = et.includes('approval_granted') ? 'approval_granted' : 'task_completed';
  } else if (et.includes('manual') || et.includes('paused') || et.includes('guardrail')) {
    severity = 'warning';
    type = 'guardrail_triggered';
  } else if (et.includes('started') || et.includes('resumed')) {
    severity = 'info';
    type = 'task_started';
  } else if (et.includes('delegation')) {
    severity = 'info';
    type = 'delegation';
  }

  return {
    id: ev.id,
    timestamp: ev.createdAt ? new Date(ev.createdAt).toTimeString().split(' ')[0] : 'Live',
    sourceAgentId: node.id,
    sourceAgentName: node.name,
    sourceAgentCode: node.code,
    type,
    description: `${ev.eventType.replace(/_/g, ' ')} (${String(ev.payload?.agentCode || node.code)})`,
    executionId: ev.sessionId.slice(0, 8),
    severity,
    payloadSnippet: JSON.stringify(ev.payload || {}),
  };
}

function computeMetrics(agents: AgentNode[], workflows: WorkflowPipeline[], pendingApprovals: number, eventCount: number): SystemTelemetryMetrics {
  return {
    totalAgents: agents.length,
    activeCount: agents.filter((a) => a.status === 'active').length,
    busyCount: agents.filter((a) => a.status === 'busy').length,
    idleCount: agents.filter((a) => a.status === 'idle').length,
    failedCount: agents.filter((a) => a.status === 'failed').length,
    disconnectedCount: agents.filter((a) => a.status === 'disconnected').length,
    pendingApprovals,
    eventsPerMinute: Math.max(eventCount * 4, 12),
    avgLatencyMs: 64,
    activeWorkflows: workflows.length,
  };
}

export const useAgentControlStore = create<AgentControlState>((set, get) => ({
  agents: INITIAL_AGENTS,
  connections: INITIAL_CONNECTIONS,
  events: INITIAL_EVENTS,
  workflows: SAMPLE_WORKFLOW_PIPELINES,
  liveSessions: [],
  activeSessionId: null,
  pendingApprovals: [],
  browserLogs: [],
  checkpointerBackend: 'postgres',
  sseConnected: false,

  selectedAgentId: 'agent-supervisor',
  hoveredAgentId: null,
  categoryFilter: 'all',
  statusFilter: 'all',
  searchQuery: '',
  streamingSpeed: 'high',
  isStreaming: true,
  zoom: 1,
  pan: { x: 0, y: 0 },
  activeWorkflowId: 'wf-app-submit',
  commandQuery: '',
  commandLog: null,
  metrics: computeMetrics(
    INITIAL_AGENTS,
    SAMPLE_WORKFLOW_PIPELINES,
    INITIAL_AGENTS.filter((a) => a.status === 'awaiting_approval').length,
    INITIAL_EVENTS.length
  ),

  setActiveWorkflowId: (id) => set({ activeWorkflowId: id }),
  setActiveSessionId: (id) => set({ activeSessionId: id }),
  setSseConnected: (connected) => set({ sseConnected: connected }),
  setCommandLog: (msg) => set({ commandLog: msg }),
  selectAgent: (id) => set({ selectedAgentId: id }),
  hoverAgent: (id) => set({ hoveredAgentId: id }),
  setCategoryFilter: (cat) => set({ categoryFilter: cat }),
  setStatusFilter: (status) => set({ statusFilter: status }),
  setSearchQuery: (query) => set({ searchQuery: query }),

  setStreamingSpeed: (speed) =>
    set({
      streamingSpeed: speed,
      isStreaming: speed !== 'paused',
    }),

  toggleStreaming: () => {
    const next = !get().isStreaming;
    set({
      isStreaming: next,
      streamingSpeed: next ? 'high' : 'paused',
    });
  },

  setZoom: (zoom) => set({ zoom: Math.min(Math.max(zoom, 0.4), 2.2) }),
  setPan: (pan) => set({ pan }),
  resetCamera: () => set({ zoom: 1, pan: { x: 0, y: 0 } }),

  pauseAgent: (id) => {
    const agent = get().agents.find((a) => a.id === id);
    if (!agent) return;
    const updated = get().agents.map((a) =>
      a.id === id ? { ...a, status: 'idle' as AgentStatus, currentTask: 'Paused in Control Center' } : a
    );
    set((s) => ({
      agents: updated,
      metrics: computeMetrics(updated, s.workflows, s.pendingApprovals.length, s.events.length),
    }));
  },

  resumeAgent: (id) => {
    const agent = get().agents.find((a) => a.id === id);
    if (!agent) return;
    const updated = get().agents.map((a) =>
      a.id === id ? { ...a, status: 'active' as AgentStatus, currentTask: 'Active • Ready for workflow dispatch' } : a
    );
    set((s) => ({
      agents: updated,
      metrics: computeMetrics(updated, s.workflows, s.pendingApprovals.length, s.events.length),
    }));
  },

  triggerAgentTask: (id, taskName = 'Use Execute or Launch Workflow for live backend dispatch') => {
    const agent = get().agents.find((a) => a.id === id);
    if (!agent) return;
    set({
      selectedAgentId: id,
      commandLog: `Selected ${agent.name} (${agent.code}). ${taskName}`,
    });
  },

  dispatchUserCommand: (command) => {
    const lower = command.toLowerCase().trim();
    if (!lower) return;

    if (lower.includes('failed') || lower.includes('error')) {
      set({
        statusFilter: 'failed',
        commandLog: 'Filtered network view by failed agents.',
      });
    } else if (lower.includes('approval') || lower.includes('gate') || lower.includes('pending')) {
      set({
        statusFilter: 'awaiting_approval',
        selectedAgentId: 'agent-approval-gate',
        commandLog: 'Focused on M11 Human-in-the-Loop Safety Gate.',
      });
    } else if (lower.includes('resume') || lower.includes('tailor')) {
      set({
        selectedAgentId: 'agent-resume',
        categoryFilter: 'resume',
        commandLog: 'Focused on M08 ATS Resume Intelligence & M09 NLI Gate.',
      });
    } else if (lower.includes('reset') || lower.includes('clear')) {
      set({
        categoryFilter: 'all',
        statusFilter: 'all',
        searchQuery: '',
        zoom: 1,
        pan: { x: 0, y: 0 },
        commandLog: 'Reset network filters and camera.',
      });
    } else {
      set({
        searchQuery: command,
        commandLog: `Filtered agents matching query: "${command}".`,
      });
      const match = get().agents.find(
        (a) =>
          a.name.toLowerCase().includes(lower) ||
          a.tools.some((t) => t.toLowerCase().includes(lower)) ||
          a.capabilities.some((c) => c.toLowerCase().includes(lower))
      );
      if (match) {
        set({ selectedAgentId: match.id });
      }
    }
  },

  addEvent: (eventData) => {
    const now = new Date();
    const timeStr = now.toTimeString().split(' ')[0];
    const newEvent: AgentEvent = {
      ...eventData,
      id: `ev-${Date.now()}-${Math.floor(Math.random() * 1000)}`,
      timestamp: timeStr,
    };
    set((state) => ({
      events: [newEvent, ...state.events.slice(0, 49)],
    }));
  },

  syncLiveTelemetry: ({ sessions, events, pendingApprovals, browserLogs }) => {
    const state = get();
    const latestSession = sessions[0] ?? null;
    const backendType = String(latestSession?.state?.checkpointerBackend || state.checkpointerBackend);
    const hasPending = pendingApprovals.length > 0;

    const touchedNodeCounts = new Map<string, number>();
    const lastTaskByNode = new Map<string, string>();
    for (const ev of events) {
      const nid = NODE_ID_ALIASES[ev.nodeName] || 'agent-supervisor';
      touchedNodeCounts.set(nid, (touchedNodeCounts.get(nid) ?? 0) + 1);
      lastTaskByNode.set(nid, `${ev.eventType.replace(/_/g, ' ')}`);
    }

    const updatedAgents: AgentNode[] = state.agents.map((a) => {
      const hits = touchedNodeCounts.get(a.id) ?? 0;
      let status: AgentStatus = a.status;
      if (a.id === 'agent-approval-gate') {
        status = hasPending ? 'awaiting_approval' : 'active';
      } else if (hits > 0 && latestSession?.isActive) {
        status = 'busy';
      } else if (hits > 0) {
        status = 'active';
      }
      return {
        ...a,
        status,
        currentTask: lastTaskByNode.get(a.id) ?? a.currentTask,
        executionCount: a.executionCount + (hits > 0 ? 0 : 0),
        lastActive: hits > 0 ? 'Synced' : a.lastActive,
      };
    });

    const mappedEvents =
      events.length > 0
        ? [...events].reverse().map((ev) => mapBackendEvent(ev, updatedAgents, pendingApprovals.length))
        : state.events;

    // Reflect live pipeline stages if a real session exists
    const stageStr = String(latestSession?.state?.currentStage || '');
    const updatedWorkflows = state.workflows.map((wf) => {
      if (wf.id !== 'wf-app-submit' || !latestSession) return wf;
      const doneAll = stageStr.includes('submitted') || stageStr.includes('approved_ready');
      return {
        ...wf,
        stages: wf.stages.map((st, idx) => {
          if (doneAll) return { ...st, status: 'completed' as const };
          if (hasPending && st.agentCode === 'M11') return { ...st, status: 'active' as const };
          if (idx <= 3 && events.length > 0) return { ...st, status: 'completed' as const };
          return st;
        }),
      };
    });

    set({
      liveSessions: sessions,
      activeSessionId: state.activeSessionId ?? latestSession?.id ?? null,
      pendingApprovals,
      browserLogs,
      checkpointerBackend: backendType,
      agents: updatedAgents,
      workflows: updatedWorkflows,
      events: mappedEvents.slice(0, 50),
      metrics: computeMetrics(updatedAgents, updatedWorkflows, pendingApprovals.length, mappedEvents.length),
    });
  },

  appendLiveSseEvent: (rawEvent) => {
    const state = get();
    if (state.events.some((e) => e.id === rawEvent.id)) return;
    const mapped = mapBackendEvent(rawEvent, state.agents, state.pendingApprovals.length);
    set((s) => ({
      events: [mapped, ...s.events.slice(0, 49)],
      metrics: computeMetrics(s.agents, s.workflows, s.pendingApprovals.length, s.events.length + 1),
    }));
  },

  approvePendingAction: () => {
    const first = get().pendingApprovals[0];
    set({
      commandLog: first
        ? `Ready to approve request ${first.id.slice(0, 8)} via Integrations or Applications.`
        : 'No pending approval request in queue.',
    });
  },

  rejectPendingAction: () => {
    set({ commandLog: 'Select Reject on a pending approval card to abort safely.' });
  },
}));

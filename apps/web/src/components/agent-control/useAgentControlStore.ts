'use client';

import { create } from 'zustand';
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

interface AgentControlState {
  agents: AgentNode[];
  connections: AgentConnection[];
  events: AgentEvent[];
  workflows: WorkflowPipeline[];
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
  approvePendingAction: () => void;
  rejectPendingAction: () => void;
}

export const useAgentControlStore = create<AgentControlState>((set, get) => ({
  agents: INITIAL_AGENTS,
  connections: INITIAL_CONNECTIONS,
  events: INITIAL_EVENTS,
  workflows: SAMPLE_WORKFLOW_PIPELINES,
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
  metrics: {
    totalAgents: INITIAL_AGENTS.length,
    activeCount: INITIAL_AGENTS.filter((a) => a.status === 'active').length,
    busyCount: INITIAL_AGENTS.filter((a) => a.status === 'busy').length,
    idleCount: INITIAL_AGENTS.filter((a) => a.status === 'idle').length,
    failedCount: INITIAL_AGENTS.filter((a) => a.status === 'failed').length,
    disconnectedCount: INITIAL_AGENTS.filter((a) => a.status === 'disconnected').length,
    pendingApprovals: INITIAL_AGENTS.filter((a) => a.status === 'awaiting_approval').length,
    eventsPerMinute: 48,
    avgLatencyMs: 64,
    activeWorkflows: SAMPLE_WORKFLOW_PIPELINES.length,
  },

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
      a.id === id ? { ...a, status: 'idle' as AgentStatus, currentTask: 'Paused by operator' } : a
    );

    get().addEvent({
      sourceAgentId: agent.id,
      sourceAgentName: agent.name,
      sourceAgentCode: agent.code,
      type: 'tool_invoked',
      description: `Operator paused agent ${agent.name} (${agent.code}).`,
      severity: 'warning',
    });

    set({ agents: updated });
  },

  resumeAgent: (id) => {
    const agent = get().agents.find((a) => a.id === id);
    if (!agent) return;

    const updated = get().agents.map((a) =>
      a.id === id ? { ...a, status: 'active' as AgentStatus, currentTask: 'Active • Ready for intake' } : a
    );

    get().addEvent({
      sourceAgentId: agent.id,
      sourceAgentName: agent.name,
      sourceAgentCode: agent.code,
      type: 'task_started',
      description: `Operator resumed agent ${agent.name} (${agent.code}).`,
      severity: 'success',
    });

    set({ agents: updated });
  },

  triggerAgentTask: (id, taskName = 'Synthetic test dispatch') => {
    const agent = get().agents.find((a) => a.id === id);
    if (!agent) return;

    const updated = get().agents.map((a) =>
      a.id === id
        ? {
            ...a,
            status: 'busy' as AgentStatus,
            currentTask: `Executing: ${taskName}`,
            executionCount: a.executionCount + 1,
            lastActive: 'Just now',
          }
        : a
    );

    get().addEvent({
      sourceAgentId: agent.id,
      sourceAgentName: agent.name,
      sourceAgentCode: agent.code,
      type: 'task_started',
      description: `Dispatched test payload to ${agent.name}: "${taskName}".`,
      severity: 'info',
    });

    set({ agents: updated });

    // After 2.5s, restore to active
    setTimeout(() => {
      set((state) => ({
        agents: state.agents.map((a) =>
          a.id === id ? { ...a, status: 'active' as AgentStatus, currentTask: 'Completed test run' } : a
        ),
      }));
      get().addEvent({
        sourceAgentId: agent.id,
        sourceAgentName: agent.name,
        sourceAgentCode: agent.code,
        type: 'task_completed',
        description: `Successfully executed test payload for ${agent.name} with 0 errors.`,
        severity: 'success',
      });
    }, 2500);
  },

  dispatchUserCommand: (command) => {
    const lower = command.toLowerCase().trim();
    if (!lower) return;

    if (lower.includes('failed') || lower.includes('error')) {
      set({
        statusFilter: 'failed',
        commandLog: 'Filtered network view: displaying 0 failed agents (workforce is currently healthy).',
      });
    } else if (lower.includes('approval') || lower.includes('gate') || lower.includes('pending')) {
      set({
        statusFilter: 'awaiting_approval',
        selectedAgentId: 'agent-approval-gate',
        commandLog: 'Focused on M11 Human-in-the-Loop Safety Gate: 1 pending action awaiting cryptographic approval.',
      });
    } else if (lower.includes('resume') || lower.includes('tailor')) {
      set({
        selectedAgentId: 'agent-resume',
        categoryFilter: 'resume',
        commandLog: 'Focused on M08 ATS Resume Intelligence Agent & M09 Hallucination NLI Gate.',
      });
    } else if (lower.includes('reset') || lower.includes('clear')) {
      set({
        categoryFilter: 'all',
        statusFilter: 'all',
        searchQuery: '',
        zoom: 1,
        pan: { x: 0, y: 0 },
        commandLog: 'Reset network view, cleared filters, and restored camera.',
      });
    } else {
      // General grounded agent query
      set({
        searchQuery: command,
        commandLog: `Filtered agents matching query: "${command}". 1 agent selected.`,
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
      events: [newEvent, ...state.events.slice(0, 49)], // Keep up to 50 events
    }));
  },

  approvePendingAction: () => {
    const approvalAgent = get().agents.find((a) => a.id === 'agent-approval-gate');
    if (!approvalAgent) return;

    set((state) => ({
      agents: state.agents.map((a) =>
        a.id === 'agent-approval-gate'
          ? { ...a, status: 'active', currentTask: 'Action approved • Forwarding payload to Playwright' }
          : a.id === 'agent-playwright'
          ? { ...a, status: 'busy', currentTask: 'Executing approved form submission in isolated sandbox' }
          : a
      ),
      metrics: {
        ...state.metrics,
        pendingApprovals: Math.max(0, state.metrics.pendingApprovals - 1),
      },
    }));

    get().addEvent({
      sourceAgentId: 'agent-approval-gate',
      sourceAgentName: 'Human-in-the-Loop Safety Gate',
      sourceAgentCode: 'M11',
      targetAgentId: 'agent-playwright',
      targetAgentName: 'Playwright Sandbox Executor',
      type: 'approval_granted',
      description: 'Student cryptographically approved form submission for Google SWE Intern role.',
      severity: 'success',
      payloadSnippet: '{"decision": "approved", "timestamp": "2026-11-24T19:30:00Z"}',
    });

    setTimeout(() => {
      set((state) => ({
        agents: state.agents.map((a) =>
          a.id === 'agent-playwright'
            ? { ...a, status: 'idle', currentTask: 'Submission successful • Confirmation receipt #REC-9821 saved' }
            : a
        ),
      }));
      get().addEvent({
        sourceAgentId: 'agent-playwright',
        sourceAgentName: 'Playwright Sandbox Executor',
        sourceAgentCode: 'M12',
        type: 'task_completed',
        description: 'Successfully submitted application to Google Careers portal. Receipt stored in Supabase.',
        severity: 'success',
      });
    }, 3000);
  },

  rejectPendingAction: () => {
    set((state) => ({
      agents: state.agents.map((a) =>
        a.id === 'agent-approval-gate'
          ? { ...a, status: 'active', currentTask: 'Action rejected by student • Session aborted safely' }
          : a
      ),
      metrics: {
        ...state.metrics,
        pendingApprovals: Math.max(0, state.metrics.pendingApprovals - 1),
      },
    }));

    get().addEvent({
      sourceAgentId: 'agent-approval-gate',
      sourceAgentName: 'Human-in-the-Loop Safety Gate',
      sourceAgentCode: 'M11',
      type: 'guardrail_triggered',
      description: 'Student rejected form submission. Ephemeral browser context wiped immediately.',
      severity: 'warning',
    });
  },
}));

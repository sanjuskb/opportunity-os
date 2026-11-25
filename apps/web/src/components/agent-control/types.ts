/**
 * Opportunity OS — Agent Control Center Type Definitions
 * Models the entire autonomous agent workforce, graph topology, and telemetry.
 */

export type AgentCategory =
  | 'orchestration'
  | 'discovery'
  | 'verification'
  | 'resume'
  | 'execution'
  | 'voice'
  | 'integration';

export type AgentStatus =
  | 'active'
  | 'idle'
  | 'busy'
  | 'failed'
  | 'disconnected'
  | 'awaiting_approval';

export type AgentHealth = 'healthy' | 'degraded' | 'unhealthy' | 'unknown';

export type ConnectionType =
  | 'delegation'
  | 'data_transfer'
  | 'workflow_handoff'
  | 'approval_gate'
  | 'verification';

export interface AgentNode {
  id: string;
  code: string; // e.g. M01, M02 ... matches VORTEX convention
  name: string;
  role: string;
  category: AgentCategory;
  status: AgentStatus;
  health: AgentHealth;
  description: string;
  capabilities: string[];
  tools: string[];
  inputs: string[];
  outputs: string[];
  connectedAgentIds: string[];
  currentTask?: string;
  executionCount: number;
  successRate: number; // e.g. 99.4
  avgLatencyMs: number;
  lastActive: string;
  isImplemented: boolean;
  implementationTier: 'Implemented Backend' | 'Frontend Orchestration' | 'External Bridge' | 'Planned Phase 6';
  x: number;
  y: number;
}

export interface AgentConnection {
  id: string;
  source: string;
  target: string;
  type: ConnectionType;
  label?: string;
  isActive: boolean;
  lastActivity?: string;
}

export type EventSeverity = 'info' | 'success' | 'warning' | 'error';

export interface AgentEvent {
  id: string;
  timestamp: string;
  sourceAgentId: string;
  sourceAgentName: string;
  sourceAgentCode: string;
  targetAgentId?: string;
  targetAgentName?: string;
  type:
    | 'task_started'
    | 'task_completed'
    | 'delegation'
    | 'tool_invoked'
    | 'approval_required'
    | 'approval_granted'
    | 'guardrail_triggered'
    | 'error'
    | 'recovered';
  description: string;
  executionId?: string;
  severity: EventSeverity;
  payloadSnippet?: string;
}

export interface WorkflowStage {
  name: string;
  agentId: string;
  agentCode: string;
  status: 'completed' | 'active' | 'pending' | 'failed';
  timestamp?: string;
}

export interface WorkflowPipeline {
  id: string;
  name: string;
  trigger: string;
  stages: WorkflowStage[];
}

export interface SystemTelemetryMetrics {
  totalAgents: number;
  activeCount: number;
  busyCount: number;
  idleCount: number;
  failedCount: number;
  disconnectedCount: number;
  pendingApprovals: number;
  eventsPerMinute: number;
  avgLatencyMs: number;
  activeWorkflows: number;
}

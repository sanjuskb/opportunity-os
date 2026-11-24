'use client';

import React, { useRef, useState, useCallback, useMemo } from 'react';
import { useAgentControlStore } from './useAgentControlStore';
import { AgentCategory, AgentNode, AgentStatus } from './types';
import { ZoomIn, ZoomOut, Maximize2, Move, RotateCcw } from 'lucide-react';

interface AgentNetworkGraphProps {
  className?: string;
}

const CATEGORY_COLORS: Record<AgentCategory, { stroke: string; glow: string; text: string; bg: string }> = {
  orchestration: { stroke: '#06B6D4', glow: 'rgba(6, 182, 212, 0.45)', text: '#22D3EE', bg: 'rgba(6, 182, 212, 0.12)' },
  discovery: { stroke: '#3B82F6', glow: 'rgba(59, 130, 246, 0.45)', text: '#60A5FA', bg: 'rgba(59, 130, 246, 0.12)' },
  verification: { stroke: '#10B981', glow: 'rgba(16, 185, 129, 0.45)', text: '#34D399', bg: 'rgba(16, 185, 129, 0.12)' },
  resume: { stroke: '#8B5CF6', glow: 'rgba(139, 92, 246, 0.45)', text: '#A78BFA', bg: 'rgba(139, 92, 246, 0.12)' },
  execution: { stroke: '#F59E0B', glow: 'rgba(245, 158, 11, 0.45)', text: '#FBBF24', bg: 'rgba(245, 158, 11, 0.12)' },
  voice: { stroke: '#EC4899', glow: 'rgba(236, 72, 153, 0.45)', text: '#F472B6', bg: 'rgba(236, 72, 153, 0.12)' },
  integration: { stroke: '#64748B', glow: 'rgba(100, 116, 139, 0.45)', text: '#94A3B8', bg: 'rgba(100, 116, 139, 0.12)' },
};

export function AgentNetworkGraph({ className = '' }: AgentNetworkGraphProps) {
  const {
    agents,
    connections,
    selectedAgentId,
    hoveredAgentId,
    categoryFilter,
    statusFilter,
    searchQuery,
    zoom,
    pan,
    selectAgent,
    hoverAgent,
    setZoom,
    setPan,
    resetCamera,
  } = useAgentControlStore();

  const containerRef = useRef<HTMLDivElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState<{ x: number; y: number }>({ x: 0, y: 0 });

  // Map agents by ID for fast coordinate lookup
  const agentMap = useMemo(() => {
    const map = new Map<string, AgentNode>();
    agents.forEach((a) => map.set(a.id, a));
    return map;
  }, [agents]);

  // Determine active/highlighted agents and connections
  const activeFocusId = hoveredAgentId || selectedAgentId;

  const connectedNeighborIds = useMemo(() => {
    if (!activeFocusId) return new Set<string>();
    const neighbors = new Set<string>();
    neighbors.add(activeFocusId);
    connections.forEach((c) => {
      if (c.source === activeFocusId) neighbors.add(c.target);
      if (c.target === activeFocusId) neighbors.add(c.source);
    });
    return neighbors;
  }, [activeFocusId, connections]);

  // Filter check
  const isAgentVisible = useCallback(
    (agent: AgentNode) => {
      if (categoryFilter !== 'all' && agent.category !== categoryFilter) return false;
      if (statusFilter !== 'all' && agent.status !== statusFilter) return false;
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        return (
          agent.name.toLowerCase().includes(q) ||
          agent.code.toLowerCase().includes(q) ||
          agent.role.toLowerCase().includes(q) ||
          agent.tools.some((t) => t.toLowerCase().includes(q))
        );
      }
      return true;
    },
    [categoryFilter, statusFilter, searchQuery]
  );

  // Pan interaction handlers
  const handleMouseDown = (e: React.MouseEvent) => {
    // Only drag when clicking background
    if ((e.target as HTMLElement).tagName === 'svg' || (e.target as HTMLElement).id === 'graph-canvas-bg') {
      setIsDragging(true);
      setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    setPan({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y,
    });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    const zoomDelta = e.deltaY * -0.0012;
    setZoom(zoom + zoomDelta);
  };

  return (
    <div
      ref={containerRef}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onWheel={handleWheel}
      className={`relative w-full h-full min-h-[580px] bg-[#05070B] overflow-hidden select-none cursor-grab ${
        isDragging ? 'cursor-grabbing' : ''
      } ${className}`}
    >
      {/* 1. Subtle Cyber Spatial Horizon Background Grid */}
      <div
        id="graph-canvas-bg"
        className="absolute inset-0 pointer-events-auto"
        style={{
          backgroundImage: `
            radial-gradient(circle at 50% 50%, rgba(14, 20, 32, 0.8) 0%, #05070B 85%),
            linear-gradient(to right, rgba(255, 255, 255, 0.03) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(255, 255, 255, 0.03) 1px, transparent 1px)
          `,
          backgroundSize: '100% 100%, 40px 40px, 40px 40px',
          backgroundPosition: `center, ${pan.x}px ${pan.y}px, ${pan.x}px ${pan.y}px`,
        }}
      />

      {/* Atmospheric Ambient Glow Orbs */}
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[450px] bg-cyan-600/[0.05] blur-[160px] rounded-full pointer-events-none" />
      <div className="absolute bottom-10 right-1/4 w-[500px] h-[350px] bg-violet-600/[0.06] blur-[150px] rounded-full pointer-events-none" />

      {/* 2. Interactive SVG Graph Network */}
      <svg
        className="w-full h-full relative z-10"
        viewBox="0 0 1020 720"
        preserveAspectRatio="xMidYMid meet"
      >
        <defs>
          {/* Animated data packet traveling gradient */}
          <linearGradient id="packetGlow" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#22D3EE" stopOpacity="1" />
            <stop offset="100%" stopColor="#A78BFA" stopOpacity="0.8" />
          </linearGradient>

          {/* Glowing filter */}
          <filter id="neonGlow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur in="SourceGraphic" stdDeviation="4" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>

          <filter id="strongGlow" x="-80%" y="-80%" width="260%" height="260%">
            <feGaussianBlur in="SourceGraphic" stdDeviation="8" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Global Pan and Zoom Transformation Group */}
        <g
          transform={`translate(${pan.x}, ${pan.y}) scale(${zoom})`}
          style={{ transformOrigin: '510px 360px', transition: isDragging ? 'none' : 'transform 0.15s ease-out' }}
        >
          {/* EDGES: Connection pathways */}
          <g className="connections-layer">
            {connections.map((c) => {
              const source = agentMap.get(c.source);
              const target = agentMap.get(c.target);
              if (!source || !target) return null;

              const isSourceVisible = isAgentVisible(source);
              const isTargetVisible = isAgentVisible(target);
              const isDimmed =
                activeFocusId &&
                c.source !== activeFocusId &&
                c.target !== activeFocusId;
              const isHighlighted =
                activeFocusId &&
                (c.source === activeFocusId || c.target === activeFocusId);

              // Elegant curved Bezier arc
              const midX = (source.x + target.x) / 2;
              const midY = (source.y + target.y) / 2 - 20;
              const pathD = `M ${source.x} ${source.y} Q ${midX} ${midY} ${target.x} ${target.y}`;

              const strokeColor =
                c.type === 'delegation'
                  ? '#06B6D4'
                  : c.type === 'approval_gate'
                  ? '#F59E0B'
                  : c.type === 'verification'
                  ? '#10B981'
                  : c.type === 'workflow_handoff'
                  ? '#8B5CF6'
                  : '#3B82F6';

              return (
                <g
                  key={c.id}
                  className={`transition-opacity duration-300 ${
                    !isSourceVisible || !isTargetVisible
                      ? 'opacity-10'
                      : isDimmed
                      ? 'opacity-15'
                      : isHighlighted
                      ? 'opacity-100'
                      : 'opacity-40'
                  }`}
                >
                  {/* Subtle edge glow backing when highlighted */}
                  {isHighlighted && (
                    <path
                      d={pathD}
                      fill="none"
                      stroke={strokeColor}
                      strokeWidth={5}
                      strokeOpacity={0.4}
                      filter="url(#neonGlow)"
                    />
                  )}

                  {/* Base Connection line */}
                  <path
                    d={pathD}
                    fill="none"
                    stroke={strokeColor}
                    strokeWidth={isHighlighted ? 2.5 : 1.2}
                    strokeDasharray={c.type === 'approval_gate' ? '4 4' : 'none'}
                  />

                  {/* Animated Traveling Communication Packet */}
                  {c.isActive && isSourceVisible && isTargetVisible && (
                    <circle r={isHighlighted ? 3.5 : 2.5} fill="#FFFFFF" filter="url(#neonGlow)">
                      <animateMotion
                        dur={c.type === 'approval_gate' ? '4s' : '2.2s'}
                        repeatCount="indefinite"
                        path={pathD}
                      />
                    </circle>
                  )}
                </g>
              );
            })}
          </g>

          {/* NODES: Autonomous AI Agent Entities */}
          <g className="nodes-layer">
            {agents.map((agent) => {
              const isVisible = isAgentVisible(agent);
              const isSelected = selectedAgentId === agent.id;
              const isHovered = hoveredAgentId === agent.id;
              const isNeighbor = connectedNeighborIds.has(agent.id);
              const isDimmed = activeFocusId && !isSelected && !isNeighbor;
              const colors = CATEGORY_COLORS[agent.category] || CATEGORY_COLORS.orchestration;

              return (
                <g
                  key={agent.id}
                  transform={`translate(${agent.x}, ${agent.y})`}
                  onClick={(e) => {
                    e.stopPropagation();
                    selectAgent(agent.id);
                  }}
                  onMouseEnter={() => hoverAgent(agent.id)}
                  onMouseLeave={() => hoverAgent(null)}
                  className={`cursor-pointer transition-all duration-300 ${
                    !isVisible
                      ? 'opacity-15 pointer-events-none'
                      : isDimmed
                      ? 'opacity-25'
                      : 'opacity-100'
                  }`}
                >
                  {/* Outer Pulsing Ambient Halo (Selected or Busy) */}
                  {(isSelected || agent.status === 'busy' || agent.status === 'awaiting_approval') && (
                    <circle
                      r={30}
                      fill={colors.bg}
                      stroke={colors.stroke}
                      strokeWidth={1}
                      strokeDasharray="3 3"
                      strokeOpacity={0.6}
                      className="animate-spin"
                      style={{ transformOrigin: 'center', animationDuration: '14s' }}
                    />
                  )}

                  {/* Node Outer Halo Ring */}
                  <circle
                    r={isSelected ? 22 : 18}
                    fill="#080C14"
                    stroke={colors.stroke}
                    strokeWidth={isSelected ? 2.5 : 1.5}
                    filter={isSelected ? 'url(#strongGlow)' : isHovered ? 'url(#neonGlow)' : undefined}
                    style={{
                      transition: 'all 0.2s cubic-bezier(0.16, 1, 0.3, 1)',
                    }}
                  />

                  {/* Inner Status Indicator Core */}
                  <circle
                    r={isSelected ? 10 : 8}
                    fill={
                      agent.status === 'failed'
                        ? '#EF4444'
                        : agent.status === 'awaiting_approval'
                        ? '#F59E0B'
                        : agent.status === 'busy'
                        ? '#A855F7'
                        : agent.status === 'active'
                        ? colors.stroke
                        : '#475569'
                    }
                  />

                  {/* Small Active Pulse Dot on top right */}
                  {agent.status === 'active' && (
                    <circle
                      cx={14}
                      cy={-14}
                      r={3}
                      fill="#10B981"
                      className="animate-ping"
                      style={{ animationDuration: '3s' }}
                    />
                  )}

                  {agent.status === 'awaiting_approval' && (
                    <circle
                      cx={14}
                      cy={-14}
                      r={3.5}
                      fill="#F59E0B"
                      className="animate-pulse"
                    />
                  )}

                  {/* Agent Code Badge (e.g. M01, M08) */}
                  <text
                    y={3}
                    textAnchor="middle"
                    fill="#FFFFFF"
                    fontSize={isSelected ? '9px' : '8px'}
                    fontFamily="monospace"
                    fontWeight="bold"
                    pointerEvents="none"
                  >
                    {agent.code}
                  </text>

                  {/* Agent Name Label below node */}
                  <text
                    y={isSelected ? 36 : 32}
                    textAnchor="middle"
                    fill={isSelected ? '#FFFFFF' : isHovered ? colors.text : '#CBD5E1'}
                    fontSize={isSelected ? '11px' : '10px'}
                    fontWeight={isSelected ? '600' : '500'}
                    letterSpacing="0.01em"
                    pointerEvents="none"
                    filter="drop-shadow(0 1px 3px rgba(0,0,0,0.9))"
                  >
                    {agent.name}
                  </text>

                  {/* Role / Short Tagline below name */}
                  <text
                    y={isSelected ? 48 : 44}
                    textAnchor="middle"
                    fill="#64748B"
                    fontSize="8.5px"
                    fontFamily="monospace"
                    pointerEvents="none"
                  >
                    {agent.role.length > 28 ? agent.role.slice(0, 26) + '...' : agent.role}
                  </text>
                </g>
              );
            })}
          </g>
        </g>
      </svg>

      {/* 3. Floating In-Canvas Camera & Graph Controls (VORTEX Style) */}
      <div className="absolute bottom-5 right-5 z-20 flex items-center gap-1.5 p-1.5 rounded-xl border border-white/[0.08] bg-[#0A0E18]/85 backdrop-blur-md shadow-2xl text-xs font-mono text-slate-300">
        <button
          type="button"
          onClick={() => setZoom(zoom + 0.15)}
          className="p-2 rounded-lg hover:bg-white/[0.08] hover:text-white transition"
          title="Zoom In"
        >
          <ZoomIn className="h-4 w-4 text-slate-300" />
        </button>
        <button
          type="button"
          onClick={() => setZoom(zoom - 0.15)}
          className="p-2 rounded-lg hover:bg-white/[0.08] hover:text-white transition"
          title="Zoom Out"
        >
          <ZoomOut className="h-4 w-4 text-slate-300" />
        </button>
        <div className="h-4 w-px bg-white/10 mx-0.5" />
        <button
          type="button"
          onClick={resetCamera}
          className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg hover:bg-white/[0.08] hover:text-white transition text-[11px]"
          title="Reset Camera"
        >
          <RotateCcw className="h-3.5 w-3.5 text-cyan-400" />
          <span>{Math.round(zoom * 100)}%</span>
        </button>
      </div>

      {/* Legend Badge in top left corner of canvas */}
      <div className="absolute top-4 left-4 z-20 flex items-center gap-3 px-3 py-1.5 rounded-lg border border-white/[0.07] bg-[#080C14]/75 backdrop-blur-md text-[11px] font-mono text-slate-400">
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-cyan-400 animate-pulse" />
          <span className="text-slate-300">Active Shuttles</span>
        </span>
        <span className="text-slate-600">•</span>
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-amber-400" />
          <span>Approval Gate</span>
        </span>
        <span className="text-slate-600">•</span>
        <span className="text-slate-500">Pan & Zoom Enabled</span>
      </div>
    </div>
  );
}

'use client';

import React from 'react';
import { GraduationCap, Building2, School, Compass } from 'lucide-react';

export type EcosystemRole = 'students' | 'companies' | 'universities' | 'opportunities';

interface RoleSwitcherProps {
  activeRole: EcosystemRole;
  onSelectRole: (role: EcosystemRole) => void;
}

const ROLES: {
  id: EcosystemRole;
  label: string;
  badge: string;
  color: string;
  activeBorder: string;
  activeBg: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
}[] = [
  {
    id: 'students',
    label: 'Students',
    badge: 'Career Passport',
    color: '#06B6D4',
    activeBorder: 'border-cyan-500/50',
    activeBg: 'bg-cyan-950/30 text-cyan-300',
    description: 'Verify eligibility, generate tailored ATS resumes, and voice-apply in 7 regional languages.',
    icon: GraduationCap,
  },
  {
    id: 'companies',
    label: 'Companies',
    badge: 'Verified Hiring',
    color: '#3B82F6',
    activeBorder: 'border-blue-500/50',
    activeBg: 'bg-blue-950/30 text-blue-300',
    description: 'Direct access to skill-verified Indian collegiate candidates with verified project code.',
    icon: Building2,
  },
  {
    id: 'universities',
    label: 'Universities',
    badge: 'Placement Cell',
    color: '#10B981',
    activeBorder: 'border-emerald-500/50',
    activeBg: 'bg-emerald-950/30 text-emerald-300',
    description: 'Track placement outcomes, AICTE/UGC credentials, and student application pipelines.',
    icon: School,
  },
  {
    id: 'opportunities',
    label: 'Opportunities',
    badge: 'Live Discovery',
    color: '#F59E0B',
    activeBorder: 'border-amber-500/50',
    activeBg: 'bg-amber-950/30 text-amber-300',
    description: 'Autonomous ingestion of 10,000+ internships, research grants, and global hackathons.',
    icon: Compass,
  },
];

export function RoleSwitcher({ activeRole, onSelectRole }: RoleSwitcherProps) {
  const activeRoleData = ROLES.find((r) => r.id === activeRole) ?? ROLES[0];

  return (
    <div className="w-full space-y-3 pt-2">
      <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">
        Explore Ecosystem by Perspective:
      </div>

      {/* Role Tab Buttons */}
      <div
        role="tablist"
        aria-label="Ecosystem Hub Perspectives"
        className="grid grid-cols-2 sm:grid-cols-4 gap-2"
      >
        {ROLES.map((role) => {
          const Icon = role.icon;
          const isActive = activeRole === role.id;

          return (
            <button
              key={role.id}
              role="tab"
              aria-selected={isActive}
              aria-controls={`role-panel-${role.id}`}
              id={`role-tab-${role.id}`}
              onClick={() => onSelectRole(role.id)}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg border text-xs font-medium transition text-left ${
                isActive
                  ? `${role.activeBorder} ${role.activeBg} shadow-sm ring-1 ring-inset ring-slate-700/60`
                  : 'border-slate-800 bg-slate-900/60 text-slate-400 hover:border-slate-700 hover:text-slate-200'
              }`}
            >
              <Icon className="h-4 w-4 shrink-0" />
              <span className="truncate">{role.label}</span>
            </button>
          );
        })}
      </div>

      {/* Dynamic Role Description Card */}
      <div
        id={`role-panel-${activeRole}`}
        role="tabpanel"
        aria-labelledby={`role-tab-${activeRole}`}
        className="rounded-lg border border-slate-800/80 bg-slate-900/40 p-3 text-xs text-slate-300 flex items-center justify-between gap-3 backdrop-blur-sm"
      >
        <div className="flex items-center gap-2">
          <span
            className="h-2 w-2 rounded-full shrink-0"
            style={{ backgroundColor: activeRoleData.color }}
          />
          <p className="leading-relaxed">{activeRoleData.description}</p>
        </div>
        <span className="shrink-0 px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-800 text-slate-400 border border-slate-700/60">
          {activeRoleData.badge}
        </span>
      </div>
    </div>
  );
}

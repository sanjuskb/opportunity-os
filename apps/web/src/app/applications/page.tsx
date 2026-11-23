'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Briefcase, Clock, CheckCircle2, AlertCircle, ArrowRight, Sparkles, Filter } from 'lucide-react';
import { DashboardLayout } from '../../components/dashboard/DashboardLayout';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Tabs } from '../../components/ui/Tabs';
import { useMockStore } from '../../lib/mock-data/mockStore';
import type { ApplicationStatus } from '@opportunity-os/shared-types';

export default function ApplicationsPage() {
  const { applications, opportunities, updateApplicationStatus } = useMockStore();
  const [activeTab, setActiveTab] = useState('all');

  const tabs = [
    { id: 'all', label: 'All Applications', count: applications.length },
    { id: 'submitted', label: 'Dispatched', count: applications.filter((a) => a.status === 'submitted').length },
    { id: 'ready_for_review', label: 'Review Required', count: applications.filter((a) => a.status === 'ready_for_review').length },
    { id: 'drafting', label: 'Drafting', count: applications.filter((a) => a.status === 'drafting').length },
  ];

  const filteredApplications = applications.filter((app) => {
    if (activeTab === 'all') return true;
    return app.status === activeTab;
  });

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white">Application Command Center</h1>
              <Badge variant="cyan">Autonomous Dispatch</Badge>
            </div>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Track real-time candidate package submissions, student approvals, and recruiter statuses.
            </p>
          </div>

          <Link href="/opportunities">
            <Button variant="glow" size="sm">
              <span>Apply to More Roles</span>
              <ArrowRight className="h-4 w-4 ml-1" />
            </Button>
          </Link>
        </div>

        {/* Tab Filters */}
        <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

        {/* Application Cards List */}
        <div className="grid grid-cols-1 gap-4">
          {filteredApplications.map((app) => {
            const opp = opportunities.find((o) => o.id === app.opportunityId);

            return (
              <Card key={app.id} className="hover:border-slate-700 transition">
                <CardContent className="p-5">
                  <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                    <div className="space-y-2 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-bold text-white text-base">{opp?.title || 'Applied Position'}</span>
                        <Badge
                          variant={
                            app.status === 'submitted'
                              ? 'emerald'
                              : app.status === 'ready_for_review'
                              ? 'amber'
                              : 'slate'
                          }
                        >
                          {app.status.replace(/_/g, ' ')}
                        </Badge>
                        <span className="font-mono text-xs text-cyan-400 font-bold px-2 py-0.5 rounded bg-cyan-950 border border-cyan-800">
                          {app.atsScore}% ATS Match
                        </span>
                      </div>

                      <div className="text-xs text-slate-400 flex items-center gap-4">
                        <span className="font-medium text-slate-200">{opp?.organization}</span>
                        <span>•</span>
                        <span>{opp?.location}</span>
                        <span>•</span>
                        <span>Applied on {new Date(app.appliedAt).toLocaleDateString()}</span>
                      </div>

                      {app.stageNotes && (
                        <p className="text-xs text-slate-300 bg-slate-900/60 p-2.5 rounded-lg border border-slate-800 leading-relaxed">
                          {app.stageNotes}
                        </p>
                      )}
                    </div>

                    <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
                      {app.status === 'ready_for_review' && (
                        <Button
                          variant="glow"
                          size="sm"
                          onClick={() => updateApplicationStatus(app.id, 'submitted')}
                        >
                          <span>Approve & Dispatch</span>
                        </Button>
                      )}
                      <Link href={`/opportunities/${app.opportunityId}`}>
                        <Button variant="outline" size="sm">
                          View Role
                        </Button>
                      </Link>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>
    </DashboardLayout>
  );
}

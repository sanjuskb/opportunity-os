'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { ArrowRight, Bot, CheckCircle2, ShieldCheck, AlertTriangle } from 'lucide-react';
import { DashboardLayout } from '../../components/dashboard/DashboardLayout';
import { Card, CardContent } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Tabs } from '../../components/ui/Tabs';
import { useAuth } from '@/components/auth/AuthProvider';
import {
  useApplications,
  useBrowserLogs,
  useDecideApproval,
  useExecuteApprovedApplication,
  useOpportunities,
  usePendingApprovals,
  usePrepareAutomation,
} from '@/lib/queries/useOpportunityOs';
import { BrowserScreenshotPreview } from '../../components/agent-control/BrowserScreenshotPreview';

export default function ApplicationsPage() {
  const { user } = useAuth();
  const { data: applications, isLoading } = useApplications();
  const { data: oppPage } = useOpportunities({ limit: 50 });
  const { data: pendingApprovals } = usePendingApprovals();
  const { data: browserLogs } = useBrowserLogs();
  const prepareMutation = usePrepareAutomation();
  const decideMutation = useDecideApproval();
  const executeMutation = useExecuteApprovedApplication();

  const [activeTab, setActiveTab] = useState('all');
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const apps = applications ?? [];
  const opps = oppPage?.items ?? [];
  const approvals = pendingApprovals ?? [];
  const logs = browserLogs ?? [];

  const tabs = [
    { id: 'all', label: 'All Applications', count: apps.length },
    { id: 'submitted', label: 'Submitted', count: apps.filter((a) => a.status === 'submitted').length },
    {
      id: 'ready_for_review',
      label: 'Awaiting Approval',
      count: apps.filter((a) => a.status === 'ready_for_review' || a.status === 'approved').length,
    },
    { id: 'drafting', label: 'Drafting', count: apps.filter((a) => a.status === 'drafting').length },
  ];

  const filteredApplications = apps.filter((app) => {
    if (activeTab === 'all') return true;
    if (activeTab === 'ready_for_review') {
      return app.status === 'ready_for_review' || app.status === 'approved';
    }
    return app.status === activeTab;
  });

  const handlePrepare = async (applicationId: string) => {
    setErrorMsg(null);
    setStatusMessage(null);
    try {
      const res = await prepareMutation.mutateAsync({ applicationId });
      setStatusMessage(res.message);
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'Automation prepare failed.');
    }
  };

  const handleDecision = async (approvalId: string, approved: boolean, executeSubmission = false) => {
    setErrorMsg(null);
    setStatusMessage(null);
    try {
      const res = await decideMutation.mutateAsync({ approvalId, approved, executeSubmission });
      setStatusMessage(
        `Approval decision recorded: ${res.status}${res.workflowResumed ? ` • LangGraph resumed (${res.resumedStage})` : ''}`
      );
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'Approval decision failed.');
    }
  };

  const handleExecuteApproved = async (applicationId: string, approvalRequestId: string) => {
    setErrorMsg(null);
    setStatusMessage(null);
    try {
      const res = await executeMutation.mutateAsync({ applicationId, approvalRequestId });
      setStatusMessage(res.message);
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'Approved execution failed.');
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white">Application Command Center</h1>
              <Badge variant="cyan">Human-in-the-Loop Gate</Badge>
            </div>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Playwright pre-fills supported forms and halts before submission until you explicitly approve.
            </p>
          </div>

          <Link href="/opportunities">
            <Button variant="glow" size="sm">
              <span>Discover More Roles</span>
              <ArrowRight className="h-4 w-4 ml-1" />
            </Button>
          </Link>
        </div>

        {statusMessage && (
          <div className="p-4 rounded-xl border border-emerald-500/40 bg-emerald-950/30 text-emerald-200 text-xs flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 shrink-0" />
            <span>{statusMessage}</span>
          </div>
        )}

        {errorMsg && (
          <div className="p-4 rounded-xl border border-rose-500/40 bg-rose-950/30 text-rose-200 text-xs flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {approvals.length > 0 && (
          <Card className="border-amber-500/40 bg-amber-950/15">
            <CardContent className="p-5 space-y-3">
              <div className="text-xs font-bold uppercase tracking-wider text-amber-300 flex items-center gap-2">
                <ShieldCheck className="h-4 w-4" />
                <span>Pending Human Approvals ({approvals.length})</span>
              </div>
              {approvals.map((apr) => {
                const opp = opps.find((o) => o.id === apr.opportunityId);
                const shotLog = logs.find(
                  (l) => l.sessionId === apr.sessionId && Boolean(l.screenshotUrl)
                );
                return (
                  <div key={apr.id} className="p-3 rounded-lg border border-amber-500/30 bg-[#0B0F19] space-y-3 text-xs">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                      <div>
                        <div className="font-bold text-white">{opp?.title || apr.opportunityId}</div>
                        <div className="text-slate-400">Action: {apr.actionType} • Status: {apr.status}</div>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <Button variant="outline" size="sm" onClick={() => void handleDecision(apr.id, false, false)}>
                          Reject
                        </Button>
                        <Button variant="outline" size="sm" onClick={() => void handleDecision(apr.id, true, false)}>
                          Approve
                        </Button>
                        <Button variant="glow" size="sm" onClick={() => void handleDecision(apr.id, true, true)}>
                          Approve &amp; Resume Agent
                        </Button>
                      </div>
                    </div>
                    {shotLog && <BrowserScreenshotPreview logId={shotLog.id} />}
                  </div>
                );
              })}
            </CardContent>
          </Card>
        )}

        <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

        {isLoading ? (
          <div className="h-40 rounded-xl border border-slate-800 bg-[#0B0F19] animate-pulse" />
        ) : filteredApplications.length === 0 ? (
          <div className="p-8 rounded-xl border border-slate-800 bg-[#0B0F19] text-center text-xs text-slate-400">
            No applications in this category yet.
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {filteredApplications.map((app) => {
              const opp = opps.find((o) => o.id === app.opportunityId);
              const matchedApproval = approvals.find((apr) => apr.opportunityId === app.opportunityId);
              return (
                <Card key={app.id} className="hover:border-slate-700 transition">
                  <CardContent className="p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                    <div className="space-y-1.5 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-bold text-white text-base">{opp?.title || app.opportunityId}</span>
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
                      </div>
                      <div className="text-xs text-slate-400 flex items-center gap-3">
                        <span className="font-medium text-slate-200">{opp?.organization || 'Organization'}</span>
                        <span>•</span>
                        <span>Method: {app.submissionMethod}</span>
                        <span>•</span>
                        <span>Created {app.createdAt ? new Date(app.createdAt).toLocaleDateString() : 'Recent'}</span>
                      </div>
                    </div>

                    <div className="flex flex-wrap items-center gap-2">
                      {(app.status === 'drafting' || app.status === 'eligible') && (
                        <Button
                          variant="primary"
                          size="sm"
                          disabled={!user}
                          isLoading={prepareMutation.isPending}
                          onClick={() => void handlePrepare(app.id)}
                        >
                          <Bot className="h-3.5 w-3.5 mr-1" />
                          <span>Prepare Form</span>
                        </Button>
                      )}
                      {app.status === 'approved' && matchedApproval && (
                        <Button
                          variant="glow"
                          size="sm"
                          isLoading={executeMutation.isPending}
                          onClick={() => void handleExecuteApproved(app.id, matchedApproval.id)}
                        >
                          Execute Approved Submit
                        </Button>
                      )}
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}

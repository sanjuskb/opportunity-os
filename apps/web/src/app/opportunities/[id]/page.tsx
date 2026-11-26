'use client';

import React, { use, useEffect } from 'react';
import Link from 'next/link';
import {
  ArrowLeft,
  Building2,
  MapPin,
  Calendar,
  Sparkles,
  ShieldCheck,
  CheckCircle2,
  Bookmark,
  ExternalLink,
} from 'lucide-react';
import { DashboardLayout } from '../../../components/dashboard/DashboardLayout';
import { Card, CardHeader, CardTitle, CardContent } from '../../../components/ui/Card';
import { Badge } from '../../../components/ui/Badge';
import { Button } from '../../../components/ui/Button';
import { useAuth } from '@/components/auth/AuthProvider';
import {
  useApplications,
  useCreateApplication,
  useEvaluateEligibility,
  useOpportunityDetail,
  useSavedOpportunities,
  useToggleSaveOpportunity,
} from '@/lib/queries/useOpportunityOs';

export default function OpportunityDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { user } = useAuth();
  const { data: opportunity, isLoading } = useOpportunityDetail(id);
  const { data: savedRows } = useSavedOpportunities();
  const { data: applications } = useApplications();
  const toggleSave = useToggleSaveOpportunity();
  const createApp = useCreateApplication();
  const evalElig = useEvaluateEligibility();

  useEffect(() => {
    if (user && opportunity?.id && !evalElig.data && !evalElig.isPending) {
      evalElig.mutate(opportunity.id);
    }
  }, [user, opportunity?.id, evalElig]);

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="h-64 rounded-2xl border border-slate-800 bg-[#0B0F19] animate-pulse" />
      </DashboardLayout>
    );
  }

  if (!opportunity) {
    return (
      <DashboardLayout>
        <div className="text-center py-20 space-y-4">
          <h2 className="text-xl font-bold text-white">Opportunity Not Found</h2>
          <Link href="/opportunities">
            <Button variant="outline" size="sm">
              Return to Discovery
            </Button>
          </Link>
        </div>
      </DashboardLayout>
    );
  }

  const isSaved = (savedRows ?? []).some((s) => s.id === opportunity.id);
  const isApplied = (applications ?? []).some((a) => a.opportunityId === opportunity.id);
  const eligibility = evalElig.data;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <Link href="/opportunities" className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition">
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Opportunities</span>
        </Link>

        <div className="rounded-2xl border border-slate-800 bg-[#0D1322] p-6 sm:p-8 shadow-2xl">
          <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
            <div className="space-y-3 flex-1">
              <div className="flex items-center gap-2 flex-wrap">
                {eligibility && (
                  <Badge variant={eligibility.score >= 85 ? 'cyan' : 'emerald'}>
                    <Sparkles className="h-3.5 w-3.5 mr-1" />
                    {Math.round(eligibility.score)}% Eligibility Score
                  </Badge>
                )}
                <Badge variant="slate">{opportunity.type.replace(/_/g, ' ')}</Badge>
                <span className="text-[10px] font-mono text-slate-500 uppercase px-2 py-0.5 rounded bg-slate-900 border border-slate-800">
                  Provider: {opportunity.sourceProvider}
                </span>
              </div>

              <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">{opportunity.title}</h1>

              <div className="flex flex-wrap items-center gap-4 text-xs sm:text-sm text-slate-400">
                <span className="flex items-center gap-1.5 font-bold text-slate-200">
                  <Building2 className="h-4 w-4 text-cyan-400" />
                  {opportunity.organization}
                </span>
                <span className="flex items-center gap-1.5">
                  <MapPin className="h-4 w-4 text-slate-400" />
                  {opportunity.location}
                </span>
                {opportunity.stipendOrSalary && (
                  <span className="text-emerald-400 font-bold">{opportunity.stipendOrSalary}</span>
                )}
                {opportunity.deadline && (
                  <span className="flex items-center gap-1 text-amber-400">
                    <Calendar className="h-4 w-4" />
                    Deadline: {new Date(opportunity.deadline).toLocaleDateString()}
                  </span>
                )}
              </div>
            </div>

            <div className="flex items-center gap-3 w-full lg:w-auto">
              <Button
                variant="outline"
                size="md"
                onClick={() => void toggleSave.mutate({ opportunityId: opportunity.id, saved: !isSaved })}
                className={isSaved ? 'text-amber-400 border-amber-500/40' : ''}
              >
                <Bookmark className={`h-4 w-4 mr-1.5 ${isSaved ? 'fill-amber-400' : ''}`} />
                <span>{isSaved ? 'Saved' : 'Save'}</span>
              </Button>

              {isApplied ? (
                <Button variant="secondary" size="md" disabled>
                  <CheckCircle2 className="h-4 w-4 text-emerald-400 mr-2" />
                  <span>Application Drafted</span>
                </Button>
              ) : (
                <Button variant="glow" size="md" onClick={() => void createApp.mutate(opportunity.id)}>
                  <ShieldCheck className="h-4 w-4 mr-2" />
                  <span>Create Application Draft</span>
                </Button>
              )}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Role Description &amp; Requirements</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4 text-sm text-slate-300 leading-relaxed">
                <p>{opportunity.description || 'Full details available on the official source portal.'}</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Required Technical Skills</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-wrap gap-2">
                {opportunity.requiredSkills.map((sk) => (
                  <span key={sk} className="px-3 py-1 rounded-lg text-xs font-medium bg-slate-900 text-cyan-300 border border-slate-800">
                    {sk}
                  </span>
                ))}
              </CardContent>
            </Card>

            <div className="p-4 rounded-xl border border-slate-800 bg-[#0B0F19] flex items-center justify-between text-xs text-slate-400">
              <span>Source URL verified in Opportunity OS index</span>
              <a href={opportunity.sourceUrl} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-cyan-400 hover:underline">
                <span>Original Portal</span>
                <ExternalLink className="h-3 w-3" />
              </a>
            </div>
          </div>

          <div className="space-y-6">
            <Card className="border-cyan-500/25 bg-gradient-to-b from-[#0D1322] to-[#0B0F19]">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-cyan-400" />
                  <span>Live Eligibility Evaluation</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4 text-xs">
                {!eligibility ? (
                  <Button variant="outline" size="sm" isLoading={evalElig.isPending} onClick={() => evalElig.mutate(opportunity.id)}>
                    Evaluate My Eligibility
                  </Button>
                ) : (
                  <>
                    <div className="flex items-center justify-between p-3 rounded-xl border border-slate-800 bg-slate-900/60">
                      <span className="text-slate-300">Deterministic Match</span>
                      <span className="text-xl font-black text-cyan-400">{Math.round(eligibility.score)}%</span>
                    </div>
                    {eligibility.skillOverlap && (
                      <div className="p-3 rounded-xl border border-slate-800 bg-[#0B0F19] space-y-1.5">
                        <div>
                          <span className="text-emerald-400 font-semibold">Matched: </span>
                          <span>{eligibility.skillOverlap.matchedSkills.join(', ') || 'None'}</span>
                        </div>
                        {eligibility.skillOverlap.missingSkills.length > 0 && (
                          <div>
                            <span className="text-amber-400 font-semibold">Skill Gaps: </span>
                            <span>{eligibility.skillOverlap.missingSkills.join(', ')}</span>
                          </div>
                        )}
                      </div>
                    )}
                    <p className="text-slate-300 leading-relaxed">{eligibility.explanation}</p>
                  </>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}

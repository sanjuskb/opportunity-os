'use client';

import React, { use } from 'react';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import {
  ArrowLeft,
  Building2,
  MapPin,
  Calendar,
  Sparkles,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  Bookmark,
  Share2,
  ExternalLink,
} from 'lucide-react';
import { DashboardLayout } from '../../../components/dashboard/DashboardLayout';
import { Card, CardHeader, CardTitle, CardContent } from '../../../components/ui/Card';
import { Badge } from '../../../components/ui/Badge';
import { Button } from '../../../components/ui/Button';
import { useMockStore } from '../../../lib/mock-data/mockStore';
import { MOCK_ELIGIBILITY_CACHE } from '../../../lib/mock-data/opportunities';

interface OpportunityDetailPageProps {
  params: Promise<{ id: string }>;
}

export default function OpportunityDetailPage({ params }: OpportunityDetailPageProps) {
  const { id } = use(params);
  const { opportunities, savedOpportunityIds, toggleSaveOpportunity, applyToOpportunity, applications, studentProfile } =
    useMockStore();

  const opportunity = opportunities.find((o) => o.id === id);

  if (!opportunity) {
    return (
      <DashboardLayout>
        <div className="text-center py-20 space-y-4">
          <h2 className="text-xl font-bold text-white">Opportunity Not Found</h2>
          <p className="text-xs text-slate-400">The requested opportunity ID does not exist in the active ingestion feed.</p>
          <Link href="/opportunities">
            <Button variant="outline" size="sm">
              Return to Discovery
            </Button>
          </Link>
        </div>
      </DashboardLayout>
    );
  }

  const isSaved = savedOpportunityIds.includes(opportunity.id);
  const isApplied = applications.some((a) => a.opportunityId === opportunity.id);
  const eligibility = MOCK_ELIGIBILITY_CACHE[opportunity.id] || {
    opportunityId: opportunity.id,
    isEligible: true,
    score: 88,
    deterministicChecks: {
      batchMatched: true,
      degreeMatched: true,
      cgpaMatched: (studentProfile.cgpa || 8.0) >= (opportunity.minCgpa || 7.0),
    },
    skillOverlap: {
      matchedSkills: opportunity.requiredSkills.filter((sk) => studentProfile.skills.includes(sk)),
      missingSkills: opportunity.requiredSkills.filter((sk) => !studentProfile.skills.includes(sk)),
    },
    explanation: 'Deterministic eligibility satisfied based on current student Career Passport data.',
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Back Link */}
        <div>
          <Link href="/opportunities" className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition">
            <ArrowLeft className="h-4 w-4" />
            <span>Back to Opportunities</span>
          </Link>
        </div>

        {/* Opportunity Hero Header Card */}
        <div className="rounded-2xl border border-slate-800 bg-[#0D1322] p-6 sm:p-8 shadow-2xl relative overflow-hidden">
          <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
            <div className="space-y-3 flex-1">
              <div className="flex items-center gap-2 flex-wrap">
                <Badge variant={eligibility.score >= 90 ? 'cyan' : 'emerald'}>
                  <Sparkles className="h-3.5 w-3.5 mr-1" />
                  {eligibility.score}% AI Match Score
                </Badge>
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
                <span className="text-emerald-400 font-bold">{opportunity.stipendOrSalary}</span>
                {opportunity.deadline && (
                  <span className="flex items-center gap-1 text-amber-400">
                    <Calendar className="h-4 w-4" />
                    Deadline: {opportunity.deadline}
                  </span>
                )}
              </div>
            </div>

            {/* Quick Actions */}
            <div className="flex items-center gap-3 w-full lg:w-auto">
              <Button
                variant="outline"
                size="md"
                onClick={() => toggleSaveOpportunity(opportunity.id)}
                className={isSaved ? 'text-amber-400 border-amber-500/40' : ''}
              >
                <Bookmark className={`h-4 w-4 mr-1.5 ${isSaved ? 'fill-amber-400' : ''}`} />
                <span>{isSaved ? 'Saved' : 'Save'}</span>
              </Button>

              {isApplied ? (
                <Button variant="secondary" size="md" disabled>
                  <CheckCircle2 className="h-4 w-4 text-emerald-400 mr-2" />
                  <span>Applied</span>
                </Button>
              ) : (
                <Button variant="glow" size="md" onClick={() => applyToOpportunity(opportunity.id)}>
                  <ShieldCheck className="h-4 w-4 mr-2" />
                  <span>Apply with Career Passport</span>
                </Button>
              )}
            </div>
          </div>
        </div>

        {/* Content Layout: Left 2 Cols (Details) + Right 1 Col (Eligibility Breakdown) */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            {/* Description Card */}
            <Card>
              <CardHeader>
                <CardTitle>Role Description & Impact</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4 text-sm text-slate-300 leading-relaxed">
                <p>{opportunity.description}</p>
                <p>
                  As an engineer in this cohort, you will collaborate with cross-functional research teams, deliver verified code directly to production repositories, and work under senior mentor supervision.
                </p>
              </CardContent>
            </Card>

            {/* Required Skills Matrix */}
            <Card>
              <CardHeader>
                <CardTitle>Required Technical Skills</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {opportunity.requiredSkills.map((sk) => {
                    const hasSkill = studentProfile.skills.includes(sk);
                    return (
                      <span
                        key={sk}
                        className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border ${
                          hasSkill
                            ? 'bg-cyan-950/60 text-cyan-300 border-cyan-500/40'
                            : 'bg-slate-900 text-slate-400 border-slate-800'
                        }`}
                      >
                        {hasSkill ? <CheckCircle2 className="h-3.5 w-3.5 text-cyan-400" /> : <XCircle className="h-3.5 w-3.5 text-slate-500" />}
                        <span>{sk}</span>
                      </span>
                    );
                  })}
                </div>
              </CardContent>
            </Card>

            {/* Source Verification Box */}
            <div className="p-4 rounded-xl border border-slate-800 bg-[#0B0F19] flex items-center justify-between text-xs text-slate-400">
              <div>
                <span>Crawled from Official Ingestion Feed • Ingest Timestamp: </span>
                <span className="font-mono text-slate-300">{new Date(opportunity.retrievalTimestamp).toLocaleString()}</span>
              </div>
              <a
                href={opportunity.sourceUrl}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 text-cyan-400 hover:underline"
              >
                <span>Original Portal</span>
                <ExternalLink className="h-3 w-3" />
              </a>
            </div>
          </div>

          {/* Right Column: AI Eligibility Breakdown */}
          <div className="space-y-6">
            <Card className="border-cyan-500/25 bg-gradient-to-b from-[#0D1322] to-[#0B0F19]">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-cyan-400" />
                  <span>Explainable Match Breakdown</span>
                </CardTitle>
              </CardHeader>

              <CardContent className="space-y-4">
                {/* Score Dial */}
                <div className="flex items-center justify-between p-3 rounded-xl border border-slate-800 bg-slate-900/60">
                  <span className="text-xs text-slate-300">Composite Match Score</span>
                  <span className="text-xl font-black text-cyan-400">{eligibility.score}%</span>
                </div>

                {/* Deterministic Checks */}
                <div className="space-y-2 text-xs">
                  <div className="font-semibold text-slate-400 uppercase tracking-wider text-[10px]">
                    Deterministic Pre-checks:
                  </div>

                  <div className="flex items-center justify-between p-2 rounded-lg bg-[#0B0F19]">
                    <span className="text-slate-300">Graduation Batch ({opportunity.eligibleBatches.join(', ')})</span>
                    <span className="flex items-center gap-1 text-emerald-400 font-semibold">
                      <CheckCircle2 className="h-3.5 w-3.5" />
                      Matched ({studentProfile.graduationYear})
                    </span>
                  </div>

                  <div className="flex items-center justify-between p-2 rounded-lg bg-[#0B0F19]">
                    <span className="text-slate-300">Degree Program ({opportunity.eligibleDegrees.join(', ')})</span>
                    <span className="flex items-center gap-1 text-emerald-400 font-semibold">
                      <CheckCircle2 className="h-3.5 w-3.5" />
                      Eligible ({studentProfile.degree})
                    </span>
                  </div>

                  <div className="flex items-center justify-between p-2 rounded-lg bg-[#0B0F19]">
                    <span className="text-slate-300">Minimum CGPA ({opportunity.minCgpa || 7.0})</span>
                    <span className="flex items-center gap-1 text-emerald-400 font-semibold">
                      <CheckCircle2 className="h-3.5 w-3.5" />
                      Qualified ({studentProfile.cgpa})
                    </span>
                  </div>
                </div>

                {/* Skill Overlap Breakdown */}
                <div className="space-y-2 text-xs">
                  <div className="font-semibold text-slate-400 uppercase tracking-wider text-[10px]">
                    Skill Overlap:
                  </div>
                  <div className="p-3 rounded-xl border border-slate-800 bg-[#0B0F19] space-y-2">
                    <div>
                      <span className="text-[11px] text-emerald-400 font-semibold">Matched Skills: </span>
                      <span className="text-slate-300">{eligibility.skillOverlap.matchedSkills.join(', ') || 'None'}</span>
                    </div>
                    {eligibility.skillOverlap.missingSkills.length > 0 && (
                      <div>
                        <span className="text-[11px] text-amber-400 font-semibold">Skills to Brush Up: </span>
                        <span className="text-slate-400">{eligibility.skillOverlap.missingSkills.join(', ')}</span>
                      </div>
                    )}
                  </div>
                </div>

                <div className="p-3 rounded-lg border border-slate-800/80 bg-slate-900/40 text-xs text-slate-400 leading-relaxed">
                  {eligibility.explanation}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}

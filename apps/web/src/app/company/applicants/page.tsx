'use client';

import React from 'react';
import Link from 'next/link';
import { Briefcase, CheckCircle2, Clock, Eye, Sparkles } from 'lucide-react';
import { DashboardLayout } from '../../../components/dashboard/DashboardLayout';
import { Card, CardHeader, CardTitle, CardContent } from '../../../components/ui/Card';
import { Badge } from '../../../components/ui/Badge';
import { Button } from '../../../components/ui/Button';
import { useMockStore } from '../../../lib/mock-data/mockStore';

export default function ApplicantPipelinePage() {
  const { applications, opportunities, candidates } = useMockStore();

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white">Applicant Review Pipeline</h1>
              <Badge variant="sapphire">Recruitment Kanban</Badge>
            </div>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Review and advance candidate packages with verified Digilocker transcripts and ATS match breakdown.
            </p>
          </div>
        </div>

        {/* Applications List */}
        <div className="space-y-3">
          {applications.map((app) => {
            const opp = opportunities.find((o) => o.id === app.opportunityId);
            const cand = candidates[0]; // Sanju S. Kumar

            return (
              <Card key={app.id}>
                <CardContent className="p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                  <div className="space-y-1.5 flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-bold text-white text-base">{cand.fullName}</span>
                      <span className="text-xs text-slate-400">applying for</span>
                      <span className="font-semibold text-cyan-300 text-sm">{opp?.title}</span>
                      <Badge variant="cyan">{app.atsScore}% ATS Match</Badge>
                    </div>

                    <div className="text-xs text-slate-400">
                      {cand.collegeName} • CGPA: <span className="text-emerald-400 font-bold">{cand.cgpa}</span> • Applied {new Date(app.appliedAt).toLocaleDateString()}
                    </div>

                    <p className="text-xs text-slate-300 italic pt-1">
                      &quot;{app.stageNotes}&quot;
                    </p>
                  </div>

                  <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
                    <Link href="/career-passport">
                      <Button variant="outline" size="sm">
                        Inspect Passport
                      </Button>
                    </Link>
                    <Button variant="primary" size="sm">
                      Advance to Interview
                    </Button>
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

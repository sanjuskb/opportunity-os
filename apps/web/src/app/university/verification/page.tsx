'use client';

import React, { useState } from 'react';
import { ShieldCheck, CheckCircle2, Award, Clock } from 'lucide-react';
import { DashboardLayout } from '../../../components/dashboard/DashboardLayout';
import { Card, CardHeader, CardTitle, CardContent } from '../../../components/ui/Card';
import { Badge } from '../../../components/ui/Badge';
import { Button } from '../../../components/ui/Button';
import { useMockStore } from '../../../lib/mock-data/mockStore';

export default function UniversityVerificationPage() {
  const { candidates, verifiedStudentIds, verifyStudentCredential } = useMockStore();
  const [activeTab, setActiveTab] = useState<'pending' | 'verified'>('pending');

  const pendingList = candidates.filter((c) => !verifiedStudentIds.includes(c.id));
  const verifiedList = candidates.filter((c) => verifiedStudentIds.includes(c.id));

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white">Institutional Verification</h1>
              <Badge variant="emerald">DigiLocker Gateway</Badge>
            </div>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Verify degree credentials, official CGPA transcripts, and AICTE compliance for graduating cohorts.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 border-b border-slate-800">
          <button
            type="button"
            onClick={() => setActiveTab('pending')}
            className={`px-4 py-2 text-xs font-bold border-b-2 transition ${
              activeTab === 'pending'
                ? 'border-emerald-500 text-white'
                : 'border-transparent text-slate-400 hover:text-white'
            }`}
          >
            Pending Verification ({pendingList.length})
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('verified')}
            className={`px-4 py-2 text-xs font-bold border-b-2 transition ${
              activeTab === 'verified'
                ? 'border-emerald-500 text-white'
                : 'border-transparent text-slate-400 hover:text-white'
            }`}
          >
            Accredited & Verified ({verifiedList.length})
          </button>
        </div>

        <div className="space-y-3">
          {(activeTab === 'pending' ? pendingList : verifiedList).map((cand) => (
            <Card key={cand.id}>
              <CardContent className="p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div className="space-y-1">
                  <div className="font-bold text-white text-sm">{cand.fullName}</div>
                  <div className="text-xs text-slate-400">
                    {cand.degree} in {cand.branch} • Reported CGPA: <span className="text-emerald-400 font-bold">{cand.cgpa}</span>
                  </div>
                  <div className="font-mono text-[10px] text-slate-500">{cand.careerPassportId}</div>
                </div>

                <div>
                  {activeTab === 'pending' ? (
                    <Button variant="glow" size="sm" onClick={() => verifyStudentCredential(cand.id)}>
                      <ShieldCheck className="h-4 w-4 mr-1 text-emerald-300" />
                      <span>Approve DigiLocker Credential</span>
                    </Button>
                  ) : (
                    <Badge variant="emerald">
                      <CheckCircle2 className="h-3.5 w-3.5 mr-1" />
                      Accredited
                    </Badge>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}

          {(activeTab === 'pending' ? pendingList : verifiedList).length === 0 && (
            <div className="text-center py-12 text-xs text-slate-500">
              No students found in this category.
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}

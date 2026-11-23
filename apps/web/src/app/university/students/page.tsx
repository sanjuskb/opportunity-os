'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Users, Search, ShieldCheck, Award } from 'lucide-react';
import { DashboardLayout } from '../../../components/dashboard/DashboardLayout';
import { Card, CardHeader, CardTitle, CardContent } from '../../../components/ui/Card';
import { Badge } from '../../../components/ui/Badge';
import { Button } from '../../../components/ui/Button';
import { Input } from '../../../components/ui/Input';
import { useMockStore } from '../../../lib/mock-data/mockStore';

export default function UniversityStudentsPage() {
  const { candidates } = useMockStore();
  const [searchQuery, setSearchQuery] = useState('');

  const filtered = candidates.filter((c) =>
    c.fullName.toLowerCase().includes(searchQuery.toLowerCase()) ||
    c.branch.toLowerCase().includes(searchQuery.toLowerCase()) ||
    c.skills.some((s) => s.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white">Student Cohort Directory</h1>
              <Badge variant="emerald">Institutional Roster</Badge>
            </div>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Complete student cohort with verified transcripts, CGPA, and career passport records.
            </p>
          </div>
        </div>

        <div className="p-4 rounded-xl border border-slate-800 bg-[#0B0F19]">
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Filter students by name, branch, or technical skill..."
          />
        </div>

        <div className="grid grid-cols-1 gap-3">
          {filtered.map((cand) => (
            <Card key={cand.id}>
              <CardContent className="p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-white text-sm">{cand.fullName}</span>
                    <Badge variant="emerald">Verified</Badge>
                    <span className="font-mono text-xs text-cyan-400 font-bold">{cand.cgpa} CGPA</span>
                  </div>
                  <div className="text-xs text-slate-400">
                    {cand.degree} in {cand.branch} • Batch of {cand.graduationYear}
                  </div>
                  <div className="flex flex-wrap gap-1 pt-1">
                    {cand.skills.map((s) => (
                      <span key={s} className="px-1.5 py-0.5 rounded text-[10px] bg-slate-900 text-slate-300 border border-slate-800">
                        {s}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
                  <Link href="/career-passport">
                    <Button variant="outline" size="sm">
                      Inspect Passport
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </DashboardLayout>
  );
}

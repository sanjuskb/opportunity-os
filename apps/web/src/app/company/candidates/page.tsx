'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Users, Search, Award, ShieldCheck, CheckCircle2, ArrowRight } from 'lucide-react';
import { DashboardLayout } from '../../../components/dashboard/DashboardLayout';
import { Card, CardHeader, CardTitle, CardContent } from '../../../components/ui/Card';
import { Badge } from '../../../components/ui/Badge';
import { Button } from '../../../components/ui/Button';
import { Input } from '../../../components/ui/Input';
import { useMockStore } from '../../../lib/mock-data/mockStore';

export default function CandidateDiscoveryPage() {
  const { candidates } = useMockStore();
  const [searchQuery, setSearchQuery] = useState('');
  const [shortlisted, setShortlisted] = useState<string[]>([]);

  const toggleShortlist = (id: string) => {
    setShortlisted((prev) => (prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]));
  };

  const filteredCandidates = candidates.filter((c) => {
    return (
      c.fullName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.collegeName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.skills.some((sk) => sk.toLowerCase().includes(searchQuery.toLowerCase()))
    );
  });

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white">Candidate Discovery Feed</h1>
              <Badge variant="sapphire">Pre-Screened Talent</Badge>
            </div>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Discover skill-verified engineering students from accredited Indian colleges.
            </p>
          </div>

          <div className="text-xs text-slate-400 font-mono">
            Showing <span className="text-blue-400 font-bold">{filteredCandidates.length}</span> verified profiles
          </div>
        </div>

        <div className="p-4 rounded-xl border border-slate-800 bg-[#0B0F19]">
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search candidates by name, college (e.g. NIT Trichy, IIIT), or skill (e.g. Go, PyTorch)..."
          />
        </div>

        {/* Candidate Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredCandidates.map((cand) => {
            const isShortlisted = shortlisted.includes(cand.id);

            return (
              <Card key={cand.id} className="hover:border-slate-700 transition">
                <CardContent className="p-5 space-y-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="font-bold text-base text-white">{cand.fullName}</div>
                      <div className="text-xs text-cyan-400 font-medium">{cand.headline}</div>
                      <div className="text-xs text-slate-400 mt-0.5">
                        {cand.degree} • {cand.collegeName} (Batch of {cand.graduationYear})
                      </div>
                    </div>
                    <div className="text-right shrink-0">
                      <div className="font-bold text-emerald-400 text-sm">{cand.cgpa} CGPA</div>
                      <span className="text-[10px] text-slate-400 font-mono">Passport Verified</span>
                    </div>
                  </div>

                  <p className="text-xs text-slate-300 line-clamp-2 leading-relaxed">{cand.about}</p>

                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {cand.skills.map((sk) => (
                      <span key={sk} className="px-2 py-0.5 rounded text-[10px] bg-slate-900 text-slate-300 border border-slate-800">
                        {sk}
                      </span>
                    ))}
                  </div>

                  <div className="pt-3 border-t border-slate-800 flex items-center justify-between">
                    <span className="font-mono text-[10px] text-slate-500">{cand.careerPassportId}</span>
                    <Button
                      variant={isShortlisted ? 'secondary' : 'primary'}
                      size="sm"
                      onClick={() => toggleShortlist(cand.id)}
                    >
                      {isShortlisted ? 'Shortlisted' : 'Shortlist Candidate'}
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

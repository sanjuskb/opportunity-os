'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Award, ShieldCheck, CheckCircle2, Copy, Check, ExternalLink, QrCode, Sparkles, GraduationCap } from 'lucide-react';
import { DashboardLayout } from '../../components/dashboard/DashboardLayout';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { useMockStore } from '../../lib/mock-data/mockStore';

export default function CareerPassportPage() {
  const { studentProfile } = useMockStore();
  const [copied, setCopied] = useState(false);

  const handleCopyShareLink = () => {
    navigator.clipboard.writeText(`https://nexteras.in/passport/${studentProfile.careerPassportId}`);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header Strip */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white">Verified Career Passport</h1>
              <Badge variant="cyan">AICTE & UGC Linked</Badge>
            </div>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Cryptographically verified academic credentials, coursework, and GitHub project records for zero-hallucination hiring.
            </p>
          </div>

          <Button variant="outline" size="sm" onClick={handleCopyShareLink}>
            {copied ? <Check className="h-4 w-4 mr-1.5 text-emerald-400" /> : <Copy className="h-4 w-4 mr-1.5" />}
            <span>{copied ? 'Copied Public Link!' : 'Share Passport'}</span>
          </Button>
        </div>

        {/* Digital Passport Identity Card (Physical Maquette Look) */}
        <div className="rounded-2xl border-2 border-cyan-500/30 bg-gradient-to-br from-[#0B132B] via-[#090D16] to-[#070B14] p-6 sm:p-8 shadow-2xl relative overflow-hidden">
          <div className="absolute top-0 right-0 p-8 opacity-10 pointer-events-none">
            <Award className="h-64 w-64 text-cyan-400" />
          </div>

          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6 relative z-10 pb-6 border-b border-slate-800/80">
            <div className="flex items-center gap-4">
              <div className="h-16 w-16 rounded-2xl bg-gradient-to-tr from-cyan-600 to-indigo-600 p-0.5 shadow-xl">
                <div className="h-full w-full rounded-2xl bg-[#090D16] flex items-center justify-center font-black text-2xl text-cyan-300">
                  {studentProfile.fullName.charAt(0)}
                </div>
              </div>
              <div>
                <h2 className="text-xl sm:text-2xl font-black text-white">{studentProfile.fullName}</h2>
                <p className="text-xs sm:text-sm text-cyan-300 font-medium">{studentProfile.headline}</p>
                <div className="text-xs text-slate-400 mt-0.5">
                  {studentProfile.collegeName} • Batch of {studentProfile.graduationYear}
                </div>
              </div>
            </div>

            <div className="text-left sm:text-right space-y-1">
              <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Passport Identifier:</div>
              <div className="font-mono text-sm font-bold text-cyan-400 bg-slate-900/80 px-3 py-1 rounded-lg border border-slate-800">
                {studentProfile.careerPassportId}
              </div>
              <div className="text-[11px] text-emerald-400 flex items-center gap-1 justify-start sm:justify-end">
                <ShieldCheck className="h-3.5 w-3.5" />
                <span>DigiLocker Verified</span>
              </div>
            </div>
          </div>

          {/* Academic Snapshot */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-6 relative z-10 text-xs">
            <div className="p-3 rounded-xl border border-slate-800 bg-[#0B0F19]/80">
              <span className="text-slate-400">Cumulative CGPA</span>
              <div className="text-lg font-bold text-white mt-1">{studentProfile.cgpa} / 10.0</div>
            </div>
            <div className="p-3 rounded-xl border border-slate-800 bg-[#0B0F19]/80">
              <span className="text-slate-400">Degree & Major</span>
              <div className="text-lg font-bold text-white mt-1 truncate">{studentProfile.degree} CSE</div>
            </div>
            <div className="p-3 rounded-xl border border-slate-800 bg-[#0B0F19]/80">
              <span className="text-slate-400">ATS Match Readiness</span>
              <div className="text-lg font-bold text-cyan-400 mt-1">{studentProfile.atsScore}%</div>
            </div>
            <div className="p-3 rounded-xl border border-slate-800 bg-[#0B0F19]/80">
              <span className="text-slate-400">Verified Credentials</span>
              <div className="text-lg font-bold text-emerald-400 mt-1">{studentProfile.verifiedCredentials.length} Badges</div>
            </div>
          </div>
        </div>

        {/* Verified Credential Badges Section */}
        <div className="space-y-4">
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-emerald-400" />
            <span>Institutionally Verified Credentials</span>
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {studentProfile.verifiedCredentials.map((cred) => (
              <Card key={cred.id} className="hover:border-slate-700 transition">
                <CardContent className="p-5 space-y-3">
                  <div className="flex items-center justify-between">
                    <Badge variant="emerald">{cred.verificationSource}</Badge>
                    <span className="text-[10px] text-slate-400">{cred.issueDate}</span>
                  </div>

                  <div className="font-bold text-white text-sm leading-snug">{cred.title}</div>
                  <div className="text-xs text-slate-400">Issuer: {cred.issuer}</div>

                  <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-xs">
                    <span className="font-semibold text-cyan-400">{cred.gradeOrScore}</span>
                    <a
                      href={cred.credentialUrl}
                      target="_blank"
                      rel="noreferrer"
                      className="text-slate-400 hover:text-white flex items-center gap-1"
                    >
                      <span>Verify</span>
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Verified Projects Section */}
        <div className="space-y-4 pt-2">
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-cyan-400" />
            <span>Verified Engineering Projects</span>
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {studentProfile.projects.map((proj) => (
              <Card key={proj.title}>
                <CardContent className="p-5 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-white text-sm">{proj.title}</span>
                    {proj.verifiedCommitHash && (
                      <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-emerald-400">
                        SHA: {proj.verifiedCommitHash}
                      </span>
                    )}
                  </div>

                  <p className="text-xs text-slate-300 leading-relaxed">{proj.description}</p>

                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {proj.technologies.map((t) => (
                      <span key={t} className="px-2 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300 border border-slate-700">
                        {t}
                      </span>
                    ))}
                  </div>

                  {proj.githubUrl && (
                    <div className="pt-2 border-t border-slate-800 text-xs">
                      <a href={proj.githubUrl} target="_blank" rel="noreferrer" className="text-cyan-400 hover:underline flex items-center gap-1">
                        <span>View Repository</span>
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}

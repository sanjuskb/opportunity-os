'use client';

import React from 'react';
import Link from 'next/link';
import { School, Users, Award, ShieldCheck, TrendingUp, CheckCircle2, ArrowRight } from 'lucide-react';
import { DashboardLayout } from '../../../components/dashboard/DashboardLayout';
import { Card, CardHeader, CardTitle, CardContent } from '../../../components/ui/Card';
import { Badge } from '../../../components/ui/Badge';
import { Button } from '../../../components/ui/Button';
import { MetricCard } from '../../../components/ui/MetricCard';
import { useMockStore } from '../../../lib/mock-data/mockStore';

export default function UniversityDashboardPage() {
  const { candidates } = useMockStore();

  const departmentStats = [
    { dept: 'Computer Science & Engineering', total: 240, placed: 218, rate: '90.8%' },
    { dept: 'Data Science & Artificial Intelligence', total: 120, placed: 106, rate: '88.3%' },
    { dept: 'Electronics & Communication', total: 180, placed: 142, rate: '78.9%' },
    { dept: 'Electrical & Electronics', total: 140, placed: 98, rate: '70.0%' },
  ];

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white">University Placement Cell</h1>
              <Badge variant="emerald">NIT Tiruchirappalli</Badge>
            </div>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Institutional placement monitoring, DigiLocker academic verification, and recruiter coordination.
            </p>
          </div>

          <Link href="/university/verification">
            <Button variant="glow" size="sm">
              <ShieldCheck className="h-4 w-4 mr-1.5 text-emerald-300" />
              <span>Verify Pending Credentials</span>
            </Button>
          </Link>
        </div>

        {/* 4 Metric Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            title="Eligible Students"
            value="680"
            subtitle="Batch of 2025 & 2026"
            icon={Users}
            color="emerald"
          />
          <MetricCard
            title="Placement Rate"
            value="82.4%"
            subtitle="564 students placed"
            trend="+8.2% YoY"
            icon={TrendingUp}
            color="cyan"
          />
          <MetricCard
            title="Avg Verified Stipend"
            value="₹48,500"
            subtitle="Top tier across NITs"
            icon={Award}
            color="amber"
          />
          <MetricCard
            title="Accredited Records"
            value="100%"
            subtitle="AICTE / UGC DigiLocker"
            icon={ShieldCheck}
            color="sapphire"
          />
        </div>

        {/* Two-Column Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Department Placement Breakdown */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <School className="h-4 w-4 text-emerald-400" />
                <span>Department Placement Matrix</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="divide-y divide-slate-800 text-xs">
                {departmentStats.map((d) => (
                  <div key={d.dept} className="py-3 flex items-center justify-between">
                    <div>
                      <div className="font-bold text-white">{d.dept}</div>
                      <div className="text-slate-400">
                        {d.placed} of {d.total} students placed
                      </div>
                    </div>
                    <div className="text-right">
                      <span className="font-mono text-sm font-bold text-emerald-400">{d.rate}</span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Top Recruiters Hiring on Campus */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Award className="h-4 w-4 text-cyan-400" />
                <span>Active Corporate Recruiters</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-xs">
              <div className="p-3 rounded-lg border border-slate-800 bg-[#0B0F19] flex items-center justify-between">
                <div>
                  <div className="font-bold text-white">Google India</div>
                  <div className="text-slate-400">Software Engineering & AI Systems Internships</div>
                </div>
                <Badge variant="cyan">12 Offers</Badge>
              </div>

              <div className="p-3 rounded-lg border border-slate-800 bg-[#0B0F19] flex items-center justify-between">
                <div>
                  <div className="font-bold text-white">AI4Bharat (IIT Madras)</div>
                  <div className="text-slate-400">Indic Speech & NLP Research Fellowships</div>
                </div>
                <Badge variant="violet">8 Offers</Badge>
              </div>

              <div className="p-3 rounded-lg border border-slate-800 bg-[#0B0F19] flex items-center justify-between">
                <div>
                  <div className="font-bold text-white">Zerodha Tech</div>
                  <div className="text-slate-400">Full Stack & Go High-Performance Engineering</div>
                </div>
                <Badge variant="sapphire">15 Offers</Badge>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
}

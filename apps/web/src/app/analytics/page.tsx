'use client';

import React from 'react';
import { BarChart3, TrendingUp, MapPin, Sparkles, Building2, Award } from 'lucide-react';
import { DashboardLayout } from '../../components/dashboard/DashboardLayout';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { MetricCard } from '../../components/ui/MetricCard';

export default function AnalyticsPage() {
  const hubSalaries = [
    { city: 'Bangalore', role: 'AI / ML Engineer', stipend: '₹45,000 – ₹1,20,000', openRoles: '4,280' },
    { city: 'Hyderabad', role: 'Distributed Systems & Go', stipend: '₹35,000 – ₹90,000', openRoles: '2,940' },
    { city: 'Pune / Mumbai', role: 'Full Stack & Cloud', stipend: '₹30,000 – ₹75,000', openRoles: '2,110' },
    { city: 'Chennai', role: 'Computer Vision & Robotics', stipend: '₹35,000 – ₹85,000', openRoles: '1,840' },
    { city: 'Delhi NCR', role: 'NLP & Indic Language AI', stipend: '₹40,000 – ₹95,000', openRoles: '2,400' },
  ];

  const inDemandSkills = [
    { skill: 'PyTorch & Transformers', demand: '96%', growth: '+34%' },
    { skill: 'Next.js & React 19', demand: '92%', growth: '+28%' },
    { skill: 'Go & Distributed Systems', demand: '88%', growth: '+42%' },
    { skill: 'Docker & Kubernetes', demand: '85%', growth: '+19%' },
    { skill: 'Indic Speech & ASR', demand: '81%', growth: '+56%' },
  ];

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white">Market Intelligence & Analytics</h1>
              <Badge variant="cyan">Indian Tech Telemetry</Badge>
            </div>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Aggregated stipend benchmarks, hiring hub demand, and skill growth across 10,000+ collegiate postings.
            </p>
          </div>
        </div>

        {/* 3 Overview Metrics */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <MetricCard
            title="Avg AI Internship Stipend"
            value="₹52,000"
            subtitle="Bangalore tech hub benchmark"
            trend="+18% YoY"
            icon={TrendingUp}
            color="emerald"
          />
          <MetricCard
            title="Highest Growth Domain"
            value="Indic Speech"
            subtitle="+56% surge in regional AI hiring"
            trend="+56%"
            icon={Sparkles}
            color="violet"
          />
          <MetricCard
            title="Active Indian Tech Hubs"
            value="5 Metros"
            subtitle="Bangalore, Hyd, Pune, Chennai, Delhi"
            icon={MapPin}
            color="cyan"
          />
        </div>

        {/* Two-Column Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Tech Hub Stipend Table */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MapPin className="h-4 w-4 text-cyan-400" />
                <span>Regional Tech Hub Benchmarks</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="divide-y divide-slate-800 text-xs">
                {hubSalaries.map((hub) => (
                  <div key={hub.city} className="py-3 flex items-center justify-between">
                    <div>
                      <div className="font-bold text-white">{hub.city}</div>
                      <div className="text-slate-400">{hub.role}</div>
                    </div>
                    <div className="text-right">
                      <div className="font-bold text-emerald-400">{hub.stipend}</div>
                      <div className="text-slate-500">{hub.openRoles} active roles</div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* In-Demand Skills Tracker */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-emerald-400" />
                <span>Top In-Demand Technical Skills</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4 text-xs">
                {inDemandSkills.map((sk) => (
                  <div key={sk.skill} className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-white">{sk.skill}</span>
                      <span className="text-emerald-400 font-semibold">{sk.growth} growth</span>
                    </div>
                    <div className="h-2 w-full rounded-full bg-slate-800 overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-indigo-500 to-cyan-400 rounded-full"
                        style={{ width: sk.demand }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
}

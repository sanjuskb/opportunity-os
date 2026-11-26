'use client';

import React from 'react';
import { TrendingUp, MapPin, Sparkles, Briefcase } from 'lucide-react';
import { DashboardLayout } from '../../components/dashboard/DashboardLayout';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { MetricCard } from '../../components/ui/MetricCard';
import { useAnalyticsOverview } from '@/lib/queries/useOpportunityOs';

export default function AnalyticsPage() {
  const { data: overview, isLoading } = useAnalyticsOverview();

  const totalOpps = overview?.totalOpportunities ?? 0;
  const totalApps = overview?.totalApplications ?? 0;
  const topLocation = overview?.topLocations?.[0]?.location ?? '—';
  const topSkill = overview?.topSkills?.[0]?.skill ?? '—';

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white">Market Intelligence &amp; Analytics</h1>
              <Badge variant="cyan">Live PostgreSQL Telemetry</Badge>
            </div>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Real-time opportunity distribution, top requested skills, and your personal application funnel.
            </p>
          </div>
        </div>

        {isLoading ? (
          <div className="h-44 rounded-xl border border-slate-800 bg-[#0B0F19] animate-pulse" />
        ) : (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <MetricCard
                title="Indexed Active Opportunities"
                value={totalOpps}
                subtitle="Verified in PostgreSQL"
                icon={Briefcase}
                color="emerald"
              />
              <MetricCard
                title="Top Requested Skill"
                value={topSkill}
                subtitle="Across opportunity eligibility requirements"
                icon={Sparkles}
                color="violet"
              />
              <MetricCard
                title="Leading Tech Hub"
                value={topLocation}
                subtitle={`${totalApps} user application(s) tracked`}
                icon={MapPin}
                color="cyan"
              />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <MapPin className="h-4 w-4 text-cyan-400" />
                    <span>Opportunities by Location</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {(overview?.topLocations ?? []).length === 0 ? (
                    <p className="text-xs text-slate-400">No location metrics available yet.</p>
                  ) : (
                    <div className="divide-y divide-slate-800 text-xs">
                      {overview?.topLocations.map((hub) => (
                        <div key={hub.location} className="py-3 flex items-center justify-between">
                          <span className="font-bold text-white">{hub.location}</span>
                          <span className="text-emerald-400 font-mono font-bold">{hub.count} roles</span>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="h-4 w-4 text-emerald-400" />
                    <span>Top In-Demand Skills in Index</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {(overview?.topSkills ?? []).length === 0 ? (
                    <p className="text-xs text-slate-400">No skill metrics available yet.</p>
                  ) : (
                    <div className="space-y-4 text-xs">
                      {overview?.topSkills.map((sk) => {
                        const pct = Math.min(100, Math.round((sk.count / Math.max(1, totalOpps)) * 100));
                        return (
                          <div key={sk.skill} className="space-y-1.5">
                            <div className="flex items-center justify-between">
                              <span className="font-bold text-white">{sk.skill}</span>
                              <span className="text-emerald-400 font-semibold">{sk.count} postings</span>
                            </div>
                            <div className="h-2 w-full rounded-full bg-slate-800 overflow-hidden">
                              <div
                                className="h-full bg-gradient-to-r from-indigo-500 to-cyan-400 rounded-full"
                                style={{ width: `${pct}%` }}
                              />
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </>
        )}
      </div>
    </DashboardLayout>
  );
}

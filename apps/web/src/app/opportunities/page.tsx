'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Search, Filter, Bookmark, Sparkles, MapPin, Building2, Calendar, ArrowRight, CheckCircle2 } from 'lucide-react';
import { DashboardLayout } from '../../components/dashboard/DashboardLayout';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { useMockStore } from '../../lib/mock-data/mockStore';
import { MOCK_ELIGIBILITY_CACHE } from '../../lib/mock-data/opportunities';

export default function OpportunitiesPage() {
  const { opportunities, savedOpportunityIds, toggleSaveOpportunity, applyToOpportunity, applications } = useMockStore();

  const [searchQuery, setSearchQuery] = useState('');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [selectedLocation, setSelectedLocation] = useState<string>('all');

  const filteredOpportunities = opportunities.filter((opp) => {
    const matchesSearch =
      opp.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      opp.organization.toLowerCase().includes(searchQuery.toLowerCase()) ||
      opp.requiredSkills.some((sk) => sk.toLowerCase().includes(searchQuery.toLowerCase()));

    const matchesType = selectedType === 'all' || opp.type === selectedType;
    const matchesLocation =
      selectedLocation === 'all' ||
      opp.location.toLowerCase().includes(selectedLocation.toLowerCase());

    return matchesSearch && matchesType && matchesLocation;
  });

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Page Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white">Opportunity Discovery</h1>
              <Badge variant="cyan">Ingested Feeds</Badge>
            </div>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Live internships, fellowships, and scholarships crawled from Olostep, Crustdata, and direct company portals.
            </p>
          </div>

          <div className="text-xs text-slate-400 font-mono">
            Showing <span className="text-cyan-400 font-bold">{filteredOpportunities.length}</span> of {opportunities.length} opportunities
          </div>
        </div>

        {/* Search & Filter Toolbar */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3 p-4 rounded-xl border border-slate-800 bg-[#0B0F19]">
          <div className="md:col-span-2">
            <Input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by title, organization, or skill (e.g. PyTorch, React)..."
            />
          </div>

          <div>
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="flex h-10 w-full rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
            >
              <option value="all">All Types</option>
              <option value="internship">Internship</option>
              <option value="fellowship">Fellowship</option>
              <option value="government_scheme">Government Scheme</option>
              <option value="hackathon">Hackathon</option>
            </select>
          </div>

          <div>
            <select
              value={selectedLocation}
              onChange={(e) => setSelectedLocation(e.target.value)}
              className="flex h-10 w-full rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
            >
              <option value="all">All Locations</option>
              <option value="bangalore">Bangalore</option>
              <option value="chennai">Chennai</option>
              <option value="hyderabad">Hyderabad</option>
              <option value="remote">Remote / Hybrid</option>
            </select>
          </div>
        </div>

        {/* Opportunity Card List */}
        <div className="grid grid-cols-1 gap-4">
          {filteredOpportunities.map((opp) => {
            const isSaved = savedOpportunityIds.includes(opp.id);
            const isApplied = applications.some((a) => a.opportunityId === opp.id);
            const match = MOCK_ELIGIBILITY_CACHE[opp.id];

            return (
              <Card key={opp.id} className="hover:border-slate-700 transition">
                <CardContent className="p-5">
                  <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
                    {/* Left: Opportunity Overview */}
                    <div className="space-y-2 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <Link
                          href={`/opportunities/${opp.id}`}
                          className="text-base font-bold text-white hover:text-cyan-300 transition"
                        >
                          {opp.title}
                        </Link>
                        {match && (
                          <Badge variant={match.score >= 90 ? 'cyan' : 'emerald'}>
                            <Sparkles className="h-3 w-3 mr-1" />
                            {match.score}% Match
                          </Badge>
                        )}
                        <Badge variant="slate" size="sm">
                          {opp.type.replace(/_/g, ' ')}
                        </Badge>
                        <span className="text-[10px] font-mono text-slate-500 uppercase px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800">
                          {opp.sourceProvider}
                        </span>
                      </div>

                      <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400">
                        <span className="flex items-center gap-1 font-semibold text-slate-200">
                          <Building2 className="h-3.5 w-3.5 text-slate-400" />
                          {opp.organization}
                        </span>
                        <span className="flex items-center gap-1">
                          <MapPin className="h-3.5 w-3.5 text-slate-400" />
                          {opp.location}
                        </span>
                        <span className="flex items-center gap-1 text-emerald-400 font-semibold">
                          {opp.stipendOrSalary}
                        </span>
                        {opp.deadline && (
                          <span className="flex items-center gap-1 text-amber-400">
                            <Calendar className="h-3.5 w-3.5" />
                            Deadline: {opp.deadline}
                          </span>
                        )}
                      </div>

                      <p className="text-xs text-slate-300 line-clamp-2 max-w-3xl leading-relaxed">
                        {opp.description}
                      </p>

                      <div className="flex flex-wrap items-center gap-1.5 pt-1">
                        <span className="text-[11px] text-slate-400 mr-1">Required:</span>
                        {opp.requiredSkills.map((sk) => (
                          <span
                            key={sk}
                            className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-900 text-slate-300 border border-slate-800"
                          >
                            {sk}
                          </span>
                        ))}
                      </div>
                    </div>

                    {/* Right: Actions */}
                    <div className="flex items-center gap-2.5 w-full lg:w-auto justify-end border-t lg:border-t-0 pt-3 lg:pt-0 border-slate-800">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => toggleSaveOpportunity(opp.id)}
                        className={isSaved ? 'text-amber-400' : 'text-slate-400'}
                        aria-label="Bookmark Opportunity"
                      >
                        <Bookmark className={`h-4 w-4 ${isSaved ? 'fill-amber-400' : ''}`} />
                      </Button>

                      <Link href={`/opportunities/${opp.id}`}>
                        <Button variant="outline" size="sm">
                          Inspect
                        </Button>
                      </Link>

                      {isApplied ? (
                        <Button variant="secondary" size="sm" disabled>
                          <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 mr-1" />
                          Applied
                        </Button>
                      ) : (
                        <Button variant="primary" size="sm" onClick={() => applyToOpportunity(opp.id)}>
                          <span>Apply</span>
                          <ArrowRight className="h-3.5 w-3.5 ml-1" />
                        </Button>
                      )}
                    </div>
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

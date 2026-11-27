'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import {
  Search,
  Bookmark,
  Sparkles,
  MapPin,
  Building2,
  Calendar,
  ArrowRight,
  CheckCircle2,
  Globe,
} from 'lucide-react';
import { DashboardLayout } from '../../components/dashboard/DashboardLayout';
import { Card, CardContent } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { useAuth } from '@/components/auth/AuthProvider';
import {
  useApplications,
  useCreateApplication,
  useDiscoverOpportunities,
  useOpportunities,
  useSavedOpportunities,
  useToggleSaveOpportunity,
} from '@/lib/queries/useOpportunityOs';
import type { ApiOpportunity } from '@opportunity-os/shared-types';

export default function OpportunitiesPage() {
  const { user, apiClient } = useAuth();
  const { data: oppPage, isLoading, error } = useOpportunities({ limit: 50 });
  const { data: savedRows } = useSavedOpportunities();
  const { data: applications } = useApplications();
  const discoverMutation = useDiscoverOpportunities();
  const toggleSave = useToggleSaveOpportunity();
  const createApp = useCreateApplication();

  const [searchQuery, setSearchQuery] = useState('');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [selectedLocation, setSelectedLocation] = useState<string>('all');
  const [semanticHits, setSemanticHits] = useState<ApiOpportunity[] | null>(null);
  const [researchBusy, setResearchBusy] = useState(false);
  const [researchStatus, setResearchStatus] = useState<string | null>(null);

  const opportunities = semanticHits ?? oppPage?.items ?? [];
  const savedSet = new Set((savedRows ?? []).map((r) => r.id));
  const appliedSet = new Set((applications ?? []).map((a) => a.opportunityId));

  const filteredOpportunities = opportunities.filter((opp) => {
    const q = searchQuery.toLowerCase();
    const matchesSearch =
      !q ||
      opp.title.toLowerCase().includes(q) ||
      opp.organization.toLowerCase().includes(q) ||
      opp.requiredSkills.some((sk) => sk.toLowerCase().includes(q));
    const matchesType = selectedType === 'all' || opp.type === selectedType;
    const matchesLocation =
      selectedLocation === 'all' || opp.location.toLowerCase().includes(selectedLocation.toLowerCase());
    return matchesSearch && matchesType && matchesLocation;
  });

  const handleHybridSearch = async () => {
    const q = searchQuery.trim();
    if (q.length < 2) {
      setSemanticHits(null);
      return;
    }
    try {
      const res = await discoverMutation.mutateAsync({
        query: q,
        type: selectedType !== 'all' ? selectedType : undefined,
        limit: 20,
      });
      setSemanticHits(res.items);
    } catch {
      setSemanticHits(null);
    }
  };

  const handleLiveOlostepResearch = async () => {
    if (!user || !searchQuery.trim()) return;
    setResearchBusy(true);
    setResearchStatus(null);
    try {
      const res = await apiClient.researchOpportunities({
        query: searchQuery.trim(),
        limit: 8,
        enrichCompanies: true,
      });
      setSemanticHits(res.opportunities);
      setResearchStatus(
        `Olostep & Crustdata discovered ${res.discoveredCount} new (${res.deduplicatedCount} deduplicated) opportunities.`
      );
    } catch (err) {
      setResearchStatus(err instanceof Error ? err.message : 'External research unavailable.');
    } finally {
      setResearchBusy(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white">Opportunity Discovery</h1>
              <Badge variant="cyan">pgvector + Olostep</Badge>
            </div>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Hybrid semantic search, deterministic eligibility ranking, and live Olostep web discovery.
            </p>
          </div>

          <div className="text-xs text-slate-400 font-mono">
            Showing <span className="text-cyan-400 font-bold">{filteredOpportunities.length}</span> opportunities
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-6 gap-3 p-4 rounded-xl border border-slate-800 bg-[#0B0F19]">
          <div className="md:col-span-2">
            <Input
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                if (!e.target.value.trim()) setSemanticHits(null);
              }}
              placeholder="Search skills, orgs, or query (e.g. FastAPI, PyTorch)..."
            />
          </div>

          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="flex h-10 w-full rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-xs text-slate-200"
          >
            <option value="all">All Types</option>
            <option value="internship">Internship</option>
            <option value="full_time">Full Time</option>
            <option value="fellowship">Fellowship</option>
            <option value="government_scheme">Government Scheme</option>
            <option value="hackathon">Hackathon</option>
          </select>

          <select
            value={selectedLocation}
            onChange={(e) => setSelectedLocation(e.target.value)}
            className="flex h-10 w-full rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-xs text-slate-200"
          >
            <option value="all">All Locations</option>
            <option value="bangalore">Bangalore</option>
            <option value="chennai">Chennai</option>
            <option value="hyderabad">Hyderabad</option>
            <option value="remote">Remote / Hybrid</option>
          </select>

          <Button
            variant="primary"
            size="md"
            disabled={!user || searchQuery.trim().length < 2}
            isLoading={discoverMutation.isPending}
            onClick={() => void handleHybridSearch()}
          >
            <Search className="h-3.5 w-3.5 mr-1" />
            <span>Semantic Rank</span>
          </Button>

          <Button
            variant="outline"
            size="md"
            disabled={!user || searchQuery.trim().length < 2}
            isLoading={researchBusy}
            onClick={() => void handleLiveOlostepResearch()}
          >
            <Globe className="h-3.5 w-3.5 mr-1 text-cyan-400" />
            <span>Web Crawl</span>
          </Button>
        </div>

        {researchStatus && (
          <div className="p-3 rounded-xl border border-cyan-500/30 bg-cyan-950/20 text-xs text-cyan-200">
            {researchStatus}
          </div>
        )}

        {error && (
          <div className="p-4 rounded-xl border border-rose-500/40 bg-rose-950/30 text-xs text-rose-200">
            Could not load opportunities: {error instanceof Error ? error.message : 'Error'}
          </div>
        )}

        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((k) => (
              <div key={k} className="h-28 rounded-xl border border-slate-800 bg-[#0B0F19] animate-pulse" />
            ))}
          </div>
        ) : filteredOpportunities.length === 0 ? (
          <div className="p-8 rounded-xl border border-slate-800 bg-[#0B0F19] text-center text-xs text-slate-400">
            No matching opportunities found. Try clearing filters or running a Web Crawl above.
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {filteredOpportunities.map((opp) => {
              const isSaved = savedSet.has(opp.id);
              const isApplied = appliedSet.has(opp.id);
              return (
                <Card key={opp.id} className="hover:border-slate-700 transition">
                  <CardContent className="p-5">
                    <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
                      <div className="space-y-2 flex-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <Link href={`/opportunities/${opp.id}`} className="text-base font-bold text-white hover:text-cyan-300 transition">
                            {opp.title}
                          </Link>
                          {opp.matchScore != null && (
                            <Badge variant={opp.matchScore >= 85 ? 'cyan' : 'emerald'}>
                              <Sparkles className="h-3 w-3 mr-1" />
                              {Math.round(opp.matchScore)}% Match
                            </Badge>
                          )}
                          <Badge variant="slate" size="sm">
                            {opp.type.replace(/_/g, ' ')}
                          </Badge>
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
                          {opp.stipendOrSalary && (
                            <span className="text-emerald-400 font-semibold">{opp.stipendOrSalary}</span>
                          )}
                          {opp.deadline && (
                            <span className="flex items-center gap-1 text-amber-400">
                              <Calendar className="h-3.5 w-3.5" />
                              Deadline: {new Date(opp.deadline).toLocaleDateString()}
                            </span>
                          )}
                        </div>

                        <div className="flex flex-wrap items-center gap-1.5 pt-1">
                          {opp.requiredSkills.map((sk) => (
                            <span key={sk} className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-900 text-slate-300 border border-slate-800">
                              {sk}
                            </span>
                          ))}
                        </div>
                      </div>

                      <div className="flex items-center gap-2.5 w-full lg:w-auto justify-end border-t lg:border-t-0 pt-3 lg:pt-0 border-slate-800">
                        <Button
                          variant="ghost"
                          size="sm"
                          disabled={!user}
                          onClick={() => void toggleSave.mutate({ opportunityId: opp.id, saved: !isSaved })}
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
                          <Button
                            variant="primary"
                            size="sm"
                            disabled={!user}
                            onClick={() => void createApp.mutate(opp.id)}
                          >
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
        )}
      </div>
    </DashboardLayout>
  );
}

'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  Compass,
  FileText,
  Briefcase,
  Award,
  Video,
  BarChart3,
  Settings,
  Bell,
  Search,
  Globe,
  Mic,
  Menu,
  X,
  LogOut,
  Users,
  ShieldCheck,
  PlusCircle,
  ChevronRight,
  Network,
  Building2,
  School,
} from 'lucide-react';
import { APP_CONFIG } from '@opportunity-os/shared-config';
import { useMockStore, UserRole } from '../../lib/mock-data/mockStore';
import { VoiceDrawer } from './VoiceDrawer';
import { cn } from '../../lib/utils';
import { useAuth } from '@/components/auth/AuthProvider';
import {
  useMarkNotificationRead,
  useNotifications,
  useStudentProfile,
  useUpdateUserProfile,
  useUserProfile,
} from '@/lib/queries/useOpportunityOs';

interface DashboardLayoutProps {
  children: React.ReactNode;
}

export function DashboardLayout({ children }: DashboardLayoutProps) {
  const pathname = usePathname();
  const { user, signOut } = useAuth();
  const { userRole, setUserRole, setIsVoiceAssistantOpen, activeLanguage, setActiveLanguage } =
    useMockStore();
  const { data: userProfile } = useUserProfile();
  const { data: studentProfile } = useStudentProfile();
  const { data: liveNotifications } = useNotifications();
  const markRead = useMarkNotificationRead();
  const updateProfile = useUpdateUserProfile();

  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [langDropdownOpen, setLangDropdownOpen] = useState(false);

  useEffect(() => {
    if (userProfile?.userRole && ['student', 'company', 'university'].includes(userProfile.userRole)) {
      setUserRole(userProfile.userRole as UserRole);
    }
    if (userProfile?.preferredLanguage) {
      setActiveLanguage(userProfile.preferredLanguage as typeof activeLanguage);
    }
  }, [userProfile, setUserRole, setActiveLanguage]);

  const notifications = liveNotifications ?? [];
  const unreadNotifications = notifications.filter((n) => !n.isRead).length;
  const displayName = userProfile?.fullName || user?.email?.split('@')[0] || 'Student';
  const displayCollege = studentProfile?.collegeName || user?.email || 'NexteRaS Workspace';

  const handleRoleChange = (role: UserRole) => {
    setUserRole(role);
    if (user) {
      void updateProfile.mutateAsync({ userRole: role }).catch(() => undefined);
    }
  };

  const handleLangChange = (code: string) => {
    setActiveLanguage(code as typeof activeLanguage);
    setLangDropdownOpen(false);
    if (user) {
      void updateProfile.mutateAsync({ preferredLanguage: code }).catch(() => undefined);
    }
  };

  const handleMarkAllRead = async () => {
    for (const n of notifications) {
      if (!n.isRead) {
        await markRead.mutateAsync(n.id).catch(() => undefined);
      }
    }
  };

  const studentNavItems = [
    { label: 'Overview', href: '/overview', icon: Compass },
    { label: 'Opportunities', href: '/opportunities', icon: Search, badge: 'Live' },
    { label: 'Career Passport', href: '/career-passport', icon: Award, badge: 'Verified' },
    { label: 'ATS Resume Studio', href: '/resume', icon: FileText },
    { label: 'Applications', href: '/applications', icon: Briefcase },
    { label: 'Mock Interview AI', href: '/interview', icon: Video },
    { label: 'Market Analytics', href: '/analytics', icon: BarChart3 },
    { label: 'Agent Control Center', href: '/agent-control-center', icon: Network, badge: 'Telemetry' },
    { label: 'Settings', href: '/settings', icon: Settings },
  ];

  const companyNavItems = [
    { label: 'Recruiter Dashboard', href: '/company/dashboard', icon: Building2 },
    { label: 'Post Opportunity', href: '/company/create', icon: PlusCircle, badge: 'New' },
    { label: 'Candidate Discovery', href: '/company/candidates', icon: Users },
    { label: 'Applicant Pipeline', href: '/company/applicants', icon: Briefcase },
    { label: 'Agent Control Center', href: '/agent-control-center', icon: Network },
    { label: 'Settings', href: '/settings', icon: Settings },
  ];

  const universityNavItems = [
    { label: 'Placement Dashboard', href: '/university/dashboard', icon: School },
    { label: 'Student Directory', href: '/university/students', icon: Users },
    { label: 'Institutional Verification', href: '/university/verification', icon: ShieldCheck },
    { label: 'Agent Control Center', href: '/agent-control-center', icon: Network },
    { label: 'Settings', href: '/settings', icon: Settings },
  ];

  let currentNavItems = studentNavItems;
  if (userRole === 'company') currentNavItems = companyNavItems;
  if (userRole === 'university') currentNavItems = universityNavItems;

  const activeLangObj = APP_CONFIG.SUPPORTED_LANGUAGES.find((l) => l.code === activeLanguage);

  return (
    <div className="min-h-screen bg-[#080B10] text-slate-100 flex">
      <aside className="hidden lg:flex flex-col w-64 border-r border-white/[0.06] bg-[#05070A] fixed inset-y-0 left-0 z-30">
        <div className="h-16 flex items-center px-6 border-b border-white/[0.06] justify-between">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-600/20 border border-indigo-500/40">
              <span className="h-2 w-2 rounded-full bg-cyan-400 animate-pulse" />
            </div>
            <span className="font-bold text-base tracking-tight text-white">
              Nexte<span className="text-cyan-400">RaS</span>
            </span>
          </Link>
          <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-indigo-950 text-indigo-300 border border-indigo-800">
            v0.1
          </span>
        </div>

        <div className="px-4 pt-4 pb-2">
          <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 mb-2">
            Active Workspace Role:
          </div>
          <div className="grid grid-cols-3 gap-1 p-1 rounded-lg border border-slate-800 bg-slate-900/80 text-xs">
            <button
              type="button"
              onClick={() => handleRoleChange('student')}
              className={cn(
                'py-1 rounded text-center font-medium transition',
                userRole === 'student'
                  ? 'bg-cyan-950 text-cyan-300 border border-cyan-800/80'
                  : 'text-slate-400 hover:text-white'
              )}
            >
              Student
            </button>
            <button
              type="button"
              onClick={() => handleRoleChange('company')}
              className={cn(
                'py-1 rounded text-center font-medium transition',
                userRole === 'company'
                  ? 'bg-blue-950 text-blue-300 border border-blue-800/80'
                  : 'text-slate-400 hover:text-white'
              )}
            >
              Company
            </button>
            <button
              type="button"
              onClick={() => handleRoleChange('university')}
              className={cn(
                'py-1 rounded text-center font-medium transition',
                userRole === 'university'
                  ? 'bg-emerald-950 text-emerald-300 border border-emerald-800/80'
                  : 'text-slate-400 hover:text-white'
              )}
            >
              Univ
            </button>
          </div>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {currentNavItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;

            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-medium transition select-none',
                  isActive
                    ? 'bg-indigo-600/15 text-white border-l-2 border-indigo-500 font-semibold'
                    : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
                )}
              >
                <div className="flex items-center gap-2.5 truncate">
                  <Icon className={cn('h-4 w-4 shrink-0', isActive ? 'text-cyan-400' : 'text-slate-400')} />
                  <span className="truncate">{item.label}</span>
                </div>
                {item.badge && (
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-300 border border-slate-700">
                    {item.badge}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>

        <div className="p-3 border-t border-white/[0.06] bg-[#05070A]">
          <div className="flex items-center gap-3 p-2 rounded-lg bg-white/[0.02] border border-white/[0.06]">
            <div className="h-8 w-8 rounded-full bg-cyan-600/20 border border-cyan-500/40 flex items-center justify-center text-cyan-300 font-bold text-xs">
              {displayName.charAt(0).toUpperCase()}
            </div>
            <div className="truncate flex-1">
              <div className="text-xs font-semibold text-white truncate">{displayName}</div>
              <div className="text-[10px] text-slate-400 truncate">{displayCollege}</div>
            </div>
            <button
              type="button"
              onClick={() => void signOut()}
              className="text-slate-500 hover:text-rose-300 transition"
              title="Sign Out"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </aside>

      <div className="flex-1 lg:pl-64 flex flex-col min-h-screen bg-[#080B10]">
        <header className="sticky top-0 z-20 h-16 w-full border-b border-white/[0.06] bg-[#080B10]/85 backdrop-blur-xl flex items-center justify-between px-4 sm:px-6">
          <div className="flex items-center gap-3 lg:hidden">
            <button
              type="button"
              onClick={() => setMobileSidebarOpen(true)}
              className="p-1.5 rounded-lg text-slate-400 hover:bg-slate-800 hover:text-white"
              aria-label="Open sidebar"
            >
              <Menu className="h-5 w-5" />
            </button>
            <Link href="/" className="font-bold text-sm tracking-tight text-white">
              Nexte<span className="text-cyan-400">RaS</span>
            </Link>
          </div>

          <div className="hidden sm:flex items-center gap-2 text-xs text-slate-400">
            <span className="text-slate-400">Workspace</span>
            <ChevronRight className="h-3 w-3 text-slate-600" />
            <span className="capitalize font-semibold text-white">
              {pathname.replace('/', '').replace(/-/g, ' ') || 'Overview'}
            </span>
          </div>

          <div className="flex items-center gap-3">
            <div className="relative">
              <button
                type="button"
                onClick={() => setLangDropdownOpen(!langDropdownOpen)}
                className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-slate-800 bg-slate-900/80 text-xs font-medium text-slate-300 hover:text-white hover:border-slate-700 transition"
                aria-label="Select Spoken Language"
              >
                <Globe className="h-3.5 w-3.5 text-cyan-400" />
                <span className="hidden sm:inline">{activeLangObj?.name}</span>
                <span className="sm:hidden">{activeLangObj?.code.toUpperCase()}</span>
              </button>

              {langDropdownOpen && (
                <div className="absolute right-0 mt-2 w-48 rounded-lg border border-slate-800 bg-[#0F172A] p-1.5 shadow-xl ring-1 ring-black/40 z-50">
                  <div className="px-2 py-1 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                    9 Regional Languages
                  </div>
                  {APP_CONFIG.SUPPORTED_LANGUAGES.map((lang) => (
                    <button
                      key={lang.code}
                      onClick={() => handleLangChange(lang.code)}
                      className={`flex w-full items-center justify-between rounded-md px-2.5 py-1.5 text-left text-xs transition ${
                        activeLanguage === lang.code
                          ? 'bg-indigo-600/20 text-cyan-300 font-semibold'
                          : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                      }`}
                    >
                      <span>{lang.name}</span>
                      <span className="text-[11px] text-slate-400">{lang.native}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div className="relative">
              <button
                type="button"
                onClick={() => setNotificationsOpen(!notificationsOpen)}
                className="relative p-2 rounded-lg border border-slate-800 bg-slate-900/80 text-slate-300 hover:text-white hover:border-slate-700 transition"
                aria-label="Notifications"
              >
                <Bell className="h-4 w-4" />
                {unreadNotifications > 0 && (
                  <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-cyan-500 text-[10px] font-bold text-black ring-2 ring-[#090D16]">
                    {unreadNotifications}
                  </span>
                )}
              </button>

              {notificationsOpen && (
                <div className="absolute right-0 mt-2 w-80 sm:w-96 rounded-xl border border-slate-800 bg-[#0F172A] p-3 shadow-2xl z-50">
                  <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                    <Link href="/notifications" className="text-xs font-bold text-white uppercase tracking-wider hover:text-cyan-300">
                      Notifications
                    </Link>
                    {unreadNotifications > 0 && (
                      <button
                        type="button"
                        onClick={() => void handleMarkAllRead()}
                        className="text-[11px] text-cyan-400 hover:underline"
                      >
                        Mark all as read
                      </button>
                    )}
                  </div>

                  <div className="max-h-72 overflow-y-auto space-y-2 py-2">
                    {notifications.length === 0 ? (
                      <p className="text-xs text-slate-400 py-4 text-center">No notifications yet.</p>
                    ) : (
                      notifications.map((notif) => (
                        <div
                          key={notif.id}
                          onClick={() => {
                            if (!notif.isRead) void markRead.mutate(notif.id);
                          }}
                          className={cn(
                            'p-2.5 rounded-lg border text-xs cursor-pointer transition',
                            notif.isRead
                              ? 'border-slate-800/60 bg-slate-900/40 text-slate-400'
                              : 'border-cyan-500/30 bg-cyan-950/20 text-slate-200'
                          )}
                        >
                          <div className="font-semibold text-white flex items-center justify-between">
                            <span>{notif.title}</span>
                            <span className="text-[10px] text-slate-400">
                              {notif.createdAt ? new Date(notif.createdAt).toLocaleDateString() : ''}
                            </span>
                          </div>
                          <p className="mt-1 text-slate-300 leading-relaxed text-[11px]">{notif.message}</p>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>

            <Link
              href="/"
              className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-900/80 text-xs font-medium text-slate-300 hover:text-white"
            >
              <span>Public Landing</span>
            </Link>
          </div>
        </header>

        <main className="flex-1 pb-24 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto">{children}</main>

        <div className="fixed bottom-6 right-6 z-40">
          <button
            type="button"
            onClick={() => setIsVoiceAssistantOpen(true)}
            className="group relative flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-r from-indigo-600 via-indigo-500 to-cyan-500 text-white shadow-xl shadow-cyan-500/25 ring-4 ring-[#090D16] hover:scale-105 active:scale-95 transition"
            aria-label="Open Voice AI Copilot"
          >
            <span className="absolute -inset-1 rounded-full bg-cyan-400/20 blur-sm group-hover:bg-cyan-400/40 animate-pulse" />
            <Mic className="relative h-6 w-6 text-white" />
          </button>
        </div>

        <VoiceDrawer />
      </div>

      {mobileSidebarOpen && (
        <div className="fixed inset-0 z-50 lg:hidden flex">
          <div className="fixed inset-0 bg-black/75 backdrop-blur-sm" onClick={() => setMobileSidebarOpen(false)} />
          <div className="relative w-72 bg-[#070B14] border-r border-slate-800 p-4 flex flex-col justify-between z-10">
            <div>
              <div className="flex items-center justify-between pb-4 border-b border-slate-800">
                <span className="font-bold text-sm text-white">
                  Nexte<span className="text-cyan-400">RaS</span>
                </span>
                <button type="button" onClick={() => setMobileSidebarOpen(false)} className="p-1 rounded text-slate-400 hover:text-white">
                  <X className="h-5 w-5" />
                </button>
              </div>

              <div className="pt-3 pb-2">
                <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 mb-1.5">Workspace Role:</div>
                <div className="grid grid-cols-3 gap-1 p-1 rounded-lg border border-slate-800 bg-slate-900 text-xs">
                  {(['student', 'company', 'university'] as const).map((r) => (
                    <button
                      key={r}
                      type="button"
                      onClick={() => handleRoleChange(r)}
                      className={cn(
                        'py-1 rounded text-center capitalize',
                        userRole === r ? 'bg-cyan-950 text-cyan-300' : 'text-slate-400'
                      )}
                    >
                      {r === 'university' ? 'Univ' : r}
                    </button>
                  ))}
                </div>
              </div>

              <nav className="space-y-1 pt-2">
                {currentNavItems.map((item) => {
                  const Icon = item.icon;
                  const isActive = pathname === item.href;
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      onClick={() => setMobileSidebarOpen(false)}
                      className={cn(
                        'flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-medium',
                        isActive ? 'bg-indigo-600/20 text-white font-semibold' : 'text-slate-400 hover:bg-slate-800 hover:text-white'
                      )}
                    >
                      <div className="flex items-center gap-2.5">
                        <Icon className="h-4 w-4" />
                        <span>{item.label}</span>
                      </div>
                      {item.badge && (
                        <span className="px-1.5 py-0.5 rounded text-[10px] bg-slate-800 text-slate-400">{item.badge}</span>
                      )}
                    </Link>
                  );
                })}
              </nav>
            </div>

            <div className="pt-4 border-t border-slate-800">
              <button
                type="button"
                onClick={() => {
                  setMobileSidebarOpen(false);
                  void signOut();
                }}
                className="flex items-center gap-2 text-xs text-slate-400 hover:text-white"
              >
                <LogOut className="h-4 w-4" />
                <span>Sign Out</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

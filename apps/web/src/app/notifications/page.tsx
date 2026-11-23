'use client';

import React from 'react';
import { Bell, Sparkles, CheckCircle2, ShieldCheck, Clock } from 'lucide-react';
import { DashboardLayout } from '../../components/dashboard/DashboardLayout';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { useMockStore } from '../../lib/mock-data/mockStore';

export default function NotificationsPage() {
  const { notifications, markNotificationRead, clearAllNotifications } = useMockStore();

  return (
    <DashboardLayout>
      <div className="space-y-6 max-w-4xl">
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white">Notifications Tray</h1>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Autonomous agent activity, application updates, and matching alerts.
            </p>
          </div>

          <Button variant="outline" size="sm" onClick={clearAllNotifications}>
            <span>Mark All as Read</span>
          </Button>
        </div>

        <div className="space-y-3">
          {notifications.map((notif) => (
            <div
              key={notif.id}
              onClick={() => markNotificationRead(notif.id)}
              className={`p-4 rounded-xl border text-xs cursor-pointer transition flex items-start gap-3.5 ${
                notif.read ? 'border-slate-800 bg-[#0B0F19] text-slate-400' : 'border-cyan-500/40 bg-cyan-950/20 text-slate-200'
              }`}
            >
              <div className="p-2 rounded-lg bg-slate-800 text-cyan-400 shrink-0 mt-0.5">
                <Bell className="h-4 w-4" />
              </div>
              <div className="flex-1 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-white text-sm">{notif.title}</span>
                  <span className="text-[11px] text-slate-400">{notif.timestamp}</span>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">{notif.message}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </DashboardLayout>
  );
}

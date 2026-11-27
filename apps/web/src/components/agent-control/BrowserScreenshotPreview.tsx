'use client';

import React, { useEffect, useState } from 'react';
import { ImageIcon } from 'lucide-react';
import { useAuth } from '@/components/auth/AuthProvider';

export function BrowserScreenshotPreview({
  logId,
  label = 'Playwright Pre-Submit Screenshot',
}: {
  logId: string;
  label?: string;
}) {
  const { apiClient, user } = useAuth();
  const [imgUrl, setImgUrl] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (!user || !logId) return;
    let active = true;
    let objectUrl: string | null = null;

    void apiClient
      .fetchBrowserLogScreenshot(logId)
      .then((blob) => {
        if (!active) return;
        objectUrl = URL.createObjectURL(blob);
        setImgUrl(objectUrl);
      })
      .catch((e) => {
        if (!active) return;
        setErr(e instanceof Error ? e.message : 'Preview unavailable');
      });

    return () => {
      active = false;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [apiClient, user, logId]);

  if (err) {
    return (
      <div className="p-2 rounded-lg border border-white/[0.08] bg-[#070A12] text-[10px] text-slate-500">
        {label}: {err}
      </div>
    );
  }

  if (!imgUrl) {
    return (
      <div className="p-2 rounded-lg border border-white/[0.08] bg-[#070A12] text-[10px] text-slate-400 flex items-center gap-1.5">
        <ImageIcon className="h-3.5 w-3.5 text-cyan-400 animate-pulse" />
        <span>Loading {label}...</span>
      </div>
    );
  }

  return (
    <div className="space-y-1">
      <div className="text-[10px] font-mono text-slate-400">{label}</div>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={imgUrl}
        alt={label}
        className="w-full max-h-56 object-contain rounded-lg border border-white/[0.1] bg-black"
      />
    </div>
  );
}

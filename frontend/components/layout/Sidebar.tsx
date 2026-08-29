'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  Home, Download, History, Layers, Settings, Info, Sparkles, Menu, X,
  Image, FileText, ScanLine, FolderOpen,
} from 'lucide-react';
import { useState } from 'react';
import { cn } from '@/lib/utils';
import { ThemeToggle } from '@/components/ThemeToggle';

const nav = [
  { href: '/', label: 'Home', icon: Home },
  { href: '/downloads', label: 'Downloads', icon: Download },
  { href: '/files', label: 'Files', icon: FolderOpen },
  { href: '/history', label: 'History', icon: History },
  { href: '/batch', label: 'Batch', icon: Layers },
  { href: '/images', label: 'Images', icon: Image },
  { href: '/pdf', label: 'PDF Tools', icon: FileText },
  { href: '/scanner', label: 'Scanner', icon: ScanLine },
  { href: '/settings', label: 'Settings', icon: Settings },
  { href: '/about', label: 'About', icon: Info },
];

export function Sidebar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 rounded-lg bg-[hsl(var(--card))] border border-[hsl(var(--border))] shadow"
      >
        <Menu className="h-5 w-5" />
      </button>

      {open && (
        <div className="lg:hidden fixed inset-0 z-40 bg-black/60 backdrop-blur-sm" onClick={() => setOpen(false)} />
      )}

      <aside
        className={cn(
          'fixed top-0 left-0 z-50 h-full w-64 glass-panel flex flex-col transition-transform lg:translate-x-0',
          open ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex items-center justify-between p-4 border-b border-[hsl(var(--border))]">
          <div className="flex items-center gap-2.5">
            <div className="h-9 w-9 rounded-xl bg-gradient-to-br from-brand-400 to-brand-700 flex items-center justify-center logo-3d">
              <Sparkles className="h-5 w-5 text-white" />
            </div>
            <div>
              <div className="font-bold leading-none tracking-tight">AreebFetch</div>
              <div className="text-[10px] text-[hsl(var(--muted-foreground))]">All-in-One Studio</div>
            </div>
          </div>
          <button className="lg:hidden p-1" onClick={() => setOpen(false)}>
            <X className="h-5 w-5" />
          </button>
        </div>

        <nav className="flex-1 p-3 space-y-0.5 overflow-y-auto">
          {nav.map(({ href, label, icon: Icon }) => {
            const active = pathname === href;
            return (
              <Link
                key={href}
                href={href}
                onClick={() => setOpen(false)}
                className={cn(
                  'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all',
                  active
                    ? 'bg-brand-600 text-white shadow-lg shadow-brand-600/25'
                    : 'text-[hsl(var(--muted-foreground))] hover:bg-[hsl(var(--muted))] hover:text-[hsl(var(--foreground))]'
                )}
              >
                <Icon className="h-4 w-4 shrink-0" />
                {label}
              </Link>
            );
          })}
        </nav>

        <div className="p-4 border-t border-[hsl(var(--border))]">
          <ThemeToggle />
        </div>
      </aside>
    </>
  );
}

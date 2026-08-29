import type { Metadata } from 'next';
import './globals.css';
import { Sidebar } from '@/components/layout/Sidebar';

export const metadata: Metadata = {
  title: 'AreebFetch – Universal Video & Audio Downloader',
  description: 'Download videos and audio from thousands of websites. Fast, modern, private.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen antialiased">
        <Sidebar />
        <main className="lg:pl-64 min-h-screen">
          {children}
        </main>
      </body>
    </html>
  );
}
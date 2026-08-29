import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { JobInfo, MediaInfo } from './api';

interface HistoryItem {
  id: string;
  title: string;
  url: string;
  thumbnail?: string;
  filename?: string;
  status: string;
  created_at: string;
}

interface AppState {
  theme: 'light' | 'dark' | 'system';
  setTheme: (t: 'light' | 'dark' | 'system') => void;

  history: HistoryItem[];
  addToHistory: (item: HistoryItem) => void;
  clearHistory: () => void;
  removeFromHistory: (id: string) => void;

  currentMedia: MediaInfo | null;
  setCurrentMedia: (m: MediaInfo | null) => void;

  activeJob: JobInfo | null;
  setActiveJob: (j: JobInfo | null) => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      theme: 'dark',
      setTheme: (theme) => set({ theme }),

      history: [],
      addToHistory: (item) =>
        set((s) => ({
          history: [item, ...s.history.filter((h) => h.id !== item.id)].slice(0, 50),
        })),
      clearHistory: () => set({ history: [] }),
      removeFromHistory: (id) =>
        set((s) => ({ history: s.history.filter((h) => h.id !== id) })),

      currentMedia: null,
      setCurrentMedia: (currentMedia) => set({ currentMedia }),

      activeJob: null,
      setActiveJob: (activeJob) => set({ activeJob }),
    }),
    {
      name: 'areebfetch-storage',
      partialize: (s) => ({ theme: s.theme, history: s.history }),
    }
  )
);
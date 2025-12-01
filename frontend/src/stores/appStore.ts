import { create } from 'zustand';

interface AppState {
  selectedSiteId: string | null;
  sidebarOpen: boolean;
  setSelectedSiteId: (id: string | null) => void;
  toggleSidebar: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  selectedSiteId: null,
  sidebarOpen: true,
  setSelectedSiteId: (id) => set({ selectedSiteId: id }),
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
}));

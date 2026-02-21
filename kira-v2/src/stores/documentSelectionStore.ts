import { create } from "zustand";

type DocumentSelectionState = {
  selectedIds: Record<string, boolean>;
  setSelected: (id: string, value: boolean) => void;
  setManySelected: (ids: string[], value: boolean) => void;
  clearSelected: () => void;
};

export const useDocumentSelectionStore = create<DocumentSelectionState>((set) => ({
  selectedIds: {},
  setSelected: (id, value) =>
    set((state) => ({
      selectedIds: {
        ...state.selectedIds,
        [id]: value,
      },
    })),
  setManySelected: (ids, value) =>
    set((state) => {
      const next = { ...state.selectedIds };
      ids.forEach((id) => {
        next[id] = value;
      });
      return { selectedIds: next };
    }),
  clearSelected: () => set({ selectedIds: {} }),
}));

import { create } from "zustand";
import { persist } from "zustand/middleware";
import { api } from "@/services/api";

const DEMO_EMAIL = "admin@arrematex.com.br";
const DEMO_PASSWORD = "Admin12345";

interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  mfa_enabled: boolean;
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  setTokens: (access: string, refresh: string) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,

      login: async (email, password) => {
        if (email.trim().toLowerCase() === DEMO_EMAIL && password === DEMO_PASSWORD) {
          set({
            accessToken: "demo-access-token",
            refreshToken: "demo-refresh-token",
            user: {
              id: "demo-admin",
              email: DEMO_EMAIL,
              full_name: "Administrador Demo",
              role: "admin",
              mfa_enabled: false,
            },
            isAuthenticated: true,
          });
          return;
        }

        const { data } = await api.post("/auth/login/", { email, password });
        set({
          accessToken: data.access,
          refreshToken: data.refresh,
          user: data.user,
          isAuthenticated: true,
        });
      },

      logout: () => {
        set({ user: null, accessToken: null, refreshToken: null, isAuthenticated: false });
        // Blacklist do token no backend (best-effort)
        const refresh = useAuthStore.getState().refreshToken;
        if (refresh) api.post("/auth/logout/", { refresh }).catch(() => null);
      },

      setTokens: (access, refresh) =>
        set({ accessToken: access, refreshToken: refresh }),
    }),
    {
      name: "arrematex-auth",
      partialize: (s) => ({
        accessToken: s.accessToken,
        refreshToken: s.refreshToken,
        user: s.user,
        isAuthenticated: s.isAuthenticated,
      }),
    }
  )
);

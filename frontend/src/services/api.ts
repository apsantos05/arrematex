import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";
import { useAuthStore } from "@/store/auth";
import toast from "react-hot-toast";

const BASE_URL = import.meta.env.VITE_API_URL || "/api/v1";

export const api = axios.create({ baseURL: BASE_URL });

// ── Request interceptor: injeta Bearer token ─────────────────────────────────
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = useAuthStore.getState().accessToken;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// ── Response interceptor: refresh automático ─────────────────────────────────
let refreshing = false;
let queue: Array<(token: string) => void> = [];

api.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    const original = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;

      if (refreshing) {
        return new Promise((resolve) => {
          queue.push((token) => {
            original.headers.Authorization = `Bearer ${token}`;
            resolve(api(original));
          });
        });
      }

      refreshing = true;
      try {
        const refresh = useAuthStore.getState().refreshToken;
        if (!refresh) throw new Error("No refresh token");

        const { data } = await axios.post(`${BASE_URL}/auth/refresh/`, { refresh });
        const newAccess: string = data.access;
        useAuthStore.getState().setTokens(newAccess, refresh);
        queue.forEach((cb) => cb(newAccess));
        queue = [];
        original.headers.Authorization = `Bearer ${newAccess}`;
        return api(original);
      } catch {
        useAuthStore.getState().logout();
        toast.error("Sessão expirada. Faça login novamente.");
        return Promise.reject(error);
      } finally {
        refreshing = false;
      }
    }

    // Mensagens de erro amigáveis
    const msg =
      (error.response?.data as any)?.detail ||
      (error.response?.data as any)?.message ||
      "Erro inesperado. Tente novamente.";

    if (error.response?.status !== 401) toast.error(msg);

    return Promise.reject(error);
  }
);

// ── Helpers offline ───────────────────────────────────────────────────────────
export function isOffline(): boolean {
  return !navigator.onLine;
}

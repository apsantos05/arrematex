import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { useAuthStore } from "@/store/auth";
import LoginPage from "@/pages/LoginPage";
import DashboardLayout from "@/layouts/DashboardLayout";
import EventosPage from "@/pages/EventosPage";
import LotesPage from "@/pages/LotesPage";
import PainelLeiloeiro from "@/pages/PainelLeiloeiro";
import FinanceiroPage from "@/pages/FinanceiroPage";
import RelatoriosPage from "@/pages/RelatoriosPage";
import FiscalPage from "@/pages/FiscalPage";
import TelaoPage from "@/pages/TelaoPage";
import UsuariosPage from "@/pages/UsuariosPage";

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        {/* Telão — sem layout, tela cheia */}
        <Route path="/telao/:eventoId" element={<TelaoPage />} />
        <Route
          path="/"
          element={
            <PrivateRoute>
              <DashboardLayout />
            </PrivateRoute>
          }
        >
          <Route index element={<Navigate to="/eventos" replace />} />
          <Route path="eventos" element={<EventosPage />} />
          <Route path="eventos/:eventoId/lotes" element={<LotesPage />} />
          <Route path="eventos/:eventoId/leilao" element={<PainelLeiloeiro />} />
          <Route path="financeiro" element={<FinanceiroPage />} />
          <Route path="relatorios" element={<RelatoriosPage />} />
          <Route path="fiscal" element={<FiscalPage />} />
          <Route path="usuarios" element={<UsuariosPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

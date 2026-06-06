import { Outlet, NavLink, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { useAuthStore } from "@/store/auth";
import { useEffect, useState } from "react";

const NAV = [
  { to: "/eventos",    label: "Eventos",   icon: "📅", roles: ["super_admin","admin","leiloeiro","operador","caixa","fiscal","comprador"] },
  { to: "/financeiro", label: "Financeiro",icon: "💰", roles: ["super_admin","admin","caixa","fiscal"] },
  { to: "/fiscal",     label: "Fiscal",    icon: "🧾", roles: ["super_admin","admin","fiscal"] },
  { to: "/relatorios", label: "Relatórios",icon: "📊", roles: ["super_admin","admin","caixa","fiscal","leiloeiro"] },
  { to: "/usuarios",   label: "Usuários",  icon: "👥", roles: ["super_admin","admin"] },
];

export default function DashboardLayout() {
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const navigate = useNavigate();
  const [offline, setOffline] = useState(!navigator.onLine);

  useEffect(() => {
    const on = () => setOffline(false);
    const off = () => setOffline(true);
    window.addEventListener("online", on);
    window.addEventListener("offline", off);
    return () => { window.removeEventListener("online", on); window.removeEventListener("offline", off); };
  }, []);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const allowed = NAV.filter((n) => user && n.roles.includes(user.role));

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      {/* Topbar */}
      <header style={{
        background: "#16213e", borderBottom: "2px solid #f5a623",
        padding: "0 24px", height: 52,
        display: "flex", alignItems: "center", gap: 0,
        position: "sticky", top: 0, zIndex: 100,
      }}>
        <div style={{ fontSize: 18, fontWeight: 900, color: "#f5a623", letterSpacing: 2, marginRight: 32 }}>
          🐄 ARREMATEX
        </div>
        {allowed.map((n) => (
          <NavLink
            key={n.to}
            to={n.to}
            style={({ isActive }) => ({
              display: "flex", alignItems: "center", gap: 6,
              color: isActive ? "#f5a623" : "#888",
              fontWeight: 700, fontSize: 12, textTransform: "uppercase", letterSpacing: 1,
              textDecoration: "none", padding: "0 16px", height: 52,
              borderBottom: isActive ? "3px solid #f5a623" : "3px solid transparent",
              transition: "all .2s",
            })}
          >
            <span>{n.icon}</span> {n.label}
          </NavLink>
        ))}

        {/* Spacer */}
        <div style={{ flex: 1 }} />

        {/* Usuário + logout */}
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{ fontSize: 12, color: "#888" }}>{user?.full_name}</div>
          <motion.button
            onClick={handleLogout}
            className="btn btn-ghost btn-sm"
            whileTap={{ scale: .96 }}
          >
            Sair
          </motion.button>
        </div>
      </header>

      {/* Conteúdo */}
      <main style={{ flex: 1 }}>
        <Outlet />
      </main>

      {/* Banner offline */}
      {offline && (
        <div className="offline-banner">
          ⚠️ Você está offline — operações serão sincronizadas ao reconectar
        </div>
      )}
    </div>
  );
}

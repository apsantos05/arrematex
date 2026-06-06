/**
 * Relatórios — dashboard com métricas e gráficos.
 */
import { useQuery } from "@tanstack/react-query";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import { api } from "@/services/api";

export default function RelatoriosPage() {
  const { data: summary } = useQuery({
    queryKey: ["relatorios-summary"],
    queryFn: () => api.get("/relatorios/resumo/").then((r) => r.data),
  });

  const fmtBRL = (v: number) =>
    new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(v);

  const cards = [
    { label: "Eventos Realizados", value: summary?.total_eventos ?? "—" },
    { label: "Lotes Vendidos",     value: summary?.lotes_vendidos ?? "—" },
    { label: "Faturamento Total",  value: summary?.faturamento ? fmtBRL(summary.faturamento) : "—" },
    { label: "Ticket Médio",       value: summary?.ticket_medio ? fmtBRL(summary.ticket_medio) : "—" },
  ];

  return (
    <div style={{ padding: 24 }}>
      <h1 style={{ fontSize: 22, fontWeight: 900, color: "#f5a623", marginBottom: 24 }}>Relatórios</h1>

      {/* KPI Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16, marginBottom: 24 }}>
        {cards.map((c) => (
          <div key={c.label} className="card" style={{ textAlign: "center" }}>
            <div style={{ fontSize: 11, color: "#888", textTransform: "uppercase", letterSpacing: 1, marginBottom: 8 }}>
              {c.label}
            </div>
            <div style={{ fontSize: 28, fontWeight: 900, color: "#f5a623" }}>{c.value}</div>
          </div>
        ))}
      </div>

      {/* Faturamento por mês */}
      {summary?.faturamento_mensal && (
        <div className="card">
          <div style={{ fontSize: 13, fontWeight: 700, color: "#f5a623", marginBottom: 16 }}>
            Faturamento Mensal (R$)
          </div>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={summary.faturamento_mensal}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e2d4a" />
              <XAxis dataKey="mes" stroke="#555" tick={{ fontSize: 11 }} />
              <YAxis stroke="#555" tick={{ fontSize: 11 }} tickFormatter={(v) => `R$${(v/1000).toFixed(0)}k`} />
              <Tooltip
                contentStyle={{ background: "#16213e", border: "1px solid #f5a623", borderRadius: 6, fontSize: 12 }}
                formatter={(v: number) => [fmtBRL(v), "Faturamento"]}
              />
              <Bar dataKey="valor" fill="#f5a623" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

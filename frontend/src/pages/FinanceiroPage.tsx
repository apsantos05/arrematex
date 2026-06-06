/**
 * PDV / Financeiro — registra vendas e recebimentos manuais.
 * Sem gateway de pagamento; formas: dinheiro, pix, transferência, cheque, débito, crédito.
 */
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { motion } from "framer-motion";
import { api } from "@/services/api";
import toast from "react-hot-toast";

interface Venda {
  id: string;
  comprador_nome: string;
  arrematante_nome: string;
  lote_numero: number;
  lote_descricao: string;
  valor_total: string;
  valor_pago: string;
  valor_em_aberto: string;
  status: string;
  created_at: string;
}

interface RecebForm {
  forma: string;
  valor: string;
  observacao?: string;
}

const FORMAS = [
  { value: "dinheiro",     label: "💵 Dinheiro" },
  { value: "pix",          label: "📱 PIX" },
  { value: "transferencia",label: "🏦 Transferência" },
  { value: "cheque",       label: "📝 Cheque" },
  { value: "debito",       label: "💳 Débito" },
  { value: "credito",      label: "💳 Crédito" },
];

const STATUS_LABEL: Record<string, string> = {
  pendente: "Pendente",
  parcial: "Parcial",
  pago: "Pago",
  cancelado: "Cancelado",
};

const STATUS_COLOR: Record<string, string> = {
  pendente: "#e24b4a",
  parcial: "#f5a623",
  pago: "#6fcf6f",
  cancelado: "#888",
};

export default function FinanceiroPage() {
  const qc = useQueryClient();
  const [selectedVenda, setSelectedVenda] = useState<Venda | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["vendas"],
    queryFn: () => api.get("/financeiro/vendas/").then((r) => r.data.results || r.data),
  });

  const { register, handleSubmit, reset, formState: { isSubmitting } } = useForm<RecebForm>();

  const registrar = useMutation({
    mutationFn: (body: RecebForm) =>
      api.post("/financeiro/recebimentos/", { ...body, venda: selectedVenda!.id }),
    onSuccess: () => {
      toast.success("Recebimento registrado!");
      qc.invalidateQueries({ queryKey: ["vendas"] });
      setSelectedVenda(null);
      reset();
    },
    onError: () => toast.error("Erro ao registrar pagamento."),
  });

  const togglePago = useMutation({
    mutationFn: ({ id, novoStatus }: { id: string; novoStatus: string }) =>
      api.patch(`/financeiro/vendas/${id}/`, { status: novoStatus }),
    onSuccess: (_, { novoStatus }) => {
      toast.success(novoStatus === "pago" ? "Marcado como pago!" : "Marcado como pendente!");
      qc.invalidateQueries({ queryKey: ["vendas"] });
    },
    onError: () => toast.error("Erro ao alterar status."),
  });

  const fmtBRL = (v: string | number) =>
    new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(Number(v));
  const fmtDate = (d: string) => new Date(d).toLocaleDateString("pt-BR");

  return (
    <div style={{ padding: 24 }}>
      <h1 style={{ fontSize: 22, fontWeight: 900, color: "#f5a623", marginBottom: 20 }}>Financeiro / PDV</h1>

      {isLoading ? (
        <div style={{ color: "#555", padding: 40, textAlign: "center" }}>Carregando...</div>
      ) : (data || []).length === 0 ? (
        <div style={{ color: "rgba(255,255,255,0.3)", padding: 40, textAlign: "center" }}>
          Nenhuma venda registrada. Lotes vendidos aparecerão aqui automaticamente.
        </div>
      ) : (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <table>
            <thead>
              <tr>
                <th>Lote</th>
                <th>Arrematante</th>
                <th>Total</th>
                <th>Pago</th>
                <th>Em Aberto</th>
                <th>Status</th>
                <th>Data</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {(data || []).map((v: Venda) => (
                <tr key={v.id}>
                  <td>
                    <strong style={{ color: "#f5a623" }}>#{v.lote_numero}</strong>
                    <span style={{ color: "rgba(255,255,255,0.6)", fontSize: 12, marginLeft: 6 }}>
                      {v.lote_descricao}
                    </span>
                  </td>
                  <td>{v.comprador_nome || v.arrematante_nome}</td>
                  <td>{fmtBRL(v.valor_total)}</td>
                  <td style={{ color: "#6fcf6f" }}>{fmtBRL(v.valor_pago)}</td>
                  <td style={{ color: Number(v.valor_em_aberto) > 0 ? "#e24b4a" : "#6fcf6f" }}>
                    {fmtBRL(v.valor_em_aberto)}
                  </td>
                  <td>
                    <span style={{
                      padding: "3px 10px", borderRadius: 99, fontSize: 12, fontWeight: 700,
                      background: (STATUS_COLOR[v.status] ?? "#888") + "22",
                      color: STATUS_COLOR[v.status] ?? "#888",
                      border: `1px solid ${(STATUS_COLOR[v.status] ?? "#888")}44`,
                    }}>
                      {STATUS_LABEL[v.status] ?? v.status}
                    </span>
                  </td>
                  <td>{fmtDate(v.created_at)}</td>
                  <td style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                    {/* Toggle pago / pendente */}
                    {v.status !== "cancelado" && (
                      v.status === "pago" ? (
                        <button
                          className="btn btn-sm"
                          style={{ background: "#e24b4a22", color: "#e24b4a", border: "1px solid #e24b4a44" }}
                          disabled={togglePago.isPending}
                          onClick={() => togglePago.mutate({ id: v.id, novoStatus: "pendente" })}
                        >
                          ✕ Pendente
                        </button>
                      ) : (
                        <button
                          className="btn btn-sm"
                          style={{ background: "#6fcf6f22", color: "#6fcf6f", border: "1px solid #6fcf6f44" }}
                          disabled={togglePago.isPending}
                          onClick={() => togglePago.mutate({ id: v.id, novoStatus: "pago" })}
                        >
                          ✓ Pago
                        </button>
                      )
                    )}
                    {/* Registrar pagamento parcial */}
                    {v.status !== "pago" && v.status !== "cancelado" && (
                      <button className="btn btn-primary btn-sm" onClick={() => setSelectedVenda(v)}>
                        Registrar Pgto
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal de recebimento */}
      {selectedVenda && (
        <div style={{
          position: "fixed", inset: 0, background: "rgba(0,0,0,.75)",
          display: "flex", alignItems: "center", justifyContent: "center", zIndex: 200,
        }} onClick={(e) => e.target === e.currentTarget && setSelectedVenda(null)}>
          <motion.div
            initial={{ scale: .9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
            className="card" style={{ width: 440 }}
          >
            <h3 style={{ color: "#f5a623", marginBottom: 4 }}>Registrar Pagamento</h3>
            <div style={{ color: "#888", fontSize: 13, marginBottom: 20 }}>
              Lote #{selectedVenda.lote_numero} — {selectedVenda.comprador_nome || selectedVenda.arrematante_nome}
              <br />Em aberto: {fmtBRL(selectedVenda.valor_em_aberto)}
            </div>
            <form onSubmit={handleSubmit((d) => registrar.mutate(d))} style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              <div>
                <label style={{ fontSize: 11, color: "#f5a623", textTransform: "uppercase" }}>Forma de Pagamento</label>
                <select {...register("forma", { required: true })} style={{ marginTop: 6 }}>
                  {FORMAS.map((f) => <option key={f.value} value={f.value}>{f.label}</option>)}
                </select>
              </div>
              <div>
                <label style={{ fontSize: 11, color: "#f5a623", textTransform: "uppercase" }}>Valor (R$)</label>
                <input
                  type="number" step="0.01" min="0.01"
                  defaultValue={selectedVenda.valor_em_aberto}
                  {...register("valor", { required: true })}
                  style={{ marginTop: 6 }}
                />
              </div>
              <div>
                <label style={{ fontSize: 11, color: "#f5a623", textTransform: "uppercase" }}>Observação</label>
                <input placeholder="Opcional" {...register("observacao")} style={{ marginTop: 6 }} />
              </div>
              <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
                <button type="button" className="btn btn-ghost" style={{ flex: 1 }} onClick={() => setSelectedVenda(null)}>Cancelar</button>
                <button type="submit" className="btn btn-primary" style={{ flex: 1 }} disabled={isSubmitting}>Confirmar</button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </div>
  );
}


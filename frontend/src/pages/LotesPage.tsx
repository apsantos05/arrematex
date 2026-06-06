/**
 * Cadastro de Lotes de um Evento.
 */
import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { motion } from "framer-motion";
import { api } from "@/services/api";
import toast from "react-hot-toast";

interface Lote {
  id: string;
  numero: number;
  descricao: string;
  categoria_nome: string;
  vendedor_nome: string;
  quantidade: number;
  peso_total: string;
  lance_inicial: string;
  status: string;
}

interface LoteForm {
  numero: number;
  descricao: string;
  quantidade: number;
  peso_total: string;
  lance_inicial: string;
}

export default function LotesPage() {
  const { eventoId } = useParams<{ eventoId: string }>();
  const qc = useQueryClient();
  const [showModal, setShowModal] = useState(false);

  const { data: evento } = useQuery({
    queryKey: ["evento", eventoId],
    queryFn: () => api.get(`/lotes/eventos/${eventoId}/`).then((r) => r.data),
    enabled: !!eventoId,
  });

  const { data, isLoading } = useQuery({
    queryKey: ["lotes", eventoId],
    queryFn: () => api.get(`/lotes/lotes/?evento=${eventoId}`).then((r) => r.data.results || r.data),
    enabled: !!eventoId,
  });

  const { register, handleSubmit, reset, formState: { isSubmitting } } = useForm<LoteForm>();

  const criar = useMutation({
    mutationFn: (body: LoteForm) => api.post("/lotes/lotes/", { ...body, evento: eventoId }),
    onSuccess: () => {
      toast.success("Lote criado!");
      qc.invalidateQueries({ queryKey: ["lotes", eventoId] });
      setShowModal(false);
      reset();
    },
  });

  const fmtBRL = (v: string | number) =>
    new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(Number(v));

  return (
    <div style={{ padding: 24 }}>
      {/* Breadcrumb */}
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16, fontSize: 13 }}>
        <Link to="/eventos" style={{ color: "#f5a623", textDecoration: "none", fontWeight: 600 }}>
          ← Eventos
        </Link>
        <span style={{ color: "rgba(255,255,255,0.3)" }}>/</span>
        <span style={{ color: "rgba(255,255,255,0.6)" }}>Lotes</span>
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <h1 style={{ fontSize: 22, fontWeight: 900, color: "#f5a623" }}>Lotes do Evento</h1>
        <div style={{ display: "flex", gap: 10 }}>
          {evento?.status === "aberto" && (
            <Link to={`/eventos/${eventoId}/leilao`} className="btn btn-primary">
              🔨 Ir para Leilão
            </Link>
          )}
          <button className="btn btn-ghost" onClick={() => setShowModal(true)}>+ Novo Lote</button>
        </div>
      </div>

      {isLoading ? (
        <div style={{ color: "#555", padding: 40, textAlign: "center" }}>Carregando...</div>
      ) : (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <table>
            <thead>
              <tr><th>Nº</th><th>Descrição</th><th>Qtd</th><th>Peso Total</th><th>Lance Inicial</th><th>Status</th></tr>
            </thead>
            <tbody>
              {(data || []).map((l: Lote) => (
                <tr key={l.id}>
                  <td><strong>{l.numero}</strong></td>
                  <td>{l.descricao}</td>
                  <td>{l.quantidade}</td>
                  <td>{l.peso_total} kg</td>
                  <td>{fmtBRL(l.lance_inicial)}</td>
                  <td><span className={`badge badge-${l.status}`}>{l.status.replace("_", " ")}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showModal && (
        <div style={{
          position: "fixed", inset: 0, background: "rgba(0,0,0,.7)",
          display: "flex", alignItems: "center", justifyContent: "center", zIndex: 200,
        }} onClick={(e) => e.target === e.currentTarget && setShowModal(false)}>
          <motion.div
            initial={{ scale: .9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
            className="card" style={{ width: 440 }}
          >
            <h3 style={{ color: "#f5a623", marginBottom: 20 }}>Novo Lote</h3>
            <form onSubmit={handleSubmit((d) => criar.mutate(d))} style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              <input type="number" placeholder="Número do lote" {...register("numero", { required: true, valueAsNumber: true })} />
              <input placeholder="Descrição (ex: 5 bois nelore)" {...register("descricao", { required: true })} />
              <input type="number" placeholder="Quantidade de animais" {...register("quantidade", { required: true, valueAsNumber: true })} />
              <input type="number" step="0.1" placeholder="Peso total (kg)" {...register("peso_total", { required: true })} />
              <input type="number" step="0.01" placeholder="Lance inicial (R$)" {...register("lance_inicial", { required: true })} />
              <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
                <button type="button" className="btn btn-ghost" style={{ flex: 1 }} onClick={() => setShowModal(false)}>Cancelar</button>
                <button type="submit" className="btn btn-primary" style={{ flex: 1 }} disabled={isSubmitting}>Criar</button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </div>
  );
}

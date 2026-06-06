import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { motion, AnimatePresence } from "framer-motion";
import { api } from "@/services/api";
import toast from "react-hot-toast";
import IosDateTimePicker from "@/components/IosDateTimePicker";

interface Evento {
  id: string;
  nome: string;
  data: string;
  hora_inicio: string | null;
  local: string;
  status: string;
}

interface EventoForm {
  nome: string;
  data: string;
  hora_inicio: string;
  local: string;
}

const STATUS_LABEL: Record<string, string> = {
  agendado: "Agendado",
  aberto: "Aberto",
  encerrado: "Encerrado",
};

function fmtData(d: string, h: string | null) {
  if (!d) return "—";
  const date = new Date(`${d}T12:00:00`);
  const dateStr = date.toLocaleDateString("pt-BR", { day: "2-digit", month: "short", year: "numeric" });
  return h ? `${dateStr} às ${h.slice(0, 5)}` : dateStr;
}

export default function EventosPage() {
  const qc = useQueryClient();
  const [showModal, setShowModal] = useState(false);
  const [dateVal, setDateVal] = useState("");
  const [timeVal, setTimeVal] = useState("");

  const { data: eventos, isLoading } = useQuery({
    queryKey: ["eventos"],
    queryFn: () => api.get("/lotes/eventos/").then((r) => r.data.results ?? r.data),
  });

  const { register, handleSubmit, reset, formState: { isSubmitting, errors } } = useForm<EventoForm>();

  const criar = useMutation({
    mutationFn: (body: EventoForm) => api.post("/lotes/eventos/", body),
    onSuccess: () => {
      toast.success("Evento criado com sucesso!");
      qc.invalidateQueries({ queryKey: ["eventos"] });
      setShowModal(false);
      reset();
      setDateVal("");
      setTimeVal("");
    },
    onError: (err: any) => {
      const msg = err?.response?.data
        ? JSON.stringify(err.response.data)
        : "Erro ao criar evento";
      toast.error(msg);
    },
  });

  const alterarStatus = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      api.patch(`/lotes/eventos/${id}/`, { status }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["eventos"] }),
    onError: () => toast.error("Erro ao alterar status"),
  });

  async function onSubmit(formData: EventoForm) {
    if (!dateVal) { toast.error("Selecione a data do evento"); return; }
    await criar.mutateAsync({ ...formData, data: dateVal, hora_inicio: timeVal || "" });
  }

  function openModal() {
    reset();
    setDateVal("");
    setTimeVal("");
    setShowModal(true);
  }

  return (
    <div style={{ padding: 24 }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 900, color: "#f5a623" }}>Eventos de Leilão</h1>
        <button className="btn btn-primary" onClick={openModal}>+ Novo Evento</button>
      </div>

      {/* Table */}
      {isLoading ? (
        <div style={{ color: "#555", padding: 40, textAlign: "center" }}>Carregando...</div>
      ) : (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <table>
            <thead>
              <tr>
                <th>Nome</th>
                <th>Data / Hora</th>
                <th>Local</th>
                <th>Status</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {(eventos || []).length === 0 ? (
                <tr>
                  <td colSpan={5} style={{ textAlign: "center", color: "rgba(255,255,255,0.3)", padding: "40px 0" }}>
                    Nenhum evento cadastrado
                  </td>
                </tr>
              ) : (
                (eventos || []).map((e: Evento) => (
                  <tr key={e.id}>
                    <td><strong>{e.nome}</strong></td>
                    <td style={{ whiteSpace: "nowrap" }}>{fmtData(e.data, e.hora_inicio)}</td>
                    <td>{e.local || "—"}</td>
                    <td>
                      <span className={`badge badge-${e.status}`}>
                        {STATUS_LABEL[e.status] ?? e.status}
                      </span>
                    </td>
                    <td style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                      <Link to={`/eventos/${e.id}/lotes`} className="btn btn-ghost btn-sm">Lotes</Link>
                      {e.status === "agendado" && (
                        <button
                          className="btn btn-sm"
                          style={{ background: "#22c55e22", color: "#22c55e", border: "1px solid #22c55e44" }}
                          onClick={() => alterarStatus.mutate({ id: e.id, status: "aberto" })}
                        >
                          ▶ Abrir
                        </button>
                      )}
                      {e.status === "aberto" && (
                        <>
                          <Link to={`/eventos/${e.id}/leilao`} className="btn btn-primary btn-sm">🔨 Leilão</Link>
                          <button
                            className="btn btn-sm"
                            style={{ background: "#ef444422", color: "#ef4444", border: "1px solid #ef444444" }}
                            onClick={() => alterarStatus.mutate({ id: e.id, status: "encerrado" })}
                          >
                            ■ Encerrar
                          </button>
                        </>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal */}
      <AnimatePresence>
        {showModal && (
          <div
            style={{
              position: "fixed", inset: 0,
              background: "rgba(0,0,0,.75)",
              backdropFilter: "blur(6px)",
              display: "flex", alignItems: "center", justifyContent: "center", zIndex: 200,
            }}
            onClick={(e) => e.target === e.currentTarget && setShowModal(false)}
          >
            <motion.div
              initial={{ y: 40, opacity: 0, scale: 0.96 }}
              animate={{ y: 0, opacity: 1, scale: 1 }}
              exit={{ y: 20, opacity: 0, scale: 0.96 }}
              transition={{ type: "spring", stiffness: 340, damping: 28 }}
              className="card"
              style={{ width: 460, padding: 28 }}
            >
              {/* Modal header */}
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 24 }}>
                <h3 style={{ color: "#f5a623", fontSize: 18, fontWeight: 800, margin: 0 }}>Novo Evento</h3>
                <button
                  onClick={() => setShowModal(false)}
                  style={{ background: "none", border: "none", color: "rgba(255,255,255,0.4)", fontSize: 20, cursor: "pointer", lineHeight: 1 }}
                >
                  ✕
                </button>
              </div>

              <form onSubmit={handleSubmit(onSubmit)} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                {/* Nome */}
                <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  <span style={{ fontSize: 11, fontWeight: 600, letterSpacing: ".08em", color: "#f5a623", textTransform: "uppercase" }}>
                    Nome do Evento
                  </span>
                  <input
                    placeholder="Ex: Leilão de Gado Nelore — Junho"
                    {...register("nome", { required: "Nome obrigatório" })}
                    style={errors.nome ? { borderColor: "#ff5a5a" } : {}}
                  />
                  {errors.nome && (
                    <span style={{ fontSize: 11, color: "#ff5a5a" }}>{errors.nome.message}</span>
                  )}
                </div>

                {/* Date + Time */}
                <IosDateTimePicker
                  label="Data e Hora do Evento"
                  date={dateVal}
                  time={timeVal}
                  onDateChange={setDateVal}
                  onTimeChange={setTimeVal}
                />

                {/* Local */}
                <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  <span style={{ fontSize: 11, fontWeight: 600, letterSpacing: ".08em", color: "#f5a623", textTransform: "uppercase" }}>
                    Local
                  </span>
                  <input placeholder="Ex: Parque de Exposições SJRP" {...register("local")} />
                </div>

                {/* Actions */}
                <div style={{ display: "flex", gap: 10, marginTop: 8 }}>
                  <button
                    type="button"
                    className="btn btn-ghost"
                    style={{ flex: 1 }}
                    onClick={() => setShowModal(false)}
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    className="btn btn-primary"
                    style={{ flex: 2 }}
                    disabled={isSubmitting || criar.isPending}
                  >
                    {isSubmitting || criar.isPending ? "Criando..." : "Criar Evento"}
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}

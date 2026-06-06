/**
 * Painel do Leiloeiro — controla lotes, lances em tempo real e telão.
 * Usa WebSocket para comunicação bidirecional.
 */
import { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { useAuthStore } from "@/store/auth";
import { leilaoWS } from "@/services/websocket";
import { api } from "@/services/api";
import toast from "react-hot-toast";

interface Lote {
  id: string;
  numero: number;
  descricao: string;
  peso_total: string;
  lance_inicial: string;
  lance_atual: string;
  status: string;
}

interface LanceInfo {
  valor: string;
  arrematante: string;
  preco_kg: string;
  timestamp: string;
}

export default function PainelLeiloeiro() {
  const { eventoId } = useParams<{ eventoId: string }>();
  const user = useAuthStore((s) => s.user);
  const token = useAuthStore((s) => s.accessToken);

  const [lotes, setLotes] = useState<Lote[]>([]);
  const [sessaoAtiva, setSessaoAtiva] = useState<string | null>(null);
  const [loteAtivo, setLoteAtivo] = useState<Lote | null>(null);
  const [lanceAtual, setLanceAtual] = useState<LanceInfo | null>(null);
  const [historico, setHistorico] = useState<LanceInfo[]>([]);
  const [novoLance, setNovoLance] = useState("");
  const [arrematante, setArrematante] = useState("");
  const [mensagemTelao, setMensagemTelao] = useState("");
  const [wsStatus, setWsStatus] = useState<"connecting" | "connected" | "error">("connecting");

  // Conecta WebSocket
  useEffect(() => {
    if (!eventoId || !token) return;
    leilaoWS.connect("leilao", eventoId, token);
    leilaoWS.onStatusChange = (s) => {
      setWsStatus(s);
      // Ao conectar (ou reconectar), pede estado atual do leilão
      if (s === "connected") leilaoWS.send({ action: "get_estado" });
    };

    const unsub = leilaoWS.on((msg) => {
      // Tanto lote_aberto (ao abrir) quanto estado_atual (ao reconectar/recarregar)
      if (msg.type === "lote_aberto" || msg.type === "estado_atual") {
        const sessaoId = (msg.sessao_id ?? msg.id) as string;
        const lances = (msg.lances as Array<{ valor: string; arrematante: string; preco_kg: string; timestamp: string }>) ?? [];
        const lanceCorrente = msg.lance_corrente as string | null;

        setSessaoAtiva(sessaoId);
        setLoteAtivo({
          id: msg.lote_id as string,
          numero: msg.lote_numero as number,
          descricao: msg.lote_descricao as string,
          peso_total: msg.lote_peso as string,
          lance_inicial: msg.lance_inicial as string,
          lance_atual: lanceCorrente ?? (msg.lance_inicial as string),
          status: "em_leilao",
        });
        setHistorico(lances);
        setLanceAtual(lances.length > 0 ? lances[0] : null);
        if (msg.type === "lote_aberto") toast.success(`Lote ${msg.lote_numero} aberto!`);
      }

      if (msg.type === "lance_registrado") {
        const info: LanceInfo = {
          valor: msg.valor as string,
          arrematante: msg.arrematante as string,
          preco_kg: msg.preco_kg as string,
          timestamp: msg.timestamp as string,
        };
        setLanceAtual(info);
        setHistorico((prev) => [info, ...prev].slice(0, 10));
        setNovoLance("");
        setArrematante("");
      }

      if (msg.type === "lote_fechado") {
        setSessaoAtiva(null);
        setLoteAtivo(null);
        setLanceAtual(null);
        setHistorico([]);
        if (msg.vendido) toast.success(`Vendido por R$ ${msg.valor_final} — ${msg.arrematante}`);
        else toast("Lote retirado sem lance.");
      }
    });

    return () => {
      unsub();
      leilaoWS.disconnect();
    };
  }, [eventoId, token]);

  // Carrega lotes do evento
  useEffect(() => {
    if (!eventoId) return;
    api.get(`/lotes/lotes/?evento=${eventoId}`).then((r) => setLotes(r.data.results || r.data));
  }, [eventoId]);

  const abrirLote = (lote: Lote) => {
    leilaoWS.send({ action: "abrir_lote", lote_id: lote.id });
  };

  const registrarLance = () => {
    if (!sessaoAtiva || !novoLance) return;
    leilaoWS.send({
      action: "novo_lance",
      sessao_id: sessaoAtiva,
      valor: novoLance,
      arrematante_nome: arrematante,
    });
  };

  const fecharLote = () => {
    if (!sessaoAtiva) return;
    if (!confirm("Confirma o fechamento do lote?")) return;
    leilaoWS.send({ action: "fechar_lote", sessao_id: sessaoAtiva });
  };

  const enviarMensagem = () => {
    if (!mensagemTelao) return;
    leilaoWS.send({ action: "enviar_mensagem_telao", mensagem: mensagemTelao });
    setMensagemTelao("");
    toast.success("Mensagem enviada ao telão.");
  };

  const abrirTelao = () => {
    window.open(`/telao/${eventoId}`, "_blank", "fullscreen=yes");
  };

  const fmtBRL = (v: string | number) =>
    new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(Number(v));

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 340px", gap: 20, padding: 24 }}>

      {/* Coluna esquerda — preview do lote ativo */}
      <div>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <h2 style={{ color: "#f5a623", fontSize: 20, fontWeight: 800, textTransform: "uppercase" }}>
              🔨 Painel do Leiloeiro
            </h2>
            {/* WS status pill */}
            <span style={{
              fontSize: 10, fontWeight: 700, letterSpacing: ".06em",
              padding: "3px 10px", borderRadius: 99, textTransform: "uppercase",
              background: wsStatus === "connected" ? "#16a34a22" : wsStatus === "connecting" ? "#ca8a0422" : "#dc262622",
              color: wsStatus === "connected" ? "#4ade80" : wsStatus === "connecting" ? "#fbbf24" : "#f87171",
              border: `1px solid ${wsStatus === "connected" ? "#16a34a55" : wsStatus === "connecting" ? "#ca8a0455" : "#dc262655"}`,
            }}>
              {wsStatus === "connected" ? "● Online" : wsStatus === "connecting" ? "○ Conectando..." : "✕ Desconectado"}
            </span>
          </div>
          <button className="btn btn-ghost btn-sm" onClick={abrirTelao}>
            📺 Abrir Telão
          </button>
        </div>

        {/* Preview do lote ativo */}
        <AnimatePresence mode="wait">
          {loteAtivo ? (
            <motion.div
              key={loteAtivo.id}
              initial={{ opacity: 0, scale: .97 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: .97 }}
              className="card"
              style={{ border: "2px solid #f5a623", marginBottom: 16 }}
            >
              <div style={{ fontSize: 13, color: "#888", marginBottom: 8 }}>LOTE EM LEILÃO</div>
              <div style={{ fontSize: 22, fontWeight: 900, color: "#f5a623" }}>
                Lote {loteAtivo.numero} — {loteAtivo.descricao}
              </div>
              <div style={{ color: "#aaa", marginTop: 4 }}>
                Peso: <strong>{loteAtivo.peso_total} kg</strong>
              </div>

              {/* Lance atual */}
              <div style={{ marginTop: 20, textAlign: "center" }}>
                <div style={{ fontSize: 12, color: "#888", textTransform: "uppercase" }}>Lance Atual</div>
                <motion.div
                  key={lanceAtual?.valor}
                  initial={{ scale: 1.2, color: "#ffc147" }}
                  animate={{ scale: 1, color: "#f5a623" }}
                  style={{ fontSize: 44, fontWeight: 900, lineHeight: 1.1, marginTop: 4 }}
                >
                  {lanceAtual ? fmtBRL(lanceAtual.valor) : fmtBRL(loteAtivo.lance_inicial)}
                </motion.div>
                {lanceAtual && (
                  <div style={{ color: "#aaa", fontSize: 13, marginTop: 6 }}>
                    {lanceAtual.arrematante} · R$ {lanceAtual.preco_kg}/kg
                  </div>
                )}
              </div>

              {/* Histórico rápido */}
              {historico.length > 0 && (
                <div style={{ marginTop: 16, borderTop: "1px solid #334", paddingTop: 12 }}>
                  <div style={{ fontSize: 11, color: "#888", marginBottom: 8 }}>ÚLTIMOS LANCES</div>
                  {historico.slice(0, 5).map((l, i) => (
                    <div key={i} style={{ display: "flex", justifyContent: "space-between", padding: "4px 0", fontSize: 12, color: i === 0 ? "#f5a623" : "#aaa" }}>
                      <span>{l.arrematante || "—"}</span>
                      <span>{fmtBRL(l.valor)}</span>
                    </div>
                  ))}
                </div>
              )}

              <button className="btn btn-danger" style={{ width: "100%", marginTop: 16, justifyContent: "center" }} onClick={fecharLote}>
                🔒 Fechar Lote
              </button>
            </motion.div>
          ) : (
            <motion.div
              key="empty"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="card"
              style={{ textAlign: "center", color: "#444", padding: "60px 0", marginBottom: 16 }}
            >
              Nenhum lote em leilão. Selecione um lote ao lado.
            </motion.div>
          )}
        </AnimatePresence>

        {/* Lista de lotes */}
        <div className="card">
          <div style={{ fontSize: 13, fontWeight: 700, color: "#f5a623", marginBottom: 12, textTransform: "uppercase" }}>
            Lotes do Evento
          </div>
          <table>
            <thead>
              <tr>
                <th>Lote</th><th>Descrição</th><th>Peso</th><th>Lance Inicial</th><th>Status</th><th></th>
              </tr>
            </thead>
            <tbody>
              {lotes.map((l) => (
                <tr key={l.id}>
                  <td><strong>{l.numero}</strong></td>
                  <td>{l.descricao}</td>
                  <td>{l.peso_total} kg</td>
                  <td>{fmtBRL(l.lance_inicial)}</td>
                  <td><span className={`badge badge-${l.status}`}>{l.status.replace("_", " ")}</span></td>
                  <td>
                    {l.status === "aguardando" && (
                      <button className="btn btn-primary btn-sm" onClick={() => abrirLote(l)}>
                        Abrir
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Coluna direita — controles */}
      <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>

        {/* Registrar lance */}
        <div className="card">
          <div style={{ fontSize: 12, fontWeight: 700, color: "#f5a623", textTransform: "uppercase", marginBottom: 12 }}>
            Registrar Lance
          </div>

          {/* Status hint */}
          {!sessaoAtiva && (
            <div style={{
              fontSize: 11, color: "#fbbf24", background: "#ca8a0415",
              border: "1px solid #ca8a0430", borderRadius: 8, padding: "8px 12px", marginBottom: 10,
            }}>
              Abra um lote na tabela para habilitar os lances.
            </div>
          )}
          {wsStatus !== "connected" && (
            <div style={{
              fontSize: 11, color: "#f87171", background: "#dc262615",
              border: "1px solid #dc262630", borderRadius: 8, padding: "8px 12px", marginBottom: 10,
            }}>
              WebSocket {wsStatus === "connecting" ? "conectando..." : "desconectado. Aguarde reconexão."}
            </div>
          )}

          <label style={{ fontSize: 11, color: "#888" }}>Arrematante</label>
          <input
            placeholder="Nome do arrematante"
            value={arrematante}
            onChange={(e) => setArrematante(e.target.value)}
            style={{ marginBottom: 10, marginTop: 4 }}
          />
          <label style={{ fontSize: 11, color: "#888" }}>Valor (R$)</label>
          <input
            type="number"
            placeholder="0,00"
            value={novoLance}
            onChange={(e) => setNovoLance(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && registrarLance()}
            style={{ marginBottom: 12, marginTop: 4 }}
          />
          <button
            className="btn btn-primary"
            style={{ width: "100%", justifyContent: "center", opacity: (!sessaoAtiva || !novoLance || wsStatus !== "connected") ? 0.5 : 1 }}
            disabled={!sessaoAtiva || !novoLance || wsStatus !== "connected"}
            onClick={registrarLance}
          >
            ✓ Dar Lance
          </button>
        </div>

        {/* Mensagem telão */}
        {user?.role === "admin" || user?.role === "leiloeiro" ? (
          <div className="card">
            <div style={{ fontSize: 12, fontWeight: 700, color: "#f5a623", textTransform: "uppercase", marginBottom: 12 }}>
              Mensagem no Telão
            </div>
            <input
              placeholder="Digite a mensagem..."
              value={mensagemTelao}
              onChange={(e) => setMensagemTelao(e.target.value)}
              style={{ marginBottom: 10 }}
            />
            <button className="btn btn-ghost" style={{ width: "100%", justifyContent: "center" }} onClick={enviarMensagem}>
              📡 Enviar ao Telão
            </button>
          </div>
        ) : null}
      </div>
    </div>
  );
}

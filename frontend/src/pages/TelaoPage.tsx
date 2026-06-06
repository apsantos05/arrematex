/**
 * Tela do Telão — exibição em TV, modo fullscreen.
 * Conecta ao canal WS público (sem autenticação).
 * Atualiza em tempo real via WebSocket.
 */
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { telaoWS } from "@/services/websocket";

interface LoteInfo {
  numero: number;
  descricao: string;
  peso_total: string;
  lance_inicial: string;
}

interface LanceInfo {
  valor: string;
  arrematante: string;
  preco_kg: string;
}

export default function TelaoPage() {
  const { eventoId } = useParams<{ eventoId: string }>();
  const [lote, setLote] = useState<LoteInfo | null>(null);
  const [lanceAtual, setLanceAtual] = useState<LanceInfo | null>(null);
  const [historico, setHistorico] = useState<LanceInfo[]>([]);
  const [mensagem, setMensagem] = useState<string>("");
  const [statusLote, setStatusLote] = useState<"aguardando" | "aberto" | "fechado">("aguardando");

  useEffect(() => {
    if (!eventoId) return;
    telaoWS.connect("telao", eventoId);

    const unsub = telaoWS.on((msg) => {
      if (msg.type === "lote_aberto") {
        setLote({
          numero: msg.lote_numero as number,
          descricao: msg.lote_descricao as string,
          peso_total: msg.lote_peso as string,
          lance_inicial: msg.lance_inicial as string,
        });
        setLanceAtual(null);
        setHistorico([]);
        setStatusLote("aberto");
        setMensagem("");
      }

      if (msg.type === "atualizar_lance" || msg.type === "lance_registrado") {
        const info: LanceInfo = {
          valor: msg.valor as string,
          arrematante: msg.arrematante as string,
          preco_kg: msg.preco_kg as string,
        };
        setLanceAtual(info);
        setHistorico((prev) => [info, ...prev].slice(0, 8));
      }

      if (msg.type === "lote_fechado") {
        setStatusLote("fechado");
        setTimeout(() => {
          setLote(null);
          setLanceAtual(null);
          setStatusLote("aguardando");
        }, 8000);
      }

      if (msg.type === "mensagem_telao") {
        setMensagem(msg.mensagem as string);
        setTimeout(() => setMensagem(""), 10000);
      }
    });

    return () => {
      unsub();
      telaoWS.disconnect();
    };
  }, [eventoId]);

  const fmtBRL = (v: string | number) =>
    new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(Number(v));

  return (
    <div style={{
      position: "fixed", inset: 0,
      background: "#000",
      display: "flex", flexDirection: "column",
      fontFamily: "'Barlow', sans-serif",
      overflow: "hidden",
    }}>

      {/* Header */}
      <div style={{
        background: "#111",
        borderBottom: "3px solid #f5a623",
        padding: "16px 40px",
        display: "flex", alignItems: "center", justifyContent: "space-between",
      }}>
        <div style={{ fontSize: 28, fontWeight: 900, color: "#f5a623", letterSpacing: 3 }}>
          🐄 ARREMATEX
        </div>
        <div style={{ fontSize: 14, color: "#888", letterSpacing: 2 }}>LEILÃO PECUÁRIO</div>
        <div style={{ fontSize: 14, color: "#f5a623" }}>
          {new Date().toLocaleDateString("pt-BR", { weekday: "long", day: "2-digit", month: "long" })}
        </div>
      </div>

      {/* Conteúdo principal */}
      <div style={{ flex: 1, display: "flex", alignItems: "stretch" }}>

        {/* Lote + Lance */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", justifyContent: "center", padding: "40px 60px" }}>

          <AnimatePresence mode="wait">
            {!lote ? (
              <motion.div
                key="idle"
                initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                style={{ textAlign: "center" }}
              >
                <div style={{ fontSize: 60, marginBottom: 16 }}>🐄</div>
                <div style={{ fontSize: 28, color: "#444", fontWeight: 700 }}>Aguardando próximo lote...</div>
              </motion.div>
            ) : statusLote === "fechado" ? (
              <motion.div
                key="fechado"
                initial={{ scale: .8, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ opacity: 0 }}
                style={{ textAlign: "center" }}
              >
                <div style={{ fontSize: 80 }}>🔨</div>
                <div style={{ fontSize: 40, fontWeight: 900, color: "#6fcf6f", marginTop: 16 }}>VENDIDO!</div>
                {lanceAtual && (
                  <div style={{ fontSize: 56, fontWeight: 900, color: "#f5a623", marginTop: 8 }}>
                    {fmtBRL(lanceAtual.valor)}
                  </div>
                )}
                {lanceAtual?.arrematante && (
                  <div style={{ fontSize: 24, color: "#aaa", marginTop: 8 }}>{lanceAtual.arrematante}</div>
                )}
              </motion.div>
            ) : (
              <motion.div
                key={lote.numero}
                initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 20 }}
              >
                {/* Número do lote */}
                <div style={{ fontSize: 16, color: "#888", textTransform: "uppercase", letterSpacing: 3, marginBottom: 8 }}>
                  Lote em Leilão
                </div>
                <div style={{ fontSize: 72, fontWeight: 900, color: "#f5a623", lineHeight: 1 }}>
                  #{lote.numero}
                </div>
                <div style={{ fontSize: 32, fontWeight: 700, color: "#eee", marginTop: 8, marginBottom: 16 }}>
                  {lote.descricao}
                </div>
                <div style={{ fontSize: 18, color: "#aaa" }}>
                  Peso: <strong style={{ color: "#eee" }}>{lote.peso_total} kg</strong>
                </div>

                {/* Lance atual */}
                <div style={{ marginTop: 40 }}>
                  <div style={{ fontSize: 14, color: "#888", textTransform: "uppercase", letterSpacing: 2 }}>
                    Lance Atual
                  </div>
                  <motion.div
                    key={lanceAtual?.valor ?? "inicial"}
                    initial={{ scale: 1.15, color: "#fff" }}
                    animate={{ scale: 1, color: "#f5a623" }}
                    transition={{ duration: .4 }}
                    style={{ fontSize: 88, fontWeight: 900, lineHeight: 1 }}
                  >
                    {lanceAtual ? fmtBRL(lanceAtual.valor) : fmtBRL(lote.lance_inicial)}
                  </motion.div>

                  {lanceAtual && (
                    <motion.div
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      style={{ marginTop: 8 }}
                    >
                      <div style={{ fontSize: 22, color: "#aaa" }}>{lanceAtual.arrematante || "—"}</div>
                      <div style={{ fontSize: 18, color: "#666" }}>R$ {lanceAtual.preco_kg}/kg</div>
                    </motion.div>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Histórico de lances */}
        <div style={{
          width: 340,
          background: "#0a0a0a",
          borderLeft: "1px solid #1a1a1a",
          padding: "32px 24px",
          overflowY: "auto",
        }}>
          <div style={{ fontSize: 12, color: "#555", textTransform: "uppercase", letterSpacing: 2, marginBottom: 16 }}>
            Últimos Lances
          </div>
          <AnimatePresence>
            {historico.map((l, i) => (
              <motion.div
                key={`${l.valor}-${i}`}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * .03 }}
                style={{
                  padding: "12px 0",
                  borderBottom: "1px solid #1a1a1a",
                  opacity: i === 0 ? 1 : 1 - i * 0.1,
                }}
              >
                <div style={{ fontSize: i === 0 ? 26 : 20, fontWeight: 800, color: i === 0 ? "#f5a623" : "#555" }}>
                  {fmtBRL(l.valor)}
                </div>
                <div style={{ fontSize: 13, color: "#444", marginTop: 2 }}>{l.arrematante || "—"}</div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      </div>

      {/* Mensagem do administrador */}
      <AnimatePresence>
        {mensagem && (
          <motion.div
            key="msg"
            initial={{ y: 100, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: 100, opacity: 0 }}
            style={{
              position: "absolute", bottom: 0, left: 0, right: 0,
              background: "#f5a623", color: "#1a1a2e",
              textAlign: "center", padding: "16px 40px",
              fontSize: 22, fontWeight: 800, letterSpacing: 1,
            }}
          >
            📢 {mensagem}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

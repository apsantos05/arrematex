/**
 * Fiscal — upload de certificado A1 e emissão de NF-e.
 */
import { useRef, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { api } from "@/services/api";
import toast from "react-hot-toast";

interface NotaFiscal {
  id: string;
  numero: number;
  serie: number;
  status: string;
  chave_acesso: string;
  xml_url: string;
  danfe_url: string;
  created_at: string;
}

export default function FiscalPage() {
  const qc = useQueryClient();
  const certRef = useRef<HTMLInputElement>(null);
  const [certPass, setCertPass] = useState("");
  const [nfeVenda, setNfeVenda] = useState("");

  const { data: notas, isLoading } = useQuery({
    queryKey: ["notas"],
    queryFn: () => api.get("/fiscal/notas/").then((r) => r.data.results || r.data),
  });

  const uploadCert = useMutation({
    mutationFn: (fd: FormData) => api.post("/fiscal/certificado/upload/", fd, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
    onSuccess: () => { toast.success("Certificado enviado!"); setCertPass(""); },
    onError: () => toast.error("Erro ao enviar certificado."),
  });

  const emitir = useMutation({
    mutationFn: (vendaId: string) => api.post("/fiscal/nfe/emitir/", { venda_id: vendaId }),
    onSuccess: () => { toast.success("NF-e emitida!"); qc.invalidateQueries({ queryKey: ["notas"] }); setNfeVenda(""); },
    onError: () => toast.error("Erro ao emitir NF-e."),
  });

  const handleCertUpload = () => {
    const file = certRef.current?.files?.[0];
    if (!file || !certPass) { toast.error("Selecione o arquivo .pfx e informe a senha."); return; }
    const fd = new FormData();
    fd.append("arquivo", file);
    fd.append("senha", certPass);
    uploadCert.mutate(fd);
  };

  const statusColor: Record<string, string> = {
    autorizada: "#6fcf6f", rejeitada: "#e24b4a",
    cancelada: "#e24b4a", aguardando: "#f5a623", rascunho: "#888",
  };

  return (
    <div style={{ padding: 24 }}>
      <h1 style={{ fontSize: 22, fontWeight: 900, color: "#f5a623", marginBottom: 24 }}>Gestão Fiscal</h1>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginBottom: 24 }}>
        {/* Upload certificado */}
        <div className="card">
          <h3 style={{ color: "#f5a623", marginBottom: 16, fontSize: 14 }}>🔑 Certificado Digital A1</h3>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            <input type="file" accept=".pfx,.p12" ref={certRef} />
            <input
              type="password"
              placeholder="Senha do certificado"
              value={certPass}
              onChange={(e) => setCertPass(e.target.value)}
            />
            <button
              className="btn btn-primary"
              onClick={handleCertUpload}
              disabled={uploadCert.isPending}
            >
              {uploadCert.isPending ? "Enviando..." : "Enviar Certificado"}
            </button>
          </div>
        </div>

        {/* Emitir NF-e */}
        <div className="card">
          <h3 style={{ color: "#f5a623", marginBottom: 16, fontSize: 14 }}>🧾 Emitir NF-e</h3>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            <input
              placeholder="ID da Venda"
              value={nfeVenda}
              onChange={(e) => setNfeVenda(e.target.value)}
            />
            <button
              className="btn btn-primary"
              onClick={() => emitir.mutate(nfeVenda)}
              disabled={!nfeVenda || emitir.isPending}
            >
              {emitir.isPending ? "Emitindo..." : "Emitir NF-e para esta Venda"}
            </button>
          </div>
        </div>
      </div>

      {/* Lista de notas */}
      <div className="card" style={{ padding: 0, overflow: "hidden" }}>
        <table>
          <thead>
            <tr><th>Nº</th><th>Série</th><th>Status</th><th>Chave de Acesso</th><th>Data</th><th>Ações</th></tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr><td colSpan={6} style={{ textAlign: "center", color: "#555", padding: 40 }}>Carregando...</td></tr>
            ) : (notas || []).map((n: NotaFiscal) => (
              <tr key={n.id}>
                <td>{n.numero}</td>
                <td>{n.serie}</td>
                <td>
                  <span style={{ color: statusColor[n.status] || "#aaa", fontWeight: 700 }}>
                    {n.status.toUpperCase()}
                  </span>
                </td>
                <td style={{ fontSize: 11, color: "#666", fontFamily: "monospace" }}>
                  {n.chave_acesso || "—"}
                </td>
                <td>{new Date(n.created_at).toLocaleDateString("pt-BR")}</td>
                <td style={{ display: "flex", gap: 6 }}>
                  {n.xml_url && <a href={n.xml_url} target="_blank" className="btn btn-ghost btn-sm">XML</a>}
                  {n.danfe_url && <a href={n.danfe_url} target="_blank" className="btn btn-primary btn-sm">DANFE</a>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

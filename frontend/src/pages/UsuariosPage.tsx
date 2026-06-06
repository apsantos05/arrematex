/**
 * Gestão de Usuários — cadastro e listagem (admin only).
 */
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { motion } from "framer-motion";
import { api } from "@/services/api";
import toast from "react-hot-toast";

interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
}

interface UserForm {
  email: string;
  full_name: string;
  password: string;
  role: string;
}

const ROLES = [
  { value: "admin",      label: "Administrador" },
  { value: "leiloeiro",  label: "Leiloeiro" },
  { value: "operador",   label: "Operador" },
  { value: "caixa",      label: "Caixa" },
  { value: "fiscal",     label: "Fiscal" },
  { value: "comprador",  label: "Comprador" },
];

export default function UsuariosPage() {
  const qc = useQueryClient();
  const [showModal, setShowModal] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ["usuarios"],
    queryFn: () => api.get("/auth/users/").then((r) => r.data.results || r.data),
  });

  const { register, handleSubmit, reset, formState: { isSubmitting } } = useForm<UserForm>();

  const criar = useMutation({
    mutationFn: (body: UserForm) => api.post("/auth/users/", body),
    onSuccess: () => {
      toast.success("Usuário criado!");
      qc.invalidateQueries({ queryKey: ["usuarios"] });
      setShowModal(false);
      reset();
    },
  });

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <h1 style={{ fontSize: 22, fontWeight: 900, color: "#f5a623" }}>Usuários</h1>
        <button className="btn btn-primary" onClick={() => setShowModal(true)}>+ Novo Usuário</button>
      </div>

      {isLoading ? (
        <div style={{ color: "#555", padding: 40, textAlign: "center" }}>Carregando...</div>
      ) : (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <table>
            <thead>
              <tr><th>Nome</th><th>E-mail</th><th>Perfil</th><th>Status</th></tr>
            </thead>
            <tbody>
              {(data || []).map((u: User) => (
                <tr key={u.id}>
                  <td>{u.full_name}</td>
                  <td style={{ color: "#888" }}>{u.email}</td>
                  <td>
                    <span className="badge badge-em_leilao" style={{ textTransform: "capitalize" }}>
                      {ROLES.find((r) => r.value === u.role)?.label ?? u.role}
                    </span>
                  </td>
                  <td>
                    <span style={{ color: u.is_active ? "#6fcf6f" : "#e24b4a", fontWeight: 700 }}>
                      {u.is_active ? "Ativo" : "Inativo"}
                    </span>
                  </td>
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
            className="card" style={{ width: 420 }}
          >
            <h3 style={{ color: "#f5a623", marginBottom: 20 }}>Novo Usuário</h3>
            <form onSubmit={handleSubmit((d) => criar.mutate(d))} style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              <input placeholder="Nome completo" {...register("full_name", { required: true })} />
              <input type="email" placeholder="E-mail" {...register("email", { required: true })} />
              <input type="password" placeholder="Senha" {...register("password", { required: true })} />
              <select {...register("role", { required: true })}>
                {ROLES.map((r) => <option key={r.value} value={r.value}>{r.label}</option>)}
              </select>
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

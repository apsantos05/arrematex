import { motion } from "framer-motion";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useAuthStore } from "@/store/auth";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";

const schema = z.object({
  email: z.string().email("E-mail inválido"),
  password: z.string().min(1, "Senha obrigatória"),
});
type Form = z.infer<typeof schema>;

export default function LoginPage() {
  const login = useAuthStore((s) => s.login);
  const navigate = useNavigate();
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<Form>({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (data: Form) => {
    try {
      await login(data.email, data.password);
      navigate("/eventos");
    } catch {
      toast.error("E-mail ou senha incorretos.");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center"
      style={{ background: "radial-gradient(ellipse at 30% 20%, #16213e 0%, #1a1a2e 70%)" }}>

      <motion.div
        initial={{ opacity: 0, y: 32 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: .4, ease: "easeOut" }}
        className="card w-full max-w-sm"
        style={{ border: "1px solid #f5a62355", boxShadow: "0 0 40px rgba(245,166,35,.08)" }}
      >
        {/* Logo */}
        <div className="text-center mb-8">
          <div style={{ fontSize: 28, fontWeight: 900, color: "#f5a623", letterSpacing: 3 }}>
            🐄 ARREMATEX
          </div>
          <div style={{ fontSize: 12, color: "#888", marginTop: 4, letterSpacing: 2 }}>
            LEILÃO PECUÁRIO
          </div>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div>
            <label style={{ fontSize: 11, fontWeight: 700, color: "#f5a623", textTransform: "uppercase", letterSpacing: 1 }}>
              E-mail
            </label>
            <input type="email" placeholder="seu@email.com.br" {...register("email")} style={{ marginTop: 6 }} />
            {errors.email && <span style={{ color: "#e24b4a", fontSize: 12 }}>{errors.email.message}</span>}
          </div>

          <div>
            <label style={{ fontSize: 11, fontWeight: 700, color: "#f5a623", textTransform: "uppercase", letterSpacing: 1 }}>
              Senha
            </label>
            <input type="password" placeholder="••••••••" {...register("password")} style={{ marginTop: 6 }} />
            {errors.password && <span style={{ color: "#e24b4a", fontSize: 12 }}>{errors.password.message}</span>}
          </div>

          <motion.button
            type="submit"
            className="btn btn-primary"
            style={{ width: "100%", justifyContent: "center", marginTop: 8 }}
            disabled={isSubmitting}
            whileTap={{ scale: 0.97 }}
          >
            {isSubmitting ? "Entrando..." : "Entrar"}
          </motion.button>
        </form>
      </motion.div>
    </div>
  );
}

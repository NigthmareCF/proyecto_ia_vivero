import { FormEvent, useState } from "react";
import axios from "axios";
import { login, register } from "../../api/authApi";
import { useAuthStore } from "../../store/authStore";

type AuthMode = "login" | "register";
type PublicRole = "CONTROLLER" | "VIEWER";

export function LoginForm() {
  const setSession = useAuthStore((state) => state.setSession);
  const [mode, setMode] = useState<AuthMode>("login");
  const [firstName, setFirstName] = useState("Fer");
  const [lastName, setLastName] = useState("Castillo");
  const [email, setEmail] = useState("admin@vivero.com");
  const [password, setPassword] = useState("admin123");
  const [role, setRole] = useState<PublicRole>("CONTROLLER");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    try {
      setLoading(true);
      setError(null);

      const session =
        mode === "login"
          ? await login(email, password)
          : await register({ firstName, lastName, email, password, role });

      setSession(session);
    } catch (err) {
      if (mode === "login") {
        const fallback = "No fue posible iniciar sesion con correo y contraseña.";
        if (axios.isAxiosError(err)) {
          const responseMessage =
            typeof err.response?.data?.message === "string" ? err.response.data.message : null;
          const responseError =
            typeof err.response?.data?.error === "string" ? err.response.data.error : null;
          const status = err.response?.status ? `HTTP ${err.response.status}` : null;
          const detail = responseMessage ?? responseError ?? status;
          setError(detail ? `${fallback} Detalle: ${detail}.` : fallback);
        } else if (err instanceof Error && err.message) {
          setError(`${fallback} Detalle: ${err.message}.`);
        } else {
          setError(fallback);
        }
      } else {
        setError("No fue posible registrar la cuenta con los datos ingresados.");
      }
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4 rounded-[2rem] bg-white p-8 shadow-xl">
      <div className="flex gap-2 rounded-2xl bg-sand p-2">
        <button
          type="button"
          className={`flex-1 rounded-2xl px-4 py-2 text-sm font-semibold ${
            mode === "login" ? "bg-ink text-white" : "text-moss"
          }`}
          onClick={() => setMode("login")}
        >
          Iniciar sesion
        </button>
        <button
          type="button"
          className={`flex-1 rounded-2xl px-4 py-2 text-sm font-semibold ${
            mode === "register" ? "bg-ink text-white" : "text-moss"
          }`}
          onClick={() => setMode("register")}
        >
          Registrarse
        </button>
      </div>

      <h2 className="font-display text-4xl text-ink">
        {mode === "login" ? "Ingreso operativo" : "Registro de usuario"}
      </h2>
      <p className="text-moss">
        Acceso por correo y contraseña. Los nuevos usuarios solo pueden elegir `CONTROLLER` o `VIEWER`.
      </p>

      {mode === "register" && (
        <div className="grid gap-3 sm:grid-cols-2">
          <input
            className="w-full rounded-2xl border border-ink/10 px-4 py-3"
            value={firstName}
            onChange={(event) => setFirstName(event.target.value)}
            placeholder="Nombres"
          />
          <input
            className="w-full rounded-2xl border border-ink/10 px-4 py-3"
            value={lastName}
            onChange={(event) => setLastName(event.target.value)}
            placeholder="Apellidos"
          />
        </div>
      )}

      <input
        className="w-full rounded-2xl border border-ink/10 px-4 py-3"
        value={email}
        onChange={(event) => setEmail(event.target.value)}
        placeholder="Correo"
      />
      <input
        className="w-full rounded-2xl border border-ink/10 px-4 py-3"
        type="password"
        value={password}
        onChange={(event) => setPassword(event.target.value)}
        placeholder="Contrasena"
      />

      {mode === "register" && (
        <select
          className="w-full rounded-2xl border border-ink/10 px-4 py-3"
          value={role}
          onChange={(event) => setRole(event.target.value as PublicRole)}
        >
          <option value="CONTROLLER">CONTROLLER</option>
          <option value="VIEWER">VIEWER</option>
        </select>
      )}

      {error && <p className="text-sm text-alert">{error}</p>}

      <button
        type="submit"
        disabled={loading}
        className="w-full rounded-2xl bg-clay px-4 py-3 font-semibold text-white disabled:opacity-60"
      >
        {loading ? "Procesando..." : mode === "login" ? "Entrar" : "Crear cuenta"}
      </button>
    </form>
  );
}

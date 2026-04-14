import { FormEvent, useState } from "react";
import { login, socialLogin } from "../../api/authApi";
import { useAuthStore } from "../../store/authStore";
import { SocialLoginButton } from "./SocialLoginButton";

export function LoginForm() {
  const setSession = useAuthStore((state) => state.setSession);
  const [email, setEmail] = useState("admin@vivero.com");
  const [password, setPassword] = useState("admin123");
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    try {
      setError(null);
      const session = await login(email, password);
      setSession(session);
    } catch (err) {
      setError("No fue posible iniciar sesion con credenciales locales.");
      console.error(err);
    }
  }

  async function handleSocial(provider: "GOOGLE" | "APPLE") {
    const fakeToken = window.prompt(`Ingresa un id_token valido para ${provider}`) ?? "";
    if (!fakeToken) return;
    const session = await socialLogin(provider, fakeToken);
    setSession(session);
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4 rounded-[2rem] bg-white p-8 shadow-xl">
      <h2 className="font-display text-4xl text-ink">Ingreso operativo</h2>
      <p className="text-moss">JWT local y OAuth 2.0 para Google o Apple.</p>
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
      {error && <p className="text-sm text-alert">{error}</p>}
      <button type="submit" className="w-full rounded-2xl bg-clay px-4 py-3 font-semibold text-white">
        Entrar
      </button>
      <div className="grid grid-cols-2 gap-3">
        <SocialLoginButton provider="GOOGLE" onClick={() => handleSocial("GOOGLE")} />
        <SocialLoginButton provider="APPLE" onClick={() => handleSocial("APPLE")} />
      </div>
    </form>
  );
}

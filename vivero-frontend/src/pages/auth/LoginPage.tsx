import { LoginForm } from "../../components/auth/LoginForm";

export function LoginPage() {
  return (
    <main className="grid min-h-screen place-items-center px-6">
      <div className="grid w-full max-w-5xl gap-8 lg:grid-cols-[1.1fr_0.9fr]">
        <section className="rounded-[2.5rem] bg-ink p-10 text-sand shadow-2xl">
          <p className="text-sm uppercase tracking-[0.24em] text-sand/70">Plataforma V3</p>
          <h1 className="mt-4 font-display text-6xl leading-none">Vivero inteligente con robotica e IA</h1>
          <p className="mt-6 max-w-xl text-lg text-sand/80">
            Backend Spring Boot, robot Pi, reportes documentados y centro de control del patrullaje.
          </p>
        </section>
        <LoginForm />
      </div>
    </main>
  );
}

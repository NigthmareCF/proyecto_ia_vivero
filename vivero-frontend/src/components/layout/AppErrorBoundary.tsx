import { Component, ErrorInfo, ReactNode } from "react";

type Props = {
  children: ReactNode;
};

type State = {
  hasError: boolean;
  message: string;
};

export class AppErrorBoundary extends Component<Props, State> {
  state: State = {
    hasError: false,
    message: "",
  };

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      message: error.message,
    };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("Frontend render failure", error, info);
  }

  resetSession() {
    localStorage.removeItem("vivero-auth");
    window.location.href = "/";
  }

  render() {
    if (!this.state.hasError) {
      return this.props.children;
    }

    return (
      <main className="grid min-h-screen place-items-center px-6">
        <section className="max-w-2xl rounded-[2rem] bg-white p-8 shadow-xl">
          <p className="text-sm uppercase tracking-[0.2em] text-alert">Error de interfaz</p>
          <h1 className="mt-3 font-display text-5xl text-ink">No se pudo cargar la vista</h1>
          <p className="mt-4 text-moss">
            La sesion local o una vista produjo un error. Puedes limpiar la sesion y volver al login.
          </p>
          {this.state.message && (
            <pre className="mt-4 overflow-auto rounded-2xl bg-sand p-4 text-xs text-ink">
              {this.state.message}
            </pre>
          )}
          <button
            type="button"
            className="mt-6 rounded-2xl bg-ink px-5 py-3 font-semibold text-white"
            onClick={() => this.resetSession()}
          >
            Limpiar sesion y volver
          </button>
        </section>
      </main>
    );
  }
}

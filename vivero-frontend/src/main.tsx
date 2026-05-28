import "./polyfills";
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import "./styles.css";

type BoundaryState = {
  errorMessage: string | null;
};

class AppErrorBoundary extends React.Component<React.PropsWithChildren, BoundaryState> {
  constructor(props: React.PropsWithChildren) {
    super(props);
    this.state = { errorMessage: null };
  }

  static getDerivedStateFromError(error: unknown): BoundaryState {
    const message = error instanceof Error ? error.stack || error.message : String(error);
    return { errorMessage: message };
  }

  componentDidCatch(error: unknown) {
    console.error("Frontend runtime error:", error);
  }

  render() {
    if (this.state.errorMessage) {
      return (
        <main className="grid min-h-screen place-items-center px-6">
          <section className="w-full max-w-4xl rounded-[2rem] bg-white p-8 shadow-xl">
            <p className="text-sm uppercase tracking-[0.24em] text-moss">Frontend Error</p>
            <h1 className="mt-4 font-display text-4xl text-ink">La aplicación falló al renderizar</h1>
            <pre className="mt-6 overflow-auto rounded-3xl bg-sand p-4 text-sm text-ink whitespace-pre-wrap">
              {this.state.errorMessage}
            </pre>
          </section>
        </main>
      );
    }

    return this.props.children;
  }
}

window.addEventListener("error", (event) => {
  console.error("Window error event:", event.error || event.message);
});

window.addEventListener("unhandledrejection", (event) => {
  console.error("Unhandled promise rejection:", event.reason);
});

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <AppErrorBoundary>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </AppErrorBoundary>
  </React.StrictMode>,
);

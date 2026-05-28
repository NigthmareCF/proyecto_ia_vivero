import React from "react";

type RenderGuardProps = React.PropsWithChildren<{
  title: string;
}>;

type RenderGuardState = {
  errorMessage: string | null;
};

class RenderGuardBoundary extends React.Component<RenderGuardProps, RenderGuardState> {
  constructor(props: RenderGuardProps) {
    super(props);
    this.state = { errorMessage: null };
  }

  static getDerivedStateFromError(error: unknown): RenderGuardState {
    const message = error instanceof Error ? error.stack || error.message : String(error);
    return { errorMessage: message };
  }

  componentDidCatch(error: unknown) {
    console.error(`RenderGuard error in ${this.props.title}:`, error);
  }

  render() {
    if (this.state.errorMessage) {
      return (
        <section className="rounded-[2rem] border border-alert/20 bg-white p-6 shadow-sm">
          <p className="text-xs uppercase tracking-[0.18em] text-alert">Modulo con error</p>
          <h2 className="mt-2 font-display text-2xl text-ink">{this.props.title}</h2>
          <pre className="mt-4 overflow-auto rounded-3xl bg-sand p-4 text-sm text-ink whitespace-pre-wrap">
            {this.state.errorMessage}
          </pre>
        </section>
      );
    }

    return this.props.children;
  }
}

export function RenderGuard({ title, children }: RenderGuardProps) {
  return <RenderGuardBoundary title={title}>{children}</RenderGuardBoundary>;
}

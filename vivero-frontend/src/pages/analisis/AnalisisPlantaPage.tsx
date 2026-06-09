import { useState } from "react";
import { AnalisisPlanta } from "../../components/analisis/AnalisisPlanta";
import { DeepAnalysisPanel } from "../../components/analisis/DeepAnalysisPanel";
import { ManualAnalysisPanel } from "../../components/analisis/ManualAnalysisPanel";

export function AnalisisPlantaPage() {
  const [mode, setMode] = useState<"tests" | "manual" | "deep">("tests");

  return (
    <section className="space-y-6">
      <nav className="flex flex-wrap gap-3 rounded-[2rem] bg-white p-4 shadow-sm">
        {[
          ["tests", "Pruebas"],
          ["manual", "Registro manual"],
          ["deep", "Profundo"],
        ].map(([value, label]) => (
          <button
            key={value}
            type="button"
            onClick={() => setMode(value as "tests" | "manual" | "deep")}
            className={`rounded-2xl px-5 py-3 text-sm font-semibold transition ${mode === value ? "bg-clay text-white" : "bg-sand text-ink"}`}
          >
            {label}
          </button>
        ))}
      </nav>
      {mode === "tests" ? <AnalisisPlanta /> : null}
      {mode === "manual" ? <ManualAnalysisPanel /> : null}
      {mode === "deep" ? <DeepAnalysisPanel /> : null}
    </section>
  );
}

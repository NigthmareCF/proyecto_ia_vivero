import { useState } from "react";
import { analizarPlanta } from "../../api/analisisApi";
import { useAnalisisWebSocket } from "../../hooks/useAnalisisWebSocket";
import { PlantReportCard } from "./PlantReportCard";

function toBase64(file: File) {
  return new Promise<{ mimeType: string; imagenBase64: string }>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = String(reader.result);
      const [, payload] = result.split(",");
      if (!payload) {
        reject(new Error("No se pudo convertir la imagen a base64"));
        return;
      }
      resolve({ mimeType: file.type, imagenBase64: payload });
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

export function AnalisisPlanta() {
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [observaciones, setObservaciones] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useAnalisisWebSocket(setResult);

  async function handleAnalyze() {
    if (!file) return;
    setLoading(true);
    setErrorMessage(null);

    try {
      const image = await toBase64(file);
      const response = await analizarPlanta({
        ...image,
        observacionesOperador: observaciones,
      });
      setResult(response);
    } catch (error) {
      const message = error instanceof Error ? error.message : "No se pudo completar el analisis";
      setErrorMessage(message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
      <div className="rounded-[2rem] bg-white p-6 shadow-sm">
        <h2 className="font-display text-3xl text-ink">Analisis de planta</h2>
        <p className="mt-2 text-sm text-moss">Una sola casilla libre para observaciones del operador.</p>
        <input
          className="mt-4 w-full rounded-2xl border border-ink/10 px-4 py-3"
          type="file"
          accept="image/*"
          onChange={(event) => setFile(event.target.files?.[0] ?? null)}
        />
        <textarea
          className="mt-4 min-h-40 w-full rounded-2xl border border-ink/10 px-4 py-3"
          placeholder="Describa lo que observa en la planta..."
          value={observaciones}
          onChange={(event) => setObservaciones(event.target.value)}
        />
        <button
          type="button"
          onClick={handleAnalyze}
          className="mt-4 rounded-2xl bg-clay px-5 py-3 font-semibold text-white"
          disabled={!file || loading}
        >
          {loading ? "Analizando..." : "Analizar planta"}
        </button>
        {errorMessage ? <p className="mt-3 text-sm text-alert">{errorMessage}</p> : null}
      </div>
      <PlantReportCard result={result} />
    </section>
  );
}

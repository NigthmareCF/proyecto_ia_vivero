import { useState } from "react";
import { getReportPdf, notifyReport } from "../../api/reportsApi";

type Props = {
  report: any;
};

export function ReportCard({ report }: Props) {
  const [opening, setOpening] = useState(false);
  const [sending, setSending] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function handleOpenPdf() {
    const previewWindow = window.open("", "_blank");
    if (previewWindow) previewWindow.opener = null;
    setOpening(true);
    setMessage(null);
    try {
      const blob = await getReportPdf(report.id);
      const url = URL.createObjectURL(blob);
      if (previewWindow) {
        previewWindow.location.href = url;
      } else {
        window.open(url, "_blank", "noopener,noreferrer");
      }
      window.setTimeout(() => URL.revokeObjectURL(url), 60_000);
    } catch {
      previewWindow?.close();
      setMessage("No se pudo abrir el PDF.");
    } finally {
      setOpening(false);
    }
  }

  async function handleSend() {
    setSending(true);
    setMessage(null);
    try {
      const sent = await notifyReport(report.id);
      setMessage(`Reporte enviado por ${sent} canal(es).`);
    } catch {
      setMessage("No se pudo enviar el reporte. Revise los canales activos.");
    } finally {
      setSending(false);
    }
  }

  return (
    <article className="rounded-[2rem] bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.16em] text-clay">Reporte #{report.id}</p>
          <h3 className="mt-1 font-semibold">{report.title}</h3>
        </div>
        <div className="flex flex-wrap gap-2">
          <button type="button" onClick={handleOpenPdf} disabled={opening} className="rounded-full bg-sand px-3 py-1 text-xs font-semibold text-ink disabled:opacity-50">
            {opening ? "Abriendo..." : "Ver PDF"}
          </button>
          <button type="button" onClick={handleSend} disabled={sending} className="rounded-full bg-clay px-3 py-1 text-xs font-semibold text-white disabled:opacity-50">
            {sending ? "Enviando..." : "Enviar"}
          </button>
        </div>
      </div>
      <p className="mt-2 text-sm text-moss">{report.summary}</p>
      <div className="mt-4 grid grid-cols-3 gap-3 text-sm">
        <div className="rounded-2xl bg-sand p-3">
          <p className="text-xs uppercase tracking-[0.14em] text-moss">Sano</p>
          <strong>{report.healthyCount ?? 0}</strong>
        </div>
        <div className="rounded-2xl bg-sand p-3">
          <p className="text-xs uppercase tracking-[0.14em] text-moss">Atencion</p>
          <strong>{report.attentionCount ?? 0}</strong>
        </div>
        <div className="rounded-2xl bg-sand p-3">
          <p className="text-xs uppercase tracking-[0.14em] text-moss">Peligro</p>
          <strong>{report.dangerCount ?? 0}</strong>
        </div>
        <div className="rounded-2xl bg-sand p-3">
          <p className="text-xs uppercase tracking-[0.14em] text-moss">Manual</p>
          <strong>{report.manualReviewCount ?? 0}</strong>
        </div>
        <div className="rounded-2xl bg-sand p-3">
          <p className="text-xs uppercase tracking-[0.14em] text-moss">Inconclusa</p>
          <strong>{report.inconclusiveCount ?? 0}</strong>
        </div>
        <div className="rounded-2xl bg-sand p-3">
          <p className="text-xs uppercase tracking-[0.14em] text-moss">Total</p>
          <strong>{report.observationsCount ?? 0}</strong>
        </div>
      </div>
      {message ? <p className="mt-3 text-sm text-moss">{message}</p> : null}
    </article>
  );
}

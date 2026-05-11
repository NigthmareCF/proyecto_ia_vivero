import { useState } from "react";
import { getReportPdfBlob } from "../../api/reportsApi";

type Props = {
  report: any;
};

export function ReportCard({ report }: Props) {
  const [openingPdf, setOpeningPdf] = useState(false);

  async function handleOpenPdf() {
    try {
      setOpeningPdf(true);
      const blob = await getReportPdfBlob(report.id);
      const url = window.URL.createObjectURL(blob);
      const opened = window.open(url, "_blank", "noopener,noreferrer");

      if (!opened) {
        const link = document.createElement("a");
        link.href = url;
        link.download = `report-${report.id}.pdf`;
        document.body.appendChild(link);
        link.click();
        link.remove();
      }

      window.setTimeout(() => window.URL.revokeObjectURL(url), 60_000);
    } finally {
      setOpeningPdf(false);
    }
  }

  return (
    <article className="rounded-[2rem] bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.16em] text-clay">Reporte #{report.id}</p>
          <h3 className="mt-1 font-semibold">{report.title}</h3>
        </div>
        <button
          type="button"
          className="rounded-full bg-sand px-3 py-1 text-xs font-semibold text-ink"
          onClick={() => void handleOpenPdf()}
          disabled={openingPdf}
        >
          {openingPdf ? "Abriendo..." : "Ver PDF"}
        </button>
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
    </article>
  );
}

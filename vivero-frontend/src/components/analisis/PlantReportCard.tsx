type Props = {
  result: any;
};

export function PlantReportCard({ result }: Props) {
  if (!result) return null;

  return (
    <article className="rounded-[2rem] bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between">
        <span className="rounded-full bg-ink px-3 py-1 text-xs text-white">{result.estadoGeneral}</span>
        <span className="text-sm text-moss">Urgencia {result.urgencia}</span>
      </div>
      <div className="mt-4 h-3 rounded-full bg-sand">
        <div className="h-3 rounded-full bg-clay" style={{ width: `${(result.confianza ?? 0) * 100}%` }} />
      </div>
      <p className="mt-4 text-sm text-moss">{result.diagnostico}</p>
      <ul className="mt-4 list-disc pl-5 text-sm">
        {(result.hallazgos ?? []).map((item: string) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
      <ol className="mt-4 list-decimal pl-5 text-sm">
        {(result.recomendaciones ?? []).map((item: string) => (
          <li key={item}>{item}</li>
        ))}
      </ol>
    </article>
  );
}

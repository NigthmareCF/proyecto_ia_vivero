type Props = {
  report: any;
};

export function ReportCard({ report }: Props) {
  return (
    <article className="rounded-[2rem] bg-white p-5 shadow-sm">
      <h3 className="font-semibold">{report.title}</h3>
      <p className="mt-2 text-sm text-moss">{report.summary}</p>
      <p className="mt-3 text-xs uppercase tracking-[0.16em] text-clay">
        observaciones {report.observationsCount}
      </p>
    </article>
  );
}

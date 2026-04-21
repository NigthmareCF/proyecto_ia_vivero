import { useEffect, useState } from "react";
import { getNotificationConfigs, getReports } from "../../api/reportsApi";
import { NotificationConfigForm } from "../../components/reports/NotificationConfigForm";
import { ReportCard } from "../../components/reports/ReportCard";

export function ReportsPage() {
  const [reports, setReports] = useState<any[]>([]);
  const [configs, setConfigs] = useState<any[]>([]);

  useEffect(() => {
    getReports().then(setReports).catch(() => setReports([]));
    getNotificationConfigs().then(setConfigs).catch(() => setConfigs([]));
  }, []);

  return (
    <section className="grid gap-6">
      <div className="grid gap-4 md:grid-cols-2">
        {reports.map((report) => (
          <ReportCard key={report.id} report={report} />
        ))}
      </div>
      <NotificationConfigForm configs={configs} />
    </section>
  );
}

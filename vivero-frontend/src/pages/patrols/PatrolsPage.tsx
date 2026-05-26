import { useEffect, useState } from "react";
import { getPatrols } from "../../api/patrolsApi";

export function PatrolsPage() {
  const [patrols, setPatrols] = useState<any[]>([]);

  useEffect(() => {
    getPatrols().then(setPatrols).catch(() => setPatrols([]));
  }, []);

  return (
    <section className="rounded-[2rem] bg-white p-6 shadow-sm">
      <h2 className="font-display text-3xl">Patrullajes</h2>
      <div className="mt-4 space-y-3">
        {patrols.map((patrol) => (
          <article key={patrol.id} className="rounded-3xl border border-ink/10 p-4">
            <p className="font-semibold">Patrullaje #{patrol.id}</p>
            <p className="text-sm text-moss">{patrol.status}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

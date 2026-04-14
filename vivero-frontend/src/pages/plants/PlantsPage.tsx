import { useEffect, useState } from "react";
import { getPlants } from "../../api/plantsApi";

export function PlantsPage() {
  const [plants, setPlants] = useState<any[]>([]);

  useEffect(() => {
    getPlants().then(setPlants).catch(() => setPlants([]));
  }, []);

  return (
    <section className="rounded-[2rem] bg-white p-6 shadow-sm">
      <h2 className="font-display text-3xl">Plantas</h2>
      <div className="mt-4 grid gap-4 md:grid-cols-2">
        {plants.map((plant) => (
          <article key={plant.id ?? plant.qrCode} className="rounded-3xl border border-ink/10 p-4">
            <p className="font-semibold">{plant.name ?? plant.qrCode}</p>
            <p className="text-sm text-moss">{plant.location ?? "Sin ubicacion"}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
